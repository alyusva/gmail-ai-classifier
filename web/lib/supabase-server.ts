import { createClient } from '@supabase/supabase-js'

/** Cliente con service_role — solo usar en Server Components / API routes */
export const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
)
