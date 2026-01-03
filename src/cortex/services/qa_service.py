"""
Question and Answering Service.

Uses Ollama (Qwen2.5 by default) for Q&A with optional RAG support.
Supports multiple expert personas for specialized responses.
"""

import logging
import os
import re
import uuid
from functools import lru_cache
from io import BytesIO
from typing import Any

import httpx
import pandas as pd
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OllamaSettings(BaseSettings):
    """Ollama LLM configuration settings."""

    ollama_url: str = "http://host.docker.internal:11434"
    ollama_default_model: str = "qwen2.5:14b"
    ollama_timeout: int = 120
    ollama_temperature: float = 0.7
    ollama_num_predict: int = 2048
    ollama_num_ctx: int = 4096
    excel_output_dir: str = "generated_files"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_ollama_settings() -> OllamaSettings:
    """Get cached Ollama settings."""
    return OllamaSettings()


# Supported chat models
SUPPORTED_MODELS: dict[str, str] = {
    "qwen2.5:14b": "Default chat model for richer responses",
    "qwen3:8b": "Lightweight chat model (compatible with OCR workflow expectations)",
}

# Expert persona aliases for normalization
_EXPERT_ALIASES: dict[str, str] = {
    "assistant": "assistant",
    "default": "assistant",
    "general": "general",
    "general_expert": "general",
    "generalexpert": "general",
    "helper": "assistant",
    # HR
    "hr": "hr",
    "human_resources": "hr",
    "hr_expert": "hr",
    "humanresources": "hr",
    "human_resources_expert": "hr",
    # Legal
    "legal": "legal",
    "law": "legal",
    "legal_expert": "legal",
    "legalexpert": "legal",
    # Political
    "political": "political",
    "politics": "political",
    "political_expert": "political",
    "politicalexpert": "political",
    # Intelligence
    "intelligence": "intelligence",
    "intel": "intelligence",
    "intelligence_expert": "intelligence",
    "intelligenceexpert": "intelligence",
    # Data Analytics
    "data_analytics": "data_analytics",
    "dataanalytics": "data_analytics",
    "data-analytics": "data_analytics",
    "analytics": "data_analytics",
    "analyst": "data_analytics",
    "data_analyst": "data_analytics",
    "data_analytics_expert": "data_analytics",
    "dataanalyticsexpert": "data_analytics",
    # Media
    "media": "media",
    "media_expert": "media",
    "mediaexpert": "media",
}

# Experts that require strict ChromaDB-only mode (no LLM base knowledge)
STRICT_CONTEXT_EXPERTS: set[str] = {"hr", "legal"}

