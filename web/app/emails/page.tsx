'use client'

import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import type { EmailWithClassification } from '@/lib/types'

const PAGE_SIZE = 50
type Filter = 'all' | 'classified' | 'unclassified' | 'applied'

function fmt(d: string | null) {
  if (!d) return '—'
  try { return new Date(d).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }) }
  catch { return d }
}

const FILTERS: [Filter, string][] = [
  ['all', 'Todos'],
  ['classified', 'Clasificados'],
  ['unclassified', 'Sin clasificar'],
  ['applied', 'Aplicados'],
]

export default function EmailsPage() {
  const [emails, setEmails] = useState<EmailWithClassification[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]  = useState('')
  const [filter, setFilter]  = useState<Filter>('all')
  const [page, setPage]      = useState(0)
  const [total, setTotal]    = useState(0)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      let q = supabase
        .from('emails')
        .select('*, classifications(labels, applied, classified_at, confidence)', { count: 'exact' })
        .order('extracted_at', { ascending: false })
        .range(page * PAGE_SIZE, (page + 1) * PAGE_SIZE - 1)

      if (search.trim()) {
        q = q.or(`subject.ilike.%${search}%,sender_email.ilike.%${search}%,sender.ilike.%${search}%`)
      }

      const { data, count, error } = await q
      if (error) { console.error(error); return }

      let rows = (data ?? []) as EmailWithClassification[]
      if (filter === 'classified')   rows = rows.filter(e => e.classifications)
      if (filter === 'unclassified') rows = rows.filter(e => !e.classifications)
      if (filter === 'applied')      rows = rows.filter(e => (e.classifications as any)?.applied)

      setEmails(rows)
      setTotal(count ?? 0)
    } finally {
      setLoading(false)
    }
  }, [search, filter, page])

  useEffect(() => { setPage(0) }, [search, filter])
  useEffect(() => { fetch() }, [fetch])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  /* ─── render ─── */
  return (
    <div style={{ padding: 32, maxWidth: 1440 }}>

      {/* Header */}
      <div style={{ marginBottom: 26 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: '#E8EFF8', letterSpacing: '-0.01em' }}>Emails</h1>
        <p style={{ fontSize: 12, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', marginTop: 4 }}>
          {total.toLocaleString()} emails · pág. {page + 1}/{totalPages}
        </p>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 18, alignItems: 'center', flexWrap: 'wrap' }}>

        {/* Search */}
        <div style={{ position: 'relative', flex: '1 1 280px', maxWidth: 380 }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4A6285" strokeWidth="2"
            style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text" placeholder="Buscar por asunto o remitente…" value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%', padding: '9px 12px 9px 34px',
              backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 7,
              color: '#B8C9E0', fontSize: 13, outline: 'none',
            }}
          />
        </div>

        {/* Filter tabs */}
        <div style={{ display: 'flex', gap: 3, backgroundColor: '#0A1020', padding: 3, borderRadius: 7, border: '1px solid #152040' }}>
          {FILTERS.map(([val, lbl]) => (
            <button key={val} onClick={() => setFilter(val)} style={{
              padding: '6px 13px', borderRadius: 5, border: filter === val ? '1px solid #1E3060' : '1px solid transparent',
              cursor: 'pointer', fontSize: 12, transition: 'all 0.15s',
              backgroundColor: filter === val ? '#0D1428' : 'transparent',
              color: filter === val ? '#5BA4F5' : '#4A6285',
              fontWeight: filter === val ? 500 : 400,
            }}>
              {lbl}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={{ backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 10, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #152040' }}>
              {[['FECHA','110px'],['REMITENTE','190px'],['ASUNTO','auto'],['CATEGORÍAS','220px'],['ESTADO','105px']].map(([h,w]) => (
                <th key={h} style={{ padding: '11px 16px', textAlign: 'left', fontSize: 10, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', letterSpacing: '0.08em', fontWeight: 500, width: w }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ padding: 60, textAlign: 'center', color: '#2A3D5C', fontSize: 13, fontFamily: 'IBM Plex Mono, monospace' }}>Cargando…</td></tr>
            ) : emails.length === 0 ? (
              <tr><td colSpan={5} style={{ padding: 60, textAlign: 'center', color: '#2A3D5C', fontSize: 13 }}>No se encontraron emails</td></tr>
            ) : emails.map((email, idx) => {
              const cls        = email.classifications as any
              const isClassified = !!cls
              const isApplied    = !!cls?.applied
              const labels       = (cls?.labels ?? []) as string[]

              const badge = isApplied
                ? { txt: '✓ aplicado',    bg: 'rgba(16,185,129,0.09)',  color: '#10B981', border: 'rgba(16,185,129,0.22)' }
                : isClassified
                ? { txt: '◎ clasificado', bg: 'rgba(139,92,246,0.09)', color: '#8B5CF6', border: 'rgba(139,92,246,0.22)' }
                : { txt: '○ pendiente',   bg: 'rgba(74,98,133,0.07)',  color: '#4A6285', border: 'rgba(74,98,133,0.18)' }

              return (
                <tr key={email.id}
                  style={{ borderBottom: idx < emails.length - 1 ? '1px solid #0F1E35' : 'none', cursor: 'default' }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#0F1828')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td style={{ padding: '11px 16px', fontSize: 11, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', whiteSpace: 'nowrap' }}>
                    {fmt(email.extracted_at)}
                  </td>
                  <td style={{ padding: '11px 16px', maxWidth: 190 }}>
                    <div style={{ fontSize: 12, color: '#B8C9E0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {email.sender || '—'}
                    </div>
                    {email.sender_email && email.sender && (
                      <div style={{ fontSize: 11, color: '#4A6285', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
                        {email.sender_email}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '11px 16px' }}>
                    <div style={{ fontSize: 12, color: '#B8C9E0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {email.subject || '(sin asunto)'}
                    </div>
                    {email.snippet && (
                      <div style={{ fontSize: 11, color: '#4A6285', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
                        {email.snippet}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '11px 16px' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {labels.slice(0, 3).map(l => (
                        <span key={l} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, backgroundColor: 'rgba(45,124,240,0.07)', color: '#5BA4F5', border: '1px solid rgba(45,124,240,0.15)' }}>
                          {l}
                        </span>
                      ))}
                      {labels.length > 3 && <span style={{ fontSize: 10, color: '#4A6285', alignSelf: 'center' }}>+{labels.length - 3}</span>}
                      {!isClassified && <span style={{ fontSize: 11, color: '#2A3D5C' }}>—</span>}
                    </div>
                  </td>
                  <td style={{ padding: '11px 16px' }}>
                    <span style={{ fontSize: 10, padding: '3px 8px', borderRadius: 4, fontFamily: 'IBM Plex Mono, monospace', whiteSpace: 'nowrap', backgroundColor: badge.bg, color: badge.color, border: `1px solid ${badge.border}` }}>
                      {badge.txt}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10, marginTop: 20 }}>
          <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
            style={{ padding: '7px 16px', backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 6, color: page === 0 ? '#2A3D5C' : '#B8C9E0', fontSize: 12, cursor: page === 0 ? 'default' : 'pointer' }}>
            ← Anterior
          </button>
          <span style={{ fontSize: 11, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace' }}>{page + 1} / {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
            style={{ padding: '7px 16px', backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 6, color: page >= totalPages - 1 ? '#2A3D5C' : '#B8C9E0', fontSize: 12, cursor: page >= totalPages - 1 ? 'default' : 'pointer' }}>
            Siguiente →
          </button>
        </div>
      )}
    </div>
  )
}
