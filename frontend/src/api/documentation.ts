import { apiRequest } from "./client";
import type {
  DocumentationListResponse,
  DocumentationTreeResponse,
  SectionContentResponse
} from "./types";

export function listDocumentations(limit = 50, offset = 0): Promise<DocumentationListResponse> {
  return apiRequest<DocumentationListResponse>(`/documentation?limit=${limit}&offset=${offset}`);
}

export function getDocumentationTree(documentationId: string): Promise<DocumentationTreeResponse> {
  return apiRequest<DocumentationTreeResponse>(`/documentation/${documentationId}/tree`);
}

export function getSectionContent(documentationId: string, sectionPath: string): Promise<SectionContentResponse> {
  const params = new URLSearchParams({ path: sectionPath });
  return apiRequest<SectionContentResponse>(`/documentation/${documentationId}/content?${params.toString()}`);
}
