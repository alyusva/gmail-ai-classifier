'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import type { Taxonomy, ClassificationSummary } from '@/lib/types'

interface CategoryRow extends Taxonomy { email_count: number }

const BAR_COLORS = ['#2D7CF0','#8B5CF6','#10B981','#F59E0B','#EF4444','#06B6D4','#EC4899','#3B82F6','#A78BFA','#34D399','#FBBF24','#F87171','#60A5FA','#C084FC','#4ADE80']

export default function CategoriasPage() {
  const [rows, setRows]       = useState<CategoryRow[]>([])
  const [loading, setLoading] = useState(true)
  const [maxCount, setMax]    = useState(1)

  useEffect(() => {
    async function load() {
      const [taxRes, sumRes] = await Promise.all([
        supabase.from('taxonomy').select('*').order('label'),
        supabase.from('classification_summary').select('*'),
      ])
      const tax = (taxRes.data ?? []) as Taxonomy[]
      const sum = (sumRes.data ?? []) as ClassificationSummary[]
      const map = new Map(sum.map(s => [s.label, s.email_count]))

      const merged: CategoryRow[] = tax.map(t => ({ ...t, email_count: map.get(t.label) ?? 0 }))

      // add summary rows not in taxonomy
      sum.forEach(s => {
        if (!tax.find(t => t.label === s.label))
          merged.push({ label: s.label, gmail_label_id: '', created_at: '', email_count: s.email_count })
      })

      merged.sort((a, b) => b.email_count - a.email_count)
      setMax(Math.max(...merged.map(r => r.email_count), 1))
      setRows(merged)
      setLoading(false)
    }
    load()
  }, [])

  const total = rows.reduce((s, r) => s + r.email_count, 0)

  return (
    <div style={{ padding: 32, maxWidth: 920 }}>

      {/* Header */}
      <div style={{ marginBottom: 26 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: '#E8EFF8', letterSpacing: '-0.01em' }}>Categorías</h1>
        <p style={{ fontSize: 12, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', marginTop: 4 }}>
          {rows.length} categorías · {total.toLocaleString()} emails clasificados
        </p>
      </div>

      {/* Table */}
      <div style={{ backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 10, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #152040' }}>
              {[['#','44px'],['CATEGORÍA','auto'],['DISTRIBUCIÓN','210px'],['EMAILS','80px'],['GMAIL LABEL','130px']].map(([h, w]) => (
                <th key={h} style={{ padding: '11px 16px', textAlign: 'left', fontSize: 10, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', letterSpacing: '0.08em', fontWeight: 500, width: w }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ padding: 60, textAlign: 'center', color: '#2A3D5C', fontSize: 13, fontFamily: 'IBM Plex Mono, monospace' }}>Cargando…</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={5} style={{ padding: 60, textAlign: 'center', color: '#2A3D5C', fontSize: 13 }}>Sin categorías. Ejecuta primero el clasificador.</td></tr>
            ) : rows.map((row, idx) => {
              const pct   = Math.round((row.email_count / maxCount) * 100)
              const color = BAR_COLORS[idx % BAR_COLORS.length]
              const hasLabel = row.gmail_label_id && row.gmail_label_id !== ''

              return (
                <tr key={row.label}
                  style={{ borderBottom: idx < rows.length - 1 ? '1px solid #0F1E35' : 'none' }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#0F1828')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td style={{ padding: '14px 16px', fontSize: 10, color: '#2A3D5C', fontFamily: 'IBM Plex Mono, monospace' }}>
                    {String(idx + 1).padStart(2, '0')}
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: 13, color: '#B8C9E0', fontWeight: 500 }}>
                    {row.label}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ flex: 1, height: 5, backgroundColor: '#152040', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${pct}%`, backgroundColor: color, borderRadius: 3, transition: 'width 0.4s ease' }} />
                      </div>
                      <span style={{ fontSize: 10, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', width: 34, textAlign: 'right' }}>
                        {pct}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: 13, color, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 600 }}>
                    {row.email_count.toLocaleString()}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    {hasLabel
                      ? <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, backgroundColor: 'rgba(16,185,129,0.08)', color: '#10B981', border: '1px solid rgba(16,185,129,0.2)', fontFamily: 'IBM Plex Mono, monospace' }}>✓ vinculado</span>
                      : <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, backgroundColor: 'rgba(74,98,133,0.06)', color: '#4A6285', border: '1px solid rgba(74,98,133,0.15)', fontFamily: 'IBM Plex Mono, monospace' }}>— sin label</span>
                    }
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
