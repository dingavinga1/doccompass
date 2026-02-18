import type { IngestionStatusResponse } from "../api/types";

interface JobStatusPanelProps {
  status: IngestionStatusResponse | null;
  isLoading: boolean;
  onStop: () => Promise<void>;
  isStopping: boolean;
}

const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED", "STOPPED"]);

export function JobStatusPanel({ status, isLoading, onStop, isStopping }: JobStatusPanelProps) {
  const canStop = status && !TERMINAL_STATUSES.has(status.status);

  return (
    <section className="panel" aria-live="polite">
      <h2>Job Status</h2>
      {isLoading ? <p>Loading latest status...</p> : null}
      {!status ? <p>No active ingestion selected.</p> : null}
      {status ? (
        <>
          <p><strong>Job:</strong> {status.job_id}</p>
          <p><strong>Status:</strong> {status.status}</p>
          <p><strong>Progress:</strong> {status.progress_percent}%</p>
          <p><strong>Pages Processed:</strong> {status.pages_processed}</p>
          <p><strong>Stop Requested:</strong> {status.stop_requested ? "Yes" : "No"}</p>
          {status.error_message ? <p className="error">{status.error_message}</p> : null}
          <button type="button" onClick={() => void onStop()} disabled={!canStop || isStopping}>
            {isStopping ? "Stopping..." : "Stop Ingestion"}
          </button>
        </>
      ) : null}
    </section>
  );
}
