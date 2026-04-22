import os
from typing import List, Dict, Any
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

class MemoryRAG:
    def __init__(self, persist_directory: str = "memory_rag"):
        if chromadb is None:
            self.client = None
            return
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="sherly_memory")

    def add_document(self, text: str, metadata: Dict[str, Any] = None, doc_id: str = None):
        if not self.client:
            return
        
        # Simple chunking logic
        chunks = [text[i:i+2000] for i in range(0, len(text), 1500)]
        import uuid
        
        for i, chunk in enumerate(chunks):
            self.collection.add(
                documents=[chunk],
                metadatas=[{**(metadata or {}), "chunk": i}],
                ids=[f"{doc_id or str(uuid.uuid4())}_{i}"]
            )

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted = []
        if results['documents']:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                formatted.append({"text": doc, "metadata": meta})
        return formatted

    def search_with_summarization(self, query: str, ask_model, n_results: int = 10) -> str:
        """
        Retrieves multiple chunks and summarizes them to fit in context.
        """
        results = self.search(query, n_results=n_results)
        if not results:
            return "No relevant context found."
        
        full_text = "\n---\n".join([r["text"] for r in results])
        
        # If context is too long, ask the model to summarize it
        if len(full_text) > 4000:
            summary_prompt = f"Summarize the following project context focusing on: {query}\n\nContext:\n{full_text}"
            return ask_model(summary_prompt, store_history=False)
            
        return full_text

    def index_project(self, project_path: str):
        """
        Index all text files in the project with deep scanning.
        Uses multi-threading for performance optimization.
        """
        if not self.client:
            return
        
        import os
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from runtime_utils import log
        
        log(f"[RAG] Starting multi-threaded index of {project_path}")
        
        files_to_index = []
        for root, _, files in os.walk(project_path):
            if any(skip in root for skip in (".git", "__pycache__", "venv", ".gemini", "node_modules")):
                continue
            for file in files:
                if file.endswith((".py", ".md", ".txt", ".json", ".toml", ".css", ".qss")):
                    files_to_index.append(os.path.join(root, file))
        
        def _read_and_add(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content:
                        self.add_document(
                            text=content,
                            metadata={"path": path, "filename": os.path.basename(path)},
                            doc_id=path
                        )
                        return True
            except Exception:
                pass
            return False

        count = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_read_and_add, p) for p in files_to_index]
            for future in as_completed(futures):
                if future.result():
                    count += 1
                    
        log(f"[RAG] Multi-threaded index complete. Indexed {count} files.")
