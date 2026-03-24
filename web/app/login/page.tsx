'use client'

import { signIn } from 'next-auth/react'
import { useState } from 'react'

export default function LoginPage() {
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    setLoading(true)
    await signIn('google', { callbackUrl: '/' })
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      backgroundColor: '#050913',
      backgroundImage: 'radial-gradient(circle, #1a2744 1px, transparent 1px)',
      backgroundSize: '28px 28px',
    }}>
      <div style={{
        width: 420, padding: '48px 40px',
        backgroundColor: '#0D1428', border: '1px solid #1E3060',
        borderRadius: 16, textAlign: 'center', position: 'relative', overflow: 'hidden',
      }}>
        {/* Top gradient */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: 'linear-gradient(to right, #2D7CF0, #6D28D9)' }} />

        {/* Logo */}
        <div style={{
          width: 56, height: 56, margin: '0 auto 24px',
          background: 'linear-gradient(135deg, #2D7CF0, #6D28D9)',
          borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 26,
        }}>✉</div>

        <h1 style={{ fontSize: 22, fontWeight: 600, color: '#E8EFF8', marginBottom: 8 }}>
          Gmail Classifier
        </h1>
        <p style={{ fontSize: 13, color: '#4A6285', marginBottom: 36, lineHeight: 1.6 }}>
          Clasifica tu bandeja de entrada automáticamente<br />con inteligencia artificial.
        </p>

        {/* Sign in button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          style={{
            width: '100%', padding: '13px 20px',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
            backgroundColor: loading ? '#0A1020' : '#fff',
            border: '1px solid #1E3060',
            borderRadius: 9, cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: 14, fontWeight: 500,
            color: loading ? '#4A6285' : '#1a1a1a',
            transition: 'all 0.2s',
          }}
        >
          {!loading && (
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          )}
          {loading ? 'Conectando…' : 'Continuar con Google'}
        </button>

        <p style={{ fontSize: 11, color: '#2A3D5C', marginTop: 24, lineHeight: 1.7 }}>
          Al continuar, autorizas el acceso a tu Gmail para clasificar emails.<br />
          Nunca enviamos ni almacenamos el contenido de tus mensajes.
        </p>

        {/* Plans teaser */}
        <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid #152040', display: 'flex', justifyContent: 'center', gap: 24 }}>
          {[['Free', '1K emails/mes'], ['Pro', '15K emails/mes'], ['Business', 'Ilimitado']].map(([plan, desc]) => (
            <div key={plan} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: '#5BA4F5' }}>{plan}</div>
              <div style={{ fontSize: 10, color: '#2A3D5C', marginTop: 2 }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
