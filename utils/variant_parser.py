"""
variant_parser.py — Parse genetic variant notation into structured data.

Supports HGVS notation, rsIDs, genomic coordinates, and gene+variant combos.
"""
import re
from typing import Optional


class ParsedVariant:
    """Structured representation of a parsed genetic variant."""

    def __init__(self):
        self.gene: Optional[str] = None
        self.variant: Optional[str] = None
        self.hgvs_c: Optional[str] = None
        self.hgvs_p: Optional[str] = None
        self.rsid: Optional[str] = None
        self.chromosome: Optional[str] = None
        self.position: Optional[int] = None
        self.ref: Optional[str] = None
        self.alt: Optional[str] = None
        self.variant_type: Optional[str] = None
        self.raw_input: str = ""
        self.parse_method: str = "unknown"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def search_term(self) -> str:
        """Generate the best search term for database queries."""
        if self.rsid:
            return self.rsid
        if self.gene and self.variant:
            return f"{self.gene} {self.variant}"
        if self.gene and self.hgvs_c:
            return f"{self.gene} {self.hgvs_c}"
        if self.chromosome and self.position:
            return f"chr{self.chromosome}:{self.position}"
        return self.raw_input

    def display_name(self) -> str:
        """Human-readable variant name."""
        parts = []
        if self.gene:
            parts.append(self.gene)
        if self.variant:
            parts.append(self.variant)
        elif self.hgvs_c:
            parts.append(self.hgvs_c)
        elif self.rsid:
            parts.append(self.rsid)
        return " ".join(parts) if parts else self.raw_input


