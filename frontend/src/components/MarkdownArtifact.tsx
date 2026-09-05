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
    <div className={`prose prose-invert max-w-none p-6 overflow-y-auto ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          // Custom component overrides for better styling
          h1: ({ node, ...props }) => (
            <h1 className="text-3xl font-bold mb-4 mt-8 first:mt-0 text-text-primary" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-2xl font-semibold mb-3 mt-6 text-text-primary" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xl font-semibold mb-2 mt-4 text-text-primary" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="mb-4 leading-relaxed text-text-secondary" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside mb-4 space-y-2 text-text-secondary" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside mb-4 space-y-2 text-text-secondary" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="ml-4" {...props} />
          ),
          code: ({ node, inline, ...props }: any) =>
            inline ? (
              <code className="bg-surface-elevated px-1.5 py-0.5 rounded text-sm text-primary" {...props} />
            ) : (
              <code className="block bg-surface-elevated p-4 rounded-md overflow-x-auto text-sm" {...props} />
            ),
          pre: ({ node, ...props }) => (
            <pre className="mb-4 overflow-x-auto" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-primary/50 pl-4 italic my-4 text-text-muted" {...props} />
          ),
          a: ({ node, ...props }) => (
            <a
              className="text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto mb-4">
              <table className="min-w-full border border-border" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-surface-elevated" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="border border-border px-4 py-2 text-left font-semibold" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-border px-4 py-2" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
