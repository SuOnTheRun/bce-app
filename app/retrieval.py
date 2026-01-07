from typing import Any, Dict, List, Tuple
from app.db import list_cases, get_case

def _normalize_list(s: str) -> List[str]:
    if not s:
        return []
    return [x.strip().lower() for x in s.split(",") if x.strip()]

def score_similarity(query: Dict[str, Any], cand: Dict[str, Any]) -> Tuple[int, List[str]]:
    reasons = []
    score = 0

    q_cat = (query.get("Category") or "").strip().lower()
    q_mkt = (query.get("Market") or "").strip().lower()
    q_dt  = (query.get("Decision_Type") or "").strip().lower()
    q_dw  = (query.get("Decision_Window") or "").strip().lower()
    q_ch  = _normalize_list((query.get("Channels") or "").lower())

    c_cat = (cand.get("category") or "").strip().lower()
    c_mkt = (cand.get("market") or "").strip().lower()
    c_dt  = (cand.get("decision_type") or "").strip().lower()
    c_dw  = (cand.get("decision_window") or "").strip().lower()
    c_ch  = _normalize_list((cand.get("channels") or "").lower())

    if q_cat and c_cat and q_cat == c_cat:
        score += 30
        reasons.append("Same category")

    if q_mkt and c_mkt and q_mkt == c_mkt:
        score += 25
        reasons.append("Same market")

    if q_dt and c_dt and q_dt == c_dt:
        score += 25
        reasons.append("Same decision type")

    if q_dw and c_dw and q_dw == c_dw:
        score += 20
        reasons.append("Same decision window")

    overlap = sorted(set(q_ch).intersection(set(c_ch)))
    if overlap:
        score += min(15, 5 * len(overlap))
        reasons.append(f"Channel overlap: {', '.join(overlap)}")

    return score, reasons

def find_similar_cases(query_campaign: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
    # Pull a recent pool then score locally
    pool, _ = list_cases(limit=200, offset=0)
    scored = []
    for c in pool:
        s, reasons = score_similarity(query_campaign, c)
        if s <= 0:
            continue
        c2 = dict(c)
        c2["similarity_score"] = s
        c2["match_reasons"] = reasons
        scored.append(c2)

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_k]

def hydrate_case(case_id: int) -> Dict[str, Any]:
    c = get_case(case_id)
    return c or {}
