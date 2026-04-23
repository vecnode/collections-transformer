from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from typing import List

class TransformerEmbedder:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def embed(self, texts: List[str]) -> np.ndarray:
        with torch.no_grad():
            encoded_input = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
            model_output = self.model(**encoded_input)
            # Mean pooling
            embeddings = model_output.last_hidden_state.mean(dim=1)
            return embeddings.cpu().numpy()
