import Stripe from 'stripe'

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-04-10',
})

export const PLANS = {
  free: {
    name: 'Free',
    price: 0,
    emails_limit: 1_000,
    features: ['1.000 emails/mes', 'Clasificación con IA', 'Dashboard básico'],
    priceId: null,
  },
  pro: {
    name: 'Pro',
    price: 9,
    emails_limit: 15_000,
    features: ['15.000 emails/mes', 'Todo lo de Free', 'Categorías personalizadas', 'Soporte prioritario'],
    priceId: process.env.STRIPE_PRICE_PRO,
  },
  business: {
    name: 'Business',
    price: 29,
    emails_limit: 999_999,
    features: ['Emails ilimitados', 'Todo lo de Pro', 'API access', 'SLA 99.9%'],
    priceId: process.env.STRIPE_PRICE_BUSINESS,
  },
} as const

export type PlanKey = keyof typeof PLANS
