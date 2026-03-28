import type { NextAuthOptions } from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import { createClient } from '@supabase/supabase-js'

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
)

export const authOptions: NextAuthOptions = {
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
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, account }) {
      // Al hacer login, guardar el refresh_token en Supabase y en el token JWT
      if (account?.provider === 'google') {
        token.accessToken = account.access_token
        if (account.refresh_token) {
          token.refreshToken = account.refresh_token
          await supabaseAdmin.from('gmail_tokens').upsert({
            user_id:    token.sub,
            email:      token.email,
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
            scopes:     ['gmail.modify', 'gmail.labels'],
            updated_at: new Date().toISOString(),
          }, { onConflict: 'user_id' })
        }
      }
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).id  = token.sub
        ;(session as any).accessToken = token.accessToken
      }
      return session
    },
  },
  pages: {
    signIn: '/login',
    error:  '/login',
  },
  secret: process.env.NEXTAUTH_SECRET,
}
