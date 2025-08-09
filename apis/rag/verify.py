from __future__ import annotations

from typing import Any, Dict, List, Tuple
import re


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


def _split_sentences(text: str) -> List[str]:
    # Simple sentence splitter: split on newline or punctuation boundaries.
    # Preserve bullets as separate sentences.
    lines = []
    for raw in text.split("\n"):
        s = raw.strip()
        if not s:
            lines.append("")
            continue
        if s.startswith(('- ', '* ', '•')):
            lines.append(s)
            continue
        parts = re.split(r"(?<=[\.!?])\s+", s)
        lines.extend(parts)
    return lines


def verify_answer_support(
    answer_text: str,
    sources_meta: List[Dict[str, Any]],
    *,
    min_support: float = 0.08,
) -> Tuple[str, Dict[str, Any]]:
    """Flag sentences that are insufficiently supported by sources using lexical overlap.

    Returns (possibly annotated answer_text, verification_report)
    verification_report includes summary counts and per-sentence best match info.
    """
    if not answer_text or not sources_meta:
        return answer_text, {
            "total_sentences": 0,
            "supported": 0,
            "unsupported": 0,
            "details": [],
        }

    # Pre-tokenize source chunks
    src_tokens = {}
    for s in sources_meta:
        idx = s.get("index")
        chunk = s.get("chunk") or s.get("preview") or ""
        src_tokens[idx] = _tokenize(chunk)

    sentences = _split_sentences(answer_text)
    new_sentences: List[str] = []
    details: List[Dict[str, Any]] = []
    supported = 0
    unsupported = 0

    for i, sent in enumerate(sentences):
        stripped = sent.strip()
        if not stripped:
            new_sentences.append(sent)
            continue
        # Skip if this line is purely feedback UI text (heuristic)
        if stripped.lower().startswith(("was this answer helpful", "yes,", "no,")):
            new_sentences.append(sent)
            continue
        # Skip if already contains a [n] marker; assume supported
        if re.search(r"\[\d+\]", stripped):
            new_sentences.append(sent)
            details.append({"index": i, "best_marker": None, "best_score": None, "supported": True})
            supported += 1
            continue

        toks = _tokenize(stripped)
        best_idx, best_score = None, 0.0
        for idx, stoks in src_tokens.items():
            score = _jaccard(toks, stoks)
            if score > best_score:
                best_idx, best_score = idx, score

        if best_idx is not None and best_score >= min_support:
            # Attach a citation marker to show support
            annotated = sent + ("" if sent.endswith(" ") else " ") + f"[{best_idx}]"
            new_sentences.append(annotated)
            supported += 1
            details.append({"index": i, "best_marker": best_idx, "best_score": best_score, "supported": True})
        else:
            # Flag as insufficient support
            annotated = sent + ("" if sent.endswith(" ") else " ") + "(insufficient support)"
            new_sentences.append(annotated)
            unsupported += 1
            details.append({"index": i, "best_marker": best_idx, "best_score": best_score, "supported": False})

    annotated_answer = "\n".join(new_sentences)
    report = {
        "total_sentences": len([s for s in sentences if s.strip()]),
        "supported": supported,
        "unsupported": unsupported,
        "details": details,
    }
    return annotated_answer, report


