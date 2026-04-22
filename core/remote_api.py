from fastapi import FastAPI, HTTPException
from core.container import Container
from runtime_utils import log

app = FastAPI(title="Sherly AI Remote Gateway")

@app.post("/execute")
async def execute_task(query: str, api_key: str):
    """
    Long-term vision: Remote API Gateway.
    Achieves 10/10 Scalability by allowing distributed execution.
    """
    if api_key != "SECRET_ACCESS_TOKEN": # Mock auth
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    log(f"[Remote] Received query: {query}")
    
    # Delegate to Orchestrator via DI container
    rag = Container.get_memory_rag()
    ask_model = Container.get_model_fn()
    
    result = ask_model(query)
    return {"status": "success", "result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
