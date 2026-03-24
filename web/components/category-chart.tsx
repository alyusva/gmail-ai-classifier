'use client'

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'
import type { ClassificationSummary } from '@/lib/types'

const PALETTE = [
  '#2D7CF0', '#8B5CF6', '#10B981', '#F59E0B',
  '#EF4444', '#06B6D4', '#EC4899', '#3B82F6',
  '#A78BFA', '#34D399',
]

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      backgroundColor: '#0D1428',
      border: '1px solid #1E3060',
      borderRadius: 7,
      padding: '8px 13px',
      fontSize: 12,
      fontFamily: 'IBM Plex Mono, monospace',
    }}>
      <p style={{ color: '#B8C9E0', marginBottom: 2 }}>{label}</p>
      <p style={{ color: '#5BA4F5' }}>{payload[0].value.toLocaleString()} emails</p>
    </div>
  )
}

export function CategoryChart({ data }: { data: ClassificationSummary[] }) {
  return (
    <ResponsiveContainer width="100%" height={290}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
        <XAxis
          type="number"
          tick={{ fontSize: 10, fill: '#4A6285', fontFamily: 'IBM Plex Mono, monospace' }}
          axisLine={false} tickLine={false}
        />
        <YAxis
          type="category" dataKey="label" width={138}
          tick={{ fontSize: 12, fill: '#B8C9E0', fontFamily: 'IBM Plex Sans, sans-serif' }}
          axisLine={false} tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(45,124,240,0.05)' }} />
        <Bar dataKey="email_count" radius={[0, 4, 4, 0]} maxBarSize={18}>
          {data.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
