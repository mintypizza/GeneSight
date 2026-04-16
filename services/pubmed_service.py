"""
pubmed_service.py — Search PubMed for relevant biomedical literature.

Uses NCBI E-Utilities (esearch + esummary) to find and return
research papers related to genetic variants and genes.
"""
import requests
import time
from typing import Optional
from utils.cache_manager import get_cached, set_cached


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_LIMIT_DELAY = 0.35


def search_pubmed(query: str, max_results: int = 5) -> dict:
    """
    Search PubMed for relevant literature about a variant or gene.

    Args:
        query: Search term (gene name, variant, disease, etc.)
        max_results: Maximum number of papers to return.

    Returns:
        Dictionary with paper titles, authors, abstracts, and PubMed links.
    """
    cached = get_cached("pubmed", query)
    if cached:
        return cached

    result = {
        "source": "PubMed (NCBI)",
        "query": query,
        "papers": [],
        "total_results": 0,
        "summary": "",
        "error": None
    }

    try:
        # Step 1: Search for paper IDs
        search_resp = requests.get(
            f"{BASE_URL}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            },
            timeout=15
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        total = int(search_data.get("esearchresult", {}).get("count", 0))
        result["total_results"] = total

        if not id_list:
            result["summary"] = f"No PubMed articles found for '{query}'."
            set_cached("pubmed", query, result)
            return result

        time.sleep(RATE_LIMIT_DELAY)

        # Step 2: Get summaries
        summary_resp = requests.get(
            f"{BASE_URL}/esummary.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json"
            },
            timeout=15
        )
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        records = summary_data.get("result", {})
        uid_list = records.get("uids", [])

        for uid in uid_list:
            record = records.get(uid, {})
            if not isinstance(record, dict):
                continue

            # Parse authors
            authors = record.get("authors", [])
            author_names = []
            if isinstance(authors, list):
                for auth in authors[:3]:
                    if isinstance(auth, dict):
                        author_names.append(auth.get("name", ""))
                if len(authors) > 3:
                    author_names.append("et al.")

            # Parse publication date
            pub_date = record.get("pubdate", "")
            epub_date = record.get("epubdate", "")

            paper = {
                "pmid": uid,
                "title": record.get("title", "No title"),
                "authors": author_names,
                "journal": record.get("fulljournalname", record.get("source", "")),
                "pub_date": pub_date,
                "epub_date": epub_date,
                "doi": record.get("elocationid", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                "volume": record.get("volume", ""),
                "issue": record.get("issue", ""),
                "pages": record.get("pages", "")
            }

            result["papers"].append(paper)

        # Build summary
        if result["papers"]:
            paper_lines = []
            for i, p in enumerate(result["papers"][:3], 1):
                authors_str = ", ".join(p["authors"][:2])
                paper_lines.append(
                    f"{i}. **{p['title']}** — {authors_str} ({p['pub_date']}) "
                    f"[PubMed]({p['url']})"
                )
            result["summary"] = (
                f"Found **{total}** relevant articles in PubMed. "
                f"Top results:\n" + "\n".join(paper_lines)
            )
        else:
            result["summary"] = f"PubMed returned {total} results but details could not be parsed."

    except requests.exceptions.RequestException as e:
        result["error"] = f"PubMed API error: {str(e)}"
        result["summary"] = f"Unable to search PubMed: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        result["summary"] = f"Error processing PubMed data: {str(e)}"

    set_cached("pubmed", query, result)
    return result
