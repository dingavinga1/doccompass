import type { DocumentationSummary } from "../api/types";

interface DocumentationListProps {
  items: DocumentationSummary[];
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function DocumentationList({ items, selectedId, onSelect }: DocumentationListProps) {
  if (!items.length) {
    return <p>No documentations yet.</p>;
  }

  return (
    <ul className="doc-list" aria-label="Documentation list">
      {items.map((item) => (
        <li key={item.id}>
          <button
            className={item.id === selectedId ? "selected" : ""}
            onClick={() => onSelect(item.id)}
            type="button"
          >
            <span>{item.title ?? item.url}</span>
            <small>{item.last_job_status ?? "No jobs"}</small>
          </button>
        </li>
      ))}
    </ul>
  );
}
