from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from scipy.sparse import hstack
import re
import os
from lxml import html as lxml_html, etree

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------- Completely generic helpers ----------
_CAMEL_RE = re.compile(r"([a-z])([A-Z])")
_NONWORD_SPLIT = re.compile(r"[^a-z0-9]+", re.I)

def _normalize_text(s: str) -> str:
    """Simple text normalization - no hardcoded stop words."""
    s = s.replace("_", " ").replace("-", " ")
    s = _CAMEL_RE.sub(r"\1 \2", s)
    s = _NONWORD_SPLIT.sub(" ", s)
    return " ".join(s.lower().split())

def _extract_all_tokens(text: str) -> str:
    """Extract all meaningful tokens from any text - completely generic."""
    tokens = []
    
    # Extract all quoted strings
    tokens += re.findall(r"['\"]([^'\"]+)['\"]", text)
    
    # Extract all words with hyphens/underscores
    tokens += re.findall(r"[a-zA-Z][\w-]*", text)
    
    # Extract all attribute-like patterns
    tokens += re.findall(r"@(\w+)\s*=\s*['\"]([^'\"]+)['\"]", text)
    tokens += re.findall(r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]", text)
    
    # Extract CSS-like patterns
    tokens += re.findall(r"#([\w-]+)", text)
    tokens += re.findall(r"\.([\w-]+)", text)
    
    # Flatten and normalize
    all_tokens = []
    for token in tokens:
        if isinstance(token, tuple):
            all_tokens.extend([str(t).lower() for t in token])
        else:
            all_tokens.append(str(token).lower())
    
    return " ".join(all_tokens)

def _signature_from_bs4(el: Tag):
    """Generic signature creation."""
    cls = el.get("class") or []
    return (
        (el.name or "").lower(),
        (el.get("id") or "").lower(),
        (el.get("name") or "").lower(),
        tuple(sorted([c.lower() for c in cls])),
    )

def _signature_from_lxml(node: etree._Element):
    """Generic signature creation."""
    classes = (node.attrib.get("class") or "").split()
    return (
        (node.tag or "").lower(),
        (node.attrib.get("id") or "").lower(),
        (node.attrib.get("name") or "").lower(),
        tuple(sorted([c.lower() for c in classes])),
    )

def _try_locator_match(html: str, soup: BeautifulSoup, locator_value: str):
    """Try to match elements using locator - completely generic."""
    if not locator_value:
        return set(), [], False
    
    matched_sigs = set()
    matched_htmls = []
    
    try:
        # Try as XPath first (if starts with //)
        if locator_value.strip().startswith("//"):
            root = lxml_html.fromstring(html)
            nodes = root.xpath(locator_value)
            for nd in nodes:
                if isinstance(nd, etree._Element):
                    matched_sigs.add(_signature_from_lxml(nd))
                    matched_htmls.append(etree.tostring(nd, encoding="unicode"))
        else:
            # Try as CSS selector
            bs_matches = soup.select(locator_value)
            for el in bs_matches:
                matched_sigs.add(_signature_from_bs4(el))
                matched_htmls.append(str(el))
        
        has_matches = len(matched_sigs) > 0
        if has_matches:
            logger.info(f"[IntentLocator] Locator matched {len(matched_sigs)} elements.")
        else:
            logger.info(f"[IntentLocator] Locator matched no elements. Using extracted tokens.")
            
    except Exception as e:
        logger.info(f"[IntentLocator] Locator error: {str(e)}. Using extracted tokens.")
        has_matches = False
    
    return matched_sigs, matched_htmls, has_matches

