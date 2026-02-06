from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from scipy.sparse import hstack
import re

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------- Normalization helpers ----------
_CAMEL_RE = re.compile(r"([a-z])([A-Z])")
_NONWORD_SPLIT = re.compile(r"[^a-z0-9]+", re.I)
_STOP_TOKENS = {"locator", "loc", "element", "el", "control", "widget"}  # generic noise


def _split_camel_and_underscores(s: str) -> str:
    s = s.replace("_", " ").replace("-", " ")
    s = _CAMEL_RE.sub(r"\1 \2", s)
    s = _NONWORD_SPLIT.sub(" ", s)
    return " ".join(s.lower().split())


def _normalize_intent(s: str) -> str:
    # split, then drop generic noise tokens
    tokens = _split_camel_and_underscores(s).split()
    tokens = [t for t in tokens if t not in _STOP_TOKENS]
    return " ".join(tokens)


# ---------- Feature builders ----------
def _build_vectors(docs: List[str], query: str):
    # WORD ngrams capture semantics; CHAR ngrams tolerate hyphens/camelCase
    word_vect = TfidfVectorizer(
        lowercase=True,
        analyzer="word",
        ngram_range=(1, 3),
        token_pattern=r"[a-z0-9]+",
    )
    char_vect = TfidfVectorizer(
        lowercase=True,
        analyzer="char_wb",
        ngram_range=(3, 5),
    )
    Xw = word_vect.fit_transform(docs + [query])
    Xc = char_vect.fit_transform(docs + [query])
    X = hstack([Xw, Xc])
    return X[:-1], X[-1]


# ---------- Domain boosts for flight intents ----------
def _intent_domain_boost(intent_norm: str) -> str:
    """Add domain tokens for flights/open/today to query vector."""
    tokens = []
    if any(w in intent_norm for w in ["flight", "flights"]):
        tokens += ["flight flights fs_flight_no flight_schedules"]
    if any(w in intent_norm for w in ["open", "opened", "opening", "status"]):
        # common encodings of "open" in ops feeds: FO (fully open) / O (open)
        tokens += ["open opened fo o fs_flight_status_system status"]
    if any(w in intent_norm for w in ["today", "todays", "now", "current", "tonight"]):
        # typical Oracle-ish date filters:
        tokens += ["trunc sysdate current_date today fs_flight_sta_std date"]
    if any(w in intent_norm for w in ["depart", "dep", "outbound"]):
        tokens += ["fs_dep_station etd atd std fs_flight_eta_etd fs_flight_ata_atd"]
    if not tokens:
        return intent_norm
    return f"{intent_norm} " + " ".join(tokens)


# ---------- Doc parsing (schemas / queries / relationships) ----------
# Sections are optional/fault tolerant; everything degrades gracefully.

_SEC_SCHEMA = re.compile(r"^##\s*1\)\s*Table Schemas.*?$", re.I | re.M)
_SEC_QUERIES = re.compile(r"^##\s*2\)\s*Queries.*?$", re.I | re.M)
_SEC_REL = re.compile(r"^##\s*3\)\s*Relationships.*?$", re.I | re.M)

_H3 = re.compile(r"^###\s+.*$", re.M)

_BACKTICK_SQL = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.I)
_TABLE_NAME_INLINE = re.compile(r"`([^`]+)`")


def _slice_section(
    content: str, anchor_re: re.Pattern, next_anchors: List[re.Pattern]
) -> str:
    m = anchor_re.search(content)
    if not m:
        return ""
    start = m.start()
    end = len(content)
    for na in next_anchors:
        nm = na.search(content, pos=start + 1)
        if nm:
            end = min(end, nm.start())
    return content[start:end].strip()


def _extract_schema_chunks(content: str) -> List[Dict[str, Any]]:
    # Standard knowledge doc parsing
    section = _slice_section(content, _SEC_SCHEMA, [_SEC_QUERIES, _SEC_REL])

    # If no standard section found, use the whole content (handles auto-generated schema md)
    if not section:
        section = content

    chunks: List[Dict[str, Any]] = []
    # Split by ### headers (each table schema sits under an H3)
    # The header might be "### 1.1) `TABLE_NAME`" or "### Table: TABLE_NAME"
    positions = [m.start() for m in _H3.finditer(section)] + [len(section)]

    if len(positions) <= 1:
        # fallback: try to find any mention of tables
        names = _TABLE_NAME_INLINE.findall(section)
        if names:
            chunks.append({"type": "schema", "label": names[0], "text": section})
        return chunks

    # iterate H3 blocks
    h3_iter = list(_H3.finditer(section))
    for i, h3 in enumerate(h3_iter):
        h3_start = h3.start()
        h3_end = positions[i + 1]
        block = section[h3_start:h3_end].strip()

        # label extraction
        hdr_line = h3.group(0)
        # 1. Try backticks in header: ### Table `name`
        names = _TABLE_NAME_INLINE.findall(hdr_line)
        if not names:
            # 2. Try "Table: Name" format
            m = re.search(r"Table:\s*([a-zA-Z0-9_]+)", hdr_line, re.I)
            if m:
                names = [m.group(1)]
        if not names:
            # 3. Try backticks in block first line
            names = _TABLE_NAME_INLINE.findall(block.splitlines()[0])

        label = names[0] if names else hdr_line.replace("#", "").strip()
        chunks.append({"type": "schema", "label": label, "text": block})
    return chunks


