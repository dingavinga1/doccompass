import { useCallback, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { deleteDocumentation, listDocumentations } from "../api/documentation";
import { startIngestion } from "../api/ingestion";
import type { StartIngestionRequest } from "../api/types";
import { DocumentationList } from "../components/DocumentationList";
import { IngestionForm, type IngestionFormValues } from "../components/IngestionForm";
import { IngestionJobList } from "../components/IngestionJobList";
import { ToastItem, ToastStack } from "../components/ToastStack";

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
  const [selectedDocumentationId, setSelectedDocumentationId] = useState<string | undefined>();
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((message: string, tone: "success" | "error") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, tone }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id));
    }, 3000);
  }, []);

  const docsQuery = useQuery({
    queryKey: ["documentations"],
    queryFn: () => listDocumentations()
  });

  const startMutation = useMutation({
    mutationFn: (payload: { request: StartIngestionRequest; url: string }) =>
      startIngestion(payload.request),
    onSuccess: (data, variables) => {
      setSelectedDocumentationId(data.documentation_id);
      addToast("Ingestion job started.", "success");
      void queryClient.invalidateQueries({ queryKey: ["documentations"] });
      void queryClient.invalidateQueries({ queryKey: ["ingestion-jobs"] });
    },
    onError: () => addToast("Failed to start ingestion.", "error")
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => deleteDocumentation(docId),
    onSuccess: (_data, docId) => {
      addToast("Documentation deleted.", "success");
      if (selectedDocumentationId === docId) {
        setSelectedDocumentationId(undefined);
      }
      void queryClient.invalidateQueries({ queryKey: ["documentations"] });
    },
    onError: () => addToast("Failed to delete documentation.", "error")
  });

  const docs = useMemo(() => docsQuery.data?.items ?? [], [docsQuery.data]);

  async function handleSubmit(values: IngestionFormValues): Promise<void> {
    await startMutation.mutateAsync({
      request: toRequestPayload(values),
      url: values.webUrl
    });
  }

  function handleDelete(docId: string) {
    deleteMutation.mutate(docId);
  }

  return (
    <div className="page-grid">
      <header className="page-header">
        <h1>DocCompass</h1>
        <p>Ingest, browse, and serve documentation via MCP.</p>
      </header>

      <IngestionForm onSubmit={handleSubmit} isSubmitting={startMutation.isPending} />


      <IngestionJobList />

      <section className="panel">
        <div className="panel-title-row">
          <h2>Documentations</h2>
          <button type="button" onClick={() => void docsQuery.refetch()}>
            Refresh
          </button>
        </div>
        {docsQuery.isLoading ? <p className="empty-state">Loading documentations...</p> : null}
        {docsQuery.isError ? <p className="error">Could not load documentation list.</p> : null}
        {!docsQuery.isLoading && !docsQuery.isError ? (
          <DocumentationList
            items={docs}
            selectedId={selectedDocumentationId}
            onSelect={(id) => setSelectedDocumentationId(id)}
            onDelete={handleDelete}
          />
        ) : null}
        {selectedDocumentationId ? (
          <Link to={`/explorer/${selectedDocumentationId}`} className="link-button">
            Open Explorer →
          </Link>
        ) : null}
      </section>

      <ToastStack toasts={toasts} />
    </div >
  );
}