def _read_html(html_or_path: str) -> str:
    """Read HTML from string or file."""
    if isinstance(html_or_path, str) and ("<" in html_or_path and "</" in html_or_path):
        return html_or_path
    if isinstance(html_or_path, str) and os.path.exists(html_or_path):
        with open(html_or_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return html_or_path

def _element_to_text(el: Tag) -> str:
    """Convert element to searchable text - completely generic."""
    parts = []
    
    # Add tag name
    if el.name:
        parts.append(el.name)
    
    # Add all attributes
    for attr_name, attr_value in el.attrs.items():
        if isinstance(attr_value, list):
            attr_value = " ".join(map(str, attr_value))
        parts.append(f"{attr_name}:{str(attr_value)}")
    
    # Add visible text
    text = el.get_text(" ", strip=True)
    if text:
        parts.append(text)
    
    return " ".join(parts).lower()

def _build_weighted_vectors(docs: List[str], intent_str: str, locator_tokens: str):
    """Build TF-IDF vectors with proper intent weighting."""
    
    # Create weighted documents - repeat intent multiple times to give it more weight
    intent_normalized = _normalize_text(intent_str)
    
    # Weight the intent heavily (repeat it 3 times)
    weighted_docs = []
    for doc in docs:
        weighted_docs.append(doc)
    
    # Create weighted query - intent gets much more weight than locator tokens
    weighted_query = f"{intent_normalized} {intent_normalized} {intent_normalized} {locator_tokens}".strip()
    
    logger.info(f"[IntentLocator] Weighted query: '{weighted_query}'")
    
    word_vect = TfidfVectorizer(
        lowercase=True,
        analyzer="word",
        ngram_range=(1, 2),
        token_pattern=r"[a-z0-9]+",
    )
    char_vect = TfidfVectorizer(
        lowercase=True,
        analyzer="char_wb",
        ngram_range=(3, 4),
    )
    
    Xw = word_vect.fit_transform(weighted_docs + [weighted_query])
    Xc = char_vect.fit_transform(weighted_docs + [weighted_query])
    X = hstack([Xw, Xc])
    
    return X[:-1], X[-1]

def _calculate_intent_boost(el: Tag, intent_str: str, locator_tokens: str) -> float:
    """Calculate additional boost based on intent matching."""
    boost = 0.0
    
    # Get element text
    element_text = _element_to_text(el)
    intent_normalized = _normalize_text(intent_str)
    locator_words = locator_tokens.split()
    
    # Boost for intent word matches
    intent_words = intent_normalized.split()
    for intent_word in intent_words:
        if intent_word in element_text:
            boost += 0.05  # Small boost per intent word match
    
    # Boost for exact locator token matches
    for locator_word in locator_words:
        if locator_word in element_text:
            boost += 0.02  # Smaller boost per locator word match
    
    # Special boost for exact attribute matches
    if "username" in intent_normalized:
        if "user-name" in (el.get("id") or "").lower():
            boost += 0.1
        if "username" in (el.get("name") or "").lower():
            boost += 0.1
        if "username" in (el.get("placeholder") or "").lower():
            boost += 0.1
    
    if "password" in intent_normalized:
        if "password" in (el.get("id") or "").lower():
            boost += 0.1
        if "password" in (el.get("name") or "").lower():
            boost += 0.1
        if "password" in (el.get("placeholder") or "").lower():
            boost += 0.1
    
    if "login" in intent_normalized:
        if "login" in (el.get("id") or "").lower():
            boost += 0.1
        if "login" in (el.get("name") or "").lower():
            boost += 0.1
        if "login" in (el.get("value") or "").lower():
            boost += 0.1
    
    return boost

class IntentLocatorLibrary:
    """Completely generic library with proper intent weighting."""

    def find_elements_outerhtml_by_intent(
        self,
        html_or_path: str,
        intent_str: str,
        top_k: int = 5,
        min_score: float = 0.0,
        locator_value: str = "",
    ) -> List[str]:
        """
        Generic approach with proper intent weighting:
        1. Try to match elements using locator_value
        2. Weight intent_str much more heavily than locator tokens
        3. Add boosts for exact attribute matches
        4. Return outerHTML of top scoring elements
        """
        top_k = int(top_k)
        min_score = float(min_score)

        html = _read_html(html_or_path)
        soup = BeautifulSoup(html, "lxml")
        elements = soup.find_all(True)

        # Try to match elements using locator value
        matched_sigs, _, has_locator_matches = _try_locator_match(html, soup, locator_value)
        
        # Extract tokens from locator value
        locator_tokens = _extract_all_tokens(locator_value)
        
        # Convert elements to text for matching
        docs = [_element_to_text(el) for el in elements]

        # Build weighted vectors with intent priority
        elem_vecs, q_vec = _build_weighted_vectors(docs, intent_str, locator_tokens)
        sims = linear_kernel(q_vec, elem_vecs).flatten()

        # Score elements with intent boosting
        scored = []
        for idx, el in enumerate(elements):
            score = float(sims[idx])
            
            # Boost exact locator matches (if any)
            if _signature_from_bs4(el) in matched_sigs:
                score += 0.1
            
            # Add intent-based boosting
            intent_boost = _calculate_intent_boost(el, intent_str, locator_tokens)
            score += intent_boost
            
            scored.append((score, idx))

        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top results
        results = []
        for score, idx in scored[:top_k]:
            if score >= min_score:
                results.append(str(elements[idx]))
                logger.info(f"[IntentLocator] Element {len(results)}: score={score:.3f}, tag={elements[idx].name}")
        
        logger.info(f"[IntentLocator] Found {len(results)} elements with score >= {min_score}")
        return results

    def rank_elements_by_intent(
        self,
        html_or_path: str,
        intent_str: str,
        top_k: int = 10,
        min_score: float = 0.0,
        locator_value: str = "",
    ) -> List[Dict[str, Any]]:
        """Generic ranking with proper intent weighting."""
        top_k = int(top_k)
        min_score = float(min_score)

        html = _read_html(html_or_path)
        soup = BeautifulSoup(html, "lxml")
        elements = soup.find_all(True)

        matched_sigs, _, has_locator_matches = _try_locator_match(html, soup, locator_value)
        locator_tokens = _extract_all_tokens(locator_value)

        docs = [_element_to_text(el) for el in elements]
        elem_vecs, q_vec = _build_weighted_vectors(docs, intent_str, locator_tokens)
        sims = linear_kernel(q_vec, elem_vecs).flatten()

        scored = []
        for idx, el in enumerate(elements):
            score = float(sims[idx])
            if _signature_from_bs4(el) in matched_sigs:
                score += 0.1
            
            intent_boost = _calculate_intent_boost(el, intent_str, locator_tokens)
            score += intent_boost
            
            scored.append((score, idx))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, idx in scored[:top_k]:
            if score < min_score:
                continue
            el = elements[idx]
            results.append({
                "score": round(score, 6),
                "tag": el.name,
                "id": el.get("id"),
                "classes": el.get("class"),
                "text": el.get_text(" ", strip=True),
                "outerHTML": str(el),
            })
            logger.info(f"[IntentLocator] Ranked element: score={score:.3f}, tag={el.name}")
        
        logger.info(f"[IntentLocator] Ranked {len(results)} elements with score >= {min_score}")
        return results

    def find_elements_outerhtml_with_score_backoff(
        self,
        html_or_path: str,
        intent_str: str,
        top_k: int = 5,
        start: float = 0.5,
        min_floor: float = 0.0,
        step: float = 0.05,
        locator_value: str = "",
    ):
        """Try different score thresholds until finding results."""
        top_k = int(top_k)
        start = float(start)
        min_floor = float(min_floor)
        step = abs(float(step))

        thr = start
        last = []
        while thr + 1e-9 >= min_floor:
            matches = self.find_elements_outerhtml_by_intent(
                html_or_path, intent_str, top_k=top_k, min_score=thr, locator_value=locator_value
            )
            logger.info(f"[IntentLocator] backoff try min_score={thr}: {len(matches)} match(es)")
            if matches:
                return matches
            last = matches
            thr -= step
        return last

    def rank_elements_with_score_backoff(
        self,
        html_or_path: str,
        intent_str: str,
        top_k: int = 10,
        start: float = 0.5,
        min_floor: float = 0.0,
        step: float = 0.05,
        locator_value: str = "",
    ):
        """Try different score thresholds until finding results."""
        top_k = int(top_k)
        start = float(start)
        min_floor = float(min_floor)
        step = abs(float(step))

        thr = start
        last = []
        while thr + 1e-9 >= min_floor:
            ranked = self.rank_elements_by_intent(
                html_or_path, intent_str, top_k=top_k, min_score=thr, locator_value=locator_value
            )
            logger.info(f"[IntentLocator] backoff try min_score={thr}: {len(ranked)} row(s)")
            if ranked:
                return ranked
            last = ranked
            thr -= step
        return last
