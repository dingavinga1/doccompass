import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getDocumentationTree, getSectionContent, listDocumentations } from "../api/documentation";
import { DocumentationList } from "../components/DocumentationList";
import { SectionTree } from "../components/SectionTree";
import { SectionViewer } from "../components/SectionViewer";

export function ExplorerPage() {
  const { documentationId } = useParams<{ documentationId: string }>();
  const navigate = useNavigate();
  const [selectedSectionPath, setSelectedSectionPath] = useState<string | null>(null);

  const docsQuery = useQuery({
    queryKey: ["documentations"],
    queryFn: () => listDocumentations()
  });

  const treeQuery = useQuery({
    queryKey: ["documentation-tree", documentationId],
    queryFn: () => getDocumentationTree(documentationId as string),
    enabled: Boolean(documentationId)
  });

  const sectionQuery = useQuery({
    queryKey: ["section-content", documentationId, selectedSectionPath],
    queryFn: () => getSectionContent(documentationId as string, selectedSectionPath as string),
    enabled: Boolean(documentationId && selectedSectionPath)
  });

  const docs = useMemo(() => docsQuery.data?.items ?? [], [docsQuery.data]);

  return (
    <div className="page-grid">
      <header className="page-header">
        <h1>Documentation Explorer</h1>
        <p>Browse section tree and view parsed content.</p>
        <Link to="/" className="link-button">← Dashboard</Link>
      </header>

      <div className="explorer-grid">
        <section className="panel">
          <h2>Documentations</h2>
          {docsQuery.isLoading ? <p className="empty-state">Loading...</p> : null}
          {docsQuery.isError ? <p className="error">Unable to load documentation list.</p> : null}
          {!docsQuery.isLoading && !docsQuery.isError ? (
            <DocumentationList
              items={docs}
              selectedId={documentationId}
              onSelect={(id) => {
                setSelectedSectionPath(null);
                navigate(`/explorer/${id}`);
              }}
            />
          ) : null}
        </section>

        <section className="panel">
          <h2>Section Tree</h2>
          {treeQuery.isLoading ? <p className="empty-state">Loading tree...</p> : null}
          {treeQuery.isError ? <p className="error">Unable to load tree.</p> : null}
          {!treeQuery.isLoading && !treeQuery.isError ? (
            <SectionTree
              roots={treeQuery.data?.roots ?? []}
              selectedPath={selectedSectionPath ?? undefined}
              onSelect={(path) => setSelectedSectionPath(path)}
            />
          ) : null}
        </section>

        <section>
          <SectionViewer section={sectionQuery.data ?? null} isLoading={sectionQuery.isLoading} />
          {sectionQuery.isError ? <p className="error">Unable to load section content.</p> : null}
        </section>
      </div>
    </div>
  );
}
