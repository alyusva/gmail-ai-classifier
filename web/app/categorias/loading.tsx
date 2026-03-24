export default function Loading() {
  return (
    <div style={{ padding: 32, maxWidth: 920 }}>
      <div style={{ marginBottom: 26 }}>
        <div style={{ height: 26, width: 140, borderRadius: 6, backgroundColor: '#0D1428', marginBottom: 8 }} className="pulse" />
        <div style={{ height: 14, width: 220, borderRadius: 4, backgroundColor: '#0A1020' }} className="pulse" />
      </div>
      <div style={{ backgroundColor: '#0D1428', border: '1px solid #152040', borderRadius: 10, overflow: 'hidden' }}>
        {[...Array(10)].map((_, i) => (
          <div key={i} style={{
            height: 56, borderBottom: '1px solid #0F1E35', display: 'flex', alignItems: 'center',
            padding: '0 16px', gap: 20,
          }}>
            <div style={{ height: 12, width: 24, borderRadius: 3, backgroundColor: '#0F1E35' }} className="pulse" />
            <div style={{ height: 12, width: 130, borderRadius: 3, backgroundColor: '#0F1E35' }} className="pulse" />
            <div style={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#0F1E35' }} className="pulse" />
            <div style={{ height: 12, width: 40, borderRadius: 3, backgroundColor: '#0F1E35' }} className="pulse" />
            <div style={{ height: 22, width: 80, borderRadius: 4, backgroundColor: '#0F1E35' }} className="pulse" />
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
