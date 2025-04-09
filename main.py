import asyncio
from fastapi import FastAPI
from server import webhook, create_knowledge, create_prompt
from logs.logging_config import log_queue, start_log_processor

asyncio.create_task(log_queue.put(f"Servidor iniciado..."))

app = FastAPI(on_startup=[start_log_processor])

# Incluindo os endpoints
app.include_router(webhook.router)
app.include_router(create_knowledge.router)
app.include_router(create_prompt.router)
