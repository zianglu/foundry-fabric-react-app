export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface FabricQueryRequest {
  question: string;
  thread_id?: string;
}

export interface FabricQueryResponse {
  answer?: string;
  result?: string;
  data?: unknown;
  raw?: Record<string, unknown>;
  error?: string;
}

export interface EntityListResponse {
  items: Record<string, unknown>[];
}

export interface SampleQuestions {
  questions: string[];
}
