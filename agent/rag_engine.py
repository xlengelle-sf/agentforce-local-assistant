"""Simple RAG engine for documentation search"""
import json
from pathlib import Path
from rich.console import Console

console = Console()

# Try to import sklearn, but make it optional
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    console.print("[yellow]⚠️  scikit-learn not available, using simple keyword search[/yellow]")

class RAGEngine:
    def __init__(self, docs_path="knowledge_base/processed/all_docs.json"):
        self.docs_path = Path(docs_path)
        self.docs = []
        self.vectorizer = None
        self.doc_vectors = None
        self.use_sklearn = SKLEARN_AVAILABLE
        
        if self.docs_path.exists():
            self.load_docs()
    
    def load_docs(self):
        """Load documentation from file"""
        with open(self.docs_path, 'r') as f:
            self.docs = json.load(f)
        
        # Create TF-IDF vectors for all documents if sklearn is available
        if self.use_sklearn and self.docs:
            contents = [doc['content'] for doc in self.docs]
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.doc_vectors = self.vectorizer.fit_transform(contents)
    
    def _simple_search(self, query, top_k=3):
        """Simple keyword-based search fallback"""
        query_words = set(query.lower().split())
        scores = []
        
        for idx, doc in enumerate(self.docs):
            content_words = set(doc['content'].lower().split())
            title_words = set(doc['title'].lower().split())
            
            # Calculate simple score based on word overlap
            content_score = len(query_words & content_words) / max(len(query_words), 1)
            title_score = len(query_words & title_words) / max(len(query_words), 1) * 2  # Weight title matches more
            
            total_score = content_score + title_score
            scores.append((idx, total_score))
        
        # Sort by score and get top k
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            if score > 0.1:  # Minimum threshold
                results.append({
                    "doc": self.docs[idx],
                    "score": float(score)
                })
        
        return results
    
    def search(self, query, top_k=3, verbose=False):
        """Search for relevant documentation"""
        if not self.docs:
            if verbose:
                console.print("[yellow]⚠️  No documentation loaded[/yellow]")
            return []
        
        # Use sklearn if available, otherwise fall back to simple search
        if self.use_sklearn:
            return self._sklearn_search(query, top_k, verbose)
        else:
            return self._simple_search(query, top_k)
    
    def _sklearn_search(self, query, top_k=3, verbose=False):
        """TF-IDF based search using sklearn"""
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.doc_vectors)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append({
                    "doc": self.docs[idx],
                    "score": float(similarities[idx])
                })
        
        if verbose:
            console.print(f"[green]Found {len(results)} relevant documents[/green]")
        
        return results
    
    def get_relevant_context(self, query, max_length=2000, verbose=False):
        """Get relevant context for a query"""
        results = self.search(query, top_k=5, verbose=verbose)
        
        context = ""
        for result in results:
            doc = result['doc']
            # Add title and relevant excerpt
            context += f"\n\n## {doc['title']}\n"
            context += doc['content'][:500] + "...\n"
            
            if len(context) >= max_length:
                break
        
        return context[:max_length]
