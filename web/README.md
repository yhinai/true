# CBC Web

Next.js command-center frontend for CBC.

## Local

```bash
cd web
npm ci
CBC_API_URL=http://localhost:8000 npm run dev
```

Optional realtime mirror:

```bash
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## Vercel

Set these environment variables in the Vercel project:

- `CBC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL` (optional)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (optional)

The browser talks to the Next app on the same origin.
The Next app proxies `/api/cbc/*` to `CBC_API_URL` server-side so the backend URL is not hardcoded into client fetches.
