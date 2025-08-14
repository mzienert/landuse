"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { askRag, streamRag, openRagEventStream, type RagSource, type RagCitation } from "../../lib/rag-service";

export default function RagPage() {
  const [query, setQuery] = useState("");
  const [collection, setCollection] = useState("la_plata_county_code");
  const [numResults, setNumResults] = useState(4);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<RagCitation[]>([]);
  const [sources, setSources] = useState<RagSource[]>([]);
  const [useStream, setUseStream] = useState(true);

  const outputRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [answer]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setAnswer("");
    setCitations([]);
    setSources([]);

    if (!query.trim()) {
      setError("Enter a question");
      return;
    }

    try {
      if (useStream) {
        setIsStreaming(true);
        let acc = "";
        const es = openRagEventStream(query, collection, numResults, undefined, (evt) => {
          if (evt.event === 'token' && typeof (evt as any).text === 'string') {
            acc += (evt as any).text;
            setAnswer(acc);
          } else if (evt.event === 'error') {
            setError((evt as any).message || 'Stream error');
          } else if (evt.event === 'end') {
            setIsStreaming(false);
          }
        });
        // Safety timeout to avoid dangling streams
        setTimeout(() => {
          try { es.close(); } catch {}
          setIsStreaming(false);
        }, 1000 * 60 * 3);
      } else {
        const res = await askRag(query, collection, numResults);
        setAnswer(res.answer);
        setCitations(res.citations || []);
        setSources(res.sources || []);
      }
    } catch (err: any) {
      setError(err?.message || "Unexpected error");
      setIsStreaming(false);
    }
  }

  const citationMap = useMemo(() => {
    const map = new Map<number, RagSource>();
    for (const s of sources) map.set(s.index, s);
    return map;
  }, [sources]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h1 className="text-2xl font-bold mb-4">RAG Q&A</h1>
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Question</label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about La Plata County Land Use Code..."
                  className="w-full border rounded-md p-3 h-24"
                  disabled={isStreaming}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Collection</label>
                  <select
                    value={collection}
                    onChange={(e) => setCollection(e.target.value)}
                    className="w-full border rounded-md p-2"
                    disabled={isStreaming}
                  >
                    <option value="la_plata_county_code">Land Use Code</option>
                    <option value="la_plata_assessor">Assessor Data</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Results (K)</label>
                  <select
                    value={numResults}
                    onChange={(e) => setNumResults(parseInt(e.target.value))}
                    className="w-full border rounded-md p-2"
                    disabled={isStreaming}
                  >
                    {[3,4,5,6].map((k) => (
                      <option key={k} value={k}>{k}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-end">
                  <label className="inline-flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={useStream}
                      onChange={(e) => setUseStream(e.target.checked)}
                      className="mr-2"
                      disabled={isStreaming}
                    />
                    <span className="text-sm text-gray-700">Stream tokens</span>
                  </label>
                </div>
              </div>
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
                disabled={isStreaming}
              >
                {isStreaming ? 'Streaming...' : 'Ask'}
              </button>
              {error && <div className="text-red-600 text-sm mt-2">{error}</div>}
            </form>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-3">Answer</h2>
            <div className="relative">
              <div ref={outputRef} className="border rounded-md p-3 h-64 overflow-auto whitespace-pre-wrap text-sm">
                {answer || (isStreaming ? 'Waiting for tokens...' : 'No answer yet')}
              </div>
              {isStreaming && (
                <div className="absolute top-2 right-3 flex items-center text-xs text-gray-500">
                  <span className="mr-2">Streaming</span>
                  <span className="inline-block h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                </div>
              )}
            </div>
          </div>

          {!useStream && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="font-semibold mb-2">Citations</h3>
                {citations?.length ? (
                  <ul className="text-sm space-y-1">
                    {citations.map((c, i) => (
                      <li key={i} className="text-gray-700">
                        [{c.marker}] → {c.collection} / {c.id}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-gray-500">No citations</div>
                )}
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="font-semibold mb-2">Sources</h3>
                {sources?.length ? (
                  <div className="space-y-3">
                    {sources.map((s) => (
                      <div key={s.index} className="border rounded p-2">
                        <div className="text-xs text-gray-500 mb-1">[{s.index}] {s.collection} / {s.id}</div>
                        <div className="text-sm text-gray-700 whitespace-pre-wrap">
                          {(s.preview || s.chunk || '').slice(0, 400)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">No sources</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


