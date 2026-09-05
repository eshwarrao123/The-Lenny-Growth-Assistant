/**
 * Markdown artifact renderer component.
 * 
 * Renders Markdown safely using react-markdown with:
 * - GitHub-flavored Markdown support
 * - Sanitized HTML output
 * - Syntax highlighting ready
 */

'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'

interface MarkdownArtifactProps {
  content: string
  className?: string
}

export function MarkdownArtifact({ content, className = '' }: MarkdownArtifactProps) {
  return (
    <div className={`prose prose-invert max-w-none p-8 overflow-y-auto ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          // Custom component overrides for better styling
          h1: ({ node, ...props }) => (
            <h1 className="text-4xl font-bold mb-6 mt-10 first:mt-0 text-text-primary tracking-tight leading-tight" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-3xl font-semibold mb-5 mt-8 text-text-primary tracking-tight leading-tight" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xl font-semibold mb-4 mt-6 text-text-primary" {...props} />
          ),
          h4: ({ node, ...props }) => (
            <h4 className="text-lg font-semibold mb-3 mt-4 text-text-primary" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="mb-5 leading-relaxed text-text-secondary text-base" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-outside mb-5 space-y-2 text-text-secondary ml-5" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-outside mb-5 space-y-2 text-text-secondary ml-5" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="leading-relaxed" {...props} />
          ),
          code: ({ node, inline, ...props }: any) =>
            inline ? (
              <code className="bg-surface-elevated px-2 py-0.5 rounded text-sm text-primary font-mono" {...props} />
            ) : (
              <code className="block bg-surface-elevated p-4 rounded-lg overflow-x-auto text-sm font-mono text-text-secondary" {...props} />
            ),
          pre: ({ node, ...props }) => (
            <pre className="mb-5 overflow-x-auto rounded-lg bg-background border border-border" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-primary/50 pl-6 italic my-6 text-text-muted text-base" {...props} />
          ),
          a: ({ node, ...props }) => (
            <a
              className="text-primary hover:text-primary-muted underline decoration-primary/30 hover:decoration-primary transition-colors"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto mb-6">
              <table className="min-w-full border border-border rounded-lg" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-surface-elevated border-b border-border" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="border border-border px-4 py-3 text-left font-semibold text-text-primary" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-border px-4 py-3 text-text-secondary" {...props} />
          ),
          hr: ({ node, ...props }) => (
            <hr className="my-8 border-t border-border" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
