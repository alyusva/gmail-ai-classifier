import type { Metadata } from 'next'
import { Sidebar } from '@/components/sidebar'
import { SessionProvider } from '@/components/session-provider'
import './globals.css'

export const metadata: Metadata = {
  title: 'Gmail Classifier',
  description: 'Clasifica tu bandeja de entrada automáticamente con IA',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body style={{ display: 'flex', height: '100vh', overflow: 'hidden', backgroundColor: '#050913' }}>
        <SessionProvider>
          <Sidebar />
          <main style={{ flex: 1, overflowY: 'auto' }} className="dot-grid">
            {children}
          </main>
        </SessionProvider>
      </body>
    </html>
  )
}
