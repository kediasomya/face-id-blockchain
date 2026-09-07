"""
Genuine reverse-image search for finding a real matching web / social-media post.

Pipeline:
    local image -> upload to a temporary public host -> SerpApi Google Lens
    (reverse image search) -> real matching pages -> pick best (social first).

This is a real search step, NOT a hardcoded result.
"""

import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# Domains we treat as "social media" for prioritisation / labelling.
SOCIAL_DOMAINS = (
    "instagram.com", "twitter.com", "x.com", "facebook.com", "fb.com",
    "tiktok.com", "linkedin.com", "youtube.com", "youtu.be", "reddit.com",
    "pinterest.com", "tumblr.com", "flickr.com", "threads.net", "snapchat.com",
)


class ReverseImageSearcher:
    """Finds a real matching post for a face image via SerpApi reverse image search."""

    SERPAPI_URL = "https://serpapi.com/search.json"

    def __init__(self, api_key: str, similarity_threshold: float = 0.0):
        """
        Args:
            api_key: SerpApi API key (https://serpapi.com)
            similarity_threshold: kept for interface compatibility (SerpApi ranks results)
        """
        self.api_key = api_key
        self.similarity_threshold = similarity_threshold

    # ------------------------------------------------------------------ #
    # Step 1: make the local image publicly reachable so the search
    # engine can fetch it. We try a couple of free anonymous hosts.
    # ------------------------------------------------------------------ #
    def upload_image(self, image_path: str) -> Optional[str]:
        """Upload a local image to a temporary public host, return its URL."""
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None

        # Try catbox.moe first, then 0x0.st as a fallback.
        for uploader in (self._upload_catbox, self._upload_0x0):
            try:
                url = uploader(image_path)
                if url and url.startswith("http"):
                    logger.info(f"Uploaded image to public host: {url}")
                    return url
            except Exception as e:
                logger.warning(f"Upload via {uploader.__name__} failed: {e}")
        logger.error("All image uploads failed; cannot run reverse image search")
        return None

    @staticmethod
    def _upload_catbox(image_path: str) -> Optional[str]:
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=30,
            )
        resp.raise_for_status()
        return resp.text.strip()

    @staticmethod
    def _upload_0x0(image_path: str) -> Optional[str]:
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://0x0.st",
                files={"file": f},
                headers={"User-Agent": "face-id-blockchain/1.0"},
                timeout=30,
            )
        resp.raise_for_status()
        return resp.text.strip()

    # ------------------------------------------------------------------ #
    # Step 2: reverse image search via SerpApi (Google Lens engine).
    # ------------------------------------------------------------------ #
    def search(self, image_url: str) -> List[Dict]:
        """Run a reverse image search on a public image URL via SerpApi."""
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": self.api_key,
        }
        logger.info("Running SerpApi Google Lens reverse image search...")
        resp = requests.get(self.SERPAPI_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            logger.error(f"SerpApi error: {data['error']}")
            return []

        matches = data.get("visual_matches", []) or []
        logger.info(f"SerpApi returned {len(matches)} visual match(es)")
        return self._process_matches(matches)

    def _process_matches(self, matches: List[Dict]) -> List[Dict]:
        """Normalise SerpApi visual matches into our result shape."""
        processed = []
        for i, m in enumerate(matches):
            link = m.get("link") or ""
            if not link:
                continue
            domain = urlparse(link).netloc.lower().replace("www.", "")
            is_social = any(d in domain for d in SOCIAL_DOMAINS)
            processed.append({
                "image_url": m.get("thumbnail") or m.get("image") or "",
                "host_url": link,
                "title": m.get("title", ""),
                "source": m.get("source", domain),
                "is_social_media": is_social,
                # Rank-based confidence: earlier results score higher.
                "similarity_score": round(max(0.5, 1.0 - i * 0.03), 4),
                "metadata": {"position": i + 1, "domain": domain},
            })
        return processed

    # ------------------------------------------------------------------ #
    # Step 3: pick the best real match (prefer genuine social-media posts).
    # ------------------------------------------------------------------ #
    def find_matching_post(self, image_path: str) -> Optional[Dict]:
        """
        Full genuine search: upload -> reverse image search -> best real match.

        Returns the best matching post metadata, or None if nothing was found.
        """
        public_url = self.upload_image(image_path)
        if not public_url:
            return None

        results = self.search(public_url)
        if not results:
            logger.warning("No matching web/social results found")
            return None

        # Prefer social-media matches; otherwise take the top-ranked web result.
        social = [r for r in results if r["is_social_media"]]
        pool = social if social else results
        best = max(pool, key=lambda r: r["similarity_score"])

        # Attach the public URL we searched with (useful for the on-chain record).
        best["searched_image_url"] = public_url
        best["total_matches"] = len(results)
        best["social_matches"] = len(social)

        kind = "social-media" if best["is_social_media"] else "web"
        logger.info(
            f"Best {kind} match: {best['host_url']} "
            f"(from {len(results)} results, {len(social)} social)"
        )
        return best

    @staticmethod
    def extract_social_media_handle(url: str) -> Optional[str]:
        """Extract a handle/id from a social URL path (best effort)."""
        try:
            parts = urlparse(url).path.strip("/").split("/")
            return parts[0] if parts and parts[0] else None
        except Exception:
            return None
