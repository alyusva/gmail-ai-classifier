'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

type Step = 'extract' | 'classify' | 'apply' | 'dry-run'
type Status = 'idle' | 'running' | 'ok' | 'error'

interface StepState { status: Status; elapsed?: string; log?: string }

const STEPS: { key: Step; label: string; icon: string; desc: string }[] = [
  { key: 'extract',  label: 'Extraer',    icon: '↓', desc: 'Descarga emails de Gmail' },
  { key: 'classify', label: 'Clasificar', icon: '◎', desc: 'Clasifica con Claude IA' },
  { key: 'apply',    label: 'Aplicar',    icon: '✓', desc: 'Aplica etiquetas en Gmail' },
]

const COLOR: Record<Status, { color: string; border: string; bg: string }> = {
  idle:    { color: '#4A6285', border: '#152040', bg: 'transparent' },
  running: { color: '#F59E0B', border: '#92400E', bg: 'rgba(245,158,11,0.06)' },
  ok:      { color: '#10B981', border: '#065F46', bg: 'rgba(16,185,129,0.06)' },
  error:   { color: '#EF4444', border: '#7F1D1D', bg: 'rgba(239,68,68,0.06)' },
}

async function runCommand(command: Step): Promise<{ ok: boolean; elapsed: string; log: string }> {
  const res = await fetch('/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command }),
  })
  return res.json()
}

export function RunPanel() {
  const router = useRouter()
  const [steps, setSteps] = useState<Record<Step, StepState>>({
    extract:  { status: 'idle' },
    classify: { status: 'idle' },
    apply:    { status: 'idle' },
    'dry-run':{ status: 'idle' },
  })
  const [expanded, setExpanded] = useState<Step | null>(null)
  const [globalRunning, setGlobalRunning] = useState(false)

  const setStep = (key: Step, s: Partial<StepState>) =>
    setSteps(prev => ({ ...prev, [key]: { ...prev[key], ...s } }))

  async function runOne(key: Step) {
    if (globalRunning) return
    setGlobalRunning(true)
    setStep(key, { status: 'running', log: undefined })
    setExpanded(key)
    const r = await runCommand(key)
    setStep(key, { status: r.ok ? 'ok' : 'error', elapsed: r.elapsed, log: r.log })
    setGlobalRunning(false)
    if (r.ok) router.refresh()
  }

  async function runAll() {
    if (globalRunning) return
    setGlobalRunning(true)
    for (const { key } of STEPS) {
      setStep(key, { status: 'running', log: undefined })
      setExpanded(key)
      const r = await runCommand(key)
      setStep(key, { status: r.ok ? 'ok' : 'error', elapsed: r.elapsed, log: r.log })
      if (!r.ok) break
    }
    setGlobalRunning(false)
    router.refresh()
  }

  return (
    <div style={{ backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 10, padding: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 500, color: '#B8C9E0' }}>Ejecutar Clasificador</div>
          <div style={{ fontSize: 11, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', marginTop: 2 }}>pipeline: extract → classify → apply</div>
        </div>
        <button
          onClick={runAll}
          disabled={globalRunning}
          style={{
            padding: '8px 16px', borderRadius: 7, fontSize: 12, fontWeight: 500, cursor: globalRunning ? 'not-allowed' : 'pointer',
            background: globalRunning ? 'rgba(45,124,240,0.05)' : 'linear-gradient(135deg, #2D7CF0, #6D28D9)',
            border: globalRunning ? '1px solid #152040' : '1px solid rgba(45,124,240,0.3)',
            color: globalRunning ? '#2A3D5C' : '#fff',
            transition: 'all 0.2s',
          }}
        >
          {globalRunning ? '⏳ Ejecutando…' : '▶ Ejecutar todo'}
        </button>
      </div>

      {/* Steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {STEPS.map(({ key, label, icon, desc }) => {
          const s = steps[key]
          const c = COLOR[s.status]
          const isOpen = expanded === key && s.log

          return (
            <div key={key}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                borderRadius: 7, border: `1px solid ${c.border}`, backgroundColor: c.bg,
                transition: 'all 0.2s',
              }}>
                {/* Icon badge */}
                <div style={{
                  width: 30, height: 30, borderRadius: 6, flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14, fontWeight: 600,
                  backgroundColor: s.status === 'idle' ? '#0A1020' : c.bg,
                  border: `1px solid ${c.border}`,
                  color: c.color,
                }}>
                  {s.status === 'running' ? (
                    <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
                  ) : icon}
                </div>

                {/* Label */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: c.color }}>{label}</div>
                  <div style={{ fontSize: 11, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', marginTop: 1 }}>{desc}</div>
                </div>

                {/* Elapsed */}
                {s.elapsed && (
                  <span style={{ fontSize: 10, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace' }}>{s.elapsed}</span>
                )}

                {/* Log toggle */}
                {s.log && (
                  <button onClick={() => setExpanded(isOpen ? null : key)} style={{
                    fontSize: 10, padding: '3px 8px', borderRadius: 4, cursor: 'pointer',
                    backgroundColor: 'rgba(74,98,133,0.1)', border: '1px solid #152040', color: '#4A6285',
                  }}>
                    {isOpen ? 'ocultar' : 'log'}
                  </button>
                )}

                {/* Run single */}
                <button
                  onClick={() => runOne(key)}
                  disabled={globalRunning}
                  style={{
                    fontSize: 11, padding: '4px 10px', borderRadius: 5, cursor: globalRunning ? 'not-allowed' : 'pointer',
                    backgroundColor: s.status === 'idle' ? 'rgba(45,124,240,0.07)' : 'rgba(74,98,133,0.07)',
                    border: '1px solid #1E3060', color: globalRunning ? '#2A3D5C' : '#5BA4F5',
                  }}
                >
                  ▶
                </button>
              </div>

              {/* Log output */}
              {isOpen && (
                <div style={{
                  margin: '0 0 0 42px', padding: '10px 14px',
                  backgroundColor: '#050D1A', border: '1px solid #0F1E35', borderTop: 'none',
                  borderRadius: '0 0 6px 6px', maxHeight: 200, overflowY: 'auto',
                }}>
                  <pre style={{ fontSize: 10, color: '#4A6285', fontFamily: 'IBM Plex Mono, monospace', whiteSpace: 'pre-wrap', lineHeight: 1.6, margin: 0 }}>
                    {s.log}
                  </pre>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
