import { FormEvent, useState } from "react";

export interface IngestionFormValues {
  webUrl: string;
  crawlDepth: number;
  includePatterns: string[];
  excludePatterns: string[];
}

interface IngestionFormProps {
  onSubmit: (values: IngestionFormValues) => Promise<void>;
  isSubmitting: boolean;
}

function parsePatternLines(raw: string): string[] {
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export function IngestionForm({ onSubmit, isSubmitting }: IngestionFormProps) {
  const [webUrl, setWebUrl] = useState("");
  const [crawlDepth, setCrawlDepth] = useState(3);
  const [includeRaw, setIncludeRaw] = useState("");
  const [excludeRaw, setExcludeRaw] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!webUrl.trim()) {
      setError("Web URL is required.");
      return;
    }

    try {
      await onSubmit({
        webUrl: webUrl.trim(),
        crawlDepth,
        includePatterns: parsePatternLines(includeRaw),
        excludePatterns: parsePatternLines(excludeRaw)
      });
    } catch {
      setError("Unable to start ingestion. Please retry.");
    }
  }

  return (
    <form className="panel" onSubmit={handleSubmit} aria-label="Start ingestion form">
      <h2>Start Ingestion</h2>
      <label htmlFor="web-url">Web URL</label>
      <input
        id="web-url"
        name="web-url"
        value={webUrl}
        onChange={(event) => setWebUrl(event.target.value)}
        placeholder="https://docs.example.com"
      />

      <label htmlFor="crawl-depth">Crawl Depth</label>
      <input
        id="crawl-depth"
        type="number"
        min={0}
        max={10}
        value={crawlDepth}
        onChange={(event) => setCrawlDepth(Number(event.target.value))}
      />

      <label htmlFor="include-patterns">Include Patterns (one per line)</label>
      <textarea
        id="include-patterns"
        value={includeRaw}
        onChange={(event) => setIncludeRaw(event.target.value)}
        rows={3}
      />

      <label htmlFor="exclude-patterns">Exclude Patterns (one per line)</label>
      <textarea
        id="exclude-patterns"
        value={excludeRaw}
        onChange={(event) => setExcludeRaw(event.target.value)}
        rows={3}
      />

      {error ? <p className="error" role="alert">{error}</p> : null}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Starting..." : "Start Ingestion"}
      </button>
    </form>
  );
}
