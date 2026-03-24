import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export const maxDuration = 300

type Command = 'extract' | 'classify' | 'apply' | 'stats'
const ALLOWED: Command[] = ['extract', 'classify', 'apply', 'stats']

const FASTAPI = process.env.FASTAPI_URL ?? 'http://localhost:8000'
const SECRET  = process.env.FASTAPI_SECRET ?? ''

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'No autenticado' }, { status: 401 })
  }

  const { command, args = {} } = await req.json() as { command: Command; args?: Record<string, unknown> }
  if (!ALLOWED.includes(command)) {
    return NextResponse.json({ error: `Comando no permitido: ${command}` }, { status: 400 })
  }

  const method = command === 'stats' ? 'GET' : 'POST'
  const url    = `${FASTAPI}/${command}`

  const start = Date.now()
  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'x-user-id':    session.user.id,
      'x-api-secret': SECRET,
    },
    ...(method === 'POST' ? { body: JSON.stringify(args) } : {}),
  })

  const data    = await res.json()
  const elapsed = `${((Date.now() - start) / 1000).toFixed(1)}s`

  return NextResponse.json({ ok: res.ok, command, elapsed, data, code: res.status })
}
