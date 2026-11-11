from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from config import (
    GROQ_API_KEY,
    OPENROUTER_API_KEY,
    GROQ_MODEL,
    OPENROUTER_MODEL
)


class AIProvider:

    TASK_PROVIDER_MAP = {
        "summary": "groq",
        "quiz": "groq",
        "question_answering": "openrouter",
        "reflection": "openrouter",
    }

    def __init__(self):

        self.groq_api_key = GROQ_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY

        self.groq_model = GROQ_MODEL
        self.openrouter_model = OPENROUTER_MODEL

    def _groq(self):

        if not self.groq_api_key:
            raise ValueError("Groq API Key not found.")

        return ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name=self.groq_model,
            temperature=0.3,
            max_retries=1,
        )

    def _openrouter(self):

        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API Key not found.")

        return ChatOpenAI(
            api_key=self.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model=self.openrouter_model,
            temperature=0.3,
            max_retries=1,
            timeout=90,
        )

    def _provider_order(self, task=None):
        """Preferred provider for the task first, the other one as fallback."""

        preferred_provider = self.TASK_PROVIDER_MAP.get(task)

        order = [preferred_provider] if preferred_provider else []
        order.extend(
            candidate
            for candidate in ("groq", "openrouter")
            if candidate not in order
        )

        return order

    def get_llm(self, provider="auto", task=None):
        """Return an LLM, using task routing only for provider='auto'."""

        provider = provider.lower()

        if provider == "groq":
            return self._groq()

        if provider == "openrouter":
            return self._openrouter()

        if provider == "auto":

            for candidate in self._provider_order(task):
                llm = self._try_provider(candidate)
                if llm is not None:
                    return llm

            raise Exception(
                "No valid AI provider found. Please check your API keys."
            )

        raise ValueError(
            "Provider must be: auto, groq or openrouter."
        )

    def invoke(self, prompt, provider="auto", task=None):
        """
        Run a prompt and return the response text.

        With provider="auto" the call is retried on the other provider when
        the preferred one fails at request time (rate limit, timeout,
        model unavailable ...), not only when its API key is missing.
        """

        provider = provider.lower()

        if provider != "auto":
            return self._as_text(
                self.get_llm(provider=provider, task=task).invoke(prompt)
            )

        errors = []

        for candidate in self._provider_order(task):

            llm = self._try_provider(candidate)

            if llm is None:
                continue

            try:
                return self._as_text(llm.invoke(prompt))
            except Exception as e:
                print(f"{candidate} request failed: {e}")
                errors.append(f"{candidate}: {e}")

        if errors:
            raise Exception(
                "All AI providers failed. " + " | ".join(errors)
            )

        raise Exception(
            "No valid AI provider found. Please check your API keys."
        )

    def stream(self, prompt, provider="auto", task=None):
        """
        Yield the answer piece by piece (for st.write_stream).

        With provider="auto" the other provider is used if the preferred one
        fails BEFORE the first piece arrives. Once text has started
        streaming, an error is raised instead (the answer cannot be swapped
        half-way through).
        """

        provider = provider.lower()

        if provider != "auto":
            llm = self.get_llm(provider=provider, task=task)

            for chunk in llm.stream(prompt):
                text = self._as_text(chunk)
                if text:
                    yield text

            return

        errors = []

        for candidate in self._provider_order(task):

            llm = self._try_provider(candidate)

            if llm is None:
                continue

            started = False

            try:
                for chunk in llm.stream(prompt):
                    text = self._as_text(chunk)
                    if text:
                        started = True
                        yield text

                return

            except Exception as e:

                if started:
                    raise

                print(f"{candidate} stream failed: {e}")
                errors.append(f"{candidate}: {e}")

        if errors:
            raise Exception(
                "All AI providers failed. " + " | ".join(errors)
            )

        raise Exception(
            "No valid AI provider found. Please check your API keys."
        )

    @staticmethod
    def _as_text(response):
        content = getattr(response, "content", response)

        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        return str(content)

    def _try_provider(self, provider):
        """Try one provider for automatic routing and return None on failure."""
        if provider == "groq" and self.groq_api_key:
            try:
                return self._groq()
            except Exception as e:
                print(f"Groq failed: {e}")

        if provider == "openrouter" and self.openrouter_api_key:
            try:
                return self._openrouter()
            except Exception as e:
                print(f"OpenRouter failed: {e}")

        return None

    def available_providers(self):

        providers = []

        if self.groq_api_key:
            providers.append("Groq")

        if self.openrouter_api_key:
            providers.append("OpenRouter")

        return providers
