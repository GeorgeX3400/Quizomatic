import re
import requests

class LLMAccess:
    MODEL = "qwen3:8B"
    ENDPOINT = "http://127.0.0.1:11434/v1/chat/completions"

    @classmethod
    def chat_completions(cls, messages, timeout=60):
        """
        1) Construiește payload-ul JSON
        2) Face POST către Ollama
        3) Stript `<think>…</think>`
        4) Returnează textul curat
        """
        payload = {
            "model": cls.MODEL,
            "messages": messages
        }
        try:
            resp = requests.post(cls.ENDPOINT, json=payload, timeout=timeout)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            # Aici poți loga, arunca, etc.
            raise RuntimeError(f"LLM generation error: {e}")

        # Înlătură eventualele taguri <think>…</think>
        return re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
