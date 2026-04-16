"""
tools.py — Tool definitions for Gemma 4 function calling.

Each tool is a Python function with typed parameters and detailed docstrings.
The google-genai SDK automatically converts these to JSON schemas for the model.
"""
import json
from pathlib import Path
from services.clinvar_service import query_clinvar
from services.uniprot_service import query_uniprot
from services.pubmed_service import search_pubmed


# Load ACMG guidelines for local pathogenicity assessment
_ACMG_PATH = Path(__file__).parent.parent / "data" / "acmg_guidelines.json"
with open(_ACMG_PATH, 'r', encoding='utf-8') as f:
    _ACMG_DATA = json.load(f)


def tool_query_clinvar(variant_query: str, gene_name: str = "") -> str:
    """Query the ClinVar database for clinical significance of a genetic variant.

    Use this tool when you need to determine whether a genetic variant is
    pathogenic, benign, or of uncertain significance. ClinVar aggregates
    submissions from clinical labs and expert panels worldwide.

    Args:
        variant_query: The variant identifier to search. Can be an rsID
            (e.g., 'rs80357714'), HGVS notation (e.g., 'c.68_69del'),
            or a descriptive search term.
        gene_name: Optional gene symbol to narrow search results
            (e.g., 'BRCA1', 'TP53').

    Returns:
        A JSON string containing ClinVar results including clinical significance
        classification, associated conditions, review status (star rating),
        and links to the ClinVar database entry.
    """
    result = query_clinvar(variant_query, gene=gene_name if gene_name else None)
    return json.dumps(result, indent=2, default=str)


def tool_query_uniprot(gene_name: str) -> str:
    """Query the UniProt database for protein function and structure information.

    Use this tool when you need detailed information about the protein encoded
    by a gene, including its biological function, protein domains, subcellular
    localization, known disease associations, and available 3D structures.

    Args:
        gene_name: The gene symbol to search (e.g., 'BRCA1', 'TP53', 'CFTR').
            Must be a standard HGNC gene symbol.

    Returns:
        A JSON string containing protein name, function description,
        domain architecture, disease associations, PDB structure IDs,
        and a link to the UniProt entry.
    """
    result = query_uniprot(gene_name)
    return json.dumps(result, indent=2, default=str)


def tool_search_pubmed(search_query: str, max_papers: int = 5) -> str:
    """Search PubMed for relevant biomedical research literature.

    Use this tool when you need to find published research about a genetic
    variant, gene, or disease. Returns the most relevant papers with their
    titles, authors, journals, and PubMed links.

    Args:
        search_query: The search terms for PubMed. Can include gene names,
            variant identifiers, disease names, or combinations
            (e.g., 'BRCA1 pathogenic variant breast cancer').
        max_papers: Maximum number of papers to return (1-10, default 5).

    Returns:
        A JSON string containing a list of relevant papers with titles,
        authors, journal names, publication dates, and PubMed URLs.
    """
    max_papers = min(max(1, max_papers), 10)
    result = search_pubmed(search_query, max_results=max_papers)
    return json.dumps(result, indent=2, default=str)


