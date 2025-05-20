from fastapi import FastAPI
from server import webhook, create_knowledge, create_prompt, healthcheck, ask_agent, create_agents, webhook_chat
from logs.logging_config import log_queue, start_log_processor
import uvicorn  # Importando o uvicorn

# Função assíncrona para inicializar o log
async def initialize_log():
    await log_queue.put(f"Servidor iniciado...")

app = FastAPI(on_startup=[start_log_processor, initialize_log])

# Incluindo os endpoints
app.include_router(webhook.router)
app.include_router(create_knowledge.router)
app.include_router(create_prompt.router)
app.include_router(healthcheck.router)
app.include_router(ask_agent.router) 
app.include_router(create_agents.router)
app.include_router(webhook_chat.router)

# Adicionando o bloco para rodar o servidor
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)