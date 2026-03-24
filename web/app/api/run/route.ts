import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

export const maxDuration = 300 // 5 min

type Command = 'extract' | 'classify' | 'apply' | 'stats' | 'dry-run'

const ALLOWED: Command[] = ['extract', 'classify', 'apply', 'stats', 'dry-run']

function runPython(command: Command, extraArgs: string[] = []): Promise<{ stdout: string; stderr: string; code: number }> {
  return new Promise((resolve) => {
    // Root del proyecto (web/../)
    const projectRoot = path.resolve(process.cwd(), '..')
    const args = ['-m', 'gmail_classifier.main', '--db', 'supabase', command, ...extraArgs]

    const proc = spawn('python3', args, {
      cwd: projectRoot,
      env: { ...process.env },
    })

    let stdout = ''
    let stderr = ''

    proc.stdout.on('data', (d) => { stdout += d.toString() })
    proc.stderr.on('data', (d) => { stderr += d.toString() })
    proc.on('close', (code) => resolve({ stdout, stderr, code: code ?? 1 }))
    proc.on('error', (err) => resolve({ stdout: '', stderr: err.message, code: 1 }))
  })
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { command, args: extraArgs = [] } = body as { command: Command; args?: string[] }

    if (!ALLOWED.includes(command)) {
      return NextResponse.json({ error: `Comando no permitido: ${command}` }, { status: 400 })
    }

    const start = Date.now()
    const result = await runPython(command, extraArgs)
    const elapsed = ((Date.now() - start) / 1000).toFixed(1)

    // Combinar stdout + stderr para el log (Python loguru escribe en stderr)
    const log = [result.stdout, result.stderr].filter(Boolean).join('\n').trim()

    return NextResponse.json({
      ok: result.code === 0,
      command,
      elapsed: `${elapsed}s`,
      log,
      code: result.code,
    })
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
