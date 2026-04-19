import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

type Params = {
  path?: string[];
};

function resolveApiBase(): string | null {
  const raw = process.env.CBC_API_URL || process.env.NEXT_PUBLIC_CBC_API_URL;
  if (!raw) return null;
  return raw.replace(/\/+$/, "");
}

function buildTarget(request: NextRequest, path: string[]): URL | null {
  const base = resolveApiBase();
  if (!base) return null;
  const target = new URL(`${base}/${path.join("/")}`);
  target.search = request.nextUrl.search;
  return target;
}

async function proxy(request: NextRequest, context: { params: Promise<Params> }) {
  const { path = [] } = await context.params;
  const target = buildTarget(request, path);

  if (!target) {
    return Response.json(
      {
        error: "CBC_API_URL is not configured for the web proxy.",
        hint: "Set CBC_API_URL in Vercel project env or your local shell before starting Next.js.",
      },
      { status: 503 }
    );
  }

  const headers = new Headers(request.headers);
  headers.delete("host");

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(target, init);
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export async function GET(request: NextRequest, context: { params: Promise<Params> }) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: { params: Promise<Params> }) {
  return proxy(request, context);
}

export async function OPTIONS(request: NextRequest, context: { params: Promise<Params> }) {
  return proxy(request, context);
}