# Expert system prompts
_EXPERT_SYSTEM_PROMPTS: dict[str, str] = {
    "assistant": (
        "You are a helpful AI assistant.\n"
        "- Be accurate and practical.\n"
        "- If information is missing, say what you need.\n"
        "- If you make assumptions, label them clearly.\n"
    ),
    "general": (
        "You are a helpful AI assistant with access to multiple information sources.\n"
        "- Use web search for current information and recent events.\n"
        "- Use document context (ChromaDB) for questions about uploaded files.\n"
        "- You may use your training knowledge as a last resort, but always cite sources.\n"
        "- Be clear about which source you're using: 'According to the documents...' "
        "or 'Based on web search...'\n"
        "- Provide balanced, practical responses.\n"
    ),
    "hr": (
        "You are an HR Expert specializing in employee data, policies, and procedures.\n"
        "- Answer ONLY using information from the provided HR documents (ChromaDB).\n"
        "- If information is not in the documents, explicitly state: "
        "'This information is not available in the HR knowledge base.'\n"
        "- Do NOT use general knowledge about HR practices.\n"
        "- Always cite which document or policy you are referencing.\n"
        "- Be precise with dates, policy numbers, and procedure names.\n"
        "- Use formal, professional HR language.\n"
        "- If asked about something not in the documents, suggest which type of document "
        "might contain it.\n"
    ),
    "legal": (
        "You are a Legal Expert specializing in legal documents, contracts, and regulations.\n"
        "- Answer ONLY using information from the provided legal documents (ChromaDB).\n"
        "- If information is not in the documents, explicitly state: "
        "'This information is not available in the legal knowledge base.'\n"
        "- Do NOT use general legal knowledge or provide legal advice beyond what's in "
        "the documents.\n"
        "- Always cite which document, section, or clause you are referencing.\n"
        "- Be precise with legal terminology, dates, and references.\n"
        "- Use formal, precise legal language.\n"
        "- If asked about something not in the documents, suggest which type of document "
        "might contain it.\n"
    ),
    "political": (
        "You are a Political Expert and analyst.\n"
        "- Structure your analysis with clear sections.\n"
        "- Identify stakeholders, incentives, constraints, and objectives.\n"
        "- Provide 2-4 plausible scenarios and conditions that make each more/less likely.\n"
        "- Prefer information from documents (ChromaDB) or web sources over general "
        "knowledge.\n"
        "- When using web sources, assess credibility and note potential bias.\n"
        "- When using documents, cite which document you're referencing.\n"
        "- Keep a neutral, analytical tone; separate facts from interpretations.\n"
        "- If you cite numbers/probabilities, explain the basis and label uncertainty.\n"
    ),
    "intelligence": (
        "You are an Intelligence Expert (OSINT / analytic tradecraft style).\n"
        "- Provide Key Judgments with confidence levels (High/Medium/Low).\n"
        "- List assumptions and alternative hypotheses.\n"
        "- Suggest indicators that would confirm/refute each hypothesis.\n"
        "- Prioritize information from documents (ChromaDB) and verified web sources.\n"
        "- Cite sources clearly: which document, which web source, or if using general "
        "knowledge.\n"
        "- Separate what is known, assessed, and unknown.\n"
        "- Do NOT claim access to classified sources.\n"
    ),
    "data_analytics": (
        "You are a Data Analytics Expert.\n"
        "- Your output should be quantitative and visual.\n"
        "- Prefer numbers, statistics, and calculations over generic prose.\n"
        "- If data is available in documents (ChromaDB), extract and analyze it.\n"
        "- Use web search to find external datasets or statistics when needed.\n"
        "- Cite data sources clearly (document name, web URL, or estimated from general "
        "knowledge).\n"
        "- OUTPUT REQUIREMENTS:\n"
        "  1) Include markdown tables for key metrics\n"
        "  2) Include ASCII charts in code blocks when possible\n"
        "  3) Explain what the data shows and what's driving results\n"
        "- If data is missing, explicitly state what's missing and provide "
        "templates/examples.\n"
        "- Keep units consistent and label them.\n"
        "\n"
        "SUGGESTED STRUCTURE:\n"
        "## Key Metrics\n"
        "(markdown table)\n"
        "\n"
        "## Chart\n"
        "```text\n"
        "(ASCII chart)\n"
        "```\n"
        "\n"
        "## Interpretation\n"
        "(short explanation)\n"
    ),
    "media": (
        "You are a Media Expert and journalism analyst.\n"
        "- Focus on source quality, credibility, and bias assessment.\n"
        "- Analyze framing, incentives, and what is confirmed vs unverified.\n"
        "- When using web search, evaluate source reliability and note divergences "
        "across sources.\n"
        "- When using documents (ChromaDB), note publication dates and source types.\n"
        "- Synthesize information across multiple sources when available.\n"
        "- Cite sources clearly: 'According to [web source]...' or "
        "'From document [filename]...'\n"
        "- Use journalistic language: clear, factual, with source attribution.\n"
    ),
}


def _normalize_expert(expert: str | None) -> str:
    """
    Normalize expert persona name to canonical form.

    Args:
        expert: Raw expert name from user input.

    Returns:
        Normalized expert identifier.
    """
    if not expert:
        return "assistant"
    key = str(expert).strip().lower()
    if not key:
        return "assistant"
    key = key.replace(" ", "_")
    return _EXPERT_ALIASES.get(key, "assistant")


