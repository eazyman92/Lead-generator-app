import { NextResponse } from "next/server";

const BACKEND_BASE_URL =
  process.env.BACKEND_INTERNAL_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

const FORWARDED_REQUEST_HEADERS = [
  "accept",
  "content-type",
  "cookie",
  "x-csrf-token",
  "x-request-id"
];

const FORWARDED_RESPONSE_HEADERS = ["content-type", "cache-control", "x-request-id"];

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxy(request: Request, context: RouteContext) {
  const { path } = await context.params;
  const upstreamUrl = new URL(`/api/v1/${path.join("/")}`, BACKEND_BASE_URL);
  upstreamUrl.search = new URL(request.url).search;

  const headers = new Headers();
  for (const headerName of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(headerName);
    if (value) {
      headers.set(headerName, value);
    }
  }

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const upstreamResponse = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body,
    cache: "no-store"
  });

  const responseHeaders = new Headers();
  for (const headerName of FORWARDED_RESPONSE_HEADERS) {
    const value = upstreamResponse.headers.get(headerName);
    if (value) {
      responseHeaders.set(headerName, value);
    }
  }

  const response = new NextResponse(await upstreamResponse.arrayBuffer(), {
    status: upstreamResponse.status,
    headers: responseHeaders
  });

  for (const cookie of getSetCookies(upstreamResponse.headers)) {
    response.headers.append("Set-Cookie", toHostCookie(cookie));
  }

  return response;
}

function getSetCookies(headers: Headers): string[] {
  const withGetSetCookie = headers as Headers & {
    getSetCookie?: () => string[];
  };
  const cookies = withGetSetCookie.getSetCookie?.();
  if (cookies?.length) {
    return cookies;
  }

  const cookie = headers.get("set-cookie");
  return cookie ? [cookie] : [];
}

function toHostCookie(cookie: string): string {
  return cookie
    .split(";")
    .filter((attribute) => !attribute.trim().toLowerCase().startsWith("domain="))
    .join(";");
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
