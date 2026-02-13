# Gmail AI Classifier - Web App

Web interface for Gmail AI Classifier built with Next.js 14, React, and Tailwind CSS.

## Features (Roadmap)

- [ ] Dashboard with email statistics
- [ ] Real-time classification progress
- [ ] Category management
- [ ] Label customization
- [ ] Multi-user authentication
- [ ] Analytics and charts
- [ ] Manual classification override
- [ ] Export/import settings

## Getting Started

### Prerequisites

- Node.js 18+
- Supabase account (for database)
- Environment variables configured

### Installation

```bash
# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local
# Edit .env.local with your credentials

# Run development server
npm run dev

# Open http://localhost:3000
```

### Environment Variables

Create a `.env.local` file with:

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API (Python)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

## Development

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel Dashboard
```

### Docker

```bash
# Build
docker build -t gmail-classifier-web .

# Run
docker run -p 3000:3000 gmail-classifier-web
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Charts**: Recharts
- **State Management**: React Hooks
- **Authentication**: NextAuth.js (planned)

## Project Structure

```
web/
├── app/              # Next.js app router
│   ├── page.tsx     # Home page
│   ├── dashboard/   # Dashboard routes
│   ├── api/         # API routes
│   └── layout.tsx   # Root layout
├── components/      # React components
│   ├── ui/         # Reusable UI components
│   └── dashboard/  # Dashboard-specific components
├── lib/            # Utilities
│   ├── supabase.ts # Supabase client
│   └── utils.ts    # Helper functions
└── public/         # Static assets
```

## Contributing

Contributions are welcome! See main [README](../README.md) for guidelines.

## License

MIT - See [LICENSE](../LICENSE)
