"""
gemma_agent.py — Gemma 4 Agent for genetic variant analysis.

Uses prompt-based tool calling: the model outputs JSON tool requests,
we execute them and feed results back for synthesis.
"""
import json
import time
import re
from typing import Optional
from google import genai
from google.genai import types

from core.tools import (
    tool_query_clinvar,
    tool_query_uniprot,
    tool_search_pubmed,
    tool_assess_pathogenicity,
    tool_check_drug_interactions
)

TOOL_DISPATCH = {
    "tool_query_clinvar": tool_query_clinvar,
    "tool_query_uniprot": tool_query_uniprot,
    "tool_search_pubmed": tool_search_pubmed,
    "tool_assess_pathogenicity": tool_assess_pathogenicity,
    "tool_check_drug_interactions": tool_check_drug_interactions,
}

TOOL_DESCRIPTIONS = """
Available tools (call by outputting JSON):

1. tool_query_clinvar(search_term: str, gene: str) - Query ClinVar for clinical significance
2. tool_query_uniprot(gene_name: str) - Query UniProt for protein function/domains
3. tool_search_pubmed(query: str, max_results: int) - Search PubMed for literature
4. tool_assess_pathogenicity(gene: str, variant: str, variant_type: str, clinical_significance: str, functional_impact: str, population_frequency: str) - Apply ACMG criteria
5. tool_check_drug_interactions(gene: str) - Check pharmacogenomic drug interactions
"""

SYSTEM_PROMPT = f"""You are GeneSight, an expert AI genetic variant interpreter.

{TOOL_DESCRIPTIONS}

## How to call tools
To call tools, output a JSON block like this:
```tool_call
{{"tool": "tool_query_clinvar", "args": {{"search_term": "rs80357714", "gene": "BRCA1"}}}}
```

You may call multiple tools by outputting multiple tool_call blocks.
After receiving tool results, synthesize them into a clinical report.

## Response Format (after all tools called)
### Variant Summary
### Clinical Significance (classification + confidence)
### Molecular Impact
### Disease Associations
### Pharmacogenomic Implications (if applicable)
### Supporting Literature
### Clinical Recommendations

Ground all interpretations in tool evidence. Cite database entries. Be clear about uncertainty.
Disclaimer: This is for research/educational purposes only.
"""


class GemmaAgent:
    """Gemma 4 agent for genetic variant analysis with prompt-based tool calling."""

    def __init__(self, api_key: str, model: str = "gemma-4-26b-a4b-it"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.tool_call_log = []

    def _extract_tool_calls(self, text: str) -> list:
        """Extract tool_call JSON blocks from model output."""
        calls = []
        pattern = r'```tool_call\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                if "tool" in parsed:
                    calls.append(parsed)
            except json.JSONDecodeError:
                pass
        # Also try inline JSON patterns
        if not calls:
            pattern2 = r'\{["\']tool["\']:\s*["\'](\w+)["\'],\s*["\']args["\']:\s*(\{.*?\})\}'
            for m in re.finditer(pattern2, text, re.DOTALL):
                try:
                    calls.append({"tool": m.group(1), "args": json.loads(m.group(2))})
                except json.JSONDecodeError:
                    pass
        return calls

    def analyze_variant(
        self,
        user_query: str,
        max_turns: int = 5,
        on_tool_call: Optional[callable] = None,
        on_thinking: Optional[callable] = None
    ) -> dict:
        self.tool_call_log = []
        start_time = time.time()

        conversation = f"{SYSTEM_PROMPT}\n\nUser query: {user_query}\n\nFirst, identify what tools to call for this variant analysis. Output tool_call blocks."

        config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=2048,
        )

        final_text = ""
        turn = 0

        try:
            while turn < max_turns:
                turn += 1

                if on_thinking:
                    on_thinking(f"🧠 Agent thinking (turn {turn}/{max_turns})...")

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=conversation,
                    config=config,
                )

                response_text = response.text or ""
                tool_calls = self._extract_tool_calls(response_text)

                if not tool_calls:
                    # No more tool calls — this is the final analysis
                    final_text = response_text
                    break

                # Execute tool calls
                tool_results = []
                for tc in tool_calls:
                    fname = tc.get("tool", "")
                    fargs = tc.get("args", {})

                    if on_thinking:
                        on_thinking(f"🔧 Calling tool: **{fname}**")

                    tool_fn = TOOL_DISPATCH.get(fname)
                    if tool_fn:
                        try:
                            result = tool_fn(**fargs)
                        except Exception as e:
                            result = json.dumps({"error": str(e)})
                    else:
                        result = json.dumps({"error": f"Unknown tool: {fname}"})

                    log_entry = {
                        "turn": turn,
                        "tool": fname,
                        "args": fargs,
                        "result_preview": result[:500] + "..." if len(result) > 500 else result,
                        "timestamp": time.time()
                    }
                    self.tool_call_log.append(log_entry)

                    if on_tool_call:
                        on_tool_call(fname, fargs, result)

                    tool_results.append(f"## Result from {fname}:\n{result}")

                # Append results to conversation
                results_text = "\n\n".join(tool_results)
                conversation += f"\n\nAssistant: {response_text}\n\nTool Results:\n{results_text}\n\nNow either call more tools or provide your final clinical analysis report."

        except Exception as e:
            final_text = f"## Error During Analysis\n\nAn error occurred: {str(e)}\n\nPlease check your API key and try again."

        elapsed = time.time() - start_time

        return {
            "analysis": final_text,
            "tool_calls": self.tool_call_log,
            "turns_used": turn,
            "elapsed_seconds": round(elapsed, 2),
            "model": self.model,
            "query": user_query
        }

    def generate_patient_report(self, analysis_text: str) -> str:
        prompt = f"""Based on the following clinical genetic analysis, create a clear,
compassionate, patient-friendly explanation. Avoid jargon. Include:
1. What was found (plain language)
2. What it might mean for health
3. What to discuss with their doctor
4. Important context

Technical Analysis:
{analysis_text}

Write the patient-friendly explanation now:"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=2048,
                )
            )
            return response.text or "Unable to generate patient report."
        except Exception as e:
            return f"Error generating patient report: {str(e)}"


def quick_analyze(api_key: str, variant_query: str, model: str = "gemma-4-26b-a4b-it") -> dict:
    agent = GemmaAgent(api_key=api_key, model=model)
    return agent.analyze_variant(variant_query)
