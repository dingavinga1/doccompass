import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listDocumentations } from "../api/documentation";
import { getIngestionStatus, startIngestion, stopIngestion } from "../api/ingestion";
import type { IngestionStatus, StartIngestionRequest } from "../api/types";
import { DocumentationList } from "../components/DocumentationList";
import { IngestionForm, type IngestionFormValues } from "../components/IngestionForm";
import { JobStatusPanel } from "../components/JobStatusPanel";
import { ToastItem, ToastStack } from "../components/ToastStack";

const ACTIVE_STATUSES = new Set<IngestionStatus>(["PENDING", "CRAWLING", "PARSING", "EMBEDDING", "INDEXING"]);

function toRequestPayload(values: IngestionFormValues): StartIngestionRequest {
  return {
    web_url: values.webUrl,
    crawl_depth: values.crawlDepth,
    include_patterns: values.includePatterns,
    exclude_patterns: values.excludePatterns
  };
}

export function DashboardPage() {
  const queryClient = useQueryClient();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [selectedDocumentationId, setSelectedDocumentationId] = useState<string | undefined>();
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  function addToast(message: string, tone: "success" | "error") {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, tone }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id));
    }, 3000);
  }

  const docsQuery = useQuery({
    queryKey: ["documentations"],
    queryFn: () => listDocumentations()
  });

  const startMutation = useMutation({
    mutationFn: (payload: StartIngestionRequest) => startIngestion(payload),
    onSuccess: (data) => {
      setActiveJobId(data.job_id);
      setSelectedDocumentationId(data.documentation_id);
      addToast("Ingestion job started.", "success");
      void queryClient.invalidateQueries({ queryKey: ["documentations"] });
    },
    onError: () => addToast("Failed to start ingestion.", "error")
  });

  const statusQuery = useQuery({
    queryKey: ["ingestion-status", activeJobId],
    queryFn: () => getIngestionStatus(activeJobId as string),
    enabled: Boolean(activeJobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.has(status) ? 3000 : false;
    }
  });

  const stopMutation = useMutation({
    mutationFn: (jobId: string) => stopIngestion({ job_id: jobId }),
    onSuccess: () => {
      addToast("Stop requested.", "success");
      void queryClient.invalidateQueries({ queryKey: ["ingestion-status", activeJobId] });
    },
    onError: () => addToast("Failed to request stop.", "error")
  });

  const docs = useMemo(() => docsQuery.data?.items ?? [], [docsQuery.data]);

  async function handleSubmit(values: IngestionFormValues): Promise<void> {
    await startMutation.mutateAsync(toRequestPayload(values));
  }

  async function handleStop(): Promise<void> {
    if (!activeJobId) {
      return;
    }
    await stopMutation.mutateAsync(activeJobId);
  }

  return (
    <div className="page-grid">
      <header className="page-header">
        <h1>Documentation MCP Gateway</h1>
        <p>Run ingestion jobs and monitor status in real time.</p>
      </header>

      <div className="two-col">
        <IngestionForm onSubmit={handleSubmit} isSubmitting={startMutation.isPending} />
        <JobStatusPanel
          status={statusQuery.data ?? null}
          isLoading={statusQuery.isLoading}
          onStop={handleStop}
          isStopping={stopMutation.isPending}
        />
      </div>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Documentations</h2>
          <button type="button" onClick={() => void docsQuery.refetch()}>
            Refresh
          </button>
        </div>
        {docsQuery.isLoading ? <p>Loading documentations...</p> : null}
        {docsQuery.isError ? <p className="error">Could not load documentation list.</p> : null}
        {!docsQuery.isLoading && !docsQuery.isError ? (
          <DocumentationList
            items={docs}
            selectedId={selectedDocumentationId}
            onSelect={(id) => setSelectedDocumentationId(id)}
          />
        ) : null}
        {selectedDocumentationId ? (
          <Link to={`/explorer/${selectedDocumentationId}`} className="link-button">
            Open Explorer
          </Link>
        ) : null}
      </section>

      <ToastStack toasts={toasts} />
    </div>
  );
}
