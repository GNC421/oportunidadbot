import { NextResponse } from 'next/server'

export async function GET() {
  const supabaseConfigured = Boolean(process.env.SUPABASE_URL && process.env.SUPABASE_KEY)

  return NextResponse.json(
    {
      status: 'ok',
      timestamp: new Date().toISOString(),
      supabaseConfigured,
    },
    { status: 200 }
  )
}

export const dynamic = 'force-dynamic'
