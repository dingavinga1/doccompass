export type IngestionStatus =
  | "PENDING"
  | "CRAWLING"
  | "PARSING"
  | "EMBEDDING"
  | "INDEXING"
  | "COMPLETED"
  | "FAILED"
  | "STOPPED";

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentationSummary {
  id: string;
  url: string;
  title: string | null;
  last_synced: string | null;
  created_at: string;
  updated_at: string;
  section_count: number;
  job_count: number;
  last_job_status: IngestionStatus | null;
}

export interface DocumentationListResponse {
  items: DocumentationSummary[];
  meta: PaginationMeta;
}

export interface StartIngestionRequest {
  web_url: string;
  crawl_depth: number;
  include_patterns: string[];
  exclude_patterns: string[];
}

export interface StartIngestionResponse {
  job_id: string;
  documentation_id: string;
  status: IngestionStatus;
}

export interface IngestionStatusResponse {
  job_id: string;
  documentation_id: string;
  status: IngestionStatus;
  progress_percent: number;
  pages_processed: number;
  stop_requested: boolean;
  error_message: string | null;
}

export interface StopIngestionRequest {
  job_id: string;
}

export interface StopIngestionResponse {
  job_id: string;
  status: IngestionStatus;
  stop_requested: boolean;
}

export interface IngestionJobListResponse {
  items: IngestionStatusResponse[];
  total: number;
}

export interface DocumentationTreeNode {
  id: string;
  path: string;
  parent_id: string | null;
  title: string | null;
  level: number | null;
  children: DocumentationTreeNode[];
}

export interface DocumentationTreeResponse {
  documentation_id: string;
  roots: DocumentationTreeNode[];
}

export interface SectionContentResponse {
  id: string;
  documentation_id: string;
  path: string;
  parent_id: string | null;
  title: string | null;
  summary: string | null;
  content: string | null;
  level: number | null;
  url: string | null;
  token_count: number | null;
  checksum: string | null;
}
