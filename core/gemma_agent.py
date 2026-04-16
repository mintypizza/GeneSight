"""
gemma_agent.py — Gemma 4 Agent with native function calling for genetic variant analysis.

This is the brain of GeneSight. It uses the google-genai SDK to interact with
Gemma 4 31B-IT, orchestrating multi-step variant analysis through function calling.
"""
import json
import time
from typing import Optional, Generator
from google import genai
from google.genai import types

from core.tools import (
    ALL_TOOLS,
    tool_query_clinvar,
    tool_query_uniprot,
    tool_search_pubmed,
    tool_assess_pathogenicity,
    tool_check_drug_interactions
)

# Map function names to actual implementations
TOOL_DISPATCH = {
    "tool_query_clinvar": tool_query_clinvar,
    "tool_query_uniprot": tool_query_uniprot,
    "tool_search_pubmed": tool_search_pubmed,
    "tool_assess_pathogenicity": tool_assess_pathogenicity,
    "tool_check_drug_interactions": tool_check_drug_interactions,
}

SYSTEM_PROMPT = """You are GeneSight, an expert AI genetic variant interpreter. Your role is to 
analyze genetic variants and provide comprehensive, clinically-grounded interpretations.

You have access to the following tools:
1. **tool_query_clinvar** — Query ClinVar for variant clinical significance
2. **tool_query_uniprot** — Query UniProt for protein function and domain information
3. **tool_search_pubmed** — Search PubMed for relevant research literature
4. **tool_assess_pathogenicity** — Apply ACMG/AMP criteria for systematic classification
5. **tool_check_drug_interactions** — Check pharmacogenomic drug interactions

## Your Analysis Protocol

When analyzing a genetic variant, follow this systematic approach:

1. **Identify the variant** — Parse the gene, variant notation, and variant type
2. **Query ClinVar** — Get existing clinical classification and review status
3. **Query UniProt** — Understand the protein function and where the variant falls
4. **Search PubMed** — Find relevant research supporting the interpretation
5. **Assess pathogenicity** — Apply ACMG criteria based on gathered evidence
6. **Check drug interactions** — Identify any pharmacogenomic implications

## Response Format

After gathering all evidence, provide your analysis in this structure:

### Variant Summary
Brief overview of the variant and its location.

### Clinical Significance
Classification with evidence level and confidence.

### Molecular Impact
How this variant affects protein function based on UniProt data.

### Disease Associations
Known disease connections from ClinVar and literature.

### Pharmacogenomic Implications
Any drug interaction warnings (if applicable).

### Supporting Literature
Key references from PubMed.

### Clinical Recommendations
Actionable recommendations based on the evidence.

## Important Guidelines
- Always ground your interpretations in evidence from the tools
- Cite specific database entries and papers
- Be clear about uncertainty — if evidence is limited, say so
- Include a disclaimer that this is for research/educational purposes
- Use appropriate clinical terminology but explain complex concepts
- Never overstate the significance of uncertain findings
"""


class GemmaAgent:
    """Gemma 4 agent for genetic variant analysis with function calling."""

    def __init__(self, api_key: str, model: str = "gemma-4-31b-it"):
        """
        Initialize the Gemma 4 agent.

        Args:
            api_key: Google AI Studio API key
            model: Model name (default: gemma-4-31b-it)
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.tool_call_log = []  # Track tool calls for UI display

    def analyze_variant(
        self,
        user_query: str,
        max_turns: int = 8,
        on_tool_call: Optional[callable] = None,
        on_thinking: Optional[callable] = None
    ) -> dict:
        """
        Analyze a genetic variant using multi-step function calling.

        Uses manual function calling to give visibility into each step.

        Args:
            user_query: User's question about a variant
            max_turns: Maximum agentic turns (tool call rounds)
            on_tool_call: Callback(tool_name, args, result) for UI updates
            on_thinking: Callback(message) for thinking status updates

        Returns:
            Dictionary with final analysis, tool call log, and metadata.
        """
        self.tool_call_log = []
        start_time = time.time()

        messages = [
            {"role": "user", "content": user_query}
        ]

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            automatic_function_calling=False,
            temperature=0.3,
            max_output_tokens=4096,
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
                    contents=messages,
                    config=config,
                )

                # Check if model wants to call tools
                has_function_calls = False
                function_calls = []

                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            has_function_calls = True
                            function_calls.append(part.function_call)

                if not has_function_calls:
                    # Model is done — extract final text
                    final_text = response.text or ""
                    break

                # Execute each function call
                # Add the model's response (with function calls) to messages
                messages.append({
                    "role": "model",
                    "content": response.candidates[0].content
                })

                tool_responses = []
                for fc in function_calls:
                    fname = fc.name
                    fargs = dict(fc.args) if fc.args else {}

                    if on_thinking:
                        on_thinking(f"🔧 Calling tool: **{fname}**")

                    # Execute the tool
                    tool_fn = TOOL_DISPATCH.get(fname)
                    if tool_fn:
                        try:
                            tool_result = tool_fn(**fargs)
                        except Exception as e:
                            tool_result = json.dumps({"error": f"Tool execution failed: {str(e)}"})
                    else:
                        tool_result = json.dumps({"error": f"Unknown tool: {fname}"})

                    # Log the tool call
                    log_entry = {
                        "turn": turn,
                        "tool": fname,
                        "args": fargs,
                        "result_preview": tool_result[:500] + "..." if len(tool_result) > 500 else tool_result,
                        "timestamp": time.time()
                    }
                    self.tool_call_log.append(log_entry)

                    if on_tool_call:
                        on_tool_call(fname, fargs, tool_result)

                    tool_responses.append(
                        types.Part.from_function_response(
                            name=fname,
                            response={"result": tool_result}
                        )
                    )

                # Add tool responses to messages
                messages.append({
                    "role": "user",
                    "content": tool_responses
                })

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

    def generate_patient_report(self, analysis_text: str, api_key: str = None) -> str:
        """
        Generate a patient-friendly version of the clinical analysis.

        Args:
            analysis_text: The technical analysis from analyze_variant()
            api_key: Optional override API key

        Returns:
            Patient-friendly explanation text.
        """
        prompt = f"""Based on the following clinical genetic analysis, create a clear, 
compassionate, patient-friendly explanation. Avoid medical jargon where possible. 
Explain what this means for the patient in simple terms. Include:

1. What was found (in plain language)
2. What it might mean for their health
3. What they should discuss with their doctor
4. Important context (e.g., this is one piece of the puzzle, not a diagnosis)

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


def quick_analyze(api_key: str, variant_query: str, model: str = "gemma-4-31b-it") -> dict:
    """
    Convenience function for quick variant analysis.

    Args:
        api_key: Google AI Studio API key
        variant_query: The variant to analyze
        model: Model name

    Returns:
        Analysis result dictionary
    """
    agent = GemmaAgent(api_key=api_key, model=model)
    return agent.analyze_variant(variant_query)
