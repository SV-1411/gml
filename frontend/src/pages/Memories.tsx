import { useState, useEffect } from 'react'
import { memoryApi, searchApi } from '../services/api'
import MemoryForm from '../components/Memories/MemoryForm'
import MemoryVersions from '../components/Memories/MemoryVersions'
import BatchOperations from '../components/Memories/BatchOperations'

interface MemorySearchResult {
  context_id: string
  content: Record<string, any>
  similarity_score?: number
  memory_type?: 'episodic' | 'semantic' | 'procedural'
  created_by: string
  created_at: string
}

type SearchType = 'semantic' | 'keyword' | 'hybrid' | 'legacy'

const Memories = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState<SearchType>('semantic')
  const [results, setResults] = useState<MemorySearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [searchOptions, setSearchOptions] = useState({
    threshold: 0.0,
    top_k: 10,
    memory_type: '' as '' | 'episodic' | 'semantic' | 'procedural',
    conversation_id: '',
    semantic_weight: 0.7,
    keyword_weight: 0.3,
    use_cache: true,
  })
  const [executionTime, setExecutionTime] = useState<number | null>(null)
  const [showVersions, setShowVersions] = useState(false)
  const [selectedMemoryId, setSelectedMemoryId] = useState<string | null>(null)
  const [showBatchOperations, setShowBatchOperations] = useState(false)
  const [selectedMemories, setSelectedMemories] = useState<string[]>([])
  const [stats, setStats] = useState({
    total: 0,
    withFiles: 0,
    totalFileSize: 0,
    byType: { episodic: 0, semantic: 0, procedural: 0 },
  })

  const loadStats = async () => {
    const agentId = localStorage.getItem('agent_id')
    if (!agentId) return

    try {
      // Load all memories to calculate stats
      const response = await memoryApi.search({
        query: 'memory',
        limit: 100, // Maximum allowed by API
      })
      
      const memories = response.results || []
      let withFiles = 0
      let totalFileSize = 0
      const byType = { episodic: 0, semantic: 0, procedural: 0 }

      memories.forEach((mem: any) => {
        // Count by type
        const memType = mem.memory_type || 'semantic'
        if (byType.hasOwnProperty(memType)) {
          byType[memType as keyof typeof byType]++
        }
        
        // Count files
        if (mem.content?.storage_url || mem.content?.file_url) {
          withFiles++
          totalFileSize += mem.content?.file_size || 0
        }
      })

      setStats({
        total: memories.length,
        withFiles,
        totalFileSize,
        byType,
      })
    } catch (error) {
      console.error('Failed to load memory stats:', error)
    }
  }

  useEffect(() => {
    loadStats()
    // Load all memories on mount
    loadAllMemories()
  }, [])

  const loadAllMemories = async () => {
    const agentId = localStorage.getItem('agent_id')
    if (!agentId) {
      console.log('No agent ID set, cannot load memories')
      return
    }

    try {
      setLoading(true)
      // Load all memories with a generic query
      const response = await memoryApi.search({
        query: 'memory', // Generic query to get all
        limit: 100, // Maximum allowed by API
      })
      setResults(response.results || [])
      // Update stats after loading
      await loadStats()
    } catch (error: any) {
      console.error('Failed to load memories:', error)
      let errorMsg = 'Failed to load memories'
      if (error?.response?.data?.detail) {
        errorMsg = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail)
      } else if (error?.message) {
        errorMsg = error.message
      } else if (typeof error === 'string') {
        errorMsg = error
      }
      alert(`Failed to load memories: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // If search is empty, load all memories instead
      await loadAllMemories()
      return
    }

    setLoading(true)
    setExecutionTime(null)
    
    try {
      let response: any
      const startTime = Date.now()

      // Choose search method based on searchType
      switch (searchType) {
        case 'semantic':
          response = await searchApi.semantic({
            query: searchQuery,
            top_k: searchOptions.top_k,
            threshold: searchOptions.threshold > 0 ? searchOptions.threshold : undefined,
            memory_type: searchOptions.memory_type || undefined,
            conversation_id: searchOptions.conversation_id || undefined,
            use_cache: searchOptions.use_cache,
          })
          break
          
        case 'keyword':
          response = await searchApi.keyword({
            query: searchQuery,
            top_k: searchOptions.top_k,
            memory_type: searchOptions.memory_type || undefined,
            conversation_id: searchOptions.conversation_id || undefined,
          })
          break
          
        case 'hybrid':
          response = await searchApi.hybrid({
            query: searchQuery,
            top_k: searchOptions.top_k,
            threshold: searchOptions.threshold > 0 ? searchOptions.threshold : undefined,
            semantic_weight: searchOptions.semantic_weight,
            keyword_weight: searchOptions.keyword_weight,
            memory_type: searchOptions.memory_type || undefined,
            conversation_id: searchOptions.conversation_id || undefined,
            use_cache: searchOptions.use_cache,
          })
          break
          
        case 'legacy':
        default:
          response = await memoryApi.search({
            query: searchQuery,
            limit: searchOptions.top_k,
            memory_type: searchOptions.memory_type || undefined,
            conversation_id: searchOptions.conversation_id || undefined,
          })
          break
      }

      const endTime = Date.now()
      setExecutionTime(response.execution_time_ms || (endTime - startTime))
      setResults(response.results || [])
      
      // Update stats after search
      await loadStats()
    } catch (error: any) {
      console.error('Failed to search memories:', error)
      let errorMsg = 'Failed to search memories'
      if (error?.response?.data?.detail) {
        errorMsg = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail)
      } else if (error?.message) {
        errorMsg = error.message
      } else if (typeof error === 'string') {
        errorMsg = error
      }
      alert(`Search failed: ${errorMsg}`)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getStorageUrl = (content: Record<string, any>): string | null => {
    return content.storage_url || content.file_url || null
  }

  const formatContent = (content: Record<string, any>): string => {
    if (content.text && typeof content.text === 'string') {
      return content.text
    }
    return JSON.stringify(content, null, 2)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Memories</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Search and manage agent memories</p>
        </div>
        <div className="flex gap-2">
          {selectedMemories.length > 0 && (
            <button
              onClick={() => setShowBatchOperations(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded border border-blue-600 hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Batch Operations ({selectedMemories.length})
            </button>
          )}
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 transition-colors text-sm font-medium"
          >
            Create Memory
          </button>
        </div>
      </div>

      {/* Memory Statistics */}
      {stats.total > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Memories</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stats.total}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">With Files</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stats.withFiles}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Storage</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {formatFileSize(stats.totalFileSize)}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">File Coverage</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.total > 0 ? Math.round((stats.withFiles / stats.total) * 100) : 0}%
            </p>
          </div>
        </div>
      )}

      {/* Search Controls */}
      <div className="space-y-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch()
                }
              }}
              className="w-full pl-4 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            />
          </div>
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value as SearchType)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
          >
            <option value="semantic">Semantic</option>
            <option value="keyword">Keyword</option>
            <option value="hybrid">Hybrid</option>
            <option value="legacy">Legacy</option>
          </select>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {loading ? 'Searching...' : searchQuery.trim() ? 'Search' : 'Show All'}
          </button>
          {searchQuery.trim() && (
            <button
              onClick={async () => {
                setSearchQuery('')
                await loadAllMemories()
              }}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
            >
              Clear
            </button>
          )}
          {selectedMemories.length > 0 && (
            <button
              onClick={() => setSelectedMemories([])}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
            >
              Clear Selection ({selectedMemories.length})
            </button>
          )}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
          >
            {showAdvanced ? '▲' : '▼'} Advanced
          </button>
        </div>

        {/* Advanced Search Options */}
        {showAdvanced && (
          <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Top K Results
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={searchOptions.top_k}
                  onChange={(e) => setSearchOptions({ ...searchOptions, top_k: parseInt(e.target.value) || 10 })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Similarity Threshold
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={searchOptions.threshold}
                  onChange={(e) => setSearchOptions({ ...searchOptions, threshold: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Memory Type
                </label>
                <select
                  value={searchOptions.memory_type}
                  onChange={(e) => setSearchOptions({ ...searchOptions, memory_type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                >
                  <option value="">All Types</option>
                  <option value="episodic">Episodic</option>
                  <option value="semantic">Semantic</option>
                  <option value="procedural">Procedural</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Conversation ID
                </label>
                <input
                  type="text"
                  value={searchOptions.conversation_id}
                  onChange={(e) => setSearchOptions({ ...searchOptions, conversation_id: e.target.value })}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                />
              </div>
            </div>
            {searchType === 'hybrid' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Semantic Weight ({Math.round(searchOptions.semantic_weight * 100)}%)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={searchOptions.semantic_weight}
                    onChange={(e) => {
                      const semantic = parseFloat(e.target.value)
                      setSearchOptions({
                        ...searchOptions,
                        semantic_weight: semantic,
                        keyword_weight: 1 - semantic,
                      })
                    }}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Keyword Weight ({Math.round(searchOptions.keyword_weight * 100)}%)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={searchOptions.keyword_weight}
                    onChange={(e) => {
                      const keyword = parseFloat(e.target.value)
                      setSearchOptions({
                        ...searchOptions,
                        keyword_weight: keyword,
                        semantic_weight: 1 - keyword,
                      })
                    }}
                    className="w-full"
                  />
                </div>
              </div>
            )}
            <div className="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input
                  type="checkbox"
                  checked={searchOptions.use_cache}
                  onChange={(e) => setSearchOptions({ ...searchOptions, use_cache: e.target.checked })}
                  className="rounded"
                />
                Use Cache
              </label>
            </div>
          </div>
        )}

        {/* Search Info */}
        {executionTime !== null && (
          <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
            <span>
              Search Type: <strong className="capitalize">{searchType}</strong>
            </span>
            <span>
              Execution Time: <strong>{executionTime.toFixed(2)}ms</strong>
            </span>
            {executionTime < 100 && (
              <span className="text-green-600 dark:text-green-400">Fast</span>
            )}
          </div>
        )}
      </div>

      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Showing {results.length} {searchQuery ? 'matching' : ''} memories
              {searchType !== 'legacy' && searchQuery && (
                <span className="ml-2 text-xs">({searchType} search)</span>
              )}
            </p>
            {!searchQuery && (
              <button
                onClick={loadAllMemories}
                className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
              >
                Refresh
              </button>
            )}
          </div>
          {results.map((result) => {
            const storageUrl = getStorageUrl(result.content)
            const displayContent = formatContent(result.content)
            const fileName = result.content?.text || result.content?.filename || 'Memory content'
            const fileSize = result.content?.file_size ? formatFileSize(result.content.file_size) : null
            const fileType = result.content?.file_type || ''

            return (
              <div
                key={result.context_id}
                className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-6"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <input
                        type="checkbox"
                        checked={selectedMemories.includes(result.context_id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedMemories([...selectedMemories, result.context_id])
                          } else {
                            setSelectedMemories(selectedMemories.filter(id => id !== result.context_id))
                          }
                        }}
                        className="rounded"
                      />
                      <span className="font-mono text-xs text-gray-500 dark:text-gray-400">
                        {result.context_id}
                      </span>
                      {result.memory_type && (
                        <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded text-xs capitalize">
                          {result.memory_type}
                        </span>
                      )}
                      <button
                        onClick={() => {
                          setSelectedMemoryId(result.context_id)
                          setShowVersions(true)
                        }}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                        title="View version history"
                      >
                        Versions
                      </button>
                    </div>
                    {searchQuery && result.similarity_score !== undefined && (
                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs">
                        {Math.round(result.similarity_score * 100)}% match
                      </span>
                    )}
                  </div>
                </div>

                <div className="mb-3">
                  <div className="font-medium text-gray-900 dark:text-white mb-2">{fileName}</div>
                  {result.content.text ? (
                    <div className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded whitespace-pre-wrap max-h-48 overflow-y-auto">
                      {displayContent.length > 500 ? `${displayContent.substring(0, 500)}...` : displayContent}
                    </div>
                  ) : (
                    <pre className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded overflow-x-auto max-h-48 overflow-y-auto">
                      {displayContent.length > 500 ? `${displayContent.substring(0, 500)}...` : displayContent}
                    </pre>
                  )}
                </div>

                {storageUrl && (
                  <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs font-medium text-blue-800 dark:text-blue-200">
                        Storage URL:
                      </div>
                      {fileSize && (
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          {fileSize} {fileType && `• ${fileType}`}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <a
                        href={storageUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 dark:text-blue-400 hover:underline break-all flex-1"
                      >
                        {storageUrl}
                      </a>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(storageUrl)
                          alert('URL copied to clipboard!')
                        }}
                        className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors whitespace-nowrap"
                      >
                        Copy URL
                      </button>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
                  <span>
                    Created by {result.created_by} on {new Date(result.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {results.length === 0 && !loading && (
        <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-12 text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {searchQuery ? 'No memories found matching your search' : 'No memories found. Create your first memory to get started.'}
          </p>
          {!searchQuery && (
            <button
              onClick={loadAllMemories}
              className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors text-sm font-medium"
            >
              Load Memories
            </button>
          )}
        </div>
      )}

      {showForm && (
        <MemoryForm
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false)
            loadStats() // Reload stats after creating memory
            loadAllMemories() // Reload all memories to show the new one
          }}
        />
      )}

      {showVersions && selectedMemoryId && (
        <MemoryVersions
          contextId={selectedMemoryId}
          onClose={() => {
            setShowVersions(false)
            setSelectedMemoryId(null)
            loadAllMemories() // Reload to show any changes from revert
          }}
        />
      )}

      {showBatchOperations && (
        <BatchOperations
          selectedMemories={selectedMemories}
          onSuccess={() => {
            setSelectedMemories([])
            loadAllMemories()
            loadStats()
          }}
          onClose={() => {
            setShowBatchOperations(false)
          }}
        />
      )}
    </div>
  )
}

export default Memories
