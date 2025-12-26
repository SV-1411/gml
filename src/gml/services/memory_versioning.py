"""
Memory Versioning Service

Provides versioning functionality for memories including:
- Automatic version creation
- Version retrieval and history
- Diff generation
- Rollback support
- Version compression and archival

Usage:
    >>> from src.gml.services.memory_versioning import get_versioning_service
    >>> 
    >>> service = await get_versioning_service()
    >>> 
    >>> # Create version automatically
    >>> await service.create_version(memory, author_id="user-123")
    >>> 
    >>> # Get version history
    >>> versions = await service.get_version_history("ctx-123", limit=10)
    >>> 
    >>> # Generate diff
    >>> diff = await service.generate_diff("ctx-123", version1=1, version2=2)
"""

import gzip
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import difflib
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Memory, MemoryVersion

logger = logging.getLogger(__name__)

# Configuration
MAX_VERSIONS_PER_MEMORY = 50
VERSION_COMPRESSION_THRESHOLD = 10000  # Compress if text > 10KB


class MemoryVersioningService:
    """
    Service for managing memory versions with automatic versioning,
    diff generation, and rollback support.
    """

    def __init__(self, max_versions: int = MAX_VERSIONS_PER_MEMORY) -> None:
        """
        Initialize memory versioning service.

        Args:
            max_versions: Maximum number of versions to keep per memory
        """
        self.max_versions = max_versions
        logger.info(f"MemoryVersioningService initialized (max_versions={max_versions})")

    async def create_version(
        self,
        memory: Memory,
        author_id: Optional[str] = None,
        change_type: str = "modified",
        db: Optional[AsyncSession] = None,
    ) -> MemoryVersion:
        """
        Create a new version of a memory.

        Automatically increments version number and stores complete snapshot.
        Archives old versions if limit is exceeded.

        Args:
            memory: Memory instance to version
            author_id: ID of user/agent creating the version
            change_type: Type of change (added, modified, deleted)
            db: Database session

        Returns:
            Created MemoryVersion instance

        Raises:
            ValueError: If memory is invalid
        """
        if not db:
            raise ValueError("Database session required")

        try:
            # Get next version number
            result = await db.execute(
                select(func.max(MemoryVersion.version_number)).where(
                    MemoryVersion.context_id == memory.context_id
                )
            )
            max_version = result.scalar_one_or_none()
            next_version = (max_version or 0) + 1

            # Extract text from content
            full_text = self._extract_text_from_content(memory.content or {})

            # Compress if needed
            compressed = False
            content_data = memory.content
            if len(full_text) > VERSION_COMPRESSION_THRESHOLD:
                compressed = True
                # Store compressed text
                full_text = self._compress_text(full_text)

            # Create version
            version = MemoryVersion(
                context_id=memory.context_id,
                version_number=next_version,
                full_memory_text=full_text,
                content=content_data,
                version_metadata={
                    "memory_type": memory.memory_type,
                    "visibility": memory.visibility,
                    "tags": memory.tags,
                },
                change_type=change_type,
                author_id=author_id or memory.agent_id,
                parent_version_id=None,  # Will be set if previous version exists
                compressed=compressed,
                created_at=datetime.now(timezone.utc),
            )

            # Set parent version
            if next_version > 1:
                parent_result = await db.execute(
                    select(MemoryVersion).where(
                        and_(
                            MemoryVersion.context_id == memory.context_id,
                            MemoryVersion.version_number == next_version - 1,
                        )
                    )
                )
                parent = parent_result.scalar_one_or_none()
                if parent:
                    version.parent_version_id = parent.id

            # Generate semantic summary
            if next_version > 1:
                version.semantic_summary = await self._generate_summary(
                    memory, next_version - 1, db
                )

            db.add(version)
            await db.commit()
            await db.refresh(version)

            # Archive old versions if needed
            await self._archive_old_versions(memory.context_id, db)

            logger.info(
                f"Created version {next_version} for memory {memory.context_id}"
            )
            return version

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating version: {str(e)}")
            raise

    async def get_version_history(
        self,
        context_id: str,
        limit: int = 50,
        offset: int = 0,
        db: Optional[AsyncSession] = None,
    ) -> List[MemoryVersion]:
        """
        Get version history for a memory.

        Args:
            context_id: Memory context ID
            limit: Maximum number of versions to return
            offset: Offset for pagination
            db: Database session

        Returns:
            List of MemoryVersion instances (newest first)
        """
        if not db:
            raise ValueError("Database session required")

        try:
            result = await db.execute(
                select(MemoryVersion)
                .where(MemoryVersion.context_id == context_id)
                .order_by(MemoryVersion.version_number.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            return []

    async def get_version(
        self,
        context_id: str,
        version_number: int,
        db: Optional[AsyncSession] = None,
    ) -> Optional[MemoryVersion]:
        """
        Get a specific version of a memory.

        Args:
            context_id: Memory context ID
            version_number: Version number to retrieve
            db: Database session

        Returns:
            MemoryVersion instance or None if not found
        """
        if not db:
            raise ValueError("Database session required")

        try:
            result = await db.execute(
                select(MemoryVersion).where(
                    and_(
                        MemoryVersion.context_id == context_id,
                        MemoryVersion.version_number == version_number,
                    )
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting version: {str(e)}")
            return None

    async def revert_to_version(
        self,
        context_id: str,
        version_number: int,
        author_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> Memory:
        """
        Revert memory to a specific version.

        Creates a new version with content from the specified version.

        Args:
            context_id: Memory context ID
            version_number: Version number to revert to
            author_id: ID of user/agent performing revert
            db: Database session

        Returns:
            Updated Memory instance

        Raises:
            ValueError: If version not found
        """
        if not db:
            raise ValueError("Database session required")

        try:
            # Get target version
            target_version = await self.get_version(context_id, version_number, db)
            if not target_version:
                raise ValueError(f"Version {version_number} not found for memory {context_id}")

            # Get current memory
            result = await db.execute(
                select(Memory).where(Memory.context_id == context_id)
            )
            memory = result.scalar_one_or_none()
            if not memory:
                raise ValueError(f"Memory {context_id} not found")

            # Decompress if needed
            content = target_version.content
            if target_version.compressed and target_version.full_memory_text:
                # Restore from compressed text
                decompressed_text = self._decompress_text(target_version.full_memory_text)
                # Reconstruct content from text if needed
                if not content:
                    content = {"text": decompressed_text}

            # Restore memory content
            memory.content = content
            if target_version.version_metadata:
                if "memory_type" in target_version.version_metadata:
                    memory.memory_type = target_version.version_metadata["memory_type"]
                if "visibility" in target_version.version_metadata:
                    memory.visibility = target_version.version_metadata["visibility"]
                if "tags" in target_version.version_metadata:
                    memory.tags = target_version.version_metadata["tags"]

            await db.commit()
            await db.refresh(memory)

            # Create new version with reverted content
            await self.create_version(
                memory,
                author_id=author_id,
                change_type="reverted",
                db=db,
            )

            logger.info(
                f"Reverted memory {context_id} to version {version_number}"
            )
            return memory

        except Exception as e:
            await db.rollback()
            logger.error(f"Error reverting to version: {str(e)}")
            raise

    async def generate_diff(
        self,
        context_id: str,
        version1: int,
        version2: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Generate diff between two versions of a memory.

        Args:
            context_id: Memory context ID
            version1: First version number
            version2: Second version number (None = current)
            db: Database session

        Returns:
            Dictionary with diff information including:
            - unified_diff: Unified diff format
            - side_by_side: Side-by-side comparison
            - statistics: Change statistics
            - semantic_changes: List of semantic changes
        """
        if not db:
            raise ValueError("Database session required")

        try:
            # Get versions
            v1 = await self.get_version(context_id, version1, db)
            if not v1:
                raise ValueError(f"Version {version1} not found")

            if version2 is None:
                # Compare with current memory
                result = await db.execute(
                    select(Memory).where(Memory.context_id == context_id)
                )
                memory = result.scalar_one_or_none()
                if not memory:
                    raise ValueError(f"Memory {context_id} not found")
                text2 = self._extract_text_from_content(memory.content or {})
                v2_version = None
            else:
                v2 = await self.get_version(context_id, version2, db)
                if not v2:
                    raise ValueError(f"Version {version2} not found")
                v2_version = v2
                text2 = self._get_version_text(v2)

            text1 = self._get_version_text(v1)

            # Generate unified diff
            unified_diff = "\n".join(
                difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=f"Version {version1}",
                    tofile=f"Version {version2 or 'current'}",
                    lineterm="",
                )
            )

            # Generate side-by-side comparison
            side_by_side = list(
                difflib.unified_diff(
                    text1.splitlines(),
                    text2.splitlines(),
                    lineterm="",
                )
            )

            # Calculate statistics
            diff_lines = list(difflib.unified_diff(
                text1.splitlines(),
                text2.splitlines(),
                lineterm="",
            ))
            
            additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
            deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
            modifications = sum(1 for line in diff_lines if line.startswith(" ") and line.strip() and len(line) > 1)

            statistics = {
                "additions": additions,
                "deletions": deletions,
                "modifications": modifications,
                "total_changes": additions + deletions,
            }

            return {
                "context_id": context_id,
                "version1": version1,
                "version2": version2,
                "unified_diff": unified_diff,
                "side_by_side": side_by_side[:100],  # Limit output
                "statistics": statistics,
                "semantic_changes": [],  # Could be enhanced with NLP
            }

        except Exception as e:
            logger.error(f"Error generating diff: {str(e)}")
            raise

    def _extract_text_from_content(self, content: Dict[str, Any]) -> str:
        """Extract text from memory content dictionary."""
        if not content:
            return ""

        # Try common text fields
        text_fields = ["text", "content", "message", "description", "summary"]
        for field in text_fields:
            if field in content and isinstance(content[field], str):
                return content[field]

        # If no text field, stringify
        return json.dumps(content, indent=2)

    def _get_version_text(self, version: MemoryVersion) -> str:
        """Get text content from version, decompressing if needed."""
        if version.compressed and version.full_memory_text:
            return self._decompress_text(version.full_memory_text)
        elif version.full_memory_text:
            return version.full_memory_text
        elif version.content:
            return self._extract_text_from_content(version.content)
        return ""

    def _compress_text(self, text: str) -> str:
        """Compress text using gzip."""
        try:
            compressed = gzip.compress(text.encode("utf-8"))
            return compressed.hex()  # Store as hex string
        except Exception as e:
            logger.warning(f"Error compressing text: {str(e)}")
            return text

    def _decompress_text(self, compressed_hex: str) -> str:
        """Decompress text from hex string."""
        try:
            compressed_bytes = bytes.fromhex(compressed_hex)
            decompressed = gzip.decompress(compressed_bytes)
            return decompressed.decode("utf-8")
        except Exception as e:
            logger.warning(f"Error decompressing text: {str(e)}")
            return compressed_hex  # Return as-is if decompression fails

    async def _generate_summary(
        self,
        memory: Memory,
        previous_version: int,
        db: AsyncSession,
    ) -> str:
        """Generate semantic summary of changes (placeholder)."""
        # This could be enhanced with NLP/LLM to generate better summaries
        return f"Updated memory content (version {previous_version} -> current)"

    async def _archive_old_versions(
        self,
        context_id: str,
        db: AsyncSession,
    ) -> None:
        """Archive versions beyond the limit."""
        try:
            # Count versions
            result = await db.execute(
                select(func.count(MemoryVersion.id)).where(
                    MemoryVersion.context_id == context_id,
                    MemoryVersion.is_archived == False,
                )
            )
            count = result.scalar_one_or_none() or 0

            if count > self.max_versions:
                # Get oldest versions to archive
                result = await db.execute(
                    select(MemoryVersion)
                    .where(
                        and_(
                            MemoryVersion.context_id == context_id,
                            MemoryVersion.is_archived == False,
                        )
                    )
                    .order_by(MemoryVersion.version_number.asc())
                    .limit(count - self.max_versions)
                )
                old_versions = result.scalars().all()

                for version in old_versions:
                    version.is_archived = True

                await db.commit()
                logger.info(
                    f"Archived {len(old_versions)} old versions for {context_id}"
                )

        except Exception as e:
            logger.warning(f"Error archiving versions: {str(e)}")


# Singleton instance
_versioning_service: Optional[MemoryVersioningService] = None


async def get_versioning_service() -> MemoryVersioningService:
    """Get or create the singleton versioning service instance."""
    global _versioning_service

    if _versioning_service is None:
        _versioning_service = MemoryVersioningService()
        logger.info("Memory versioning service singleton created")

    return _versioning_service


__all__ = [
    "MemoryVersioningService",
    "get_versioning_service",
    "MAX_VERSIONS_PER_MEMORY",
]

