'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { PLANS } from '@/lib/stripe'

const PALETTE = {
  free:     { accent: '#4A6285', border: '#152040', glow: 'transparent' },
  pro:      { accent: '#2D7CF0', border: '#1E3060', glow: 'rgba(45,124,240,0.12)' },
  business: { accent: '#8B5CF6', border: '#4C1D95', glow: 'rgba(139,92,246,0.12)' },
}

export default function PricingPage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [loading, setLoading] = useState<string | null>(null)

  const handleUpgrade = async (plan: keyof typeof PLANS) => {
    if (!session) { router.push('/login'); return }
    if (plan === 'free') return
    setLoading(plan)
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan }),
      })
      const { url } = await res.json()
      if (url) window.location.href = url
    } finally {
      setLoading(null)
    }
  }

  const currentPlan = (session as any)?.subscription?.plan ?? 'free'

  return (
    <div style={{ padding: '48px 32px', maxWidth: 1100, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 52 }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, color: '#E8EFF8', letterSpacing: '-0.02em' }}>
          Planes simples y transparentes
        </h1>
        <p style={{ fontSize: 15, color: '#4A6285', marginTop: 12 }}>
          Empieza gratis. Escala cuando lo necesites.
        </p>
      </div>

      {/* Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
        {(Object.entries(PLANS) as [keyof typeof PLANS, typeof PLANS[keyof typeof PLANS]][]).map(([key, plan]) => {
          const c = PALETTE[key]
          const isCurrent = currentPlan === key
          const isPopular = key === 'pro'

          return (
            <div key={key} style={{
              position: 'relative', padding: '32px 28px',
              backgroundColor: '#0D1428',
              border: `1px solid ${c.border}`,
              borderRadius: 14,
              boxShadow: c.glow !== 'transparent' ? `0 0 40px ${c.glow}` : 'none',
            }}>
              {/* Top gradient line */}
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, backgroundColor: c.accent, borderRadius: '14px 14px 0 0' }} />

              {isPopular && (
                <div style={{
                  position: 'absolute', top: 16, right: 16,
                  fontSize: 10, padding: '3px 9px', borderRadius: 20,
                  backgroundColor: 'rgba(45,124,240,0.12)', color: '#5BA4F5',
                  border: '1px solid rgba(45,124,240,0.25)', fontWeight: 600,
                  fontFamily: 'IBM Plex Mono, monospace',
                }}>POPULAR</div>
              )}

              <div style={{ fontSize: 13, color: c.accent, fontWeight: 600, letterSpacing: '0.05em', marginBottom: 12 }}>
                {plan.name.toUpperCase()}
              </div>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 6 }}>
                <span style={{ fontSize: 42, fontWeight: 700, color: '#E8EFF8', fontFamily: 'IBM Plex Mono, monospace' }}>
                  {plan.price === 0 ? '0' : plan.price}
                </span>
                <span style={{ fontSize: 14, color: '#4A6285' }}>€/mes</span>
              </div>
              <div style={{ fontSize: 12, color: '#4A6285', marginBottom: 28 }}>
                {plan.emails_limit >= 999_999 ? 'Emails ilimitados' : `${plan.emails_limit.toLocaleString()} emails/mes`}
              </div>

              {/* Features */}
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {plan.features.map((f) => (
                  <li key={f} style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 13, color: '#B8C9E0' }}>
                    <span style={{ color: c.accent, fontSize: 15, flexShrink: 0 }}>✓</span>
                    {f}
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <button
                onClick={() => handleUpgrade(key)}
                disabled={isCurrent || loading === key}
                style={{
                  width: '100%', padding: '12px', borderRadius: 8,
                  fontSize: 13, fontWeight: 600, cursor: isCurrent ? 'default' : 'pointer',
                  border: `1px solid ${c.border}`,
                  background: isCurrent
                    ? 'rgba(74,98,133,0.08)'
                    : key === 'free'
                    ? 'transparent'
                    : `linear-gradient(135deg, ${c.accent}CC, ${c.accent})`,
                  color: isCurrent ? '#4A6285' : key === 'free' ? c.accent : '#fff',
                  transition: 'opacity 0.2s',
                  opacity: loading === key ? 0.6 : 1,
                }}
              >
                {isCurrent ? '✓ Plan actual' : loading === key ? 'Procesando…' : key === 'free' ? 'Empezar gratis' : `Suscribirme a ${plan.name}`}
              </button>
            </div>
          )
        })}
      </div>

      {/* FAQ teaser */}
      <p style={{ textAlign: 'center', fontSize: 12, color: '#2A3D5C', marginTop: 40 }}>
        Pago seguro con Stripe · Cancela cuando quieras · Sin permanencia
      </p>
    </div>
  )
}
