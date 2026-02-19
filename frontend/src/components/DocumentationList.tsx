import { useState } from "react";

import type { DocumentationSummary } from "../api/types";
import { StatusBadge } from "./StatusBadge";

interface DocumentationListProps {
  items: DocumentationSummary[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function DocumentationList({ items, selectedId, onSelect, onDelete }: DocumentationListProps) {
  const [confirmId, setConfirmId] = useState<string | null>(null);

  if (!items.length) {
    return <p className="empty-state">No documentations yet.</p>;
  }

  function handleConfirmDelete() {
    if (confirmId && onDelete) {
      onDelete(confirmId);
    }
    setConfirmId(null);
  }

  return (
    <>
      <ul className="doc-list" aria-label="Documentation list">
        {items.map((item) => (
          <li key={item.id}>
            <div className={`doc-list-item${item.id === selectedId ? " selected" : ""}`}>
              <div
                className="doc-list-item-info"
                role="button"
                tabIndex={0}
                onClick={() => onSelect(item.id)}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onSelect(item.id); }}
              >
                <span className="doc-list-item-title">{item.title ?? item.url}</span>
                <div className="doc-list-item-meta">
                  <StatusBadge status={item.last_job_status} />
                  <small>{item.section_count} sections</small>
                </div>
              </div>
              {onDelete ? (
                <div className="doc-list-actions">
                  <button
                    type="button"
                    className="btn-icon btn-danger"
                    title="Delete documentation"
                    onClick={() => setConfirmId(item.id)}
                  >
                    ✕
                  </button>
                </div>
              ) : null}
            </div>
          </li>
        ))}
      </ul>

      {confirmId ? (
        <div className="confirm-overlay" onClick={() => setConfirmId(null)}>
          <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Delete Documentation</h3>
            <p>
              This will permanently remove the documentation and all its sections. This action cannot be undone.
            </p>
            <div className="confirm-actions">
              <button type="button" onClick={() => setConfirmId(null)}>Cancel</button>
              <button type="button" className="btn-danger" onClick={handleConfirmDelete}>
                Delete
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
