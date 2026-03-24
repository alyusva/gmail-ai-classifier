'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

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
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside style={{
      width: 216,
      minWidth: 216,
      backgroundColor: '#0A1020',
      borderRight: '1px solid #152040',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Logo */}
      <div style={{ padding: '22px 18px', borderBottom: '1px solid #152040' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34,
            background: 'linear-gradient(135deg, #2D7CF0 0%, #6D28D9 100%)',
            borderRadius: 9,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 17, flexShrink: 0,
          }}>
            ✉
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#B8C9E0', letterSpacing: '0.01em' }}>
              Gmail Classifier
            </div>
            <div style={{ fontSize: 10, color: '#2A3D5C', fontFamily: 'IBM Plex Mono, monospace', marginTop: 1 }}>
              ai · personal
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
              {active && (
                <span style={{ marginLeft: 'auto', width: 5, height: 5, borderRadius: '50%', backgroundColor: '#2D7CF0', flexShrink: 0 }} />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: '14px 18px', borderTop: '1px solid #152040' }}>
        <div style={{ fontSize: 10, color: '#2A3D5C', fontFamily: 'IBM Plex Mono, monospace', lineHeight: 1.6 }}>
          Supabase · eu-west-3<br />
          <span style={{ color: '#1E3060' }}>rptnhggbsnuuxgvwobmm</span>
        </div>
      </div>
    </aside>
  )
}
