import { NextRequest, NextResponse } from 'next/server'
import { stripe, PLANS, type PlanKey } from '@/lib/stripe'
import { supabaseAdmin } from '@/lib/supabase-server'
import type Stripe from 'stripe'

export const config = { api: { bodyParser: false } }

async function updateSubscription(sub: Stripe.Subscription) {
  const userId  = sub.metadata.user_id
  const plan    = (sub.metadata.plan ?? 'free') as PlanKey
  const limit   = PLANS[plan]?.emails_limit ?? 1000

  await supabaseAdmin.from('subscriptions').upsert({
    user_id:          userId,
    stripe_sub_id:    sub.id,
    stripe_customer_id: typeof sub.customer === 'string' ? sub.customer : sub.customer.id,
    plan,
    status:           sub.status === 'active' ? 'active' : sub.status === 'past_due' ? 'past_due' : 'canceled',
    emails_limit:     limit,
    period_start:     new Date(sub.current_period_start * 1000).toISOString(),
    period_end:       new Date(sub.current_period_end   * 1000).toISOString(),
    updated_at:       new Date().toISOString(),
  }, { onConflict: 'user_id' })
}

export async function POST(req: NextRequest) {
  const body      = await req.text()
  const signature = req.headers.get('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err: any) {
    return NextResponse.json({ error: `Webhook error: ${err.message}` }, { status: 400 })
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const cs = event.data.object as Stripe.CheckoutSession
      if (cs.mode === 'subscription' && cs.subscription) {
        const sub = await stripe.subscriptions.retrieve(cs.subscription as string)
        sub.metadata.user_id = cs.metadata?.user_id ?? ''
        sub.metadata.plan    = cs.metadata?.plan    ?? 'free'
        await updateSubscription(sub)
      }
      break
    }
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted':
      await updateSubscription(event.data.object as Stripe.Subscription)
      break
  }

  return NextResponse.json({ received: true })
}
