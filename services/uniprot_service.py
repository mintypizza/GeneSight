"""
uniprot_service.py — Query UniProt REST API for protein function data.

Returns protein function, domain architecture, subcellular location,
known disease associations, and PDB structure links.
"""
import requests
from typing import Optional
from utils.cache_manager import get_cached, set_cached


UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"
UNIPROT_ENTRY_URL = "https://rest.uniprot.org/uniprotkb"


def query_uniprot(gene_name: str, organism: str = "human") -> dict:
    """
    Search UniProt for protein information by gene name.

    Args:
        gene_name: Gene symbol (e.g., 'BRCA1', 'TP53')
        organism: Organism filter (default: 'human')

    Returns:
        Dictionary with protein function, domains, diseases, and structure info.
    """
    cache_key = f"{gene_name}|{organism}"
    cached = get_cached("uniprot", cache_key)
    if cached:
        return cached

    result = {
        "source": "UniProt",
        "query": gene_name,
        "protein": None,
        "summary": "",
        "error": None
    }

    organism_id = "9606" if organism.lower() == "human" else organism

    try:
        # Search for the gene
        search_resp = requests.get(
            UNIPROT_SEARCH_URL,
            params={
                "query": f"gene_exact:{gene_name} AND organism_id:{organism_id} AND reviewed:true",
                "format": "json",
                "size": 1,
                "fields": "accession,id,protein_name,gene_names,organism_name,length,"
                          "cc_function,cc_subcellular_location,cc_disease,cc_pathway,"
                          "ft_domain,ft_region,ft_binding,ft_active_site,"
                          "xref_pdb,cc_interaction"
            },
            headers={"Accept": "application/json"},
            timeout=15
        )
        search_resp.raise_for_status()
        data = search_resp.json()

        results = data.get("results", [])
        if not results:
            # Try broader search without reviewed filter
            search_resp = requests.get(
                UNIPROT_SEARCH_URL,
                params={
                    "query": f"gene:{gene_name} AND organism_id:{organism_id}",
                    "format": "json",
                    "size": 1,
                    "fields": "accession,id,protein_name,gene_names,organism_name,length,"
                              "cc_function,cc_subcellular_location,cc_disease,cc_pathway,"
                              "ft_domain,ft_region,ft_binding,ft_active_site,"
                              "xref_pdb,cc_interaction"
                },
                headers={"Accept": "application/json"},
                timeout=15
            )
            search_resp.raise_for_status()
            data = search_resp.json()
            results = data.get("results", [])

        if not results:
            result["summary"] = f"No UniProt entry found for gene '{gene_name}'."
            set_cached("uniprot", cache_key, result)
            return result

        entry = results[0]
        accession = entry.get("primaryAccession", "")

        # Parse protein info
        protein_info = {
            "accession": accession,
            "entry_name": entry.get("uniProtkbId", ""),
            "url": f"https://www.uniprot.org/uniprot/{accession}",
            "length": entry.get("sequence", {}).get("length", 0) if isinstance(entry.get("sequence"), dict) else 0,
        }

        # Protein name
        prot_desc = entry.get("proteinDescription", {})
        rec_name = prot_desc.get("recommendedName", {})
        if rec_name:
            full_name = rec_name.get("fullName", {})
            protein_info["name"] = full_name.get("value", "") if isinstance(full_name, dict) else str(full_name)
        else:
            sub_names = prot_desc.get("submissionNames", [])
            if sub_names:
                protein_info["name"] = sub_names[0].get("fullName", {}).get("value", gene_name)
            else:
                protein_info["name"] = gene_name

        # Gene names
        gene_names = entry.get("genes", [])
        if gene_names:
            primary_gene = gene_names[0].get("geneName", {})
            protein_info["gene_symbol"] = primary_gene.get("value", gene_name) if isinstance(primary_gene, dict) else gene_name
            synonyms = gene_names[0].get("synonyms", [])
            protein_info["gene_synonyms"] = [s.get("value", "") for s in synonyms if isinstance(s, dict)]
        else:
            protein_info["gene_symbol"] = gene_name
            protein_info["gene_synonyms"] = []

        # Function from comments
        comments = entry.get("comments", [])
        protein_info["function"] = ""
        protein_info["subcellular_location"] = []
        protein_info["diseases"] = []
        protein_info["pathway"] = ""

        for comment in comments:
            comment_type = comment.get("commentType", "")

            if comment_type == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    protein_info["function"] = texts[0].get("value", "")

            elif comment_type == "SUBCELLULAR LOCATION":
                locs = comment.get("subcellularLocations", [])
                for loc in locs:
                    location = loc.get("location", {})
                    if isinstance(location, dict):
                        protein_info["subcellular_location"].append(location.get("value", ""))

            elif comment_type == "DISEASE":
                disease = comment.get("disease", {})
                if isinstance(disease, dict):
                    disease_info = {
                        "name": disease.get("diseaseId", ""),
                        "description": disease.get("description", ""),
                        "acronym": disease.get("acronym", "")
                    }
                    protein_info["diseases"].append(disease_info)

            elif comment_type == "PATHWAY":
                texts = comment.get("texts", [])
                if texts:
                    protein_info["pathway"] = texts[0].get("value", "")

        # Domains from features
        features = entry.get("features", [])
        protein_info["domains"] = []
        protein_info["active_sites"] = []
        protein_info["binding_sites"] = []

        for feat in features:
            feat_type = feat.get("type", "")
            feat_desc = feat.get("description", "")
            feat_loc = feat.get("location", {})
            start = feat_loc.get("start", {}).get("value", "") if isinstance(feat_loc.get("start"), dict) else ""
            end = feat_loc.get("end", {}).get("value", "") if isinstance(feat_loc.get("end"), dict) else ""

            feat_entry = {
                "name": feat_desc,
                "start": start,
                "end": end
            }

            if feat_type == "Domain":
                protein_info["domains"].append(feat_entry)
            elif feat_type == "Active site":
                protein_info["active_sites"].append(feat_entry)
            elif feat_type == "Binding site":
                protein_info["binding_sites"].append(feat_entry)

        # PDB cross-references
        xrefs = entry.get("uniProtKBCrossReferences", [])
        protein_info["pdb_structures"] = []
        for xref in xrefs:
            if xref.get("database") == "PDB":
                pdb_id = xref.get("id", "")
                protein_info["pdb_structures"].append({
                    "pdb_id": pdb_id,
                    "url": f"https://www.rcsb.org/structure/{pdb_id}"
                })

        result["protein"] = protein_info

        # Build summary
        func_text = protein_info["function"][:200] + "..." if len(protein_info.get("function", "")) > 200 else protein_info.get("function", "")
        disease_names = [d["name"] for d in protein_info["diseases"][:3]]
        domain_names = [d["name"] for d in protein_info["domains"][:5]]

        summary_parts = [f"**{protein_info['name']}** ({protein_info['gene_symbol']}, {protein_info['length']} aa)"]
        if func_text:
            summary_parts.append(f"\n**Function:** {func_text}")
        if domain_names:
            summary_parts.append(f"\n**Domains:** {', '.join(domain_names)}")
        if disease_names:
            summary_parts.append(f"\n**Disease associations:** {', '.join(disease_names)}")
        if protein_info["pdb_structures"]:
            summary_parts.append(f"\n**3D structures:** {len(protein_info['pdb_structures'])} PDB entries available")
        summary_parts.append(f"\n[UniProt Link]({protein_info['url']})")

        result["summary"] = "\n".join(summary_parts)

    except requests.exceptions.RequestException as e:
        result["error"] = f"UniProt API error: {str(e)}"
        result["summary"] = f"Unable to query UniProt: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        result["summary"] = f"Error processing UniProt data: {str(e)}"

    set_cached("uniprot", cache_key, result)
    return result
