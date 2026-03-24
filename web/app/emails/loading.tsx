export default function Loading() {
  return (
    <div style={{ padding: 32, maxWidth: 1440 }}>
      <div style={{ marginBottom: 26 }}>
        <div style={{ height: 26, width: 100, borderRadius: 6, backgroundColor: '#0D1428', marginBottom: 8 }} className="pulse" />
        <div style={{ height: 14, width: 200, borderRadius: 4, backgroundColor: '#0A1020' }} className="pulse" />
      </div>
      <div style={{ height: 42, width: '100%', borderRadius: 8, backgroundColor: '#0D1428', marginBottom: 18 }} className="pulse" />
      <div style={{ backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 10, overflow: 'hidden' }}>
        {[...Array(12)].map((_, i) => (
          <div key={i} style={{
            height: 52, borderBottom: '1px solid #0F1E35', display: 'flex', alignItems: 'center',
            padding: '0 16px', gap: 16,
          }}>
            <div style={{ height: 12, width: 80, borderRadius: 3, backgroundColor: '#0F1E35' }} className="pulse" />
            <div style={{ height: 12, width: 140, borderRadius: 3, backgroundColor: '#0F1E35' }} className="pulse" />
            <div style={{ flex: 1, height: 12, borderRadius: 3, backgroundColor: '#0F1E35' }} className="pulse" />
            <div style={{ height: 20, width: 80, borderRadius: 4, backgroundColor: '#0F1E35' }} className="pulse" />
          </div>
        ))}
      </div>
      <style>{`
        .pulse { animation: pulse 1.6s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>
    </div>
  )
}
