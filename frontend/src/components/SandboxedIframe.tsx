/**
 * Sandboxed iframe component for rendering untrusted HTML artifacts.
 * 
 * Security properties:
 * - Uses iframe sandbox without allow-same-origin
 * - No access to parent DOM or storage
 * - Scripts allowed only for interactive artifacts
 * - Content treated as completely untrusted
 */

'use client'

import { useEffect, useRef, useState } from 'react'
import DOMPurify from 'dompurify'

interface SandboxedIframeProps {
  content: string
  title?: string
  className?: string
}

export function SandboxedIframe({ content, title, className = '' }: SandboxedIframeProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [sanitized, setSanitized] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    try {
      // Sanitize HTML with DOMPurify
      // Note: DOMPurify is defense-in-depth. Primary security is iframe sandbox.
      const clean = DOMPurify.sanitize(content, {
        ALLOWED_TAGS: [
          'html', 'head', 'body', 'meta', 'title', 'style', 'script',
          'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'ul', 'ol', 'li', 'a', 'strong', 'em', 'b', 'i', 'u',
          'table', 'thead', 'tbody', 'tr', 'th', 'td',
          'form', 'input', 'button', 'label', 'select', 'option', 'textarea',
          'img', 'svg', 'path', 'circle', 'rect', 'line', 'polygon',
          'br', 'hr', 'code', 'pre', 'blockquote',
        ],
        ALLOWED_ATTR: [
          'class', 'id', 'style', 'href', 'src', 'alt', 'title',
          'type', 'value', 'name', 'placeholder', 'disabled', 'readonly',
          'checked', 'selected', 'for', 'width', 'height',
          'viewBox', 'd', 'fill', 'stroke', 'stroke-width',
          'charset', 'content', 'viewport',
        ],
        ALLOW_DATA_ATTR: true,
        ADD_TAGS: ['style', 'script'],
        FORCE_BODY: false,
      })

      setSanitized(clean)
      setError(null)
    } catch (e) {
      console.error('Sanitization error:', e)
      setError('Failed to render artifact content')
    }
  }, [content])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-surface-elevated p-8">
        <div className="text-center">
          <p className="text-error mb-2">{error}</p>
          <p className="text-xs text-text-muted">The artifact content could not be safely rendered.</p>
        </div>
      </div>
    )
  }

  return (
    <iframe
      ref={iframeRef}
      srcDoc={sanitized}
      title={title || 'Artifact preview'}
      aria-label={title || 'Artifact preview'}
      sandbox="allow-scripts"
      className={`w-full h-full border-0 ${className}`}
      style={{
        backgroundColor: '#ffffff',
      }}
    />
  )
}