def _extract_query_chunks(content: str) -> List[Dict[str, Any]]:
    section = _slice_section(content, _SEC_QUERIES, [_SEC_REL])
    if not section:
        # Fallback: grab any SQL blocks globally
        sql_blocks = _BACKTICK_SQL.findall(content)
    else:
        sql_blocks = _BACKTICK_SQL.findall(section)
    chunks: List[Dict[str, Any]] = []
    for sql in sql_blocks:
        # derive a simple label
        first_line = next(
            (ln.strip() for ln in sql.strip().splitlines() if ln.strip()), "SQL"
        )
        label = (first_line[:80] + "…") if len(first_line) > 80 else first_line
        chunks.append({"type": "query", "label": label, "text": sql.strip()})
    return chunks


def _extract_relationship_chunks(content: str) -> List[Dict[str, Any]]:
    section = _slice_section(content, _SEC_REL, [])
    if not section:
        return []
    # Split by numbered items "1)", "2)" or by blank lines.
    items = re.split(r"\n\s*(?=\d+\)\s)|\n{2,}", section)
    chunks: List[Dict[str, Any]] = []
    for it in items:
        it = it.strip()
        if not it:
            continue
        # Ignore the header line "## 3) Relationships ..."
        if it.lower().startswith("##"):
            continue
        # label is first sentence/line
        first = it.splitlines()[0].strip()
        label = (first[:80] + "…") if len(first) > 80 else first
        chunks.append({"type": "relationship", "label": label, "text": it})
    return chunks


def _rank_chunks_by_intent(
    chunks: List[Dict[str, Any]], intent: str, min_score: float, top_k: int
) -> List[Dict[str, Any]]:
    if not chunks:
        return []
    docs = []
    for c in chunks:
        # vectorize over label + text; include type as a hint
        docs.append(f"{c.get('type','')} {c.get('label','')} {c.get('text','')}")
    intent_norm = _normalize_intent(intent)
    intent_boosted = _intent_domain_boost(intent_norm)
    elem_vecs, q_vec = _build_vectors(docs, intent_boosted)
    sims = linear_kernel(q_vec, elem_vecs).flatten()
    order = sims.argsort()[::-1]
    out: List[Dict[str, Any]] = []
    for idx in order[: int(top_k)]:
        score = float(sims[idx])
        if score < float(min_score):
            continue
        c = chunks[idx].copy()
        c["score"] = round(score, 6)
        out.append(c)
    return out


# ==============================
# Library with HTML + Doc intents
# ==============================
class IntentQueriesLibrary:
    """Python library:
    1) Ranks text knowledge (schemas/queries/relationships) by 'intent' and returns matches.
    """

    # --------- NEW: Knowledge intent over text (schemas/queries/relationships) ---------
    def rank_schemas_by_intent(
        self,
        content_text: str,
        intent_str: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Returns top-matching schema chunks: [{score, type='schema', label, text}]."""
        schemas = _extract_schema_chunks(content_text)
        return _rank_chunks_by_intent(schemas, intent_str, min_score, top_k)

    def rank_queries_by_intent(
        self,
        content_text: str,
        intent_str: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Returns top-matching SQL blocks: [{score, type='query', label, text}]."""
        queries = _extract_query_chunks(content_text)
        return _rank_chunks_by_intent(queries, intent_str, min_score, top_k)

    def rank_relationships_by_intent(
        self,
        content_text: str,
        intent_str: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Returns top relationships: [{score, type='relationship', label, text}]."""
        rels = _extract_relationship_chunks(content_text)
        return _rank_chunks_by_intent(rels, intent_str, min_score, top_k)

    def get_queries_schemas_relationships_by_intent(
        self,
        content_text: str,
        intent_str: str,
        top_k_each: int = 5,
        min_score: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Convenience: returns a dict with 'queries', 'schemas', 'relationships',
        each a ranked list of {score, type, label, text}.
        """
        res = {
            "queries": self.rank_queries_by_intent(
                content_text, intent_str, top_k_each, min_score
            ),
            "schemas": self.rank_schemas_by_intent(
                content_text, intent_str, top_k_each, min_score
            ),
            "relationships": self.rank_relationships_by_intent(
                content_text, intent_str, top_k_each, min_score
            ),
        }
        return res
