import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        base:          '#050913',
        surface:       '#0A1020',
        card:          '#0D1428',
        'border-dim':  '#152040',
        'border-mid':  '#1E3060',
        'blue-acc':    '#2D7CF0',
        'blue-bright': '#5BA4F5',
        'violet-acc':  '#6D28D9',
        'violet-bright':'#8B5CF6',
        'tx-primary':  '#B8C9E0',
        'tx-secondary':'#4A6285',
        'tx-muted':    '#2A3D5C',
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
export default config
