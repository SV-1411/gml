import { useState } from 'react'
import { agentApi } from '../../services/agentApi'

interface AgentInitializationProps {
  agentId: string
  onClose: () => void
}

const AgentInitialization = ({ agentId, onClose }: AgentInitializationProps) => {
  const [conversationId, setConversationId] = useState('')
  const [query, setQuery] = useState('')
  const [maxTokens, setMaxTokens] = useState(4000)
  const [strategy, setStrategy] = useState<'semantic' | 'keyword' | 'hybrid' | 'all'>('hybrid')
  const [formatType, setFormatType] = useState<'narrative' | 'qa' | 'structured'>('narrative')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleInitialize = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await agentApi.initialize(agentId, {
        conversation_id: conversationId || undefined,
        query: query || undefined,
        max_tokens: maxTokens,
        strategy: strategy,
        format_type: formatType,
      })

      setResult(response)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to initialize agent')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Initialize Agent
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {agentId}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Close
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-800 dark:text-red-200 text-sm">
              {error}
            </div>
          )}

          {result && (
            <div className="mb-4 space-y-4">
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded p-4">
                <div className="text-sm font-semibold text-green-800 dark:text-green-200 mb-2">
                  Initialization Successful
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm text-green-700 dark:text-green-300">
                  <div>
                    <span className="font-medium">Memories Loaded:</span> {result.memories_loaded}
                  </div>
                  <div>
                    <span className="font-medium">Token Count:</span> {result.token_count}
                  </div>
                  <div>
                    <span className="font-medium">Execution Time:</span> {result.execution_time_ms?.toFixed(2)}ms
                  </div>
                  {result.metadata?.cache_stats && (
                    <div>
                      <span className="font-medium">Cache Hit Rate:</span> {result.metadata.cache_stats.hit_rate?.toFixed(1)}%
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700 p-4">
                <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  Formatted Context Preview
                </div>
                <pre className="text-xs text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 p-3 rounded overflow-auto max-h-60 whitespace-pre-wrap">
                  {result.formatted_context?.substring(0, 1000)}
                  {result.formatted_context?.length > 1000 && '...'}
                </pre>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Conversation ID (optional)
              </label>
              <input
                type="text"
                value={conversationId}
                onChange={(e) => setConversationId(e.target.value)}
                placeholder="Leave empty for all conversations"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Query (optional, for semantic search)
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search query for relevant memories"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Max Tokens: {maxTokens}
                </label>
                <input
                  type="range"
                  min="100"
                  max="16000"
                  step="100"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Strategy
                </label>
                <select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="semantic">Semantic</option>
                  <option value="keyword">Keyword</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="all">All</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Format Type
              </label>
              <select
                value={formatType}
                onChange={(e) => setFormatType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="narrative">Narrative</option>
                <option value="qa">Q&A</option>
                <option value="structured">Structured</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleInitialize}
            disabled={loading}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Initializing...' : 'Initialize Agent'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AgentInitialization

