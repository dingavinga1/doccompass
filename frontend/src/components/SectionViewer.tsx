import type { SectionContentResponse } from "../api/types";

interface SectionViewerProps {
  section: SectionContentResponse | null;
  isLoading: boolean;
}

export function SectionViewer({ section, isLoading }: SectionViewerProps) {
  if (isLoading) {
    return <p className="empty-state">Loading section content...</p>;
  }

  if (!section) {
    return <p className="empty-state">Select a section from the tree to view content.</p>;
  }

  return (
    <article className="panel section-viewer">
      <h3>{section.title ?? section.path}</h3>
      <div className="section-viewer-meta">
        <span><strong>Path:</strong> {section.path}</span>
        {section.url ? (
          <span>
            <strong>Source:</strong>{" "}
            <a href={section.url} target="_blank" rel="noopener noreferrer">
              {section.url}
            </a>
          </span>
        ) : null}
        {section.token_count ? (
          <span><strong>Tokens:</strong> {section.token_count}</span>
        ) : null}
      </div>
      {section.summary ? <p>{section.summary}</p> : null}
      <pre>{section.content ?? "No content available."}</pre>
    </article>
  );
}
