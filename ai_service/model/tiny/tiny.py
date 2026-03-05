import os
import uvicorn
import queue
import asyncio
import traceback
import threading
import shutil
import numpy as np
import faiss
from typing import List, Optional, Any
from fastapi import FastAPI, WebSocket
from llama_cpp import Llama
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_classic.retrievers import MergerRetriever 

# ------------------------------------------------------------------------------------------
#                                Setup Paths & Server
# ------------------------------------------------------------------------------------------
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "tiny.gguf")
INDEX_DIR = os.path.join("../../vectorDB/", "faiss_index")

# ------------------------------------------------------------------------------------------
#                            KNOWLEDGE SOURCE & Retrievers 
# ------------------------------------------------------------------------------------------
embed_model = Llama(model_path=MODEL_PATH, embedding=True, n_ctx=2048, verbose=False)

class TinyEmbeddingWrapper(Embeddings):
    def _get_emb(self, text: str) -> np.ndarray:
        res = embed_model.create_embedding(text)
        emb_data = res['data'][0]['embedding']
        arr = np.array(emb_data, dtype=np.float32)
        if arr.ndim > 1:
            arr = np.mean(arr, axis=0) 
        return arr

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        embeddings = [self._get_emb(t) for t in texts]
        return np.ascontiguousarray(np.array(embeddings, dtype=np.float32))

    def embed_query(self, text: str) -> List[float]:
        return self._get_emb(text).tolist()

embeddings = TinyEmbeddingWrapper()

class WebRetriever(BaseRetriever):
    enabled: bool = False
    _search_wrapper: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
            self._search_wrapper = DuckDuckGoSearchAPIWrapper(max_results=5)
            self.enabled = True
        
        except ImportError:
            self.enabled = False

    def _get_relevant_documents(self, query: str) -> List[Document]:
        if not self.enabled or self._search_wrapper is None: 
            return []
            
        try:
            results = self._search_wrapper.results(query, max_results=5)
            
            if not results:
                return []

            docs = []
            for r in results:
                content = f"Source: {r['link']}\nTitle: {r['title']}\nInformation: {r['snippet']}"
                docs.append(Document(page_content=content))
            
            return docs
            
        except Exception as e:
            return []
        
def create_initial_vectorstore():
    if os.path.exists(INDEX_DIR): shutil.rmtree(INDEX_DIR)
    initial_text = ""
    raw_vec = np.array([embeddings.embed_query(initial_text)], dtype=np.float32)
    dim = raw_vec.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(np.ascontiguousarray(raw_vec))
    docstore = InMemoryDocstore({"root": Document(page_content=initial_text)})
    return FAISS(embeddings, index, docstore, {0: "root"})

try:
    if os.path.exists(os.path.join(INDEX_DIR, "index.faiss")):
        vectorstore = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    else: vectorstore = create_initial_vectorstore()
except: vectorstore = create_initial_vectorstore()

web_retriever = WebRetriever()
multi_retriever = MergerRetriever(retrievers=[vectorstore.as_retriever(), web_retriever])

# ------------------------------------------------------------------------------------------
#                     Model Instance Pool
# ------------------------------------------------------------------------------------------
MODEL_POOL_SIZE = 4
llm_pool = [Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=4) for _ in range(MODEL_POOL_SIZE)]
available_models = queue.Queue()
for llm in llm_pool: available_models.put(llm)

# ------------------------------------------------------------------------------------------
#                     Logic & API
# ------------------------------------------------------------------------------------------
def make_prompt(context: str, question: str) -> str:
    return (
        "<|system|>\n"
        "You are a strict factual assistant. Answer the question using ONLY the provided context. "
        "If the answer is not in the context, say 'I do not have information on this.'\n"
        f"Context: {context}\n"
        "</s>\n<|user|>\n"
        f"Question: {question}\n"
        "</s>\n<|assistant|>\n"
        "Answer: "
    )

@app.post("/ingest")
async def ingest_document(doc: dict):
    text = doc.get("content", "")
    if not text: return {"error": "No content"}
    vectorstore.add_texts([text])
    vectorstore.save_local(INDEX_DIR)
    return {"status": "Document ingested"}

@app.websocket("/generate")
async def websocket_hybrid(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        query = data.get("question", "")
        stream_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        try:
            llm_instance = await asyncio.wait_for(loop.run_in_executor(None, available_models.get), timeout=10)
        except asyncio.TimeoutError:
            await websocket.send_json({"error": "Busy"}); return

        def model_worker():
            try:
                docs = multi_retriever.invoke(query)
                context = "\n\n".join([d.page_content for d in docs])
                
                print(f"\n--- CONTEXT FED TO AI ---\n{context}\n------------------------\n")
                
                prompt = make_prompt(context, query)
                for chunk in llm_instance.create_completion(prompt, max_tokens=512, stream=True, temperature=0.1):
                    t = chunk["choices"][0]["text"]
                    if t: loop.call_soon_threadsafe(asyncio.create_task, stream_queue.put(t))
            except Exception: traceback.print_exc()
            finally: loop.call_soon_threadsafe(asyncio.create_task, stream_queue.put(None))

        threading.Thread(target=model_worker, daemon=True).start()
        while True:
            token = await stream_queue.get()
            if token is None: break
            await websocket.send_text(token)
    finally:
        if 'llm_instance' in locals(): available_models.put(llm_instance)
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)