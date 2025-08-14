export type RagCitation = {
  marker: number;
  id: string;
  collection: string;
};

export type RagSource = {
  index: number;
  id: string;
  collection: string;
  preview?: string;
  chunk?: string;
};

export type RagVerification = {
  total_sentences: number;
  supported: number;
  unsupported: number;
  details: Array<{ index: number; supported: boolean; best_marker: number | null; best_score: number | null }>;
} | null;

export type RagAnswerResponse = {
  query: string;
  collection: string;
  num_results: number;
  answer: string;
  citations: RagCitation[];
  sources: RagSource[];
  verification?: RagVerification;
};

const RAG_BASE_URL = 'http://localhost:8001';

export async function askRag(
  query: string,
  collection: string,
  numResults: number,
  opts?: { maxTokens?: number }
): Promise<RagAnswerResponse> {
  const res = await fetch(`${RAG_BASE_URL}/rag/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, collection, num_results: numResults, max_tokens: opts?.maxTokens ?? 1200 }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`RAG answer failed: ${res.status} ${res.statusText} - ${text}`);
  }
  return (await res.json()) as RagAnswerResponse;
}

export type RagStreamEvent =
  | { event: 'start'; model_loaded: boolean; collection: string }
  | { event: 'token'; text: string }
  | { event: 'error'; message: string }
  | { event: 'end'; answer: string | null; citations: any[]; sources: any[] };

// Minimal SSE parser for POST fetch streams
export async function* streamRag(
  query: string,
  collection: string,
  numResults: number,
  opts?: { maxTokens?: number }
): AsyncGenerator<RagStreamEvent, void, unknown> {
  // Prefer GET with query params to avoid body buffering in some setups
  const params = new URLSearchParams({
    query,
    collection,
    num_results: String(numResults),
    max_tokens: String(opts?.maxTokens ?? 1200),
  });
  const res = await fetch(`${RAG_BASE_URL}/rag/answer/stream?${params.toString()}`, {
    method: 'GET',
    headers: { 'Accept': 'text/event-stream' },
  });
  if (!res.ok || !res.body) {
    throw new Error(`RAG stream failed: ${res.status} ${res.statusText}`);
  }
  // Some browsers/proxies buffer unless we read progressively
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const line = chunk.split('\n').find((l) => l.startsWith('data: '));
      if (!line) continue;
      const payload = line.slice(6);
      try {
        const evt = JSON.parse(payload) as RagStreamEvent;
        yield evt;
      } catch {
        // ignore malformed
      }
    }
  }
}

// Browser-native EventSource streaming (preferred in browsers)
export function openRagEventStream(
  query: string,
  collection: string,
  numResults: number,
  opts: { maxTokens?: number } | undefined,
  onEvent: (evt: RagStreamEvent) => void
): EventSource {
  const params = new URLSearchParams({
    query,
    collection,
    num_results: String(numResults),
    max_tokens: String(opts?.maxTokens ?? 1200),
  });
  const es = new EventSource(`${RAG_BASE_URL}/rag/answer/stream?${params.toString()}`);
  es.onmessage = (e) => {
    try {
      const evt = JSON.parse(e.data) as RagStreamEvent;
      onEvent(evt);
      if ((evt as any).event === 'end') {
        es.close();
      }
    } catch {
      // ignore malformed
    }
  };
  es.onerror = () => {
    onEvent({ event: 'error', message: 'EventSource error' } as any);
  };
  return es;
}


