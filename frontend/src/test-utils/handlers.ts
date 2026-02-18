import { http, HttpResponse } from "msw";

const now = new Date().toISOString();

export const handlers = [
  http.get("/api/documentation", () => {
    return HttpResponse.json({
      items: [
        {
          id: "doc-1",
          url: "https://docs.example.com",
          title: "Example Docs",
          last_synced: now,
          created_at: now,
          updated_at: now,
          section_count: 2,
          job_count: 1,
          last_job_status: "COMPLETED"
        }
      ],
      meta: { total: 1, limit: 50, offset: 0 }
    });
  }),
  http.post("/api/documentation/ingestion", async ({ request }) => {
    const payload = (await request.json()) as { web_url: string; include_patterns: string[]; exclude_patterns: string[] };

    if (!payload.web_url) {
      return HttpResponse.json({ detail: "Invalid payload" }, { status: 422 });
    }

    return HttpResponse.json({
      job_id: "job-1",
      documentation_id: "doc-1",
      status: "PENDING"
    }, { status: 202 });
  }),
  http.get("/api/documentation/ingestion/job-1", () => {
    return HttpResponse.json({
      job_id: "job-1",
      documentation_id: "doc-1",
      status: "CRAWLING",
      progress_percent: 40,
      pages_processed: 9,
      stop_requested: false,
      error_message: null
    });
  }),
  http.post("/api/documentation/ingestion/stop", async ({ request }) => {
    const payload = (await request.json()) as { job_id: string };
    return HttpResponse.json({
      job_id: payload.job_id,
      status: "STOPPED",
      stop_requested: true
    });
  }),
  http.get("/api/documentation/doc-1/tree", () => {
    return HttpResponse.json({
      documentation_id: "doc-1",
      roots: [
        {
          id: "section-1",
          path: "/guide",
          parent_id: null,
          title: "Guide",
          level: 1,
          children: [
            {
              id: "section-2",
              path: "/guide/intro",
              parent_id: "section-1",
              title: "Intro",
              level: 2,
              children: []
            }
          ]
        }
      ]
    });
  }),
  http.get("/api/documentation/doc-1/sections/%2Fguide%2Fintro", () => {
    return HttpResponse.json({
      id: "section-2",
      documentation_id: "doc-1",
      path: "/guide/intro",
      parent_id: "section-1",
      title: "Intro",
      summary: "Welcome",
      content: "Introduction content",
      level: 2,
      url: "https://docs.example.com/guide/intro",
      token_count: 12,
      checksum: "abc"
    });
  })
];
