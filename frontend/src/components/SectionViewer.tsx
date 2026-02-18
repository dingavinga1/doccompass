import type { SectionContentResponse } from "../api/types";

interface SectionViewerProps {
  section: SectionContentResponse | null;
  isLoading: boolean;
}

export function SectionViewer({ section, isLoading }: SectionViewerProps) {
  if (isLoading) {
    return <p>Loading section content...</p>;
  }

  if (!section) {
    return <p>Select a section from the tree to view content.</p>;
  }

  return (
    <article className="panel section-viewer">
      <h3>{section.title ?? section.path}</h3>
      <p><strong>Path:</strong> {section.path}</p>
      {section.url ? <p><strong>Source:</strong> {section.url}</p> : null}
      {section.summary ? <p>{section.summary}</p> : null}
      <pre>{section.content ?? "No content available."}</pre>
    </article>
  );
}
