// @ts-nocheck — add @cloudflare/workers-types in your deploy project for stricter typing
/**
 * Cloudflare Worker: authorized POST with Markdown body → Workers AI summary (Llama 3.1).
 *
 * Deploy: set secret AUTH_TOKEN (`wrangler secret put AUTH_TOKEN`), bind AI per wrangler.toml.
 * Pages deploy is out of scope here; extend this worker to call your GitHub/Pages API or R2 pipeline.
 */
export interface Env {
  AI: Ai;
  AUTH_TOKEN: string;
}

type PublishBody = {
  markdown?: string;
  city?: string;
  targetPath?: string;
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "GET") {
      return new Response("SEO publish worker — POST /publish with Bearer AUTH_TOKEN", {
        headers: { "content-type": "text/plain;charset=UTF-8" },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/$/, "") || "/";

    const auth = request.headers.get("Authorization") ?? "";
    const token = env.AUTH_TOKEN?.trim() ?? "";
    if (!token || auth !== `Bearer ${token}`) {
      return new Response(JSON.stringify({ ok: false, error: "unauthorized" }), {
        status: 401,
        headers: { "content-type": "application/json;charset=UTF-8" },
      });
    }

    if (path !== "/publish" && path !== "") {
      return new Response(JSON.stringify({ ok: false, error: "not_found" }), {
        status: 404,
        headers: { "content-type": "application/json;charset=UTF-8" },
      });
    }

    let body: PublishBody;
    try {
      body = (await request.json()) as PublishBody;
    } catch {
      return new Response(JSON.stringify({ ok: false, error: "invalid_json" }), {
        status: 400,
        headers: { "content-type": "application/json;charset=UTF-8" },
      });
    }

    const markdown = (body.markdown ?? "").slice(0, 100_000);
    if (!markdown.trim()) {
      return new Response(JSON.stringify({ ok: false, error: "markdown_required" }), {
        status: 400,
        headers: { "content-type": "application/json;charset=UTF-8" },
      });
    }

    const prompt = [
      "You are a publishing assistant. Summarize the following Markdown for a human reviewer.",
      "Call out risks (missing disclaimers, wrong city, broken tone). Max 8 bullet points.",
      body.city ? `Target city hint: ${body.city}` : "",
      "",
      markdown.slice(0, 24_000),
    ]
      .filter(Boolean)
      .join("\n");

    const summary = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
      messages: [
        { role: "system", content: "Be concise. Output plain text bullets only." },
        { role: "user", content: prompt },
      ],
    });

    const summaryText =
      typeof summary === "string" ? summary : JSON.stringify(summary);

    return new Response(
      JSON.stringify(
        {
          ok: true,
          model: "@cf/meta/llama-3.1-8b-instruct",
          city: body.city ?? null,
          targetPath: body.targetPath ?? null,
          summary: summaryText,
          receivedChars: markdown.length,
          note: "Wire your Cloudflare Pages / GitHub deploy step here after human approval.",
        },
        null,
        2,
      ),
      {
        headers: { "content-type": "application/json;charset=UTF-8" },
      },
    );
  },
};

interface Ai {
  run(model: string, options: { messages: { role: string; content: string }[] }): Promise<unknown>;
}
