"""
clinvar_service.py — Query NCBI ClinVar for variant clinical significance.

Uses NCBI E-Utilities (esearch + esummary) to retrieve:
  - Clinical significance classification
  - Associated diseases/conditions
  - Review status and evidence level
  - Variant details and accession numbers
"""
import requests
import time
from typing import Optional
from utils.cache_manager import get_cached, set_cached


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_LIMIT_DELAY = 0.35  # seconds between requests (NCBI limit: 3/sec)


def query_clinvar(search_term: str, gene: Optional[str] = None, retmax: int = 5) -> dict:
    """
    Search ClinVar for a variant and return clinical significance data.

    Args:
        search_term: The variant to search (rsID, gene+variant, HGVS, etc.)
        gene: Optional gene name to narrow results.
        retmax: Maximum number of records to return.

    Returns:
        Dictionary with ClinVar results including clinical significance,
        associated conditions, review status, and variant details.
    """
    cache_key = f"{search_term}|{gene or ''}"
    cached = get_cached("clinvar", cache_key)
    if cached:
        return cached

    # Build search query
    query_parts = []
    if search_term:
        query_parts.append(search_term)
    if gene:
        query_parts.append(f"{gene}[gene]")
    query = " AND ".join(query_parts) if len(query_parts) > 1 else query_parts[0]

    result = {
        "source": "ClinVar (NCBI)",
        "query": query,
        "variants": [],
        "summary": "",
        "error": None
    }

    try:
        # Step 1: Search for variant IDs
        search_resp = requests.get(
            f"{BASE_URL}/esearch.fcgi",
            params={
                "db": "clinvar",
                "term": query,
                "retmax": retmax,
                "retmode": "json"
            },
            timeout=15
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        total_count = int(search_data.get("esearchresult", {}).get("count", 0))
        result["total_results"] = total_count

        if not id_list:
            result["summary"] = f"No ClinVar records found for '{query}'."
            set_cached("clinvar", cache_key, result)
            return result

        time.sleep(RATE_LIMIT_DELAY)

        # Step 2: Get summaries for found IDs
        summary_resp = requests.get(
            f"{BASE_URL}/esummary.fcgi",
            params={
                "db": "clinvar",
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

            # Extract clinical significance
            clinical_sig = record.get("clinical_significance", {})
            if isinstance(clinical_sig, dict):
                significance = clinical_sig.get("description", "Not provided")
                last_evaluated = clinical_sig.get("last_evaluated", "")
                review_status = clinical_sig.get("review_status", "")
            else:
                significance = str(clinical_sig) if clinical_sig else "Not provided"
                last_evaluated = ""
                review_status = ""

            # Extract conditions/traits
            trait_set = record.get("trait_set", [])
            conditions = []
            if isinstance(trait_set, list):
                for trait in trait_set:
                    if isinstance(trait, dict):
                        trait_name = trait.get("trait_name", "")
                        if trait_name:
                            conditions.append(trait_name)

            # Extract gene information
            genes = []
            gene_list = record.get("genes", [])
            if isinstance(gene_list, list):
                for g in gene_list:
                    if isinstance(g, dict):
                        genes.append(g.get("symbol", ""))

            # Extract variation details
            variation_set = record.get("variation_set", [])
            variant_name = record.get("title", "")

            variant_entry = {
                "clinvar_id": uid,
                "accession": record.get("accession", f"VCV{uid}"),
                "variant_name": variant_name,
                "clinical_significance": significance,
                "review_status": review_status,
                "last_evaluated": last_evaluated,
                "conditions": conditions,
                "genes": genes,
                "variant_type": record.get("obj_type", ""),
                "url": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{uid}/"
            }

            # Star rating from review status
            variant_entry["star_rating"] = _review_status_stars(review_status)

            result["variants"].append(variant_entry)

        # Build summary
        if result["variants"]:
            top = result["variants"][0]
            result["summary"] = (
                f"ClinVar classifies this variant as **{top['clinical_significance']}** "
                f"(Review: {top['star_rating']}★). "
                f"Associated conditions: {', '.join(top['conditions']) if top['conditions'] else 'None listed'}. "
                f"[ClinVar Link]({top['url']})"
            )
        else:
            result["summary"] = f"ClinVar returned {total_count} records but details could not be parsed."

    except requests.exceptions.RequestException as e:
        result["error"] = f"ClinVar API error: {str(e)}"
        result["summary"] = f"Unable to query ClinVar: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        result["summary"] = f"Error processing ClinVar data: {str(e)}"

    set_cached("clinvar", cache_key, result)
    return result


def _review_status_stars(status: str) -> int:
    """Convert ClinVar review status to star rating (0-4)."""
    status_lower = (status or "").lower()
    if "practice guideline" in status_lower:
        return 4
    elif "expert panel" in status_lower:
        return 3
    elif "multiple submitters" in status_lower:
        return 2
    elif "single submitter" in status_lower:
        return 1
    return 0
