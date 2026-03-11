from gliner import GLiNER


class NERModel:
    def __init__(self, model_name="gliner-community/gliner_small-v2.5"):
        print(f"Loading GLiNER model: {model_name}...")
        self.model = GLiNER.from_pretrained(model_name)
        print("Model loaded successfully.")

    def predict(self, text: str, labels: list[str]) -> list[dict]:
        if not labels:
            return []

        entities = self.model.predict_entities(text, labels)
        return entities


ner_model = NERModel()
