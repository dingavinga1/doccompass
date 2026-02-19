import { apiRequest } from "./client";
import type {
  IngestionStatusResponse,
  StartIngestionRequest,
  StartIngestionResponse,
  StopIngestionRequest,
  StopIngestionResponse,
  IngestionJobListResponse
} from "./types";

export function startIngestion(payload: StartIngestionRequest): Promise<StartIngestionResponse> {
  return apiRequest<StartIngestionResponse>("/documentation/ingestion", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getIngestionStatus(jobId: string): Promise<IngestionStatusResponse> {
  return apiRequest<IngestionStatusResponse>(`/documentation/ingestion/${jobId}`);
}

export function stopIngestion(payload: StopIngestionRequest): Promise<StopIngestionResponse> {
  return apiRequest<StopIngestionResponse>("/documentation/ingestion/stop", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listIngestionJobs(
  skip = 0,
  limit = 100,
  status?: string
): Promise<IngestionJobListResponse> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString()
  });
  if (status) {
    params.append("status", status);
  }
  return apiRequest<IngestionJobListResponse>(`/documentation/ingestion?${params.toString()}`);
}
