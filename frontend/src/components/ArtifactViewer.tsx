/**
 * Main artifact viewer component.
 * 
 * Displays artifacts in a split-pane layout with:
 * - Type detection (Markdown vs HTML)
 * - Version management (version switcher when history exists)
 * - Copy/download actions
 * - Responsive behavior
 * - Security-first rendering
 */

'use client'

import { useEffect, useState } from 'react'
import { X, Copy, Download, Code, Eye } from 'lucide-react'
import { SandboxedIframe } from './SandboxedIframe'
import { MarkdownArtifact } from './MarkdownArtifact'

interface Artifact {
  id: string
  type: 'html' | 'markdown'
  title?: string
  content: string
  version: number
  created_at: string
  updated_at: string
}

interface ArtifactViewerProps {
  artifact: Artifact | null
  /** Full version history for this artifact title (used for the version switcher). */
  versions?: Artifact[]
  /** Called when the user picks a different version from the switcher. */
  onSelectVersion?: (artifact: Artifact) => void
  onClose: () => void
  className?: string
}

export function ArtifactViewer({
  artifact,
  versions,
  onSelectVersion,
  onClose,
  className = '',
}: ArtifactViewerProps) {
  const [showRaw, setShowRaw] = useState(false)

  // ESC closes the viewer (documented interaction). The listener is bound only
  // while the viewer is open so keyboard users can never get trapped.
  useEffect(() => {
    if (!artifact) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [artifact, onClose])

  if (!artifact) {
    return null
  }

  const hasVersionHistory = !!versions && versions.length > 1 && !!onSelectVersion

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content)
      // TODO: Add toast notification
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const handleDownload = () => {
    const extension = artifact.type === 'html' ? 'html' : 'md'
    const filename = `${artifact.title || 'artifact'}-v${artifact.version}.${extension}`
    const blob = new Blob([artifact.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div
      role="region"
      aria-label="Artifact viewer"
      className={`flex flex-col h-full bg-surface ${className}`}
    >
      {/* Header */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-elevated text-text-muted uppercase">
              {artifact.type}
            </span>
            {hasVersionHistory ? (
              <select
                value={artifact.id}
                onChange={e => {
                  const selected = versions!.find(v => v.id === e.target.value)
                  if (selected) onSelectVersion!(selected)
                }}
                aria-label="Artifact version"
                title="Artifact version"
                className="text-xs font-mono px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-border bg-transparent focus-visible-ring cursor-pointer"
              >
                {versions!.map(v => (
                  <option key={v.id} value={v.id}>
                    v{v.version}
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-primary/10 text-primary">
                v{artifact.version}
              </span>
            )}
          </div>
          <span className="font-medium truncate text-text-primary">
            {artifact.title || 'Artifact'}
          </span>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => setShowRaw(!showRaw)}
            className="btn-ghost p-2"
            title={showRaw ? 'Show preview' : 'Show raw code'}
            aria-label={showRaw ? 'Show preview' : 'Show raw code'}
          >
            {showRaw ? <Eye className="h-4 w-4" /> : <Code className="h-4 w-4" />}
          </button>
          <button
            onClick={handleCopy}
            className="btn-ghost p-2"
            title="Copy content"
            aria-label="Copy content"
          >
            <Copy className="h-4 w-4" />
          </button>
          <button
            onClick={handleDownload}
            className="btn-ghost p-2"
            title="Download"
            aria-label="Download artifact"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            onClick={onClose}
            className="btn-ghost p-2"
            title="Close"
            aria-label="Close artifact viewer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {showRaw ? (
          <pre className="h-full overflow-auto p-4 bg-background text-sm text-text-secondary font-mono">
            {artifact.content}
          </pre>
        ) : artifact.type === 'markdown' ? (
          <MarkdownArtifact content={artifact.content} className="h-full" />
        ) : (
          <SandboxedIframe
            content={artifact.content}
            title={artifact.title || 'HTML Artifact'}
            className="h-full"
          />
        )}
      </div>
    </div>
  )
}
