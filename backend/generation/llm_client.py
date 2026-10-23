import os
import json
import logging
import httpx
from typing import List, Dict, Any
from backend.config import (
    OPENAI_API_KEY,
    GROQ_API_KEY,
    HUGGINGFACE_API_KEY,
    OLLAMA_HOST,
    LLM_PROVIDER,
)
from backend.generation.prompts import ROBOTICS_SYSTEM_PROMPT, format_rag_prompt

logger = logging.getLogger("robocode.generation")

class LLMClient:
    def __init__(self):
        self.provider = LLM_PROVIDER.lower()

    async def generate_answer(self, query: str, citations: List[Dict[str, Any]]) -> str:
        if not citations:
            return "No relevant robotics code chunks found for this query in the indexed project."

        prompt = format_rag_prompt(query, citations)

        # 1. Try Groq if configured
        if (self.provider in ["auto", "groq"]) and GROQ_API_KEY:
            try:
                ans = await self._call_groq(prompt)
                if ans:
                    return ans
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}")

        # 2. Try OpenAI if configured
        if (self.provider in ["auto", "openai"]) and OPENAI_API_KEY:
            try:
                ans = await self._call_openai(prompt)
                if ans:
                    return ans
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}")

        # 3. Try Ollama if running locally
        if self.provider in ["auto", "ollama"]:
            try:
                ans = await self._call_ollama(prompt)
                if ans:
                    return ans
            except Exception:
                pass

        # 4. Fallback: Intelligent Grounded Offline Synthesizer
        # Guaranteed to work in zero-configuration environments (Render free tier without API keys)
        return self._offline_synthesize(query, citations)

    async def _call_groq(self, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": ROBOTICS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        return ""

    async def _call_openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": ROBOTICS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        return ""

    async def _call_ollama(self, prompt: str) -> str:
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": "llama3",
            "messages": [
                {"role": "system", "content": ROBOTICS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["message"]["content"]
        return ""

    def _offline_synthesize(self, query: str, citations: List[Dict[str, Any]]) -> str:
        """
        Deterministic, grounded offline response generator.
        Synthesizes code structure, extracted symbols, and real-time assessments
        directly from the indexed source chunks.
        """
        response_parts = [
            f"### RoboCode RAG Grounded Analysis\n",
            f"**Query:** `{query}`\n",
            f"Found **{len(citations)} relevant code section(s)** matching your request:\n"
        ]

        for i, c in enumerate(citations, 1):
            file_ref = f"`{c['file_path']}:{c['start_line']}-{c['end_line']}`"
            symbol = f" (Symbol: `{c['symbol_name']}`)" if c.get("symbol_name") else ""
            response_parts.append(f"#### {i}. Reference: {file_ref}{symbol}")
            response_parts.append(f"- **Language:** {c.get('language', 'unknown')}")
            response_parts.append(f"- **Relevance Score:** {c.get('relevance_score', 0)}%")
            response_parts.append("```" + (c.get('language') or 'text'))
            # Show up to first 25 lines of snippet
            snip_lines = c['snippet'].splitlines()
            display_snip = "\n".join(snip_lines[:25])
            if len(snip_lines) > 25:
                display_snip += f"\n... [{len(snip_lines) - 25} more lines]"
            response_parts.append(display_snip)
            response_parts.append("```\n")

        response_parts.append("### Robotics & Real-Time Assessment")
        has_delay = any("delay(" in c['snippet'] or "sleep(" in c['snippet'] for c in citations)
        has_malloc = any("malloc(" in c['snippet'] or "new " in c['snippet'] for c in citations)
        
        if has_delay:
            response_parts.append("- ⚠️ **Warning:** Detected blocking delay/sleep primitives in the retrieved code. For deterministic control loops, replace with hardware timer interrupts or non-blocking timer checks.")
        if has_malloc:
            response_parts.append("- ⚠️ **Warning:** Detected dynamic memory allocation (`new` or `malloc`). Ensure allocations are completed during node initialization rather than in high-frequency control loops.")
        if not has_delay and not has_malloc:
            response_parts.append("- ✅ **Clean:** No blatant blocking sleep or unsafe dynamic allocations detected in the primary retrieved code blocks.")

        response_parts.append("\n*Note: To enable LLM natural language generation, set `OPENAI_API_KEY` or `GROQ_API_KEY` in your Render Environment Variables.*")
        return "\n".join(response_parts)

llm_client = LLMClient()