def tool_assess_pathogenicity(
    variant_type: str,
    population_frequency: str = "unknown",
    in_functional_domain: str = "unknown",
    computational_prediction: str = "unknown",
    clinical_significance_from_clinvar: str = "unknown",
    functional_evidence: str = "unknown"
) -> str:
    """Assess variant pathogenicity using ACMG/AMP guidelines framework.

    Use this tool to systematically evaluate the pathogenicity of a genetic
    variant using the American College of Medical Genetics and Genomics (ACMG)
    criteria. This provides a structured assessment based on available evidence.

    Args:
        variant_type: Type of variant. One of: 'nonsense', 'frameshift',
            'splice_site', 'missense', 'in_frame_deletion', 'in_frame_insertion',
            'synonymous', 'intronic', 'snv', 'other'.
        population_frequency: Allele frequency in general population.
            One of: 'absent', 'very_rare' (<0.01%), 'rare' (<1%),
            'common' (>1%), 'very_common' (>5%), 'unknown'.
        in_functional_domain: Whether variant is in a critical functional domain.
            One of: 'yes', 'no', 'unknown'.
        computational_prediction: In silico prediction result.
            One of: 'damaging', 'tolerated', 'conflicting', 'unknown'.
        clinical_significance_from_clinvar: ClinVar classification if available.
            One of: 'pathogenic', 'likely_pathogenic', 'uncertain',
            'likely_benign', 'benign', 'unknown'.
        functional_evidence: Whether functional studies support pathogenicity.
            One of: 'supports_damaging', 'supports_benign', 'no_data', 'unknown'.

    Returns:
        A JSON string containing ACMG criteria assessment, evidence summary,
        recommended classification, and confidence level.
    """
    criteria_met = {"pathogenic": [], "benign": []}
    evidence_notes = []

    # PVS1: Null variant in LOF gene
    if variant_type in ("nonsense", "frameshift", "splice_site"):
        criteria_met["pathogenic"].append("PVS1")
        evidence_notes.append(
            f"PVS1: {variant_type} variant — null/loss-of-function variant type "
            "(very strong pathogenic evidence)"
        )

    # PM1: Functional domain
    if in_functional_domain == "yes":
        criteria_met["pathogenic"].append("PM1")
        evidence_notes.append(
            "PM1: Variant located in a critical functional domain "
            "(moderate pathogenic evidence)"
        )

    # PM2: Absent from population
    if population_frequency in ("absent", "very_rare"):
        criteria_met["pathogenic"].append("PM2")
        evidence_notes.append(
            f"PM2: Variant is {population_frequency} in population databases "
            "(moderate pathogenic evidence)"
        )

    # BA1: Very common → standalone benign
    if population_frequency == "very_common":
        criteria_met["benign"].append("BA1")
        evidence_notes.append(
            "BA1: Allele frequency >5% in general population "
            "(standalone benign evidence)"
        )

    # BS1: Common → strong benign
    if population_frequency == "common":
        criteria_met["benign"].append("BS1")
        evidence_notes.append(
            "BS1: Allele frequency greater than expected for disorder "
            "(strong benign evidence)"
        )

    # PP3 / BP4: Computational predictions
    if computational_prediction == "damaging":
        criteria_met["pathogenic"].append("PP3")
        evidence_notes.append(
            "PP3: Computational tools predict damaging effect "
            "(supporting pathogenic evidence)"
        )
    elif computational_prediction == "tolerated":
        criteria_met["benign"].append("BP4")
        evidence_notes.append(
            "BP4: Computational tools predict no impact "
            "(supporting benign evidence)"
        )

    # PP5 / BP6: Reputable source classification
    if clinical_significance_from_clinvar in ("pathogenic", "likely_pathogenic"):
        criteria_met["pathogenic"].append("PP5")
        evidence_notes.append(
            f"PP5: ClinVar classifies as {clinical_significance_from_clinvar} "
            "(supporting pathogenic evidence)"
        )
    elif clinical_significance_from_clinvar in ("benign", "likely_benign"):
        criteria_met["benign"].append("BP6")
        evidence_notes.append(
            f"BP6: ClinVar classifies as {clinical_significance_from_clinvar} "
            "(supporting benign evidence)"
        )

    # PS3 / BS3: Functional evidence
    if functional_evidence == "supports_damaging":
        criteria_met["pathogenic"].append("PS3")
        evidence_notes.append(
            "PS3: Functional studies support damaging effect "
            "(strong pathogenic evidence)"
        )
    elif functional_evidence == "supports_benign":
        criteria_met["benign"].append("BS3")
        evidence_notes.append(
            "BS3: Functional studies show no damaging effect "
            "(strong benign evidence)"
        )

    # BP1: Missense in truncating-only gene
    if variant_type == "missense" and in_functional_domain == "no":
        criteria_met["benign"].append("BP1")
        evidence_notes.append(
            "BP1: Missense variant outside functional domain "
            "(supporting benign evidence)"
        )

    # BP7: Synonymous with no splice impact
    if variant_type == "synonymous":
        criteria_met["benign"].append("BP7")
        evidence_notes.append(
            "BP7: Synonymous variant with no predicted splice impact "
            "(supporting benign evidence)"
        )

    # Determine classification
    path_criteria = criteria_met["pathogenic"]
    ben_criteria = criteria_met["benign"]

    has_pvs1 = "PVS1" in path_criteria
    ps_count = sum(1 for c in path_criteria if c.startswith("PS"))
    pm_count = sum(1 for c in path_criteria if c.startswith("PM"))
    pp_count = sum(1 for c in path_criteria if c.startswith("PP"))
    ba_count = sum(1 for c in ben_criteria if c == "BA1")
    bs_count = sum(1 for c in ben_criteria if c.startswith("BS"))
    bp_count = sum(1 for c in ben_criteria if c.startswith("BP"))

    classification = "Uncertain Significance (VUS)"
    confidence = "low"

    # Pathogenic rules
    if (has_pvs1 and ps_count >= 1) or (ps_count >= 2):
        classification = "Pathogenic"
        confidence = "high"
    elif (has_pvs1 and pm_count >= 2) or (ps_count >= 1 and pp_count >= 3):
        classification = "Pathogenic"
        confidence = "high"
    elif has_pvs1 and pm_count >= 1:
        classification = "Likely Pathogenic"
        confidence = "moderate"
    elif (ps_count >= 1 and pm_count >= 1) or (ps_count >= 1 and pp_count >= 2):
        classification = "Likely Pathogenic"
        confidence = "moderate"
    elif pm_count >= 3 or (pm_count >= 2 and pp_count >= 2):
        classification = "Likely Pathogenic"
        confidence = "moderate"
    # Benign rules
    elif ba_count >= 1:
        classification = "Benign"
        confidence = "high"
    elif bs_count >= 2:
        classification = "Benign"
        confidence = "high"
    elif bs_count >= 1 and bp_count >= 1:
        classification = "Likely Benign"
        confidence = "moderate"
    elif bp_count >= 2:
        classification = "Likely Benign"
        confidence = "moderate"

    # Override confidence based on ClinVar agreement
    if clinical_significance_from_clinvar != "unknown":
        clinvar_class = clinical_significance_from_clinvar.replace("_", " ").title()
        if clinvar_class.lower() in classification.lower():
            confidence = "high"

    assessment = {
        "classification": classification,
        "confidence": confidence,
        "criteria_met": criteria_met,
        "evidence_notes": evidence_notes,
        "acmg_score": {
            "pathogenic_very_strong": 1 if has_pvs1 else 0,
            "pathogenic_strong": ps_count,
            "pathogenic_moderate": pm_count,
            "pathogenic_supporting": pp_count,
            "benign_standalone": ba_count,
            "benign_strong": bs_count,
            "benign_supporting": bp_count
        },
        "recommendation": _get_recommendation(classification, confidence)
    }

    return json.dumps(assessment, indent=2)


