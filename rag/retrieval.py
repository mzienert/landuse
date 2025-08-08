from __future__ import annotations

from typing import Any, Dict, List, Tuple
import requests
import re


DEFAULT_SEARCH_BASE = "http://localhost:8000"


def fetch_simple_search(
    query: str,
    *,
    collection: str = "la_plata_county_code",
    num_results: int = 5,
    base_url: str = DEFAULT_SEARCH_BASE,
    timeout_sec: int = 20,
) -> Dict[str, Any]:
    """Call the existing search_api `/search/simple` endpoint and return JSON.

    Keeps separation of concerns by delegating retrieval to the dedicated service.
    """
    url = f"{base_url}/search/simple"
    params = {
        "query": query,
        "collection": collection,
        "num_results": max(1, min(10, int(num_results))),
    }
    resp = requests.get(url, params=params, timeout=timeout_sec)
    resp.raise_for_status()
    return resp.json()


def build_prompt_with_sources(
    question: str,
    results: List[Dict[str, Any]],
    *,
    max_chunk_chars: int = 1200,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Construct a grounded prompt with enumerated sources and return (prompt, sources_meta).

    sources_meta preserves mapping for UI: index, collection, section/account, and small preview.
    """
    lines: List[str] = []

    system = (
        "You are a legal assistant for La Plata County. Answer only using the SOURCES "
        "provided below. If the sources are insufficient, explicitly state that you don't have "
        "enough information. Include citations using [1], [2], etc., that refer to the SOURCES list."
    )

    lines.append(f"SYSTEM:\n{system}\n")
    lines.append(f"QUESTION:\n{question}\n")

    sources_meta: List[Dict[str, Any]] = []
    lines.append("SOURCES:")
    for idx, r in enumerate(results, start=1):
        ident = r.get("section") or r.get("account") or r.get("id") or "unknown"
        collection = r.get("collection", "unknown")
        text = (r.get("text") or "").strip()
        chunk = text[:max_chunk_chars]
        lines.append(f"[{idx}] (collection={collection}, id={ident})\n{chunk}\n")
        sources_meta.append(
            {
                "index": idx,
                "collection": collection,
                "id": ident,
                "preview": chunk[:200],
                "chunk": chunk,
            }
        )

    lines.append(
        "INSTRUCTIONS:\nProvide a concise answer. After each material claim or paragraph, include at least one citation "
        "in the format [n] that references the SOURCES list. Do not invent citations. If a claim "
        "cannot be supported by the sources, say that the information is insufficient."
    )
    lines.append("ANSWER:")

    prompt = "\n".join(lines)
    return prompt, sources_meta


# -----------------------------
# Heuristic Reranker (v1)
# -----------------------------

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")] 


def _jaccard(a_tokens: List[str], b_tokens: List[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a_set, b_set = set(a_tokens), set(b_tokens)
    inter = len(a_set & b_set)
    union = len(a_set | b_set)
    return (inter / union) if union else 0.0


def _parse_relevance(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    *,
    max_chunk_chars: int = 1200,
    top_k: int = 6,
    diversity_threshold: float = 0.8,
) -> List[Dict[str, Any]]:
    """Heuristic rerank + diversity selection.

    - Score each candidate by lexical overlap with the query (Jaccard on tokens)
      and the provided relevance score when available.
    - Select top_k with a redundancy penalty to encourage diversity.
    """
    q_tokens = _tokenize(query)

    scored: List[Tuple[float, Dict[str, Any], List[str]]] = []
    for r in results:
        text = (r.get("text") or "")[:max_chunk_chars]
        tokens = _tokenize(text)
        overlap = _jaccard(q_tokens, tokens)
        rel = _parse_relevance(r.get("relevance"))
        # Combine: emphasize overlap, keep some weight for service-provided relevance
        score = 0.7 * overlap + 0.3 * rel
        scored.append((score, r, tokens))

    # Primary sort by score desc
    scored.sort(key=lambda x: x[0], reverse=True)

    selected: List[Dict[str, Any]] = []
    selected_tokens: List[List[str]] = []

    for score, r, tokens in scored:
        # Diversity check: skip if too similar to any already-selected chunk
        is_redundant = False
        for t_sel in selected_tokens:
            if _jaccard(tokens, t_sel) >= diversity_threshold:
                is_redundant = True
                break
        if is_redundant:
            continue

        selected.append(r)
        selected_tokens.append(tokens)
        if len(selected) >= top_k:
            break

    # If diversity dropped the count too low, fill from the remainder without checks
    if len(selected) < min(top_k, len(results)):
        for _, r, _ in scored:
            if r in selected:
                continue
            selected.append(r)
            if len(selected) >= top_k:
                break

    return selected


def extract_citations(answer_text: str, sources_meta: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse [n] markers from the answer and map them to sources.

    Returns (citations, used_sources), where citations is a list of
    {marker: int, id, collection} and used_sources is the corresponding subset of sources_meta.
    """
    if not answer_text:
        return [], []

    indices = set()
    for m in re.finditer(r"\[(\d+)\]", answer_text):
        try:
            idx = int(m.group(1))
            if idx >= 1:
                indices.add(idx)
        except Exception:
            continue

    citations: List[Dict[str, Any]] = []
    used_sources: List[Dict[str, Any]] = []

    # Build a quick lookup by index
    index_to_source = {s.get("index"): s for s in (sources_meta or [])}

    for idx in sorted(indices):
        src = index_to_source.get(idx)
        if not src:
            continue
        citations.append(
            {
                "marker": idx,
                "id": src.get("id"),
                "collection": src.get("collection"),
            }
        )
        used_sources.append(src)

    return citations, used_sources


def auto_cite_answer(answer_text: str, sources_meta: List[Dict[str, Any]], *,
                     min_jaccard: float = 0.05) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Best-effort citation insertion when the model omits [n] markers.

    - Splits the answer into lines; for each non-empty line, assigns the best-matching
      source by lexical Jaccard overlap. If the score >= min_jaccard and the line
      lacks a [n] marker, append a citation marker at the end of the line.
    - Returns the updated answer text and parsed citations/used_sources.
    """
    if not answer_text or not sources_meta:
        return answer_text, [], []

    # Pre-tokenize source chunks
    src_tokens = {}
    for s in sources_meta:
        idx = s.get("index")
        chunk = s.get("chunk") or s.get("preview") or ""
        src_tokens[idx] = _tokenize(chunk)

    lines = answer_text.split("\n")
    new_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue
        # Skip if already cites
        if re.search(r"\[\d+\]", line):
            new_lines.append(line)
            continue

        ltokens = _tokenize(stripped)
        best_idx, best_score = None, 0.0
        for idx, toks in src_tokens.items():
            score = _jaccard(ltokens, toks)
            if score > best_score:
                best_idx, best_score = idx, score

        if best_idx is not None and best_score >= min_jaccard:
            # Append citation keeping original whitespace/punctuation at end
            if line.endswith(" "):
                new_line = f"{line}[{best_idx}]"
            else:
                new_line = f"{line} [{best_idx}]"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    new_answer = "\n".join(new_lines)
    citations, used_sources = extract_citations(new_answer, sources_meta)

    # If still no citations, attach [1] to the first non-empty line as a minimal fallback
    if not citations and sources_meta:
        for i, line in enumerate(new_lines):
            if line.strip():
                new_lines[i] = (line + ("" if line.endswith(" ") else " ") + f"[1]")
                break
        new_answer = "\n".join(new_lines)
        citations, used_sources = extract_citations(new_answer, sources_meta)
    return new_answer, citations, used_sources


