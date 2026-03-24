import type { NextAuthOptions } from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import { SupabaseAdapter } from '@auth/supabase-adapter'
import { createClient } from '@supabase/supabase-js'

// Cliente Supabase con service key (solo backend)
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
)

export const authOptions: NextAuthOptions = {
  adapter: SupabaseAdapter({
    url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
    secret: process.env.SUPABASE_SERVICE_KEY!,
  }),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.labels',
          ].join(' '),
          access_type: 'offline',
          prompt: 'consent',
        },
      },
    }),
  ],
  callbacks: {
    async session({ session, user }) {
      // Adjuntar user.id a la sesión
      if (session.user) {
        session.user.id = user.id

        // Cargar suscripción
        const { data: sub } = await supabaseAdmin
          .from('subscriptions')
          .select('plan, status, emails_limit, emails_used')
          .eq('user_id', user.id)
          .single()

        ;(session as any).subscription = sub ?? { plan: 'free', status: 'active', emails_limit: 1000, emails_used: 0 }
      }
      return session
    },

    async signIn({ user, account }) {
      // Guardar el refresh_token de Gmail en gmail_tokens
      if (account?.provider === 'google' && account.refresh_token) {
        await supabaseAdmin.from('gmail_tokens').upsert({
          user_id: user.id,
          token_data: JSON.stringify({
            token:         account.access_token,
            refresh_token: account.refresh_token,
            token_uri:     'https://oauth2.googleapis.com/token',
            client_id:     process.env.GOOGLE_CLIENT_ID,
            client_secret: process.env.GOOGLE_CLIENT_SECRET,
            scopes: [
              'https://www.googleapis.com/auth/gmail.modify',
              'https://www.googleapis.com/auth/gmail.labels',
            ],
          }),
          email: user.email,
          scopes: ['gmail.modify', 'gmail.labels'],
          updated_at: new Date().toISOString(),
        }, { onConflict: 'user_id' })
      }
      return true
    },
  },
  pages: {
    signIn: '/login',
    error:  '/login',
  },
  session: { strategy: 'database' },
  secret: process.env.NEXTAUTH_SECRET,
}
