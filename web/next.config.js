/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow the web app to proxy the local FastAPI in dev and use env in prod.
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_CBC_API_URL || "http://localhost:8000";
    return [
      { source: "/api/cbc/:path*", destination: `${api}/:path*` },
    ];
  },
};
module.exports = nextConfig;
