import { NextRequest } from "next/server";

const BACKEND_BASE_URL = process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";

async function proxyRequest(
  request: NextRequest,
  params: { path: string[] },
): Promise<Response> {
  const targetPath = params.path.join("/");
  const query = request.nextUrl.search;
  const targetUrl = `${BACKEND_BASE_URL}/${targetPath}${query}`;

  try {
    const requestBody =
      request.method === "GET" || request.method === "HEAD"
        ? undefined
        : await request.text();

    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers: {
        "Content-Type": request.headers.get("content-type") ?? "application/json",
      },
      body: requestBody,
      cache: "no-store",
    });

    const responseBody = await backendResponse.text();
    const contentType = backendResponse.headers.get("content-type") ?? "application/json";

    return new Response(responseBody, {
      status: backendResponse.status,
      headers: {
        "Content-Type": contentType,
      },
    });
  } catch {
    return Response.json(
      {
        message: `Unable to reach backend at ${BACKEND_BASE_URL}. Make sure it is running.`,
      },
      { status: 502 },
    );
  }
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const params = await context.params;
  return proxyRequest(request, params);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const params = await context.params;
  return proxyRequest(request, params);
}