def parse_variant(raw_input: str) -> ParsedVariant:
    """
    Parse a variant string into a ParsedVariant object.

    Supports:
      - rsID: rs80357714
      - HGVS coding: NM_007294.4:c.68_69del, BRCA1:c.68_69del
      - HGVS protein: BRCA1 p.Glu23ValfsTer17
      - Genomic coords: chr17:41276045 G>A, 17:41276045:G:A
      - Gene + variant: BRCA1 c.68_69del, CFTR F508del
    """
    text = raw_input.strip()
    pv = ParsedVariant()
    pv.raw_input = text

    # --- rsID ---
    rs_match = re.search(r'(rs\d+)', text, re.IGNORECASE)
    if rs_match:
        pv.rsid = rs_match.group(1).lower()
        pv.parse_method = "rsid"
        # Check if gene is also provided
        remainder = text.replace(rs_match.group(0), "").strip()
        gene_m = re.match(r'([A-Z][A-Z0-9]{1,10})', remainder)
        if gene_m:
            pv.gene = gene_m.group(1).upper()
        _infer_variant_type(pv)
        return pv

    # --- Genomic coordinates: chr17:41276045 G>A or 17:41276045:G:A ---
    coord_match = re.match(
        r'(?:chr)?(\d{1,2}|[XY]):(\d+)[:\s]+([ACGT]+)[>:/]([ACGT]+)',
        text, re.IGNORECASE
    )
    if coord_match:
        pv.chromosome = coord_match.group(1)
        pv.position = int(coord_match.group(2))
        pv.ref = coord_match.group(3).upper()
        pv.alt = coord_match.group(4).upper()
        pv.parse_method = "genomic_coordinates"
        _infer_variant_type(pv)
        return pv

    # --- HGVS coding with transcript: NM_007294.4:c.68_69del ---
    hgvs_tx_match = re.match(
        r'(NM_\d+\.\d+):([cgpr]\.[\w\d_>*+\-]+)',
        text, re.IGNORECASE
    )
    if hgvs_tx_match:
        pv.hgvs_c = text
        pv.variant = hgvs_tx_match.group(2)
        pv.parse_method = "hgvs_transcript"
        _infer_variant_type(pv)
        return pv

    # --- Gene:HGVS or Gene HGVS: BRCA1:c.68_69del, BRCA1 c.68_69del ---
    gene_hgvs_match = re.match(
        r'([A-Z][A-Z0-9]{1,10})[:\s]+([cgpr]\.[\w\d_>*+\-]+)',
        text, re.IGNORECASE
    )
    if gene_hgvs_match:
        pv.gene = gene_hgvs_match.group(1).upper()
        pv.variant = gene_hgvs_match.group(2)
        if gene_hgvs_match.group(2).startswith(('c.', 'C.')):
            pv.hgvs_c = f"{pv.gene}:{pv.variant}"
        elif gene_hgvs_match.group(2).startswith(('p.', 'P.')):
            pv.hgvs_p = f"{pv.gene}:{pv.variant}"
        pv.parse_method = "gene_hgvs"
        _infer_variant_type(pv)
        return pv

    # --- Gene + common variant name: CFTR F508del, TP53 R175H ---
    gene_var_match = re.match(
        r'([A-Z][A-Z0-9]{1,10})\s+([A-Z]\d+[A-Z](?:del|ins|dup|fs)?(?:Ter\d+)?)',
        text, re.IGNORECASE
    )
    if gene_var_match:
        pv.gene = gene_var_match.group(1).upper()
        pv.variant = gene_var_match.group(2)
        pv.parse_method = "gene_variant_shorthand"
        _infer_variant_type(pv)
        return pv

    # --- Gene + star allele: CYP2D6 *4 ---
    star_match = re.match(
        r'([A-Z][A-Z0-9]{1,10})\s+\*(\d+)',
        text, re.IGNORECASE
    )
    if star_match:
        pv.gene = star_match.group(1).upper()
        pv.variant = f"*{star_match.group(2)}"
        pv.parse_method = "star_allele"
        pv.variant_type = "pharmacogenomic"
        return pv

    # --- Gene + APOE epsilon notation ---
    apoe_match = re.match(
        r'(APOE)\s*[εeE]?(\d)',
        text, re.IGNORECASE
    )
    if apoe_match:
        pv.gene = "APOE"
        pv.variant = f"ε{apoe_match.group(2)}"
        pv.parse_method = "apoe_epsilon"
        pv.variant_type = "risk_allele"
        return pv

    # --- Fallback: try to extract gene name ---
    gene_only = re.match(r'([A-Z][A-Z0-9]{1,10})\b', text)
    if gene_only:
        pv.gene = gene_only.group(1).upper()
        remainder = text[gene_only.end():].strip()
        if remainder:
            pv.variant = remainder
        pv.parse_method = "gene_fallback"
        _infer_variant_type(pv)
        return pv

    # --- Complete fallback ---
    pv.parse_method = "raw_text"
    return pv


def _infer_variant_type(pv: ParsedVariant):
    """Infer variant type from the variant string."""
    variant_str = (pv.variant or pv.hgvs_c or "").lower()
    if not variant_str:
        if pv.ref and pv.alt:
            if len(pv.ref) == 1 and len(pv.alt) == 1:
                pv.variant_type = "snv"
            elif len(pv.ref) > len(pv.alt):
                pv.variant_type = "deletion"
            else:
                pv.variant_type = "insertion"
        return

    if "del" in variant_str and "ins" in variant_str:
        pv.variant_type = "indel"
    elif "del" in variant_str:
        if "fs" in variant_str or "fster" in variant_str:
            pv.variant_type = "frameshift"
        else:
            pv.variant_type = "deletion"
    elif "ins" in variant_str:
        pv.variant_type = "insertion"
    elif "dup" in variant_str:
        pv.variant_type = "duplication"
    elif ">" in variant_str:
        pv.variant_type = "snv"
    elif re.search(r'[A-Z]\d+[A-Z]', variant_str, re.IGNORECASE):
        pv.variant_type = "missense"
    elif "splice" in variant_str or re.search(r'[+-]\d+', variant_str):
        pv.variant_type = "splice_site"
    elif "*" in variant_str or "ter" in variant_str:
        pv.variant_type = "nonsense"
