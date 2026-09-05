'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, X, Plus, ChevronLeft, ChevronRight, Settings, Sparkles, Menu } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ArtifactViewer } from '@/components/ArtifactViewer'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{ episode?: string; episode_title?: string; title?: string; guest?: string }>
  artifact_id?: string
  created_at: string
}

interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
}

interface Artifact {
  id: string
  type: 'html' | 'markdown'
  title?: string
  content: string
  version: number
  created_at: string
  updated_at: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [showArtifact, setShowArtifact] = useState(false)
  const [currentArtifact, setCurrentArtifact] = useState<Artifact | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [splitRatio, setSplitRatio] = useState(60)
  const [artifactVersions, setArtifactVersions] = useState<Artifact[]>([])
  const artifactsCacheRef = useRef<Record<string, Artifact>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_URL}/api/sessions`)
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
        if (data.length > 0 && !currentSessionId) {
          setCurrentSessionId(data[0].id)
        }
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    }
  }

  const fetchMessages = async (sessionId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/sessions/${sessionId}`)
      if (res.ok) {
        const data = await res.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  const createSession = async () => {
    try {
      const res = await fetch(`${API_URL}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' }),
      })
      if (res.ok) {
        const data = await res.json()
        setSessions(prev => [data, ...prev])
        setCurrentSessionId(data.id)
        setMessages([])
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !currentSessionId || isStreaming) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,
          message: input,
          provider: 'ollama',
          skill: 'auto',
        }),
      })

      if (!response.ok) throw new Error('Failed to send message')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ''
      let assistantMessage: Message | null = null
      let pendingSources: Message['sources'] = null
      let isArtifactMode = false
      let artifactBuffer = ''
      let artifactMetadata: Partial<Artifact> = {}

      if (reader) {
        let buffer = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          // Keep the last segment: it may be a partial line split across chunks
          buffer = lines.pop() ?? ''

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]
            if (line.startsWith('event:')) {
              const eventType = line.slice(6).trim()

              // Next line should be data
              const dataLine = lines[i + 1]
              if (dataLine && dataLine.startsWith('data:')) {
                try {
                  const data = JSON.parse(dataLine.slice(5).trim())

                  if (eventType === 'token') {
                    assistantContent += data.content || ''
                    if (!assistantMessage) {
                      assistantMessage = {
                        id: crypto.randomUUID(),
                        role: 'assistant',
                        content: assistantContent,
                        sources: pendingSources ?? undefined,
                        created_at: new Date().toISOString(),
                      }
                      pendingSources = null
                      setMessages(prev => [...prev, assistantMessage!])
                    } else {
                      setMessages(prev => prev.map(m =>
                        m.id === assistantMessage!.id ? { ...m, content: assistantContent } : m
                      ))
                    }
                  } else if (eventType === 'sources') {
                    if (assistantMessage) {
                      setMessages(prev => prev.map(m =>
                        m.id === assistantMessage!.id ? { ...m, sources: data.sources } : m
                      ))
                    } else {
                      // Retrieval precedes generation: sources can arrive
                      // before the first token. Buffer until the message exists.
                      pendingSources = data.sources
                    }
                  } else if (eventType === 'artifact_start') {
                    isArtifactMode = true
                    artifactBuffer = ''
                    artifactMetadata = {
                      type: data.type,
                      title: data.title,
                      version: 1,
                    }
                  } else if (eventType === 'artifact_chunk' && isArtifactMode) {
                    artifactBuffer += data.content || ''
                  } else if (eventType === 'artifact_done') {
                    isArtifactMode = false
                    const artifact: Artifact = {
                      id: data.artifact_id || crypto.randomUUID(),
                      type: artifactMetadata.type as 'html' | 'markdown',
                      title: artifactMetadata.title,
                      content: artifactBuffer,
                      version: artifactMetadata.version || 1,
                      created_at: new Date().toISOString(),
                      updated_at: new Date().toISOString(),
                    }
                    artifactsCacheRef.current[artifact.id] = artifact
                    setCurrentArtifact(artifact)
                    setShowArtifact(true)

                    if (currentSessionId && artifact.title) {
                      fetchArtifactVersions(currentSessionId, artifact.title)
                    }

                    if (assistantMessage) {
                      setMessages(prev => prev.map(m =>
                        m.id === assistantMessage!.id ? { ...m, artifact_id: artifact.id } : m
                      ))
                    } else {
                      // Artifact streams carry no token events. Mirror the
                      // backend, which persists an assistant message for the
                      // artifact exchange and links it to the artifact.
                      assistantMessage = {
                        id: crypto.randomUUID(),
                        role: 'assistant',
                        content: `Generated ${artifact.type} artifact`,
                        artifact_id: artifact.id,
                        sources: pendingSources ?? undefined,
                        created_at: new Date().toISOString(),
                      }
                      pendingSources = null
                      setMessages(prev => [...prev, assistantMessage!])
                    }
                  } else if (eventType === 'error') {
                    // Surface backend/stream errors instead of failing silently
                    setMessages(prev => [...prev, {
                      id: crypto.randomUUID(),
                      role: 'assistant',
                      content: `⚠️ ${data.message || 'Something went wrong while generating a response. Please try again.'}`,
                      created_at: new Date().toISOString(),
                    }])
                  }
                } catch (parseError) {
                  // Ignore parse errors for incomplete chunks
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      // Keep the user message visible and surface a clear inline error
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '⚠️ Unable to reach the server. Please check your connection and try again.',
        created_at: new Date().toISOString(),
      }])
    } finally {
      setIsStreaming(false)
    }
  }

  const fetchArtifactVersions = async (sessionId: string, title: string) => {
    try {
      const res = await fetch(
        `${API_URL}/api/artifacts/versions/${sessionId}/${encodeURIComponent(title)}`
      )
      if (res.ok) {
        const data = await res.json()
        setArtifactVersions(data.versions || [])
      } else {
        setArtifactVersions([])
      }
    } catch (error) {
      console.error('Failed to fetch artifact versions:', error)
      setArtifactVersions([])
    }
  }

  const handleArtifactClick = async (artifactId: string) => {
    // Check in-memory cache first for instant re-opening
    const cached = artifactsCacheRef.current[artifactId]
    if (cached) {
      setCurrentArtifact(cached)
      setShowArtifact(true)
      if (currentSessionId && cached.title) {
        fetchArtifactVersions(currentSessionId, cached.title)
      }
    }
    try {
      const res = await fetch(`${API_URL}/api/artifacts/${artifactId}`)
      if (res.ok) {
        const artifact = await res.json()
        artifactsCacheRef.current[artifact.id] = artifact
        setCurrentArtifact(artifact)
        setShowArtifact(true)
        if (currentSessionId && artifact.title) {
          fetchArtifactVersions(currentSessionId, artifact.title)
        }
      }
    } catch (error) {
      console.error('Failed to fetch artifact:', error)
    }
  }

  const handleResize = (e: React.MouseEvent) => {
    const startX = e.clientX
    const startRatio = splitRatio

    const onMouseMove = (moveEvent: MouseEvent) => {
      const containerWidth = chatContainerRef.current?.offsetWidth || 800
      const deltaX = moveEvent.clientX - startX
      const newRatio = Math.max(30, Math.min(70, startRatio + (deltaX / containerWidth) * 100))
      setSplitRatio(newRatio)
    }

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }

  useEffect(() => {
    fetchSessions()
    const savedRatio = localStorage.getItem('splitRatio')
    if (savedRatio) setSplitRatio(parseInt(savedRatio, 10))
  }, [])

  useEffect(() => {
    if (currentSessionId) {
      fetchMessages(currentSessionId)
    }
  }, [currentSessionId])

  useEffect(() => {
    localStorage.setItem('splitRatio', splitRatio.toString())
  }, [splitRatio])

  const currentSession = sessions.find(s => s.id === currentSessionId)

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside
        aria-label="Session sidebar"
        className={cn(
          'fixed md:relative inset-y-0 left-0 z-40 w-72 flex flex-col border-r border-border bg-surface md:transition-all md:duration-200',
          'transform md:transform-none',
          mobileNavOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
          sidebarOpen ? 'md:w-72' : 'md:w-16'
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-border">
          <h1 className={cn('font-semibold text-lg truncate', sidebarOpen && 'opacity-100', !sidebarOpen && 'opacity-0')}>
            Lenny Growth
          </h1>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="btn-ghost p-2"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          <button
            onClick={createSession}
            className="btn-primary w-full justify-start mb-4"
            disabled={isStreaming}
          >
            <Plus className="h-4 w-4" />
            {sidebarOpen && 'New Chat'}
          </button>

          <div className={cn('space-y-1', !sidebarOpen && 'hidden')}>
            <p className="px-2 text-xs font-medium text-text-muted uppercase tracking-wider mb-2">
              Recent
            </p>
            {sessions.slice(0, 10).map(session => (
              <button
                key={session.id}
                onClick={() => setCurrentSessionId(session.id)}
                className={cn(
                  'w-full text-left px-2 py-2 rounded-md text-sm transition-colors truncate',
                  currentSessionId === session.id
                    ? 'bg-primary/10 text-primary'
                    : 'text-text-secondary hover:bg-surface-elevated hover:text-text-primary'
                )}
                title={session.title}
              >
                {session.title || 'Untitled'}
              </button>
            ))}
          </div>
        </div>

        <div className="p-3 border-t border-border">
          <button className="btn-ghost w-full justify-start gap-2" disabled={isStreaming}>
            <Settings className="h-4 w-4" />
            {sidebarOpen && 'Settings'}
          </button>
        </div>
      </aside>

      {/* Mobile sidebar backdrop */}
      {mobileNavOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setMobileNavOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0" ref={chatContainerRef}>
        {/* Header */}
        <header className="flex h-16 items-center justify-between px-4 border-b border-border bg-surface">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileNavOpen(true)}
              className="btn-ghost p-2 md:hidden"
              aria-label="Open navigation menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <h2 className="font-medium text-lg truncate max-w-[300px]">
              {currentSession?.title || 'Select a session'}
            </h2>
            {currentSession && (
              <span className="text-xs text-text-muted px-2 py-0.5 rounded bg-surface-elevated">
                {messages.length} messages
              </span>
            )}
          </div>
        </header>

        {/* Chat + Artifact Split */}
        <div className="flex-1 flex relative overflow-hidden">
          {/* Chat Pane */}
          <div
            className="chat-pane-host flex flex-col overflow-hidden"
            style={{ '--chat-split': showArtifact ? `${splitRatio}%` : '100%' } as React.CSSProperties}
          >
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-text-muted">
                  <Sparkles className="h-12 w-12 mb-4 opacity-50" />
                  <p className="text-lg font-medium">Welcome to Lenny Growth Assistant</p>
                  <p className="text-sm mt-2 text-center max-w-md">
                    Ask questions about product, growth, and startups grounded in Lenny's Podcast transcripts.
                    Try <span className="text-primary">/ship30</span> for essays or <span className="text-primary">/artifact</span> for frameworks.
                  </p>
                  <div className="mt-6 flex flex-wrap gap-2 justify-center">
                    {[
                      'How do I improve retention?',
                      'Create a PLG framework',
                      '/ship30 Write about onboarding',
                      'Make a pricing calculator',
                    ].map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => setInput(suggestion)}
                        className="btn-secondary text-xs px-3 py-1"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map(message => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex gap-3 max-w-3xl mx-auto w-full',
                      message.role === 'user' && 'flex-row-reverse'
                    )}
                  >
                    <div
                      className={cn(
                        'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
                        message.role === 'user'
                          ? 'bg-primary text-background'
                          : 'bg-surface-elevated text-text-secondary'
                      )}
                    >
                      {message.role === 'user' ? 'U' : 'L'}
                    </div>
                    <div
                      className={cn(
                        'flex-1 min-w-0',
                        message.role === 'user' ? 'text-right' : 'text-left'
                      )}
                    >
                      <div className="prose prose-invert max-w-none">
                        <p className="whitespace-pre-wrap text-text-primary">{message.content}</p>
                      </div>
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border">
                          <p className="text-xs text-text-muted flex flex-wrap gap-2">
                            Sources:{' '}
                            {message.sources.map((source: any, i: number) => (
                              <span key={i} className="text-primary hover:underline cursor-pointer">
                                {source.episode || source.title || source.episode_title || source.guest || 'Episode'}
                              </span>
                            ))}
                          </p>
                        </div>
                      )}
                      {message.artifact_id && (
                        <div className="mt-3">
                          <button
                            onClick={() => handleArtifactClick(message.artifact_id!)}
                            className="btn-ghost text-xs px-3 py-1.5"
                          >
                            View Artifact
                          </button>
                        </div>
                      )}
                      <p className="mt-1 text-xs text-text-muted">
                        {new Date(message.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-border bg-surface">
              <div className="flex gap-2">
                <textarea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={isStreaming ? 'Streaming...' : 'Ask about product, growth, or create artifacts...'}
                  className="textarea flex-1"
                  rows={3}
                  disabled={isStreaming}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage(e)
                    }
                  }}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isStreaming}
                  aria-label={isStreaming ? 'Stop generating' : 'Send message'}
                  className="btn-primary self-end mb-1"
                >
                  {isStreaming ? <X className="h-4 w-4" /> : <Send className="h-4 w-4" />}
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-1 text-xs text-text-muted">
                <kbd className="px-1.5 py-0.5 bg-surface-elevated rounded border border-border">Enter</kbd> to send •
                <kbd className="px-1.5 py-0.5 bg-surface-elevated rounded border border-border">Shift+Enter</kbd> for new line
              </div>
            </form>
          </div>

          {/* Resize Handle */}
          {showArtifact && (
            <div
              onMouseDown={handleResize}
              className="relative w-1 cursor-col-resize bg-border hover:bg-primary/50 transition-colors hidden md:flex items-center justify-center"
              style={{ width: '4px' }}
              role="separator"
              aria-label="Resize panes"
              tabIndex={0}
            >
              <div className="w-px h-8 bg-border rounded-full" />
            </div>
          )}

          {/* Artifact Pane */}
          {showArtifact && currentArtifact && (
            <div
              className="artifact-pane-host"
              style={{ '--artifact-split': `${100 - splitRatio}%` } as React.CSSProperties}
            >
              <ArtifactViewer
                artifact={currentArtifact}
                versions={artifactVersions}
                onSelectVersion={selected => setCurrentArtifact(selected)}
                onClose={() => {
                  setShowArtifact(false)
                  setTimeout(() => {
                    document.querySelector<HTMLTextAreaElement>('textarea')?.focus()
                  }, 50)
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