def tool_check_drug_interactions(gene_name: str, variant_type: str = "unknown") -> str:
    """Check for pharmacogenomic drug interactions related to a gene variant.

    Use this tool when you need to determine if a genetic variant affects
    drug metabolism, efficacy, or safety. This is especially important for
    genes in the cytochrome P450 family (CYP2D6, CYP2C19, etc.) and
    other pharmacogenes.

    Args:
        gene_name: The gene symbol (e.g., 'CYP2D6', 'DPYD', 'VKORC1').
        variant_type: The type of variant if known (e.g., 'loss_of_function',
            'gain_of_function', 'reduced_function', 'unknown').

    Returns:
        A JSON string containing affected drugs, dosing recommendations,
        metabolizer status predictions, and PharmGKB references.
    """
    # Curated pharmacogenomics knowledge base
    pgx_data = {
        "CYP2D6": {
            "enzyme": "Cytochrome P450 2D6",
            "metabolizer_types": {
                "poor": "No functional CYP2D6 enzyme activity",
                "intermediate": "Reduced CYP2D6 enzyme activity",
                "normal": "Normal CYP2D6 enzyme activity",
                "ultra_rapid": "Increased CYP2D6 enzyme activity"
            },
            "affected_drugs": [
                {"drug": "Codeine", "impact": "Poor metabolizers: No conversion to morphine → reduced pain relief. Ultra-rapid metabolizers: Excess morphine → risk of toxicity.", "action": "Consider alternative analgesic"},
                {"drug": "Tramadol", "impact": "Poor metabolizers: Reduced efficacy. Ultra-rapid metabolizers: Increased risk of adverse effects.", "action": "Dose adjustment or alternative"},
                {"drug": "Tamoxifen", "impact": "Poor metabolizers: Reduced conversion to active endoxifen → potentially reduced efficacy for breast cancer treatment.", "action": "Consider alternative therapy"},
                {"drug": "Fluoxetine", "impact": "Poor metabolizers: Higher plasma levels → increased side effects.", "action": "Reduce dose by 50%"},
                {"drug": "Amitriptyline", "impact": "Poor metabolizers: Higher levels → increased side effects and toxicity risk.", "action": "Reduce dose or use alternative"}
            ],
            "url": "https://www.pharmgkb.org/gene/PA128"
        },
        "CYP2C19": {
            "enzyme": "Cytochrome P450 2C19",
            "metabolizer_types": {
                "poor": "No functional CYP2C19 enzyme activity",
                "intermediate": "Reduced CYP2C19 enzyme activity",
                "normal": "Normal CYP2C19 enzyme activity",
                "ultra_rapid": "Increased CYP2C19 enzyme activity"
            },
            "affected_drugs": [
                {"drug": "Clopidogrel (Plavix)", "impact": "Poor metabolizers: Cannot activate the drug → increased risk of cardiovascular events.", "action": "Use prasugrel or ticagrelor instead"},
                {"drug": "Omeprazole", "impact": "Poor metabolizers: Higher drug levels → stronger acid suppression. Ultra-rapid metabolizers: May need higher doses.", "action": "Adjust dose based on metabolizer status"},
                {"drug": "Voriconazole", "impact": "Poor metabolizers: Significantly higher drug levels → toxicity risk.", "action": "Reduce dose or use alternative antifungal"},
                {"drug": "Escitalopram", "impact": "Poor metabolizers: Higher plasma levels → increased side effects.", "action": "Consider 50% dose reduction"}
            ],
            "url": "https://www.pharmgkb.org/gene/PA124"
        },
        "DPYD": {
            "enzyme": "Dihydropyrimidine Dehydrogenase",
            "affected_drugs": [
                {"drug": "5-Fluorouracil (5-FU)", "impact": "DPYD deficiency: Severe, potentially fatal toxicity including neutropenia, mucositis, and neurotoxicity.", "action": "CONTRAINDICATED in complete deficiency. Reduce dose 50% in partial deficiency."},
                {"drug": "Capecitabine", "impact": "Same as 5-FU — oral prodrug converted to 5-FU.", "action": "CONTRAINDICATED in complete deficiency."}
            ],
            "clinical_urgency": "HIGH — Pre-treatment DPYD testing recommended by multiple guidelines",
            "url": "https://www.pharmgkb.org/gene/PA145"
        },
        "VKORC1": {
            "enzyme": "Vitamin K Epoxide Reductase Complex Subunit 1",
            "affected_drugs": [
                {"drug": "Warfarin", "impact": "VKORC1 variants significantly affect warfarin dose requirements. Some variants require up to 50% dose reduction.", "action": "Use pharmacogenomic dosing algorithm (with CYP2C9)"},
                {"drug": "Acenocoumarol", "impact": "Similar to warfarin — dose adjustment needed based on genotype.", "action": "Pharmacogenomic-guided dosing"}
            ],
            "url": "https://www.pharmgkb.org/gene/PA133787052"
        },
        "TPMT": {
            "enzyme": "Thiopurine S-methyltransferase",
            "affected_drugs": [
                {"drug": "Azathioprine", "impact": "TPMT deficiency: Severe myelosuppression. Intermediate activity: Moderate toxicity risk.", "action": "Reduce dose or use alternative immunosuppressant"},
                {"drug": "6-Mercaptopurine", "impact": "Same as azathioprine — severe toxicity in TPMT-deficient patients.", "action": "Reduce dose to 10% of standard in deficient patients"}
            ],
            "url": "https://www.pharmgkb.org/gene/PA356"
        },
        "HLA-B": {
            "enzyme": "Human Leukocyte Antigen B",
            "affected_drugs": [
                {"drug": "Carbamazepine", "impact": "HLA-B*15:02: High risk of Stevens-Johnson syndrome/toxic epidermal necrolysis (SJS/TEN) — life-threatening.", "action": "CONTRAINDICATED in HLA-B*15:02 carriers"},
                {"drug": "Abacavir", "impact": "HLA-B*57:01: High risk of hypersensitivity reaction.", "action": "CONTRAINDICATED in HLA-B*57:01 carriers — mandatory testing before prescription"}
            ],
            "clinical_urgency": "HIGH — Mandatory pre-treatment genotyping for several drugs",
            "url": "https://www.pharmgkb.org/gene/PA35056"
        },
        "G6PD": {
            "enzyme": "Glucose-6-Phosphate Dehydrogenase",
            "affected_drugs": [
                {"drug": "Primaquine", "impact": "G6PD deficiency: Risk of hemolytic anemia.", "action": "Contraindicated in severe deficiency. Test before prescribing."},
                {"drug": "Dapsone", "impact": "G6PD deficiency: Increased risk of hemolytic anemia.", "action": "Avoid or use with extreme caution"},
                {"drug": "Rasburicase", "impact": "G6PD deficiency: Risk of severe hemolysis.", "action": "CONTRAINDICATED"}
            ],
            "url": "https://www.pharmgkb.org/gene/PA28469"
        }
    }

    gene_upper = gene_name.upper()
    result = {
        "source": "GeneSight Pharmacogenomics Knowledge Base (curated from PharmGKB/CPIC)",
        "gene": gene_upper,
        "has_pharmacogenomic_data": gene_upper in pgx_data,
        "data": None,
        "summary": "",
        "error": None
    }

    if gene_upper in pgx_data:
        data = pgx_data[gene_upper]
        result["data"] = data

        drug_list = [d["drug"] for d in data["affected_drugs"]]
        urgency = data.get("clinical_urgency", "Standard")

        result["summary"] = (
            f"**{gene_upper}** ({data['enzyme']}) has known pharmacogenomic interactions.\n"
            f"**Affected drugs:** {', '.join(drug_list)}\n"
            f"**Clinical urgency:** {urgency}\n"
            f"[PharmGKB Link]({data['url']})"
        )
    else:
        result["summary"] = (
            f"No curated pharmacogenomic data available for **{gene_upper}**. "
            f"This gene may not have well-established drug interactions, "
            f"or data may be limited. Check [PharmGKB](https://www.pharmgkb.org/) "
            f"for the latest information."
        )

    return json.dumps(result, indent=2)


