"""Simple RAG engine for documentation search"""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from rich.console import Console

console = Console()

class RAGEngine:
    def __init__(self, docs_path="knowledge_base/processed/all_docs.json"):
        self.docs_path = Path(docs_path)
        self.docs = []
        self.vectorizer = None
        self.doc_vectors = None
        
        if self.docs_path.exists():
            self.load_docs()
    
    def load_docs(self):
        """Load documentation from file"""
        with open(self.docs_path, 'r') as f:
            self.docs = json.load(f)
        
        # Create TF-IDF vectors for all documents
        if self.docs:
            contents = [doc['content'] for doc in self.docs]
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.doc_vectors = self.vectorizer.fit_transform(contents)
    
    def search(self, query, top_k=3, verbose=False):
        """Search for relevant documentation"""
        if not self.docs:
            if verbose:
                console.print("[yellow]⚠️  No documentation loaded[/yellow]")
            return []
        
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
