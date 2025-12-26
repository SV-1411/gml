import { useState } from 'react'
import { agentsApi } from '../../services/api'

interface AgentFormProps {
  onClose: () => void
  onSuccess: () => void
}

const AgentForm: React.FC<AgentFormProps> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    agent_id: '',
    name: '',
    version: '1.0.0',
    description: '',
    capabilities: [] as string[],
  })
  const [newCapability, setNewCapability] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [apiToken, setApiToken] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (formData.capabilities.length === 0) {
      setError('Please add at least one capability')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await agentsApi.register(formData)
      setApiToken(response.api_token)
      setSuccess(true)
      localStorage.setItem('agent_id', formData.agent_id)
      
      if (response.api_token) {
        navigator.clipboard.writeText(response.api_token)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to register agent')
    } finally {
      setLoading(false)
    }
  }

  const addCapability = () => {
    if (newCapability.trim() && !formData.capabilities.includes(newCapability.trim())) {
      setFormData({
        ...formData,
        capabilities: [...formData.capabilities, newCapability.trim()],
      })
      setNewCapability('')
    }
  }

  const removeCapability = (cap: string) => {
    setFormData({
      ...formData,
      capabilities: formData.capabilities.filter((c) => c !== cap),
    })
  }

  if (success) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-6 max-w-md w-full mx-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Agent Registered Successfully
            </h2>
            <button
              onClick={() => {
                // Reset all form state
                setSuccess(false)
                setApiToken('')
                setError('')
                setFormData({
                  agent_id: '',
                  name: '',
                  version: '1.0.0',
                  description: '',
                  capabilities: [],
                })
                onClose()
              }}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-2xl leading-none"
            >
              ×
            </button>
          </div>
          
          <div className="mb-4 space-y-3">
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded">
              <p className="text-sm text-green-800 dark:text-green-200">
                Agent "{formData.name}" ({formData.agent_id}) has been registered successfully!
              </p>
            </div>

            {apiToken && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    API Token {apiToken && <span className="text-green-600 dark:text-green-400">(Copied to clipboard)</span>}
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={apiToken}
                      readOnly
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-xs break-all"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(apiToken)
                        alert('Token copied to clipboard!')
                      }}
                      className="absolute right-2 top-2 px-2 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-500"
                    >
                      Copy
                    </button>
                  </div>
                  <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                    Important: Save this token securely. It will not be shown again.
                  </p>
                </div>
              </>
            )}

            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
              <p className="text-xs text-blue-800 dark:text-blue-200">
                This agent ID has been automatically set as your default. You can change it in Settings.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => {
                // Reset all form state
                setSuccess(false)
                setApiToken('')
                setError('')
                setFormData({
                  agent_id: '',
                  name: '',
                  version: '1.0.0',
                  description: '',
                  capabilities: [],
                })
                onClose()
              }}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
            >
              Close
            </button>
            <button
              onClick={async () => {
                try {
                  // Call onSuccess first to reload agents
                  await onSuccess()
                  // Reset all form state
                  setSuccess(false)
                  setApiToken('')
                  setError('')
                  setFormData({
                    agent_id: '',
                    name: '',
                    version: '1.0.0',
                    description: '',
                    capabilities: [],
                  })
                  // Then close the form
                  onClose()
                } catch (error) {
                  console.error('Error in success handler:', error)
                  // Still close the form even if onSuccess fails
                  setSuccess(false)
                  setApiToken('')
                  onClose()
                }
              }}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 transition-colors text-sm font-medium"
            >
              View Agents
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Register New Agent</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Agent ID *
            </label>
            <input
              type="text"
              required
              value={formData.agent_id}
              onChange={(e) => setFormData({ ...formData, agent_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              placeholder="e.g., my-agent-001"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              placeholder="e.g., My AI Agent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Version
            </label>
            <input
              type="text"
              value={formData.version}
              onChange={(e) => setFormData({ ...formData, version: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              placeholder="1.0.0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              placeholder="Describe what this agent does..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Capabilities *
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newCapability}
                onChange={(e) => setNewCapability(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addCapability()
                  }
                }}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                placeholder="e.g., chat, file_processing"
              />
              <button
                type="button"
                onClick={addCapability}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.capabilities.map((cap) => (
                <span
                  key={cap}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded text-sm"
                >
                  {cap}
                  <button
                    type="button"
                    onClick={() => removeCapability(cap)}
                    className="hover:text-primary-600"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {loading ? 'Registering...' : 'Register Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AgentForm
