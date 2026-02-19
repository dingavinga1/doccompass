import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../src/App";
import { server } from "../src/test-utils/server";
import { renderWithProviders } from "../src/test-utils/render";

describe("Dashboard", () => {
  it("shows validation error if url is missing", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, "/");

    await user.click(screen.getByRole("button", { name: "Start Ingestion" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Web URL is required");
  });

  it("submits ingestion payload with parsed patterns and renders status", async () => {
    const user = userEvent.setup();
    let capturedPayload: unknown;

    server.use(
      http.post("/api/documentation/ingestion", async ({ request }) => {
        capturedPayload = await request.json();
        return HttpResponse.json(
          {
            job_id: "job-1",
            documentation_id: "doc-1",
            status: "PENDING"
          },
          { status: 202 }
        );
      })
    );

    renderWithProviders(<App />, "/");

    await user.type(screen.getByLabelText("Web URL"), "https://docs.example.com");
    await user.clear(screen.getByLabelText("Crawl Depth"));
    await user.type(screen.getByLabelText("Crawl Depth"), "2");
    await user.type(screen.getByLabelText("Include Patterns (one per line)"), "https://docs.example.com/*\n\nfoo");
    await user.type(screen.getByLabelText("Exclude Patterns (one per line)"), "bar\n");
    await user.click(screen.getByRole("button", { name: "Start Ingestion" }));

    await waitFor(() => {
      expect(screen.getByText(/CRAWLING/)).toBeInTheDocument();
    });

    expect(capturedPayload).toEqual({
      web_url: "https://docs.example.com",
      crawl_depth: 2,
      include_patterns: ["https://docs.example.com/*", "foo"],
      exclude_patterns: ["bar"]
    });
  });

  it("requests stop for active job", async () => {
    const user = userEvent.setup();

    renderWithProviders(<App />, "/");

    await user.type(screen.getByLabelText("Web URL"), "https://docs.example.com");
    await user.click(screen.getByRole("button", { name: "Start Ingestion" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Stop" }));

    await waitFor(() => {
      expect(screen.getByText("Stop requested.")).toBeInTheDocument();
    });
  });
});
