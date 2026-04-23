import os
import numpy as np

from sklearn.neighbors import KNeighborsClassifier
from typing import Tuple
from transformer_embedder import TransformerEmbedder

def load_dataset(path: str) -> Tuple[list[str], list[int], list[str]]:
	"""
	Loads labeled and unlabeled examples from a TSV file.
	Returns: (texts, labels, unlabeled_texts)
	"""
	texts, labels, unlabeled = [], [], []
	with open(path, 'r', encoding='utf-8') as f:
		for line in f:
			print(f"Line raw: {repr(line)}")
			line = line.rstrip('\n\r')
			if not line or line.startswith('#'):
				continue
			# Split on first whitespace after label if tab not present
			if '\t' in line:
				parts = line.split('\t', 1)
			else:
				parts = line.split(None, 1)  # split on any whitespace
			if len(parts) < 2:
				continue
			label, text = parts[0].strip(), parts[1].strip()
			if label == '' or label == '2':
				unlabeled.append(text)
			else:
				texts.append(text)
				labels.append(int(label))
	return texts, labels, unlabeled

def embed_texts(texts: list[str]) -> np.ndarray:
	# Use transformer-based embedding
	global embedder
	return embedder.embed(texts)

def test_knn_classifier():
	dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "embedding", "test_embed.txt")
	texts, labels, unlabeled = load_dataset(dataset_path)
	print(f"Loaded {len(texts)} labeled and {len(unlabeled)} unlabeled examples.")
	print(f"Labeled: {texts}")
	print(f"Unlabeled: {unlabeled}")
	global embedder
	embedder = TransformerEmbedder()
	X = embed_texts(texts)
	y = np.array(labels)
	clf = KNeighborsClassifier(n_neighbors=3)
	clf.fit(X, y)
	n_pos = sum(1 for label in y if label == 1)
	n_neg = sum(1 for label in y if label == 0)
	print(f"Positive examples: {n_pos}, Negative examples: {n_neg}, Total labeled: {len(y)}")
	if unlabeled:
		X_test = embed_texts(unlabeled)
		print("Unlabeled embeddings (first 5 dims):")
		for i, (text, emb) in enumerate(zip(unlabeled, X_test)):
			print(f"  {i+1}: {text[:40]}... -> {emb[:5]}")
		preds = clf.predict(X_test)
		probs = clf.predict_proba(X_test)
		for i, (text, pred, prob) in enumerate(zip(unlabeled, preds, probs)):
			print(f"Test example: '{text}' => Predicted label: {pred}, Scores: {prob}")
			assert pred in [0, 1], "Prediction should be 0 or 1"
	else:
		raise AssertionError("No unlabeled test examples found. Check for trailing newlines or whitespace in the data file.")

if __name__ == "__main__":
	test_knn_classifier()

