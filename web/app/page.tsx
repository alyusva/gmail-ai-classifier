import { supabase } from '@/lib/supabase'
import { CategoryChart } from '@/components/category-chart'
import { RunPanel } from '@/components/run-panel'
import type { ClassificationSummary, EmailWithClassification } from '@/lib/types'

/* ─── helpers ─── */
function fmt(d: string | null) {
  if (!d) return '—'
  try { return new Date(d).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }) }
  catch { return d }
}

/* ─── stat card ─── */
const COLORS = {
  blue:   { acc: '#2D7CF0', bg: 'rgba(45,124,240,0.07)',  border: 'rgba(45,124,240,0.2)'  },
  violet: { acc: '#8B5CF6', bg: 'rgba(139,92,246,0.07)', border: 'rgba(139,92,246,0.2)' },
  green:  { acc: '#10B981', bg: 'rgba(16,185,129,0.07)',  border: 'rgba(16,185,129,0.2)'  },
  amber:  { acc: '#F59E0B', bg: 'rgba(245,158,11,0.07)',  border: 'rgba(245,158,11,0.2)'  },
} as const

function StatCard({ label, value, sub, color }: { label: string; value: number; sub?: string; color: keyof typeof COLORS }) {
  const c = COLORS[color]
  return (
    <div style={{
      flex: 1, position: 'relative', overflow: 'hidden',
      backgroundColor: '#0D1428', border: `1px solid ${c.border}`,
      borderRadius: 10, padding: '20px 22px',
    }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(to right, ${c.acc}, transparent)` }} />
      <div style={{ fontSize: 10, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', letterSpacing: '0.1em', marginBottom: 10 }}>
        {label.toUpperCase()}
      </div>
      <div style={{ fontSize: 38, fontWeight: 600, color: c.acc, fontFamily: 'IBM Plex Mono, monospace', lineHeight: 1 }}>
        {value.toLocaleString()}
      </div>
      {sub && <div style={{ fontSize: 11, color: '#4A6285', marginTop: 6 }}>{sub}</div>}
    </div>
  )
}

/* ─── data fetching ─── */
async function getData() {
  const [total, classified, applied, categories, recent] = await Promise.all([
    supabase.from('emails').select('*', { count: 'exact', head: true }),
    supabase.from('classifications').select('*', { count: 'exact', head: true }),
    supabase.from('classifications').select('*', { count: 'exact', head: true }).eq('applied', true),
    supabase.from('classification_summary').select('*').limit(10),
    supabase.from('emails')
      .select('*, classifications(labels, applied, classified_at, confidence)')
      .order('extracted_at', { ascending: false })
      .limit(10),
  ])
  const t = total.count ?? 0
  const c = classified.count ?? 0
  const a = applied.count ?? 0
  return {
    total: t, classified: c, applied: a, pending: c - a,
    rate: t > 0 ? Math.round((c / t) * 100) : 0,
    categories: (categories.data ?? []) as ClassificationSummary[],
    recent: (recent.data ?? []) as EmailWithClassification[],
  }
}

/* ─── page ─── */
export default async function DashboardPage() {
  const d = await getData()

  return (
    <div style={{ padding: 32, maxWidth: 1440 }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: '#E8EFF8', letterSpacing: '-0.01em' }}>
          Panel de Control
        </h1>
        <p style={{ fontSize: 12, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', marginTop: 4 }}>
          {new Date().toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 24 }}>
        <StatCard label="Total Emails"  value={d.total}      color="blue"   sub="extraídos de Gmail" />
        <StatCard label="Clasificados"  value={d.classified} color="violet" sub={`${d.rate}% del total`} />
        <StatCard label="Aplicados"     value={d.applied}    color="green"  sub="etiquetas en Gmail" />
        <StatCard label="Pendientes"    value={d.pending}    color="amber"  sub="por aplicar" />
      </div>

      {/* Run panel */}
      <div style={{ marginBottom: 18 }}>
        <RunPanel />
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 370px', gap: 18 }}>

        {/* Chart */}
        <div style={{ backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 10, padding: 24 }}>
          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: '#B8C9E0' }}>Distribución por Categoría</div>
            <div style={{ fontSize: 11, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', marginTop: 2 }}>top 10 · emails clasificados</div>
          </div>
          {d.categories.length > 0
            ? <CategoryChart data={d.categories} />
            : <div style={{ height: 290, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2A3D5C', fontSize: 13 }}>Sin datos de clasificación aún</div>
          }
        </div>

        {/* Recent emails */}
        <div style={{ backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 10, padding: 24, overflow: 'hidden' }}>
          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: '#B8C9E0' }}>Emails Recientes</div>
            <div style={{ fontSize: 11, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', marginTop: 2 }}>últimos 10 extraídos</div>
          </div>

          {d.recent.length === 0
            ? <div style={{ textAlign: 'center', color: '#2A3D5C', fontSize: 13, padding: '40px 0' }}>Sin emails todavía</div>
            : d.recent.map((email) => {
                const cls = email.classifications as any
                const isApplied    = !!cls?.applied
                const isClassified = !!cls
                const badge = isApplied
                  ? { label: 'aplicado',    bg: 'rgba(16,185,129,0.1)',  color: '#10B981', border: 'rgba(16,185,129,0.25)' }
                  : isClassified
                  ? { label: 'clasificado', bg: 'rgba(139,92,246,0.1)', color: '#8B5CF6', border: 'rgba(139,92,246,0.25)' }
                  : { label: 'pendiente',   bg: 'rgba(74,98,133,0.08)', color: '#4A6285', border: 'rgba(74,98,133,0.2)'  }

                return (
                  <div key={email.id} style={{ padding: '10px 0', borderBottom: '1px solid #0F1E35' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 6, marginBottom: 3 }}>
                      <span style={{ fontSize: 12, color: '#B8C9E0', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                        {email.subject || '(sin asunto)'}
                      </span>
                      <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, flexShrink: 0, fontFamily: 'IBM Plex Mono, monospace', backgroundColor: badge.bg, color: badge.color, border: `1px solid ${badge.border}` }}>
                        {badge.label}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                      <span style={{ fontSize: 11, color: '#4A6285', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {email.sender_email || email.sender || '—'}
                      </span>
                      <span style={{ fontSize: 10, color: '#2A3D5C', fontFamily: 'IBM Plex Mono, monospace', flexShrink: 0 }}>
                        {fmt(email.extracted_at)}
                      </span>
                    </div>
                    {isClassified && cls?.labels?.length > 0 && (
                      <div style={{ display: 'flex', gap: 4, marginTop: 5, flexWrap: 'wrap' }}>
                        {(cls.labels as string[]).slice(0, 2).map((l: string) => (
                          <span key={l} style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3, backgroundColor: 'rgba(45,124,240,0.08)', color: '#5BA4F5', border: '1px solid rgba(45,124,240,0.15)' }}>
                            {l}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })
          }
        </div>
      </div>
    </div>
  )
}
