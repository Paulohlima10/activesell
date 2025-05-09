from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from logs.logging_config import log_queue
from agents.agentManager import global_manager

router = APIRouter()

class AskAgentRequest(BaseModel):
    partner_code: str
    ask: str
    client_id: str  # Adicionado para passar o número de telefone

@router.post("/ask-agent")
async def ask_agent(request: AskAgentRequest):
    try:
        # Verifica se o agente está em memória usando a instância global
        assistent = global_manager.get_assistant(request.partner_code)

        if assistent is None:
            await log_queue.put(f"Assistente não encontrado para o parceiro '{request.partner_code}'.")
            raise HTTPException(status_code=404, detail=f"Assistente não encontrado para o parceiro '{request.partner_code}'. Certifique-se de criá-lo primeiro.")

        # Faz a pergunta ao assistente usando o método correto
        response = assistent.ask_question(request.ask, request.client_id)
        await log_queue.put(f"Pergunta feita ao assistente '{request.partner_code}': {request.ask}")
        return {"response": response}
    except Exception as e:
        await log_queue.put(f"Erro ao perguntar ao assistente '{request.partner_code}': {str(e)}")
        return {"error": f"Erro ao perguntar ao assistente: {str(e)}"}