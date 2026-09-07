
from narwhals import List


class LocalEmbedder():
    """Generates embeddings locally using SentenceTransformers models."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        # Loads model into memory (CPU or GPU automatically)
        self.model = SentenceTransformer(model_name)
        # Automatically detect the dimension size from the model configuration
        self._dim = self.model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> List[float]:
        """Embeds a single sentence synchronously under the hood."""
        # Using .tolist() converts numpy array to native python floats
        return self.model.encode(text).tolist()

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds multiple paragraphs efficiently in one batch."""
        return self.model.encode(texts).tolist()

    @property
    def dimension(self) -> int:
        return self._dim