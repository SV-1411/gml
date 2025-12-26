import { useState } from 'react'
import { batchApi } from '../../services/batchApi'

interface BatchOperationsProps {
  selectedMemories: string[]
  onSuccess: () => void
  onClose: () => void
}

const BatchOperations = ({ selectedMemories, onSuccess, onClose }: BatchOperationsProps) => {
  const [activeTab, setActiveTab] = useState<'delete' | 'export' | 'consolidate' | 'reindex'>('delete')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // Delete options
  const [softDelete, setSoftDelete] = useState(true)
  const [cascade, setCascade] = useState(true)

  // Export options
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json')
  const [includeVersions, setIncludeVersions] = useState(false)
  const [compress, setCompress] = useState(true)

  // Consolidate options
  const [similarityThreshold, setSimilarityThreshold] = useState(0.85)
  const [dryRun, setDryRun] = useState(true)
  const [mergeStrategy, setMergeStrategy] = useState<'newest' | 'oldest' | 'longest'>('newest')

  // Reindex options
  const [batchSize, setBatchSize] = useState(100)
  const [forceReindex, setForceReindex] = useState(false)

  const handleBatchDelete = async () => {
    if (selectedMemories.length === 0) {
      setError('Please select at least one memory to delete')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await batchApi.delete({
        context_ids: selectedMemories,
        soft_delete: softDelete,
        cascade: cascade,
      })
      setResult(response)
      if (response.total_deleted > 0) {
        setTimeout(() => {
          onSuccess()
          onClose()
        }, 1500)
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to delete memories')
    } finally {
      setLoading(false)
    }
  }

  const handleBatchExport = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const blob = await batchApi.export({
        context_ids: selectedMemories.length > 0 ? selectedMemories : undefined,
        format: exportFormat,
        include_versions: includeVersions,
        compress: compress,
      })

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      a.download = `memories_export_${timestamp}.${exportFormat}${compress ? '.gz' : ''}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      setResult({ success: true, message: 'Export downloaded successfully' })
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to export memories')
    } finally {
      setLoading(false)
    }
  }

  const handleConsolidate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await batchApi.consolidate({
        similarity_threshold: similarityThreshold,
        dry_run: dryRun,
        merge_strategy: mergeStrategy,
      })
      setResult(response)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to consolidate memories')
    } finally {
      setLoading(false)
    }
  }

  const handleReindex = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await batchApi.reindex({
        context_ids: selectedMemories.length > 0 ? selectedMemories : undefined,
        batch_size: batchSize,
        force: forceReindex,
      })
      setResult(response)
      if (response.total_indexed > 0) {
        setTimeout(() => {
          onSuccess()
        }, 1500)
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to reindex memories')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Batch Operations
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Close
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="mb-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex gap-4">
              <button
                onClick={() => setActiveTab('delete')}
                className={`px-4 py-2 font-medium text-sm ${
                  activeTab === 'delete'
                    ? 'border-b-2 border-primary-600 text-primary-600'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Delete ({selectedMemories.length})
              </button>
              <button
                onClick={() => setActiveTab('export')}
                className={`px-4 py-2 font-medium text-sm ${
                  activeTab === 'export'
                    ? 'border-b-2 border-primary-600 text-primary-600'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Export
              </button>
              <button
                onClick={() => setActiveTab('consolidate')}
                className={`px-4 py-2 font-medium text-sm ${
                  activeTab === 'consolidate'
                    ? 'border-b-2 border-primary-600 text-primary-600'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Consolidate
              </button>
              <button
                onClick={() => setActiveTab('reindex')}
                className={`px-4 py-2 font-medium text-sm ${
                  activeTab === 'reindex'
                    ? 'border-b-2 border-primary-600 text-primary-600'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Reindex
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-800 dark:text-red-200 text-sm">
              {error}
            </div>
          )}

          {result && (
            <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded text-green-800 dark:text-green-200 text-sm">
              <div className="font-semibold mb-2">Operation Result:</div>
              <pre className="text-xs overflow-auto max-h-40">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}

          {activeTab === 'delete' && (
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Delete {selectedMemories.length} selected memories
                </p>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={softDelete}
                      onChange={(e) => setSoftDelete(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Soft delete (archive)</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={cascade}
                      onChange={(e) => setCascade(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Cascade delete (versions, vectors)</span>
                  </label>
                </div>
              </div>
              <button
                onClick={handleBatchDelete}
                disabled={loading || selectedMemories.length === 0}
                className="w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Deleting...' : `Delete ${selectedMemories.length} Memories`}
              </button>
            </div>
          )}

          {activeTab === 'export' && (
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Export Format
                  </label>
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value as 'json' | 'csv')}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                  </select>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeVersions}
                    onChange={(e) => setIncludeVersions(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Include version history</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={compress}
                    onChange={(e) => setCompress(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Compress export</span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {selectedMemories.length > 0
                    ? `Exporting ${selectedMemories.length} selected memories`
                    : 'Exporting all memories'}
                </p>
              </div>
              <button
                onClick={handleBatchExport}
                disabled={loading}
                className="w-full px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Exporting...' : 'Export Memories'}
              </button>
            </div>
          )}

          {activeTab === 'consolidate' && (
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Similarity Threshold: {Math.round(similarityThreshold * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={similarityThreshold}
                    onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Merge Strategy
                  </label>
                  <select
                    value={mergeStrategy}
                    onChange={(e) => setMergeStrategy(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="newest">Newest (keep most recent)</option>
                    <option value="oldest">Oldest (keep original)</option>
                    <option value="longest">Longest (keep most complete)</option>
                  </select>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={(e) => setDryRun(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Dry run (preview only)</span>
                </label>
              </div>
              <button
                onClick={handleConsolidate}
                disabled={loading}
                className="w-full px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Analyzing...' : 'Find and Consolidate Duplicates'}
              </button>
            </div>
          )}

          {activeTab === 'reindex' && (
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Batch Size: {batchSize}
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="500"
                    step="10"
                    value={batchSize}
                    onChange={(e) => setBatchSize(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={forceReindex}
                    onChange={(e) => setForceReindex(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Force reindex (even if already indexed)</span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {selectedMemories.length > 0
                    ? `Reindexing ${selectedMemories.length} selected memories`
                    : 'Reindexing all memories'}
                </p>
              </div>
              <button
                onClick={handleReindex}
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Reindexing...' : 'Rebuild Search Indexes'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default BatchOperations

