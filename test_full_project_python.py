#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for GML Project
Tests all components: Backend, Database, Redis, Qdrant, MinIO, Frontend
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

# Test results
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests: List[Dict] = []
    
    def add(self, name: str, status: str, message: str = ""):
        """Add a test result."""
        self.tests.append({
            "name": name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.skipped += 1
    
    def print_result(self, name: str, status: str, message: str = ""):
        """Print and record a test result."""
        self.add(name, status, message)
        
        if status == "PASS":
            print(f"{Colors.GREEN}✓ PASS{Colors.NC}: {name}")
            if message:
                print(f"  {Colors.GREEN}  → {message}{Colors.NC}")
        elif status == "FAIL":
            print(f"{Colors.RED}✗ FAIL{Colors.NC}: {name}")
            if message:
                print(f"  {Colors.RED}  → {message}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⊘ SKIP{Colors.NC}: {name}")
            if message:
                print(f"  {Colors.YELLOW}  → {message}{Colors.NC}")

# Global test results
results = TestResults()

async def test_http_endpoint(
    client: httpx.AsyncClient,
    url: str,
    expected_status: int = 200,
    description: str = "",
    method: str = "GET",
    headers: Optional[Dict] = None,
    json_data: Optional[Dict] = None
) -> Tuple[bool, Optional[Dict]]:
    """Test an HTTP endpoint."""
    try:
        response = await client.request(
            method,
            url,
            headers=headers or {},
            json=json_data,
            timeout=10.0
        )
        
        if response.status_code == expected_status:
            results.print_result(
                description or url,
                "PASS",
                f"HTTP {response.status_code}"
            )
            try:
                return True, response.json()
            except:
                return True, {"raw": response.text[:100]}
        else:
            results.print_result(
                description or url,
                "FAIL",
                f"Expected HTTP {expected_status}, got {response.status_code}"
            )
            return False, None
    except httpx.TimeoutException:
        results.print_result(
            description or url,
            "FAIL",
            "Request timed out"
        )
        return False, None
    except Exception as e:
        results.print_result(
            description or url,
            "FAIL",
            f"Error: {str(e)}"
        )
        return False, None

async def test_docker_service(service_name: str, description: str) -> bool:
    """Test if a Docker service is running."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if service_name in result.stdout:
            # Check if container is actually running
            status_result = subprocess.run(
                ["docker", "inspect", service_name, "--format", "{{.State.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "running" in status_result.stdout:
                results.print_result(description, "PASS", "Container is running")
                return True
            else:
                results.print_result(description, "FAIL", "Container exists but not running")
                return False
        else:
            results.print_result(description, "FAIL", "Container not found")
            return False
    except Exception as e:
        results.print_result(description, "SKIP", f"Could not check: {str(e)}")
        return False

async def test_database_connection() -> bool:
    """Test PostgreSQL database connection."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["docker", "exec", "gml-postgres", "pg_isready", "-U", "postgres"],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            results.print_result("PostgreSQL connection", "PASS", "Database accepting connections")
            return True
        else:
            results.print_result("PostgreSQL connection", "FAIL", "Database not responding")
            return False
    except Exception as e:
        results.print_result("PostgreSQL connection", "SKIP", f"Could not check: {str(e)}")
        return False

async def test_redis_connection() -> bool:
    """Test Redis connection."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["docker", "exec", "gml-redis", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "PONG" in result.stdout:
            results.print_result("Redis connection", "PASS", "Redis responding to PING")
            return True
        else:
            results.print_result("Redis connection", "FAIL", "Redis not responding")
            return False
    except Exception as e:
        results.print_result("Redis connection", "SKIP", f"Could not check: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests."""
    print("")
    print(f"{Colors.BLUE}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║     GML Project - Comprehensive Automated Test Suite         ║{Colors.NC}")
    print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")
    print("")
    
    # Environment check
    print(f"{Colors.BLUE}[1] Environment Check{Colors.NC}")
    import os
    if os.path.exists("requirements.txt") and os.path.exists("src/gml"):
        results.print_result("Project structure", "PASS", "Running from project root")
    else:
        results.print_result("Project structure", "FAIL", "Not in project root directory")
        return
    
    if os.path.exists("venv"):
        results.print_result("Virtual environment", "PASS", "venv directory exists")
    else:
        results.print_result("Virtual environment", "SKIP", "venv not found")
    
    print("")
    
    # Docker services
    print(f"{Colors.BLUE}[2] Docker Services{Colors.NC}")
    await test_docker_service("gml-postgres", "PostgreSQL container")
    await test_docker_service("gml-redis", "Redis container")
    await test_docker_service("gml-qdrant", "Qdrant container")
    await test_docker_service("gml-minio", "MinIO container")
    
    print("")
    
    # Service connectivity
    print(f"{Colors.BLUE}[3] Service Connectivity{Colors.NC}")
    await test_database_connection()
    await test_redis_connection()
    
    async with httpx.AsyncClient() as client:
        # Qdrant
        await test_http_endpoint(
            client,
            "http://localhost:6333/healthz",
            200,
            "Qdrant HTTP endpoint"
        )
        
        # MinIO
        await test_http_endpoint(
            client,
            "http://localhost:9000/minio/health/live",
            200,
            "MinIO HTTP endpoint"
        )
    
    print("")
    
    # Backend API
    print(f"{Colors.BLUE}[4] Backend API Endpoints{Colors.NC}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Basic health
        await test_http_endpoint(
            client,
            "http://localhost:8000/health",
            200,
            "Basic health endpoint"
        )
        
        # Detailed health
        success, health_data = await test_http_endpoint(
            client,
            "http://localhost:8000/api/v1/health/detailed",
            200,
            "Detailed health endpoint"
        )
        
        if success and health_data:
            all_healthy = all(
                service.get("status") == "healthy"
                for service in health_data.values()
                if isinstance(service, dict)
            )
            if all_healthy:
                print(f"  {Colors.GREEN}  → All services healthy{Colors.NC}")
            else:
                print(f"  {Colors.YELLOW}  → Some services may be unhealthy{Colors.NC}")
        
        # API docs
        await test_http_endpoint(
            client,
            "http://localhost:8000/api/docs",
            200,
            "API documentation"
        )
        
        await test_http_endpoint(
            client,
            "http://localhost:8000/api/openapi.json",
            200,
            "OpenAPI schema"
        )
        
        # Agents endpoint
        await test_http_endpoint(
            client,
            "http://localhost:8000/api/v1/agents",
            200,
            "Agents list endpoint"
        )
        
        # Ollama health
        await test_http_endpoint(
            client,
            "http://localhost:8000/api/v1/ollama/health",
            200,
            "Ollama health endpoint"
        )
    
    print("")
    
    # Frontend
    print(f"{Colors.BLUE}[5] Frontend{Colors.NC}")
    async with httpx.AsyncClient() as client:
        await test_http_endpoint(
            client,
            "http://localhost:3000",
            200,
            "Frontend homepage"
        )
    
    print("")
    
    # API Functionality
    print(f"{Colors.BLUE}[6] API Functionality{Colors.NC}")
    
    test_agent_id = f"test-agent-{int(time.time())}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Register test agent
        success, agent_data = await test_http_endpoint(
            client,
            "http://localhost:8000/api/v1/agents/register",
            201,
            "Agent registration",
            method="POST",
            headers={"Content-Type": "application/json"},
            json_data={
                "agent_id": test_agent_id,
                "name": "Test Agent",
                "version": "1.0.0",
                "description": "Automated test agent",
                "capabilities": ["testing"]
            }
        )
        
        if success:
            # Test agent retrieval
            await test_http_endpoint(
                client,
                f"http://localhost:8000/api/v1/agents/{test_agent_id}",
                200,
                "Agent retrieval",
                headers={"X-Agent-ID": test_agent_id}
            )
            
            # Test memory search
            success, _ = await test_http_endpoint(
                client,
                "http://localhost:8000/api/v1/memory/search",
                200,
                "Memory search",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": test_agent_id
                },
                json_data={"query": "test", "limit": 5}
            )
            
            if not success:
                results.print_result(
                    "Memory search",
                    "SKIP",
                    "May require valid agent ID or no memories exist"
                )
    
    print("")
    
    # Web UIs
    print(f"{Colors.BLUE}[7] Web Interfaces{Colors.NC}")
    async with httpx.AsyncClient() as client:
        await test_http_endpoint(
            client,
            "http://localhost:9001",
            200,
            "MinIO Console"
        )
        
        await test_http_endpoint(
            client,
            "http://localhost:6333/dashboard",
            200,
            "Qdrant Dashboard"
        )
    
    print("")
    
    # Summary
    print(f"{Colors.BLUE}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║                         Test Summary                         ║{Colors.NC}")
    print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")
    print("")
    print(f"  {Colors.GREEN}Passed:{Colors.NC}  {results.passed}")
    print(f"  {Colors.RED}Failed:{Colors.NC}  {results.failed}")
    print(f"  {Colors.YELLOW}Skipped:{Colors.NC} {results.skipped}")
    print("")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump({
            "summary": {
                "passed": results.passed,
                "failed": results.failed,
                "skipped": results.skipped,
                "total": len(results.tests)
            },
            "tests": results.tests,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"{Colors.CYAN}Test results saved to: test_results.json{Colors.NC}")
    print("")
    
    if results.failed == 0:
        print(f"{Colors.GREEN}✓ All critical tests passed!{Colors.NC}")
        return 0
    else:
        print(f"{Colors.RED}✗ Some tests failed. Please review the output above.{Colors.NC}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.NC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

