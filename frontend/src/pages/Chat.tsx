import { useState, useRef, useEffect } from 'react'
import { ollamaApi } from '../services/api'
import { chatApi } from '../services/chatApi'
import clsx from 'clsx'
import MarkdownRenderer from '../components/MarkdownRenderer'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  used_memories?: string[]
}

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [thinkingStep, setThinkingStep] = useState('')
  const [streamingContent, setStreamingContent] = useState('')
  const [selectedModel, setSelectedModel] = useState('gpt-oss:20b')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [usedMemories, setUsedMemories] = useState<string[]>([])
  const [showMemoryInfo, setShowMemoryInfo] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const thinkingSteps = [
    'Searching memories for relevant context...',
    'Analyzing query and context...',
    'Generating response...',
    'Formatting output...'
  ]

  useEffect(() => {
    loadModels()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, thinkingStep])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '48px'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadModels = async () => {
    try {
      const response = await ollamaApi.models()
      if (response.models && Array.isArray(response.models) && response.models.length > 0) {
        // Extract model names from response (could be array of strings or objects)
        const modelNames = response.models.map((m: any) => typeof m === 'string' ? m : m.id || m.name || m.model_id)
        setAvailableModels(modelNames)
        // Set default to first available model or fallback
        if (modelNames.length > 0) {
          setSelectedModel(modelNames[0])
        } else if (!selectedModel) {
          setSelectedModel('gpt-oss:20b') // Fallback
        }
      } else if (!availableModels.length && !selectedModel) {
        // If no models available, use fallback
        setSelectedModel('gpt-oss:20b')
      }
    } catch (error) {
      console.error('Failed to load models:', error)
      // On error, ensure we have a fallback model
      if (!selectedModel) {
        setSelectedModel('gpt-oss:20b')
      }
    }
  }

  const simulateThinking = async () => {
    setIsThinking(true)
    for (let i = 0; i < thinkingSteps.length; i++) {
      setThinkingStep(thinkingSteps[i])
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    setIsThinking(false)
    setThinkingStep('')
  }

  const simulateStreaming = async (text: string): Promise<void> => {
    return new Promise((resolve) => {
      setStreamingContent('')
      let index = 0
      const interval = setInterval(() => {
        if (index < text.length) {
          setStreamingContent(text.substring(0, index + 1))
          index++
        } else {
          clearInterval(interval)
          resolve()
        }
      }, 15)
    })
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const agentId = localStorage.getItem('agent_id')
    if (!agentId) {
      alert('Agent ID required. Please set it in Settings.')
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    const userInput = input.trim()
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setStreamingContent('')

    try {
      await simulateThinking()

      // Use new chat API with memory injection
      const response = await chatApi.sendMessage({
        agent_id: agentId,
        conversation_id: conversationId || undefined,
        message: userInput,
        stream: false,
        relevance_threshold: 0.7,
        max_memories: 10,
      })

      // Update conversation ID if new
      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id)
      }

      // Track used memories
      if (response.used_memories && response.used_memories.length > 0) {
        setUsedMemories(response.used_memories)
        setShowMemoryInfo(true)
      }

      const responseText = response.response || 'No response received'

      // Simulate streaming
      await simulateStreaming(responseText)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseText,
        timestamp: new Date(),
        used_memories: response.used_memories,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setStreamingContent('')

    } catch (error: any) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message || 'Failed to get response'}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setIsThinking(false)
      setThinkingStep('')
      setStreamingContent('')
      textareaRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Chat with Memory</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Interactive conversation with automatic memory context injection
            {conversationId && (
              <span className="ml-2 text-xs">Conversation: {conversationId.substring(0, 16)}...</span>
            )}
          </p>
          {showMemoryInfo && usedMemories.length > 0 && (
            <div className="mt-2 text-xs text-primary-600 dark:text-primary-400">
              Using {usedMemories.length} relevant memories
            </div>
          )}
        </div>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="px-4 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {availableModels.length > 0 ? (
            availableModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))
          ) : (
            <option value={selectedModel}>Model: {selectedModel}</option>
          )}
        </select>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 mb-6 scrollbar-hide">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <div className="text-4xl mb-4 text-gray-400">AI</div>
              <p className="text-gray-600 dark:text-gray-400">Start a conversation by typing a message below</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={clsx(
              'flex gap-4',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">AI</span>
              </div>
            )}

            <div
              className={clsx(
                'max-w-[80%] rounded-lg px-4 py-3',
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
              )}
            >
              {message.role === 'assistant' ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <MarkdownRenderer content={message.content} />
                </div>
              ) : (
                <div className="whitespace-pre-wrap break-words">{message.content}</div>
              )}
              {message.role === 'assistant' && message.used_memories && message.used_memories.length > 0 && (
                <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
                  Used {message.used_memories.length} memories
                </div>
              )}
              <div
                className={clsx(
                  'text-xs mt-3',
                  message.role === 'user'
                    ? 'text-primary-100'
                    : 'text-gray-500 dark:text-gray-400'
                )}
              >
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>

            {message.role === 'user' && (
              <div className="w-10 h-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">You</span>
              </div>
            )}
          </div>
        ))}

        {isThinking && thinkingStep && (
          <div className="flex gap-4 justify-start">
            <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">AI</span>
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400">{thinkingStep}</span>
              </div>
            </div>
          </div>
        )}

        {streamingContent && (
          <div className="flex gap-4 justify-start">
            <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">AI</span>
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <MarkdownRenderer content={streamingContent} />
              </div>
              <span className="inline-block w-2 h-4 bg-primary-600 ml-1 animate-pulse"></span>
            </div>
          </div>
        )}

        {isLoading && !isThinking && !streamingContent && (
          <div className="flex gap-4 justify-start">
            <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">AI</span>
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <div className="flex gap-3">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
            className="flex-1 resize-none rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            style={{ minHeight: '48px', maxHeight: '200px' }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Chat
