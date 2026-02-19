import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getIngestionStatus, stopIngestion } from "../api/ingestion";
import type { IngestionStatus, IngestionStatusResponse } from "../api/types";
import { StatusBadge } from "./StatusBadge";

const ACTIVE_STATUSES = new Set<IngestionStatus>(["PENDING", "CRAWLING", "PARSING", "EMBEDDING", "INDEXING"]);
const TERMINAL_STATUSES = new Set<IngestionStatus>(["COMPLETED", "FAILED", "STOPPED"]);

export interface TrackedJob {
    jobId: string;
    documentationId: string;
    url: string;
}

interface JobTrackerProps {
    jobs: TrackedJob[];
    onToast: (message: string, tone: "success" | "error") => void;
}

interface SingleJobCardProps {
    job: TrackedJob;
    onToast: (message: string, tone: "success" | "error") => void;
}

function SingleJobCard({ job, onToast }: SingleJobCardProps) {
    const queryClient = useQueryClient();
    const prevStatusRef = useRef<IngestionStatus | null>(null);

    const statusQuery = useQuery({
        queryKey: ["ingestion-status", job.jobId],
        queryFn: () => getIngestionStatus(job.jobId),
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            return status && ACTIVE_STATUSES.has(status) ? 3000 : false;
        }
    });

    const data: IngestionStatusResponse | undefined = statusQuery.data;
    const currentStatus = data?.status ?? null;

    useEffect(() => {
        if (
            currentStatus &&
            TERMINAL_STATUSES.has(currentStatus) &&
            prevStatusRef.current &&
            !TERMINAL_STATUSES.has(prevStatusRef.current)
        ) {
            void queryClient.invalidateQueries({ queryKey: ["documentations"] });
        }
        if (currentStatus) {
            prevStatusRef.current = currentStatus;
        }
    }, [currentStatus, queryClient]);

    const isActive = currentStatus ? ACTIVE_STATUSES.has(currentStatus) : false;
    const progress = data?.progress_percent ?? 0;

    async function handleStop() {
        try {
            await stopIngestion({ job_id: job.jobId });
            onToast("Stop requested.", "success");
            void queryClient.invalidateQueries({ queryKey: ["ingestion-status", job.jobId] });
        } catch {
            onToast("Failed to request stop.", "error");
        }
    }

    return (
        <div className={`job-card${isActive ? " active" : ""}`}>
            <div className="job-card-header">
                <span className="job-card-title" title={job.url}>{job.url}</span>
                <StatusBadge status={currentStatus} />
            </div>

            <div className="progress-bar">
                <div
                    className={`progress-bar-fill${currentStatus === "COMPLETED" ? " completed" : ""}${currentStatus === "FAILED" ? " failed" : ""}`}
                    style={{ width: `${progress}%` }}
                />
            </div>

            <div className="job-card-details">
                <span className="job-card-detail">
                    <strong>Progress:</strong> {progress}%
                </span>
                <span className="job-card-detail">
                    <strong>Pages:</strong> {data?.pages_processed ?? 0}
                </span>
                {data?.error_message ? (
                    <span className="job-card-detail error">{data.error_message}</span>
                ) : null}
            </div>

            {isActive ? (
                <button
                    type="button"
                    className="btn-sm btn-danger"
                    style={{ marginTop: "0.5rem" }}
                    onClick={() => void handleStop()}
                >
                    Stop
                </button>
            ) : null}
        </div>
    );
}

export function JobTracker({ jobs, onToast }: JobTrackerProps) {
    if (!jobs.length) {
        return (
            <section className="panel">
                <h2>Ingestion Jobs</h2>
                <p className="empty-state">No ingestion jobs started yet. Use the form to begin.</p>
            </section>
        );
    }

    return (
        <section className="panel">
            <h2>Ingestion Jobs</h2>
            <div className="job-list">
                {jobs.map((job) => (
                    <SingleJobCard key={job.jobId} job={job} onToast={onToast} />
                ))}
            </div>
        </section>
    );
}
