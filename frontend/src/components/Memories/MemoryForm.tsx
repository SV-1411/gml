import { useState, useRef } from 'react'
import { memoryApi, storageApi } from '../../services/api'

interface UploadResponse {
  url: string
  key: string
  bucket: string
  size?: number
  filename?: string
}

interface MemoryFormProps {
  onClose: () => void
  onSuccess: () => void
}

const MemoryForm: React.FC<MemoryFormProps> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    conversation_id: `conv-${Date.now()}`,
    content: '',
    contentType: 'text' as 'text' | 'json',
    memory_type: 'semantic' as 'episodic' | 'semantic' | 'procedural',
    visibility: 'private' as 'all' | 'organization' | 'private',
    tags: [] as string[],
  })
  const [uploadedFile, setUploadedFile] = useState<UploadResponse | null>(null)
  const [uploading, setUploading] = useState(false)
  const [newTag, setNewTag] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError('')

    try {
      const uploadResult = await storageApi.upload(file)
      setUploadedFile(uploadResult)
      setFormData({
        ...formData,
        content: JSON.stringify({
          text: file.name,
          file_url: uploadResult.url,
          file_key: uploadResult.key,
          file_size: file.size,
          file_type: file.type,
        }, null, 2),
        contentType: 'json',
      })
    } catch (err: any) {
      console.error('File upload error:', err)
      const errorMsg = err.response?.data?.detail || err.message || 'Unknown error'
      setError(`File upload failed: ${errorMsg}`)
      if (err.response?.status === 404) {
        setError('File upload endpoint not found. Please ensure the backend server is running and has been restarted to load the storage routes.')
      }
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      let contentObj: Record<string, any>

      if (formData.contentType === 'text') {
        // Convert text to JSON object
        contentObj = {
          text: formData.content,
          type: 'text',
        }
      } else {
        // Parse JSON
        try {
          contentObj = JSON.parse(formData.content || '{}')
        } catch (parseError) {
          setError('Invalid JSON format in content field')
          return
        }
      }

      // Add storage URL if file was uploaded
      if (uploadedFile) {
        contentObj.storage_url = uploadedFile.url
        contentObj.file_key = uploadedFile.key
      }

      setLoading(true)
      setError('')

      await memoryApi.write({
        conversation_id: formData.conversation_id,
        content: contentObj,
        memory_type: formData.memory_type,
        visibility: formData.visibility,
        tags: formData.tags,
      })

      onSuccess()
    } catch (err: any) {
      if (err.response?.data?.detail) {
        const errorMsg = err.response.data.detail
        if (errorMsg.includes('Agent ID required') || errorMsg.includes('X-Agent-ID')) {
          setError(
            'Agent ID required. Please go to Settings page and set your Agent ID, or register an agent first.'
          )
        } else {
          setError(errorMsg)
        }
      } else if (err instanceof SyntaxError) {
        setError('Invalid JSON format in content field')
      } else {
        setError('Failed to create memory')
      }
    } finally {
      setLoading(false)
    }
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag.trim()],
      })
      setNewTag('')
    }
  }

  const removeTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((t) => t !== tag),
    })
  }

  const removeFile = () => {
    setUploadedFile(null)
    setFormData({
      ...formData,
      content: '',
      contentType: 'text',
    })
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Create Memory</h2>
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
              Conversation ID
            </label>
            <input
              type="text"
              value={formData.conversation_id}
              onChange={(e) => setFormData({ ...formData, conversation_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Content Type
            </label>
            <div className="flex gap-4 mb-2">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="text"
                  checked={formData.contentType === 'text'}
                  onChange={() => setFormData({ ...formData, contentType: 'text', content: '' })}
                  className="text-primary-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Text</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="json"
                  checked={formData.contentType === 'json'}
                  onChange={() => setFormData({ ...formData, contentType: 'json', content: '' })}
                  className="text-primary-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">JSON</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Content {formData.contentType === 'text' ? '(Text)' : '(JSON)'} *
            </label>
            {formData.contentType === 'text' ? (
              <textarea
                required
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                rows={6}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                placeholder="Enter text content..."
              />
            ) : (
              <textarea
                required
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                rows={6}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
                placeholder='{"text": "User prefers dark mode", "preference": "dark"}'
              />
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Upload File (Optional)
            </label>
            <div className="space-y-2">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                disabled={uploading}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              />
              {uploading && (
                <div className="text-sm text-gray-600 dark:text-gray-400">Uploading...</div>
              )}
              {uploadedFile && (
                <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-green-800 dark:text-green-200">
                        File uploaded successfully
                      </div>
                      <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                        Storage URL: {uploadedFile.url}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={removeFile}
                      className="text-red-600 hover:text-red-700 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Memory Type *
            </label>
            <select
              value={formData.memory_type}
              onChange={(e) =>
                setFormData({ ...formData, memory_type: e.target.value as any })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="episodic">Episodic</option>
              <option value="semantic">Semantic</option>
              <option value="procedural">Procedural</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Visibility
            </label>
            <select
              value={formData.visibility}
              onChange={(e) =>
                setFormData({ ...formData, visibility: e.target.value as any })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="all">All</option>
              <option value="organization">Organization</option>
              <option value="private">Private</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tags
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addTag()
                  }
                }}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                placeholder="Add tag..."
              />
              <button
                type="button"
                onClick={addTag}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded text-sm"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
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
              disabled={loading || uploading}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {loading ? 'Creating...' : 'Create Memory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default MemoryForm
