#!/usr/bin/env python
"""
ChatAgent - Lightweight conversational AI with multi-turn support.

This agent provides:
- Multi-turn conversation with history management
- Token-based context truncation
- Optional RAG and Web Search augmentation
- Streaming response generation

Uses the unified LLM factory from BaseAgent for both cloud and local LLM support.
"""

from pathlib import Path
import sys
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

# Add project root to path
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.agents.base_agent import BaseAgent
from src.tools import rag_search, web_search
from src.services.knowledge.mastery import get_mastery_service


class ChatAgent(BaseAgent):
    """
    Lightweight conversational agent with multi-turn support.

    Features:
    - Conversation history management with token limits
    - RAG (Retrieval-Augmented Generation) support
    - Web search integration
    - Streaming response generation via BaseAgent.stream_llm()
    """

    # Default token limit for conversation history
    DEFAULT_MAX_HISTORY_TOKENS = 4000

    def __init__(
        self,
        language: str = "zh",
        config: Optional[Dict[str, Any]] = None,
        max_history_tokens: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize ChatAgent.

        Args:
            language: Language setting ('zh' | 'en')
            config: Optional configuration dictionary
            max_history_tokens: Maximum tokens for conversation history
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(
            module_name="chat",
            agent_name="chat_agent",
            language=language,
            config=config,
            **kwargs,
        )

        # Configure history token limit
        self.max_history_tokens = max_history_tokens or self.agent_config.get(
            "max_history_tokens", self.DEFAULT_MAX_HISTORY_TOKENS
        )

        self.logger.info(f"ChatAgent initialized: model={self.model}, base_url={self.base_url}")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Falls back to character-based estimation if tiktoken unavailable.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        try:
            import tiktoken

            # Use cl100k_base encoding (GPT-4, GPT-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            # Fallback: rough estimate of 4 characters per token
            return len(text) // 4

    def truncate_history(
        self,
        history: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Truncate conversation history to fit within token limit.

        Keeps the most recent messages, discarding older ones first.

        Args:
            history: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens allowed (uses default if None)

        Returns:
            Truncated history list
        """
        max_tokens = max_tokens or self.max_history_tokens

        if not history:
            return []

        # Calculate tokens for each message
        message_tokens = []
        for msg in history:
            content = msg.get("content", "")
            tokens = self.count_tokens(content)
            message_tokens.append((msg, tokens))

        # Build history from newest to oldest, stop when limit reached
        truncated = []
        total_tokens = 0

        for msg, tokens in reversed(message_tokens):
            if total_tokens + tokens > max_tokens:
                break
            truncated.insert(0, msg)
            total_tokens += tokens

        if len(truncated) < len(history):
            self.logger.info(
                f"Truncated history from {len(history)} to {len(truncated)} messages "
                f"({total_tokens} tokens)"
            )

        return truncated

    def format_history_for_prompt(self, history: List[Dict[str, str]]) -> str:
        """
        Format conversation history as a string for the prompt.

        Args:
            history: List of message dicts

        Returns:
            Formatted history string
        """
        if not history:
            return ""

        lines = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prefix = "User" if role == "user" else "Assistant"
            lines.append(f"{prefix}: {content}")

        return "\n\n".join(lines)

    async def retrieve_context(
        self,
        message: str,
        kb_name: Optional[str] = None,
        enable_rag: bool = False,
        enable_web_search: bool = False,
    ) -> tuple:
        """
        Retrieve context from RAG and/or Web Search.

        Args:
            message: User message to search for
            kb_name: Knowledge base name for RAG
            enable_rag: Whether to use RAG
            enable_web_search: Whether to use Web Search

        Returns:
            Tuple of (context_string, sources_dict)
        """
        context_parts = []
        sources = {"rag": [], "web": []}

        # RAG retrieval
        if enable_rag and kb_name:
            try:
                self.logger.info(f"RAG search: {message[:50]}...")
                rag_result = await rag_search(
                    query=message,
                    kb_name=kb_name,
                    mode="hybrid",
                )
                rag_answer = rag_result.get("answer", "")
                if rag_answer:
                    context_parts.append(f"[Knowledge Base: {kb_name}]\n{rag_answer}")
                    sources["rag"].append(
                        {
                            "kb_name": kb_name,
                            "content": rag_answer[:500] + "..."
                            if len(rag_answer) > 500
                            else rag_answer,
                        }
                    )
                    self.logger.info(f"RAG retrieved {len(rag_answer)} chars")
            except Exception as e:
                self.logger.warning(f"RAG search failed: {e}")

        # Web search
        if enable_web_search:
            try:
                self.logger.info(f"Web search: {message[:50]}...")
                web_result = web_search(query=message, verbose=False)
                web_answer = web_result.get("answer", "")
                web_citations = web_result.get("citations", [])

                if web_answer:
                    context_parts.append(f"[Web Search Results]\n{web_answer}")
                    sources["web"] = web_citations[:5]
                    self.logger.info(
                        f"Web search returned {len(web_answer)} chars, "
                        f"{len(web_citations)} citations"
                    )
            except Exception as e:
                self.logger.warning(f"Web search failed: {e}")

        context = "\n\n".join(context_parts)

        # Predictive Assistance check
        if enable_rag and context:
            mastery_service = get_mastery_service()
            assistance = mastery_service.predict_struggle("default_user", kb_name, context)
            if assistance:
                sources["predictive_assistance"] = assistance
                self.logger.info(f"Predictive assistance triggered: {assistance}")

        return context, sources

    def build_messages(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: str = "",
    ) -> List[Dict[str, str]]:
        """
        Build the messages array for the LLM API call.

        Args:
            message: Current user message
            history: Truncated conversation history
            context: Retrieved context (RAG/Web)

        Returns:
            List of message dicts for OpenAI API
        """
        messages = []

        # System prompt
        system_prompt = self.get_prompt("system", "You are a helpful AI assistant.")
        messages.append({"role": "system", "content": system_prompt})

        # Add context if available
        if context:
            context_template = self.get_prompt("context_template", "Reference context:\n{context}")
            context_msg = context_template.format(context=context)
            messages.append({"role": "system", "content": context_msg})

        # Add conversation history
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})

        # Add current message
        messages.append({"role": "user", "content": message})

        return messages

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from LLM.

        Uses BaseAgent.stream_llm() which routes to the appropriate provider
        (cloud or local) based on configuration.

        Args:
            messages: Messages array for OpenAI API

        Yields:
            Response chunks as strings
        """
        # Extract system prompt from messages
        system_prompt = ""
        user_prompt = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
                break

        # Get the last user message as user_prompt (for logging/tracking)
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_prompt = msg.get("content", "")
                break

        # Use BaseAgent's stream_llm which routes through the factory
        async for chunk in self.stream_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            messages=messages,
            stage="chat_stream",
        ):
            yield chunk

    async def generate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate complete response from LLM (non-streaming).

        Uses BaseAgent.call_llm() which routes to the appropriate provider
        (cloud or local) based on configuration.

        Args:
            messages: Messages array for OpenAI API

        Returns:
            Complete response string
        """
        # Extract system prompt from messages
        system_prompt = ""
        user_prompt = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
                break

        # Get the last user message
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_prompt = msg.get("content", "")
                break

        # Use BaseAgent's call_llm which routes through the factory
        # Note: call_llm expects simple prompt/system_prompt, but for multi-turn
        # we need to use the factory directly with messages
        from src.services.llm import complete as llm_complete

        response = await llm_complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=self.get_model(),
            api_key=self.api_key,
            base_url=self.base_url,
            messages=messages,
            temperature=self.get_temperature(),
        )

        # Track token usage
        self._track_tokens(
            model=self.get_model(),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=response,
            stage="chat",
        )

        return response

    async def process(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        kb_name: Optional[str] = None,
        enable_rag: bool = False,
        enable_web_search: bool = False,
        stream: bool = False,
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Process a chat message with optional context retrieval.

        Args:
            message: User message
            history: Conversation history (will be truncated if needed)
            kb_name: Knowledge base name for RAG
            enable_rag: Whether to enable RAG retrieval
            enable_web_search: Whether to enable web search
            stream: Whether to stream the response

        Returns:
            If stream=False: Dict with 'response', 'sources', 'truncated_history'
            If stream=True: AsyncGenerator yielding chunks
        """
        history = history or []

        # Truncate history to fit token limit
        truncated_history = self.truncate_history(history)

        # Retrieve context if needed
        context, sources = await self.retrieve_context(
            message=message,
            kb_name=kb_name,
            enable_rag=enable_rag,
            enable_web_search=enable_web_search,
        )

        # Build messages for LLM
        messages = self.build_messages(
            message=message,
            history=truncated_history,
            context=context,
        )

        if stream:
            # Return async generator for streaming
            async def stream_generator():
                full_response = ""
                async for chunk in self.generate_stream(messages):
                    full_response += chunk
                    yield {"type": "chunk", "content": chunk}

                # Update mastery after streaming is done
                # Run in background tasks if possible, but here we just await for simplicity
                await self._update_mastery(message, full_response, kb_name)

                # Yield final result with sources
                yield {
                    "type": "complete",
                    "response": full_response,
                    "sources": sources,
                    "truncated_history": truncated_history,
                }

            return stream_generator()
        else:
            # Generate complete response
            response = await self.generate(messages)

            # After generating complete response, update mastery
            await self._update_mastery(message, response, kb_name)

            return {
                "response": response,
                "sources": sources,
                "truncated_history": truncated_history,
            }

    async def _update_mastery(self, user_message: str, assistant_response: str, kb_name: Optional[str]):
        """Update knowledge tracing data based on the interaction."""
        if not kb_name:
            return
            
        try:
            mastery_service = get_mastery_service()
            # Extract concepts from user message (what they are asking/answering about)
            # and assistant response (what knowledge is being delivered)
            concepts = await mastery_service.extract_concepts(user_message + " " + assistant_response)
            
            for concept in concepts:
                # For now, we assume positive interaction. 
                # In a more advanced version, we could detect confusion/errors.
                mastery_service.update_mastery("default_user", kb_name, concept, 0.5)
        except Exception as e:
            self.logger.warning(f"Failed to update mastery in background: {e}")


__all__ = ["ChatAgent"]
