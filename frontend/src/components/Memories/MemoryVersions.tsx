import { useState, useEffect } from 'react'
import { memoryVersionsApi } from '../../services/api'

interface Version {
  id: number
  context_id: string
  version_number: number
  change_type: string
  author_id: string | null
  semantic_summary: string | null
  parent_version_id: number | null
  is_archived: boolean
  compressed: boolean
  created_at: string
}

interface Diff {
  context_id: string
  version1: number
  version2: number | null
  unified_diff: string
  side_by_side: string[]
  statistics: {
    additions: number
    deletions: number
    modifications: number
    total_changes: number
  }
}

interface MemoryVersionsProps {
  contextId: string
  onClose: () => void
}

const MemoryVersions = ({ contextId, onClose }: MemoryVersionsProps) => {
  const [versions, setVersions] = useState<Version[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null)
  const [diffVersion1, setDiffVersion1] = useState<number | null>(null)
  const [diffVersion2, setDiffVersion2] = useState<number | null>(null)
  const [diff, setDiff] = useState<Diff | null>(null)
  const [showDiff, setShowDiff] = useState(false)
  const [reverting, setReverting] = useState(false)

  useEffect(() => {
    loadVersions()
  }, [contextId])

  const loadVersions = async () => {
    setLoading(true)
    try {
      const response = await memoryVersionsApi.getHistory(contextId, { limit: 50 })
      setVersions(response.versions || [])
    } catch (error: any) {
      console.error('Failed to load versions:', error)
      alert(`Failed to load versions: ${error?.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRevert = async (versionNumber: number) => {
    if (!confirm(`Are you sure you want to revert to version ${versionNumber}?`)) {
      return
    }

    setReverting(true)
    try {
      await memoryVersionsApi.revert(contextId, versionNumber)
      alert(`Successfully reverted to version ${versionNumber}`)
      await loadVersions()
      onClose() // Close modal after revert
    } catch (error: any) {
      console.error('Failed to revert:', error)
      alert(`Failed to revert: ${error?.response?.data?.detail || error.message}`)
    } finally {
      setReverting(false)
    }
  }

  const handleShowDiff = async () => {
    if (!diffVersion1) {
      alert('Please select version 1')
      return
    }

    setLoading(true)
    try {
      const diffData = await memoryVersionsApi.getDiff(contextId, diffVersion1, diffVersion2 || undefined)
      setDiff(diffData)
      setShowDiff(true)
    } catch (error: any) {
      console.error('Failed to load diff:', error)
      alert(`Failed to load diff: ${error?.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const getChangeTypeColor = (type: string) => {
    switch (type) {
      case 'added':
        return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
      case 'modified':
        return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
      case 'deleted':
        return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
      case 'reverted':
        return 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Version History
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {contextId}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && !diff ? (
            <div className="text-center py-8">
              <p className="text-gray-600 dark:text-gray-400">Loading versions...</p>
            </div>
          ) : showDiff && diff ? (
            /* Diff View */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Diff: Version {diff.version1} vs {diff.version2 || 'Current'}
                </h3>
                <button
                  onClick={() => {
                    setShowDiff(false)
                    setDiff(null)
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  Back to List
                </button>
              </div>

              {/* Statistics */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Additions</p>
                  <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{diff.statistics.additions}</p>
                </div>
                <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Deletions</p>
                  <p className="text-lg font-bold text-red-600 dark:text-red-400">{diff.statistics.deletions}</p>
                </div>
                <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Modifications</p>
                  <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">{diff.statistics.modifications}</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Total Changes</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{diff.statistics.total_changes}</p>
                </div>
              </div>

              {/* Unified Diff */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700 p-4">
                <pre className="text-xs font-mono text-gray-900 dark:text-gray-100 whitespace-pre-wrap overflow-x-auto">
                  {diff.unified_diff}
                </pre>
              </div>
            </div>
          ) : (
            /* Versions List */
            <div className="space-y-4">
              {/* Diff Controls */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  Compare Versions
                </h3>
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Version 1
                    </label>
                    <select
                      value={diffVersion1 || ''}
                      onChange={(e) => setDiffVersion1(parseInt(e.target.value) || null)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                    >
                      <option value="">Select version...</option>
                      {versions.map((v) => (
                        <option key={v.id} value={v.version_number}>
                          Version {v.version_number} ({v.change_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Version 2 (optional, defaults to current)
                    </label>
                    <select
                      value={diffVersion2 || ''}
                      onChange={(e) => setDiffVersion2(parseInt(e.target.value) || null)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                    >
                      <option value="">Current</option>
                      {versions.map((v) => (
                        <option key={v.id} value={v.version_number}>
                          Version {v.version_number}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={handleShowDiff}
                    disabled={!diffVersion1 || loading}
                    className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    Show Diff
                  </button>
                </div>
              </div>

              {/* Versions */}
              {versions.length === 0 ? (
                <div className="text-center py-8 text-gray-600 dark:text-gray-400">
                  No versions found
                </div>
              ) : (
                <div className="space-y-2">
                  {versions.map((version) => (
                    <div
                      key={version.id}
                      className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-4 hover:border-primary-500 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-semibold text-gray-900 dark:text-white">
                              Version {version.version_number}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs capitalize ${getChangeTypeColor(version.change_type)}`}>
                              {version.change_type}
                            </span>
                            {version.compressed && (
                              <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                Compressed
                              </span>
                            )}
                            {version.is_archived && (
                              <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                Archived
                              </span>
                            )}
                          </div>
                          {version.semantic_summary && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                              {version.semantic_summary}
                            </p>
                          )}
                          <div className="text-xs text-gray-500 dark:text-gray-500">
                            <span>By: {version.author_id || 'Unknown'}</span>
                            <span className="mx-2">•</span>
                            <span>{new Date(version.created_at).toLocaleString()}</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {version.version_number > 1 && (
                            <button
                              onClick={() => handleRevert(version.version_number)}
                              disabled={reverting}
                              className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50 text-xs font-medium"
                            >
                              {reverting ? 'Reverting...' : 'Revert'}
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setDiffVersion1(version.version_number)
                              setDiffVersion2(null)
                            }}
                            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 text-xs font-medium"
                          >
                            Compare
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MemoryVersions

