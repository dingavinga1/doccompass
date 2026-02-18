import { apiRequest } from "./client";
import type {
  IngestionStatusResponse,
  StartIngestionRequest,
  StartIngestionResponse,
  StopIngestionRequest,
  StopIngestionResponse
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
