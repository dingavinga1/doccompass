import type { IngestionStatus } from "../api/types";

interface StatusBadgeProps {
    status: IngestionStatus | null;
}

export function StatusBadge({ status }: StatusBadgeProps) {
    if (!status) {
        return <span className="status-badge">No jobs</span>;
    }

    return (
        <span className={`status-badge ${status.toLowerCase()}`}>
            {status}
        </span>
    );
}