def _get_recommendation(classification: str, confidence: str) -> str:
    """Generate clinical recommendation based on classification."""
    recommendations = {
        "Pathogenic": (
            "This variant is classified as Pathogenic. Clinical action may be indicated. "
            "Recommend genetic counseling referral and discussion of implications for "
            "the patient and family members. Consider cascade genetic testing for at-risk relatives."
        ),
        "Likely Pathogenic": (
            "This variant is classified as Likely Pathogenic (>90% certainty). "
            "Clinical management should generally follow guidelines for pathogenic variants. "
            "Recommend genetic counseling and consider additional evidence gathering."
        ),
        "Uncertain Significance (VUS)": (
            "This variant is classified as a Variant of Uncertain Significance (VUS). "
            "Should NOT be used for clinical decision-making. Consider periodic reclassification "
            "review, family segregation studies, and functional studies if available."
        ),
        "Likely Benign": (
            "This variant is classified as Likely Benign. Unlikely to be causative of disease. "
            "No specific clinical action needed based on this variant alone."
        ),
        "Benign": (
            "This variant is classified as Benign. This is a normal variant in the population. "
            "No clinical action needed."
        )
    }
    return recommendations.get(classification, "Classification could not be determined. Recommend expert review.")


# List of all tools for the Gemma 4 agent
ALL_TOOLS = [
    tool_query_clinvar,
    tool_query_uniprot,
    tool_search_pubmed,
    tool_assess_pathogenicity,
    tool_check_drug_interactions
]
