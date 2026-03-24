import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { stripe, PLANS, type PlanKey } from '@/lib/stripe'
import { supabaseAdmin } from '@/lib/supabase-server'

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const { plan } = await req.json() as { plan: PlanKey }
  const planConfig = PLANS[plan]
  if (!planConfig?.priceId) return NextResponse.json({ error: 'Plan inválido' }, { status: 400 })

  // Buscar o crear customer en Stripe
  const { data: sub } = await supabaseAdmin
    .from('subscriptions')
    .select('stripe_customer_id')
    .eq('user_id', session.user.id)
    .single()

  let customerId = sub?.stripe_customer_id
  if (!customerId) {
    const customer = await stripe.customers.create({
      email: session.user.email!,
      name:  session.user.name ?? undefined,
      metadata: { user_id: session.user.id },
    })
    customerId = customer.id
    await supabaseAdmin.from('subscriptions')
      .update({ stripe_customer_id: customerId })
      .eq('user_id', session.user.id)
  }

  const checkoutSession = await stripe.checkout.sessions.create({
    customer: customerId,
    mode: 'subscription',
    line_items: [{ price: planConfig.priceId, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?upgraded=1`,
    cancel_url:  `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
    metadata: { user_id: session.user.id, plan },
  })

  return NextResponse.json({ url: checkoutSession.url })
}
