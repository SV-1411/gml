import React from 'react'

interface MarkdownRendererProps {
  content: string
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const renderMarkdown = (text: string) => {
    const lines = text.split('\n')
    const elements: React.ReactNode[] = []
    let currentParagraph: string[] = []
    let inCodeBlock = false
    let codeBlockContent: string[] = []
    let codeBlockLang = ''

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        const paragraphText = currentParagraph.join(' ')
        if (paragraphText.trim()) {
          elements.push(<p key={elements.length} className="mb-4 leading-relaxed">{renderInline(paragraphText)}</p>)
        }
        currentParagraph = []
      }
    }

    const renderInline = (text: string) => {
      // Handle bold
      text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      text = text.replace(/__(.+?)__/g, '<strong>$1</strong>')
      
      // Handle italic
      text = text.replace(/\*(.+?)\*/g, '<em>$1</em>')
      text = text.replace(/_(.+?)_/g, '<em>$1</em>')
      
      // Handle inline code
      text = text.replace(/`(.+?)`/g, '<code class="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>')
      
      // Handle links
      text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-primary-600 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>')
      
      return <span dangerouslySetInnerHTML={{ __html: text }} />
    }

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]

      // Code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // End code block
          flushParagraph()
          elements.push(
            <pre key={elements.length} className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto mb-4">
              <code className={`text-sm font-mono ${codeBlockLang}`}>{codeBlockContent.join('\n')}</code>
            </pre>
          )
          codeBlockContent = []
          inCodeBlock = false
          codeBlockLang = ''
        } else {
          // Start code block
          flushParagraph()
          inCodeBlock = true
          codeBlockLang = line.substring(3).trim()
        }
        continue
      }

      if (inCodeBlock) {
        codeBlockContent.push(line)
        continue
      }

      // Headers
      if (line.startsWith('# ')) {
        flushParagraph()
        elements.push(<h1 key={elements.length} className="text-2xl font-bold mb-4 mt-6">{line.substring(2)}</h1>)
        continue
      }
      if (line.startsWith('## ')) {
        flushParagraph()
        elements.push(<h2 key={elements.length} className="text-xl font-semibold mb-3 mt-5">{line.substring(3)}</h2>)
        continue
      }
      if (line.startsWith('### ')) {
        flushParagraph()
        elements.push(<h3 key={elements.length} className="text-lg font-semibold mb-2 mt-4">{line.substring(4)}</h3>)
        continue
      }

      // Lists
      if (line.match(/^[-*]\s/)) {
        flushParagraph()
        const listItems: string[] = [line.substring(2)]
        let j = i + 1
        while (j < lines.length && lines[j].match(/^[-*]\s/)) {
          listItems.push(lines[j].substring(2))
          j++
        }
        elements.push(
          <ul key={elements.length} className="list-disc list-inside mb-4 space-y-1">
            {listItems.map((item, idx) => (
              <li key={idx}>{renderInline(item)}</li>
            ))}
          </ul>
        )
        i = j - 1
        continue
      }

      if (line.match(/^\d+\.\s/)) {
        flushParagraph()
        const listItems: string[] = [line.substring(line.indexOf('.') + 2)]
        let j = i + 1
        while (j < lines.length && lines[j].match(/^\d+\.\s/)) {
          listItems.push(lines[j].substring(lines[j].indexOf('.') + 2))
          j++
        }
        elements.push(
          <ol key={elements.length} className="list-decimal list-inside mb-4 space-y-1">
            {listItems.map((item, idx) => (
              <li key={idx}>{renderInline(item)}</li>
            ))}
          </ol>
        )
        i = j - 1
        continue
      }

      // Empty line
      if (line.trim() === '') {
        flushParagraph()
        continue
      }

      // Regular line
      currentParagraph.push(line)
    }

    flushParagraph()

    return elements.length > 0 ? elements : <p className="mb-4">{content}</p>
  }

  return <div className="markdown-content">{renderMarkdown(content)}</div>
}

export default MarkdownRenderer

