# Importing Required Modules
import queue
import asyncio
import traceback
import threading
from llama_cpp import Llama
from fastapi import FastAPI, WebSocket

#Initilization of FastAPI Server
app = FastAPI()

#------------------------------------------------------------------------------------------

# Number of instance loaded into memory to allow n requests to process asynchronously 
MODEL_POOL_SIZE = 4

# Load Model and create multiple instances to server multiple clients 
llm_pool = [Llama(model_path="tiny.gguf", n_ctx=2048, n_threads=4) for _ in range(MODEL_POOL_SIZE)]

# Enqueue instances in available queue so client requests can grab and use them 
available_models = queue.Queue()
for llm in llm_pool:
    available_models.put(llm)
#------------------------------------------------------------------------------------------

# Convert user prompt object into model understandable form 
def make_prompt(context: str, question: str) -> str:
    context = context.strip() if context else "You are a helpful assistant for knowledge retrival task in market research."
    question = question.strip() if question else "Hello!"
    return f'''
        <|system|>
        You are a helpful assistant. Always format your answers in Markdown style with clear headings, bullet points, tables and code blocks where appropriate.
        </s>
        <|user|>
        Context: {context}
        Question: {question}
        </s>
        <|assistant|>
        '''

#------------------------------------------------------------------------------------------

#API Endpoint : generate - Utilize Available Model Instance to answer clients prompt 
@app.websocket("/generate")
async def websocket_generate(websocket: WebSocket):
    # 1. Takes Care if model instance is not available wait till available or timeout 
    # 2. Prevents comming client requests to access ongoing process in busy instances 
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        prompt = make_prompt(data.get("context"), data.get("question"))
        stream_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        # Get a model instance to generate text if not wait to get them free till set timeout 
        try:
            llm = await asyncio.wait_for(
                loop.run_in_executor(None, available_models.get),
                timeout=1000
            )
        except asyncio.TimeoutError:
            await websocket.send_json({"error": "All model instances are busy. Please try again later."})
            await websocket.close()
            return
        
        # Generator function to yield tokens from model and stream to requesting client
        def model_worker():
            try:
                for chunk in llm.create_completion(prompt, max_tokens=512, stream=True):
                    text = chunk.get("choices", [{}])[0].get("text", "")
                    if text:
                        loop.call_soon_threadsafe(asyncio.create_task, stream_queue.put(text))
            except Exception as e:
                traceback.print_exc()
                loop.call_soon_threadsafe(asyncio.create_task, stream_queue.put("[ERROR]"))
            finally:
                loop.call_soon_threadsafe(asyncio.create_task, stream_queue.put(None))

        threading.Thread(target=model_worker, daemon=True).start()

        while True:
            token = await stream_queue.get()
            if token is None:
                break
            await websocket.send_text(token)

    except Exception as e:
        traceback.print_exc()

    finally:
        if 'llm' in locals():
            available_models.put(llm)
        await websocket.close()
#------------------------------------------------------------------------------------------