import { useState, useEffect } from 'react'
import { conversationApi } from '../services/conversationApi'

const ConversationContext = () => {
  const [conversationId, setConversationId] = useState('')
  const [contextLevel, setContextLevel] = useState<'minimal' | 'full' | 'detailed'>('full')
  const [context, setContext] = useState<any>(null)
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadContext = async () => {
    if (!conversationId.trim()) {
      setError('Please enter a conversation ID')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await conversationApi.getContext(conversationId, {
        context_level: contextLevel,
      })
      setContext(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load context')
    } finally {
      setLoading(false)
    }
  }

  const loadSummary = async () => {
    if (!conversationId.trim()) {
      setError('Please enter a conversation ID')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await conversationApi.getSummary(conversationId, 'standard')
      setSummary(data.summary)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load summary')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format: 'json' | 'markdown' | 'html') => {
    if (!conversationId.trim()) {
      setError('Please enter a conversation ID')
      return
    }

    try {
      const blob = await conversationApi.exportContext(conversationId, format, {
        context_level: contextLevel,
        include_messages: true,
        include_memories: true,
      })

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `conversation-${conversationId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to export')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Conversation Context
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          View complete conversation context with all related memories
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
            placeholder="Enter conversation ID"
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <select
            value={contextLevel}
            onChange={(e) => setContextLevel(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="minimal">Minimal</option>
            <option value="full">Full</option>
            <option value="detailed">Detailed</option>
          </select>
          <button
            onClick={loadContext}
            disabled={loading}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load Context'}
          </button>
          <button
            onClick={loadSummary}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Generate Summary
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-800 dark:text-red-200">
            {error}
          </div>
        )}

        {summary && (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
            <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">Summary</h3>
            <p className="text-blue-800 dark:text-blue-300 text-sm whitespace-pre-wrap">
              {summary.summary_text}
            </p>
            {summary.key_decisions && summary.key_decisions.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium text-blue-900 dark:text-blue-200 mb-2">Key Decisions:</h4>
                <ul className="list-disc list-inside text-blue-800 dark:text-blue-300 text-sm">
                  {summary.key_decisions.map((d: string, i: number) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {context && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Conversation Context
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={() => handleExport('json')}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Export JSON
                </button>
                <button
                  onClick={() => handleExport('markdown')}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Export Markdown
                </button>
                <button
                  onClick={() => handleExport('html')}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Export HTML
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Messages:</span>{' '}
                {context.statistics?.message_count || 0}
              </div>
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Memories:</span>{' '}
                {context.statistics?.memory_count || 0}
              </div>
            </div>

            {context.messages && context.messages.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Messages</h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {context.messages.map((msg: any, i: number) => (
                    <div
                      key={i}
                      className={`p-3 rounded border ${
                        msg.role === 'user'
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                          : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-sm text-gray-700 dark:text-gray-300">
                          {msg.role}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(msg.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900 dark:text-white">{msg.content}</p>
                      {msg.used_memories && msg.used_memories.length > 0 && (
                        <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                          Used {msg.used_memories.length} memories
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {context.memories && context.memories.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Related Memories</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {context.memories.map((mem: any, i: number) => (
                    <div
                      key={i}
                      className="p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700"
                    >
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {mem.context_id}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        Type: {mem.memory_type}
                      </div>
                      <div className="text-xs text-gray-700 dark:text-gray-300 mt-2">
                        {typeof mem.content === 'string' ? mem.content : JSON.stringify(mem.content)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {context.relationships && context.relationships.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                  Memory Relationships ({context.relationships.length})
                </h4>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {context.relationships.length} relationships mapped
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationContext

