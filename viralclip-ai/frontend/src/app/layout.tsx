import type { Metadata } from 'next'
import '@/styles/globals.css'

export const metadata: Metadata = {
  title: 'ViralClip AI - Generate Viral Shorts from Long Videos',
  description: 'AI-powered tool to convert YouTube videos into viral-ready Shorts, Reels, and TikTok clips with auto-captions',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
