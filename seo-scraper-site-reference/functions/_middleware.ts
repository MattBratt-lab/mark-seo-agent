/**
 * Real HTTP 404 for unknown paths (avoids SPA-style 200 + homepage HTML).
 * Valid pathnames are generated from dist/ at build time (functions/_valid-paths.ts).
 */
import { NOT_FOUND_HTML } from "./_404-html";
import { isValidPathname } from "./_valid-paths";

export const onRequest: PagesFunction = async (context) => {
  const url = new URL(context.request.url);
  const pathname = url.pathname;

  if (pathname === "/sitemap_index.xml" || pathname === "/sitemap_index.xml/") {
    return new Response("Not Found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  if (pathname === "/get-blogs" || pathname.startsWith("/get-blogs/")) {
    return context.next();
  }

  const method = context.request.method;
  if (method !== "GET" && method !== "HEAD") {
    return context.next();
  }

  if (!isValidPathname(pathname)) {
    const html404 = NOT_FOUND_HTML;
    const baseHeaders: Record<string, string> = { "Content-Type": "text/html" };
    if (method === "HEAD") {
      const bodyBytes = new TextEncoder().encode(html404);
      return new Response(null, {
        status: 404,
        headers: { ...baseHeaders, "Content-Length": String(bodyBytes.byteLength) },
      });
    }
    return new Response(html404, { status: 404, headers: baseHeaders });
  }

  return context.next();
};