def _table_format_instructions() -> str:
    """Get markdown table formatting instructions for LLM."""
    return (
        "When presenting table data, format it as a markdown table using this format:\n"
        "| Column1 | Column2 | Column3 |\n"
        "|---------|---------|---------|\n"
        "| data1   | data2   | data3   |\n"
        "\n"
        "Make sure to include proper headers and align columns with pipes (|).\n"
    )


class QAService:
    """
    Question and Answering service with RAG and expert personas.

    Provides chat functionality with:
    - ChromaDB RAG context retrieval
    - Web search integration
    - Multiple expert personas (assistant, hr, legal, political, etc.)
    - Excel/table generation from responses
    """

    def __init__(
        self,
        settings: OllamaSettings | None = None,
        document_service: Any | None = None,
    ) -> None:
        """
        Initialize QA service.

        Args:
            settings: Ollama configuration settings.
            document_service: Optional DocumentService for RAG context.
        """
        self.settings = settings or get_ollama_settings()
        self.ollama_url = f"{self.settings.ollama_url}/api/generate"
        self.default_model = self.settings.ollama_default_model
        self.document_service = document_service
        self.excel_dir = self.settings.excel_output_dir

        os.makedirs(self.excel_dir, exist_ok=True)

    def _resolve_model(self, model_name: str | None) -> str:
        """
        Resolve the model to use.

        Args:
            model_name: Requested model name.

        Returns:
            Valid model name (falls back to default if invalid).
        """
        if model_name and model_name in SUPPORTED_MODELS:
            return model_name
        if model_name:
            logger.warning(
                f"Requested model '{model_name}' is not supported. "
                f"Falling back to default '{self.default_model}'."
            )
        return self.default_model

    def _is_table_request(self, message: str) -> bool:
        """
        Check if the user is asking for table/tabular data.

        Args:
            message: User message.

        Returns:
            True if table data is requested.
        """
        # English keywords
        table_keywords = [
            "table", "excel", "spreadsheet", "csv", "tabular",
            "list in table", "create a table", "make a table",
            "generate a table", "show in table", "format as table",
            "export to excel", "download as excel", "give me excel",
        ]
        # Arabic keywords for table/Excel requests
        arabic_keywords = [
            "صدرها الى اكسل", "صدرها إلى اكسل", "عطني ملف اكسل",
            "عطني جدول اكسل", "اكسل", "جدول", "صدر", "تصدير",
            "ملف اكسل", "جدول اكسل", "حوله لاكسل", "حوله الى اكسل",
            "انشئ جدول", "اعطني جدول",
        ]

        message_lower = message.lower()

        if any(keyword in message_lower for keyword in table_keywords):
            return True
        if any(keyword in message for keyword in arabic_keywords):
            return True
        return False

    def _parse_markdown_table(self, text: str) -> pd.DataFrame | None:
        """
        Parse a markdown table from text into a DataFrame.

        Args:
            text: Text containing markdown table.

        Returns:
            DataFrame if table found, None otherwise.
        """
        table_pattern = r"\|(.+)\|[\r\n]+\|[-:\s|]+\|[\r\n]+((?:\|.+\|[\r\n]*)+)"

        match = re.search(table_pattern, text)
        if not match:
            return None

        try:
            header_line = match.group(1)
            headers = [h.strip() for h in header_line.split("|") if h.strip()]

            data_section = match.group(2)
            rows = []
            for line in data_section.strip().split("\n"):
                if line.strip():
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cells) == len(headers):
                        rows.append(cells)

            if rows:
                return pd.DataFrame(rows, columns=headers)
        except Exception as e:
            logger.error(f"Error parsing markdown table: {e}")

        return None

    def _parse_structured_data(self, text: str) -> pd.DataFrame | None:
        """
        Try to parse structured list data into a DataFrame.

        Args:
            text: Text with structured list data.

        Returns:
            DataFrame if structured data found, None otherwise.
        """
        list_pattern = r"(?:^|\n)(?:\d+\.|[-*])\s*(.+?)(?=\n(?:\d+\.|[-*])|\n\n|$)"
        matches = re.findall(list_pattern, text, re.MULTILINE)

        if len(matches) < 2:
            return None

        try:
            all_data = []
            all_keys: set[str] = set()

            for item in matches:
                pairs = re.findall(r"(\w+(?:\s+\w+)?)\s*:\s*([^,\n]+)", item)
                if pairs:
                    row_dict = {k.strip(): v.strip() for k, v in pairs}
                    all_keys.update(row_dict.keys())
                    all_data.append(row_dict)

            if all_data and len(all_keys) > 0:
                return pd.DataFrame(all_data)
        except Exception as e:
            logger.error(f"Error parsing structured data: {e}")

        return None

    def generate_excel(self, df: pd.DataFrame) -> str:
        """
        Generate an Excel file from DataFrame.

        Args:
            df: DataFrame to export.

        Returns:
            Generated filename.
        """
        file_id = str(uuid.uuid4())[:8]
        filename = f"table_data_{file_id}.xlsx"
        filepath = os.path.join(self.excel_dir, filename)

        df.to_excel(filepath, index=False, engine="openpyxl")
        logger.info(f"Generated Excel file: {filepath}")

        return filename

    def extract_table_from_response(
        self, text: str
    ) -> tuple[pd.DataFrame | None, str | None]:
        """
        Extract table data from LLM response and generate Excel if found.

        Args:
            text: LLM response text.

        Returns:
            Tuple of (DataFrame, filename) or (None, None) if no table found.
        """
        df = self._parse_markdown_table(text)

        if df is None:
            df = self._parse_structured_data(text)

        if df is not None and not df.empty:
            filename = self.generate_excel(df)
            return df, filename

        return None, None

    def _needs_web_search(self, message: str, expert: str) -> bool:
        """
        Determine if a query needs web search based on keywords and expert type.

        Args:
            message: User message.
            expert: Expert persona identifier.

        Returns:
            True if web search is needed.
        """
        current_info_keywords = [
            "current", "recent", "latest", "today", "now", "latest news",
            "what happened", "breaking", "update", "developing",
            "current events", "recent events", "news about", "search for",
            "find information about", "look up", "what is the latest",
        ]

        message_lower = message.lower()

        if expert == "media":
            return True

        if any(keyword in message_lower for keyword in current_info_keywords):
            return True

        return False

    async def _get_web_search_context(self, message: str, expert: str) -> str:
        """
        Get web search context using MCP Search Server.

        Args:
            message: Search query.
            expert: Expert persona identifier.

        Returns:
            Formatted web search results or empty string.
        """
        try:
            from mcp_servers.search_server import create_search_server

            search_server = create_search_server()

            if expert == "media":
                result = await search_server._news_search(
                    query=message,
                    region="israel",
                    max_sources=5,
                )
            else:
                result = await search_server._news_search(
                    query=message,
                    region="gulf",
                    max_sources=3,
                )

            if result.get("error"):
                return ""

            results = result.get("results", [])
            if not results:
                return ""

            formatted_results = []
            for r in results:
                if r.get("success"):
                    formatted_results.append(
                        f"Source: {r.get('source_name', 'Unknown')} ({r.get('url', '')})\n"
                        f"Title: {r.get('title', 'N/A')}\n"
                        f"Content: {r.get('content', '')[:500]}\n"
                    )

            if formatted_results:
                return "Web Search Results:\n" + "\n---\n".join(formatted_results)

            return ""
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ""

    def _combine_contexts(
        self,
        rag_context: str,
        web_context: str,
        expert: str,
        strict_mode: bool = False,
    ) -> str:
        """
        Combine RAG and web search contexts with appropriate instructions.

        Args:
            rag_context: Context from ChromaDB.
            web_context: Context from web search.
            expert: Expert persona identifier.
            strict_mode: If True, only use ChromaDB context.

        Returns:
            Combined context string with instructions.
        """
        parts = []

        if strict_mode:
            if rag_context:
                parts.append(
                    "CRITICAL INSTRUCTIONS:\n"
                    "- Answer ONLY using the information provided in the context below.\n"
                    "- If the answer is not in the context, explicitly state: "
                    "'This information is not available in the provided documents.'\n"
                    "- Do NOT use your training data or general knowledge to answer "
                    "questions.\n"
                    "- Do NOT make assumptions beyond what is explicitly stated in the "
                    "context.\n"
                    "- Always cite which document/section you used when providing answers.\n\n"
                    "Document Context:\n"
                    f"{rag_context}\n"
                )
            else:
                parts.append(
                    "CRITICAL INSTRUCTIONS:\n"
                    "No relevant documents were found in the knowledge base for this "
                    "question.\n"
                    "You MUST state that the information is not available in the provided "
                    "documents.\n"
                    "Do NOT use your training data to answer.\n"
                )
        else:
            if rag_context and web_context:
                parts.append(
                    "Use the following information sources to answer the question:\n\n"
                    "1. Document Context (from uploaded files):\n"
                    f"{rag_context}\n\n"
                    "2. Web Search Results:\n"
                    f"{web_context}\n\n"
                    "When answering, cite which source you're using: 'According to the "
                    "documents...' or 'Based on web search...'\n"
                    "You may also use your training knowledge if the sources don't contain "
                    "the answer, but clearly indicate this.\n"
                )
            elif rag_context:
                parts.append(
                    "Use the following retrieved context from uploaded documents:\n\n"
                    f"{rag_context}\n\n"
                    "Prefer information from the documents above. If information is missing, "
                    "you may use your training knowledge but cite sources clearly.\n"
                )
            elif web_context:
                parts.append(
                    "Use the following web search results:\n\n"
                    f"{web_context}\n\n"
                    "Based on these web search results, answer the question. Cite the "
                    "sources you use.\n"
                    "You may also use your training knowledge if needed, but prefer the web "
                    "search results.\n"
                )

        return "\n".join(parts)

    async def answer_question(
        self,
        question: str,
        context: str = "",
        use_rag: bool = False,
        model_name: str | None = None,
    ) -> str:
        """
        Answer a question using the LLM.

        Args:
            question: User question.
            context: Additional context to include.
            use_rag: Whether to retrieve RAG context from ChromaDB.
            model_name: LLM model to use.

        Returns:
            LLM generated answer.

        Raises:
            ValueError: If question is empty.
            Exception: If LLM request fails.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        rag_context = ""
        if use_rag and self.document_service:
            rag_context = self.document_service.get_context_for_query(question)

        combined_context = ""
        if rag_context:
            combined_context = f"Retrieved from documents:\n{rag_context}"
        if context and context.strip():
            if combined_context:
                combined_context += f"\n\nAdditional context:\n{context}"
            else:
                combined_context = context

        if combined_context:
            prompt = f"""Context: {combined_context}

