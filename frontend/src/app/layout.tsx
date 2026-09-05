import type { Metadata, Viewport } from 'next'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'Lenny Growth Assistant',
  description: 'AI assistant grounded in Lenny\'s Podcast transcripts',
}

export const viewport: Viewport = {
  themeColor: '#0A0A0B',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    // Geist loads via the CSS font stack (see tailwind.config.js: 'Geist',
    // 'system-ui', 'sans-serif'). next/font/google does not ship Geist in
    // Next 14.2, so we rely on the local font with system fallbacks.
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-text-primary antialiased">
        {children}
      </body>
    </html>
  )
}