export { default } from 'next-auth/middleware'

export const config = {
  // Protege todo excepto login, pricing y api/auth
  matcher: ['/((?!login|pricing|api/auth|_next/static|_next/image|favicon.ico).*)'],
}
