import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { listIngestionJobs, stopIngestion } from "../api/ingestion";
import { StatusBadge } from "./StatusBadge";

export function IngestionJobList() {
    const queryClient = useQueryClient();
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [hideCompleted, setHideCompleted] = useState(false);

    const query = useQuery({
        queryKey: ["ingestion-jobs", page, pageSize, hideCompleted],
        queryFn: () =>
            listIngestionJobs(
                (page - 1) * pageSize,
                pageSize,
                hideCompleted ? "PENDING" : undefined
            ),
        refetchInterval: (query) => {
            if (query.state.data?.items.some(j => ["PENDING", "CRAWLING", "PARSING", "EMBEDDING", "INDEXING"].includes(j.status))) {
                return 3000;
            }
            return false;
        }
    });

    const [filterStatus, setFilterStatus] = useState<string>("");

    const filteredQuery = useQuery({
        queryKey: ["ingestion-jobs", page, pageSize, filterStatus],
        queryFn: () => listIngestionJobs((page - 1) * pageSize, pageSize, filterStatus || undefined),
        refetchInterval: 3000,
    });

    const data = filteredQuery.data;
    const total = data?.total ?? 0;
    const totalPages = Math.ceil(total / pageSize);

    const handlePrev = () => setPage((p) => Math.max(1, p - 1));
    const handleNext = () => setPage((p) => Math.min(totalPages, p + 1));

    async function handleStop(jobId: string) {
        try {
            await stopIngestion({ job_id: jobId });
            void filteredQuery.refetch();
        } catch (error) {
            console.error("Failed to stop job", error);
        }
    }

    const ACTIVE_STATUSES = ["PENDING", "CRAWLING", "PARSING", "EMBEDDING", "INDEXING"];

    return (
        <div className="panel">
            <div className="panel-title-row">
                <h2>Ingestion Jobs History</h2>
                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                    <select
                        value={filterStatus}
                        onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
                        className="form-input"
                        style={{ width: "auto" }}
                    >
                        <option value="">All Statuses</option>
                        <option value="PENDING">Pending</option>
                        <option value="CRAWLING">Crawling</option>
                        <option value="PARSING">Parsing</option>
                        <option value="EMBEDDING">Embedding</option>
                        <option value="INDEXING">Indexing</option>
                        <option value="COMPLETED">Completed</option>
                        <option value="FAILED">Failed</option>
                        <option value="STOPPED">Stopped</option>
                    </select>
                    <button type="button" onClick={() => void filteredQuery.refetch()}>Refresh</button>
                </div>
            </div>

            {filteredQuery.isLoading ? <p>Loading...</p> : null}
            {filteredQuery.isError ? <p className="error">Failed to load jobs</p> : null}

            {data && (
                <>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Job ID</th>
                                <th>Status</th>
                                <th>Progress</th>
                                <th>Pages</th>
                                <th>Details</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.items.map((job) => (
                                <tr key={job.job_id}>
                                    <td title={job.job_id} style={{ fontFamily: "monospace" }}>{job.job_id.slice(0, 8)}...</td>
                                    <td><StatusBadge status={job.status} /></td>
                                    <td>
                                        <div className="progress-bar" style={{ width: "100px", height: "8px", marginBottom: 0 }}>
                                            <div className={`progress-bar-fill ${job.status}`} style={{ width: `${job.progress_percent}%` }} />
                                        </div>
                                    </td>
                                    <td>{job.pages_processed}</td>
                                    <td className="text-sm">
                                        {job.error_message ? <span className="error">{job.error_message}</span> : null}
                                        {job.stop_requested ? <span className="warning">Stopping...</span> : null}
                                    </td>
                                    <td>
                                        {ACTIVE_STATUSES.includes(job.status) && !job.stop_requested ? (
                                            <button
                                                type="button"
                                                className="btn-sm btn-danger"
                                                onClick={() => void handleStop(job.job_id)}
                                            >
                                                Stop
                                            </button>
                                        ) : null}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    <div className="pagination-row" style={{ marginTop: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span>Page {page} of {totalPages || 1} ({total} total)</span>
                        <div style={{ display: "flex", gap: "0.5rem" }}>
                            <button disabled={page <= 1} onClick={handlePrev}>Previous</button>
                            <button disabled={page >= totalPages} onClick={handleNext}>Next</button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
