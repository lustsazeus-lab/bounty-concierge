"""Cross-platform engagement helpers for the RustChain ecosystem.

Star repos, check Dev.to stats, and generate social-bounty proof.
"""

from __future__ import annotations

from typing import Dict, List

import requests

from concierge import config


# ---------------------------------------------------------------------------
# GitHub star helpers
# ---------------------------------------------------------------------------

def star_repo(owner: str, repo: str, token: str) -> bool:
    """Star a single GitHub repository.

    Uses PUT /user/starred/{owner}/{repo} which is idempotent -- starring an
    already-starred repo is a no-op that still returns 204.

    Returns True on success (HTTP 204), False otherwise.
    """
    url = f"https://api.github.com/user/starred/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        resp = requests.put(url, headers=headers, timeout=15)
        return resp.status_code == 204
    except requests.RequestException:
        return False


def star_all_ecosystem_repos(token: str) -> Dict[str, bool]:
    """Star every repository listed in config.REPOS.

    Returns a dict mapping ``"owner/repo"`` to a boolean success flag.
    """
    results: Dict[str, bool] = {}
    for full_name in config.REPOS:
        owner, repo = full_name.split("/", 1)
        results[full_name] = star_repo(owner, repo, token)
    return results


# ---------------------------------------------------------------------------
# Dev.to article stats
# ---------------------------------------------------------------------------

def check_devto_articles(api_key: str) -> List[dict]:
    """Fetch the authenticated user's Dev.to articles.

    Returns a list of dicts with keys: title, url, page_views,
    positive_reactions.
    """
    url = "https://dev.to/api/articles/me"
    headers = {"api-key": api_key, "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    articles = []
    for item in resp.json():
        articles.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "page_views": item.get("page_views_count", 0),
                "positive_reactions": item.get("positive_reactions_count", 0),
            }
        )
    return articles


# ---------------------------------------------------------------------------
# Engagement proof generation
# ---------------------------------------------------------------------------

def generate_engagement_proof(platform: str, action: str, proof_url: str) -> str:
    """Format a markdown comment suitable for claiming a social bounty.

    Parameters
    ----------
    platform : str
        Name of the platform (e.g. "Twitter", "Dev.to", "Moltbook").
    action : str
        What was done (e.g. "shared article", "starred repos", "upvoted").
    proof_url : str
        A public URL that proves the action was taken.

    Returns
    -------
    str
        Markdown-formatted proof comment ready to paste into a GitHub issue.
    """
    return (
        f"**Engagement Proof**\n\n"
        f"- **Platform:** {platform}\n"
        f"- **Action:** {action}\n"
        f"- **Proof:** [{proof_url}]({proof_url})\n\n"
        f"Requesting payout per the bounty terms."
    )


# ---------------------------------------------------------------------------
# Placeholder -- SaaSCity
# ---------------------------------------------------------------------------

def saascity_upvote(dry_run: bool = False) -> dict:
    """Upvote RustChain on SaaSCity.

    Args:
        dry_run: If True, only show what would be upvoted (no API key needed)

    Returns:
        dict with results

    Raises:
        NotImplementedError: If SAASCITY_KEY env var is not set (and not dry_run)
    """
    import os
    import requests

    # Listings to upvote (RustChain, BoTTube)
    listings = [
        {"name": "RustChain", "slug": "rustchain"},
        {"name": "BoTTube", "slug": "bottube"},
    ]

    results = {"upvoted": [], "failed": [], "dry_run": dry_run}

    # Dry run doesn't need API key
    if dry_run:
        for listing in listings:
            print(f"[DRY RUN] Would upvote: {listing['name']} ({listing['slug']})")
            results["upvoted"].append(listing)
        return results

    # Real upvote requires API key
    api_key = os.getenv("SAASCITY_KEY")
    if not api_key:
        raise NotImplementedError(
            "SaaSCity API key needed. Set SAASCITY_KEY env var or visit saascity.io to register."
        )

    for listing in listings:
        if dry_run:
            print(f"[DRY RUN] Would upvote: {listing['name']} ({listing['slug']})")
            results["upvoted"].append(listing)
            continue

        try:
            # Try to upvote - the actual endpoint may vary
            response = requests.post(
                f"{base_url}/listings/{listing['slug']}/upvote",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                print(f"✓ Upvoted: {listing['name']}")
                results["upvoted"].append(listing)
            elif response.status_code == 401:
                results["failed"].append({"listing": listing, "error": "Invalid API key"})
                print(f"✗ Failed: {listing['name']} - Invalid API key")
            else:
                results["failed"].append({"listing": listing, "error": f"HTTP {response.status_code}"})
                print(f"✗ Failed: {listing['name']} - HTTP {response.status_code}")

        except requests.RequestException as e:
            results["failed"].append({"listing": listing, "error": str(e)})
            print(f"✗ Error: {listing['name']} - {e}")

    return results


# Alias for CLI
check_saascity_upvote = saascity_upvote
