import os
from ollama import Client


class LLMService:
    def __init__(self):
        host = os.getenv("OLLAMA_HOST")
        self.client = Client(host=host)
        self.model = os.getenv("LLM_MODEL")

    def get_explanation(self, text: str, context: str = None) -> str:
        system_prompt = "You are a helpful assistant. Provide a brief explanation or summary (about 3 sentences) for the given entity. Don't include any information that is not directly relevant to understanding what the entity is. Focus on the most important aspects and avoid unnecessary details."
        if context:
            system_prompt += f"\n\nContext for the entity is provided below. Use this context to understand how the entity is used and tailor your explanation if necessary.\n\nContext:\n{context}"

        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Explain what this is: {text}"},
            ],
            options={"temperature": 0.3, "num_predict": 200},
        )
        return response["message"]["content"].strip()


llm_service = LLMService()
