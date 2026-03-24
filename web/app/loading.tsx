export default function Loading() {
  return (
    <div style={{ padding: 32, maxWidth: 1440 }}>
      {/* Header skeleton */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ height: 26, width: 200, borderRadius: 6, backgroundColor: '#0D1428', marginBottom: 8 }} className="pulse" />
        <div style={{ height: 14, width: 260, borderRadius: 4, backgroundColor: '#0A1020' }} className="pulse" />
      </div>

      {/* Stat cards skeleton */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 24 }}>
        {[...Array(4)].map((_, i) => (
          <div key={i} style={{ flex: 1, height: 100, borderRadius: 10, backgroundColor: '#0D1428', border: '1px solid #152040' }} className="pulse" />
        ))}
      </div>

      {/* Main grid skeleton */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 370px', gap: 18 }}>
        <div style={{ height: 340, borderRadius: 10, backgroundColor: '#0D1428', border: '1px solid #152040' }} className="pulse" />
        <div style={{ height: 340, borderRadius: 10, backgroundColor: '#0D1428', border: '1px solid #152040' }} className="pulse" />
      </div>

      <style>{`
        .pulse { animation: pulse 1.6s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>
    </div>
  )
}
