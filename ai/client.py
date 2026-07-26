from __future__ import annotations

from typing import Dict, Iterator, List, Optional

import ollama

Message = Dict[str, str]


class OllamaClient:
    def __init__(
        self,
        model: str = "qwen2.5:3b",
        host: str = "http://localhost:11434",
        system_prompt: str = (
            "You are Arcelia, a helpful desktop AI assistant. "
            "Reply naturally, clearly, and briefly unless the user asks for detail. "
            "Always answer in Indonesian unless the user asks otherwise."
        ),
    ) -> None:
        self.model = model
        self.host = host
        self.system_prompt = system_prompt.strip()
        self.client = ollama.Client(host=host)

    def _prepare_messages(self, messages: List[Message]) -> List[Message]:
        prepared: List[Message] = []

        if self.system_prompt:
            prepared.append({"role": "system", "content": self.system_prompt})

        for msg in messages:
            role = msg.get("role", "").strip()
            content = msg.get("content", "").strip()

            if role not in {"system", "user", "assistant", "tool"}:
                raise ValueError(f"Invalid role: {role}")

            if content:
                prepared.append({"role": role, "content": content})

        if not prepared:
            raise ValueError("No valid messages to send.")

        return prepared

    def chat(self, messages: List[Message]) -> str:
        prepared = self._prepare_messages(messages)
        response = self.client.chat(
            model=self.model,
            messages=prepared,
        )
        return response["message"]["content"]

    def stream_chat(self, messages: List[Message], stats: Optional[dict] = None) -> Iterator[str]:
        """Stream a reply token by token. If `stats` (a plain dict) is
        passed, it gets filled in-place with generation stats (token
        counts, durations in nanoseconds) once Ollama sends its final
        'done' chunk — read it after the generator is exhausted."""
        prepared = self._prepare_messages(messages)

        stream = self.client.chat(
            model=self.model,
            messages=prepared,
            stream=True,
        )

        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

            if stats is not None and chunk.get("done"):
                stats["eval_count"] = chunk.get("eval_count")
                stats["eval_duration"] = chunk.get("eval_duration")
                stats["prompt_eval_count"] = chunk.get("prompt_eval_count")
                stats["prompt_eval_duration"] = chunk.get("prompt_eval_duration")
                stats["total_duration"] = chunk.get("total_duration")

    def list_models(self) -> List[str]:
        """Return the names of models currently pulled in Ollama."""
        response = self.client.list()
        models = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
        names: List[str] = []
        for m in models:
            name = m.get("model") or m.get("name") if isinstance(m, dict) else getattr(m, "model", None)
            if name:
                names.append(name)
        return names

    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    client = OllamaClient()
    reply = client.chat([{"role": "user", "content": "Halo, kamu siapa?"}])
    print(reply)