Question: {question}

Please provide a clear and concise answer based on the context above. \
If the context doesn't contain enough information, say so."""
        else:
            prompt = f"""Question: {question}

Please provide a clear and helpful answer."""

        try:
            model_to_use = self._resolve_model(model_name)
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.settings.ollama_temperature,
                    "num_predict": 512,
                    "num_ctx": self.settings.ollama_num_ctx,
                },
            }

            async with httpx.AsyncClient(
                timeout=float(self.settings.ollama_timeout)
            ) as client:
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()

                data = response.json()
                answer = data.get("response", "").strip()

            if not answer:
                return "I couldn't generate an answer. Please try again."

            return answer

        except httpx.TimeoutException as e:
            logger.error(f"Ollama API timeout: {e}")
            raise Exception(
                f"LLM request timed out after {self.settings.ollama_timeout}s"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API HTTP error: {e}")
            raise Exception(
                f"Failed to connect to LLM service: HTTP {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in QA service: {e}")
            raise

    async def chat(
        self,
        message: str,
        conversation_history: list[dict] | None = None,
        use_rag: bool = True,
        use_web_search: bool = True,
        model_name: str | None = None,
        expert: str = "assistant",
    ) -> dict[str, Any]:
        """
        Chat with conversation history support.

        Uses three data sources based on expert type:
        - ChromaDB (RAG) for document context
        - Web Search (MCP) for current/live information
        - Ollama LLM base knowledge

        Args:
            message: User message.
            conversation_history: List of {"role": "user"|"assistant", "content": "..."}.
            use_rag: Enable ChromaDB RAG context retrieval.
            use_web_search: Enable web search via MCP (only used if query needs it).
            model_name: LLM model to use.
            expert: Expert persona (affects tone/style).

        Returns:
            Dict with 'response' and optionally 'excel_file' if table data generated.

        Raises:
            ValueError: If message is empty.
            Exception: If LLM request fails.
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        expert_id = _normalize_expert(expert)

        # Strict mode experts: Force RAG, disable web search and base knowledge
        strict_mode = expert_id in STRICT_CONTEXT_EXPERTS
        if strict_mode:
            use_rag = True
            use_web_search = False

        is_table_request = self._is_table_request(message)
        should_generate_excel = is_table_request

        # Get RAG context if enabled
        rag_context = ""
        if use_rag and self.document_service:
            rag_context = self.document_service.get_context_for_query(message)

        # Get web search context if enabled and needed
        web_context = ""
        if use_web_search and not strict_mode:
            if self._needs_web_search(message, expert_id):
                web_context = await self._get_web_search_context(message, expert_id)

        # Combine contexts based on expert's strictness
        combined_context = self._combine_contexts(
            rag_context=rag_context,
            web_context=web_context,
            expert=expert_id,
            strict_mode=strict_mode,
        )

        # Build conversation prompt
        prompt_parts = []

        # System message - expert persona + formatting guidance
        system_msg = _EXPERT_SYSTEM_PROMPTS.get(
            expert_id, _EXPERT_SYSTEM_PROMPTS["assistant"]
        ).rstrip() + "\n\n"

        if is_table_request:
            system_msg += _table_format_instructions() + "\n"

        if expert_id == "data_analytics" and not is_table_request:
            system_msg += (
                "For this answer, include a compact markdown table of key metrics and "
                "an ASCII chart in a code block.\n"
                "If the needed numeric data is not available in the conversation/context, "
                "say so and provide a template + an EXAMPLE chart.\n"
                "\n"
                + _table_format_instructions()
                + "\n"
            )

        # Add combined context or just system message
        if combined_context:
            prompt_parts.append(f"""{system_msg}{combined_context}

---
""")
        else:
            prompt_parts.append(system_msg)

        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt_parts.append(f"User: {content}\n")
                else:
                    prompt_parts.append(f"Assistant: {content}\n")

        # Add current message
        prompt_parts.append(f"User: {message}\nAssistant:")

        prompt = "".join(prompt_parts)

        try:
            model_to_use = self._resolve_model(model_name)
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.settings.ollama_temperature,
                    "num_predict": self.settings.ollama_num_predict,
                    "num_ctx": self.settings.ollama_num_ctx,
                },
            }

            async with httpx.AsyncClient(
                timeout=float(self.settings.ollama_timeout)
            ) as client:
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()

                data = response.json()
                answer = data.get("response", "").strip()

            if not answer:
                return {"response": "I couldn't generate a response. Please try again."}

            result: dict[str, Any] = {"response": answer}

            if should_generate_excel:
                df, excel_filename = self.extract_table_from_response(answer)
                if excel_filename:
                    result["excel_file"] = excel_filename
                    logger.info(f"Generated Excel file for table request: {excel_filename}")

            return result

        except httpx.TimeoutException as e:
            logger.error(f"Ollama API timeout: {e}")
            raise Exception(
                f"LLM request timed out after {self.settings.ollama_timeout}s"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API HTTP error: {e}")
            raise Exception(
                f"Failed to connect to LLM service: HTTP {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in chat: {e}")
            raise


# Singleton instance
_qa_service: QAService | None = None


def get_qa_service(document_service: Any | None = None) -> QAService:
    """
    Get or create the singleton QA service instance.

    Args:
        document_service: Optional DocumentService for RAG context.

    Returns:
        QAService instance.
    """
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService(document_service=document_service)
    return _qa_service
