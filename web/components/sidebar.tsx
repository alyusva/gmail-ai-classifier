'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useSession, signOut } from 'next-auth/react'

const NAV = [
  {
    href: '/',
    label: 'Dashboard',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    href: '/emails',
    label: 'Emails',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="4" width="20" height="16" rx="2" />
        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
      </svg>
    ),
  },
  {
    href: '/categorias',
    label: 'Categorías',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 5H2v7l6.29 6.29c.94.94 2.48.94 3.42 0l3.58-3.58c.94-.94.94-2.48 0-3.42L9 5Z" />
        <path d="M6 9.01V9" />
        <path d="m15 5 6.3 6.3a2.4 2.4 0 0 1 0 3.4L17 19" />
      </svg>
    ),
  },
  {
    href: '/pricing',
    label: 'Planes',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 1 0 0 7h5a3.5 3.5 0 1 1 0 7H6" />
      </svg>
    ),
  },
]

const PLAN_COLORS: Record<string, { color: string; bg: string }> = {
  free:     { color: '#4A6285', bg: 'rgba(74,98,133,0.1)'  },
  pro:      { color: '#2D7CF0', bg: 'rgba(45,124,240,0.1)' },
  business: { color: '#8B5CF6', bg: 'rgba(139,92,246,0.1)' },
}

export function Sidebar() {
  const pathname = usePathname()
  const { data: session } = useSession()
  const plan = (session as any)?.subscription?.plan ?? 'free'
  const pc = PLAN_COLORS[plan] ?? PLAN_COLORS.free

  return (
    <aside style={{
      width: 216, minWidth: 216,
      backgroundColor: '#0A1020',
      borderRight: '1px solid #152040',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Logo */}
      <div style={{ padding: '22px 18px', borderBottom: '1px solid #152040' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34,
            background: 'linear-gradient(135deg, #2D7CF0 0%, #6D28D9 100%)',
            borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 17, flexShrink: 0,
          }}>✉</div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#B8C9E0', letterSpacing: '0.01em' }}>
              Gmail Classifier
            </div>
            <div style={{ fontSize: 10, color: '#2A3D5C', fontFamily: 'IBM Plex Mono, monospace', marginTop: 1 }}>
              ai · saas
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: '14px 10px', flex: 1 }}>
        <div style={{ fontSize: 10, color: '#2A3D5C', fontFamily: 'IBM Plex Mono, monospace', letterSpacing: '0.12em', marginBottom: 8, paddingLeft: 8 }}>
          MENÚ
        </div>
        {NAV.map(({ href, label, icon }) => {
          const active = pathname === href
          return (
            <Link key={href} href={href} style={{
              display: 'flex', alignItems: 'center', gap: 9,
              padding: '8px 10px', borderRadius: 6, marginBottom: 2,
              textDecoration: 'none', fontSize: 13,
              fontWeight: active ? 500 : 400,
              color: active ? '#5BA4F5' : '#4A6285',
              backgroundColor: active ? 'rgba(45,124,240,0.08)' : 'transparent',
              border: active ? '1px solid rgba(45,124,240,0.18)' : '1px solid transparent',
              transition: 'all 0.15s',
            }}>
              <span style={{ opacity: active ? 1 : 0.6, display: 'flex' }}>{icon}</span>
              {label}
              {active && <span style={{ marginLeft: 'auto', width: 5, height: 5, borderRadius: '50%', backgroundColor: '#2D7CF0', flexShrink: 0 }} />}
            </Link>
          )
        })}
      </nav>

      {/* User footer */}
      {session?.user && (
        <div style={{ padding: '14px 12px', borderTop: '1px solid #152040' }}>
          {/* Plan badge */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '5px 10px', borderRadius: 6, marginBottom: 10,
            backgroundColor: pc.bg, border: `1px solid ${pc.color}22`,
          }}>
            <span style={{ fontSize: 10, color: pc.color, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 600 }}>
              {plan.toUpperCase()}
            </span>
            {plan === 'free' && (
              <Link href="/pricing" style={{ fontSize: 10, color: '#2D7CF0', textDecoration: 'none' }}>
                Upgrade →
              </Link>
            )}
          </div>

          {/* User info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 10 }}>
            {session.user.image ? (
              <img src={session.user.image} alt="" style={{ width: 28, height: 28, borderRadius: '50%', flexShrink: 0 }} />
            ) : (
              <div style={{ width: 28, height: 28, borderRadius: '50%', backgroundColor: '#152040', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: '#4A6285' }}>
                {session.user.name?.[0] ?? '?'}
              </div>
            )}
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: 12, color: '#B8C9E0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {session.user.name}
              </div>
              <div style={{ fontSize: 10, color: '#2A3D5C', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {session.user.email}
              </div>
            </div>
          </div>

          {/* Logout */}
          <button
            onClick={() => signOut({ callbackUrl: '/login' })}
            style={{
              width: '100%', padding: '7px', borderRadius: 6, cursor: 'pointer',
              backgroundColor: 'transparent', border: '1px solid #152040',
              color: '#4A6285', fontSize: 11, transition: 'all 0.15s',
            }}
            onMouseEnter={e => { (e.target as HTMLButtonElement).style.borderColor = '#EF4444'; (e.target as HTMLButtonElement).style.color = '#EF4444' }}
            onMouseLeave={e => { (e.target as HTMLButtonElement).style.borderColor = '#152040'; (e.target as HTMLButtonElement).style.color = '#4A6285' }}
          >
            Cerrar sesión
          </button>
        </div>
      )}
    </aside>
  )
}
