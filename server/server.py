import re
from fastapi import FastAPI, Request
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
from agents.agentManager import SalesAssistantManager
from logs.logging_config import log_queue, start_log_processor
import asyncio
from pathlib import Path
from pydantic import BaseModel

asyncio.create_task(log_queue.put(f"Servidor iniciado..."))
app = FastAPI(on_startup=[start_log_processor])
manager = SalesAssistantManager()

client = EvolutionClient(base_url="http://localhost:8080",
                         api_token="429683C4C977415CAAFCCE10F7D57E11")

@app.post("/webhook")
async def webhook(request: Request):
    # Receber os dados como JSON
    data = await request.json()

    # Imprimir os dados para depuração
    await log_queue.put(f"Dados recebidos: {data}") 

    # Inicializar a variável conversation
    conversation = None

    if data.get("event") == "messages.upsert":
        # Verificar se data é um dicionário
        if isinstance(data.get("data"), dict):
            event_type = data.get("event", "desconhecido")
            instanceid = data.get("instance", "desconhecido")
            
            conversation = data["data"].get("message", {}).get("conversation")
            if conversation:
                remote_jid = data["data"].get("key", {}).get("remoteJid", "")
                phone_number = re.sub(r"@s\.whatsapp\.net$", "", remote_jid)
                manager.add_assistant(instanceid)
                msg = manager.get_assistant(instanceid).process_question(conversation, phone_number)
                message = TextMessage(number=phone_number, text=msg, delay=1000)
                apikey = data.get("apikey")
                response = client.messages.send_text(instance_id=instanceid, message=message, instance_token=apikey)

                # Atualizar histórico
                await log_queue.put(f"Evento: {event_type}, Instance: {instanceid}, Cliente: {phone_number}, Conversation: {conversation}")
                await log_queue.put(f"Resposta AI: {msg}")
                await log_queue.put(f"Retorno EvolutionAPI: {response}")

        else:
            await log_queue.put("Erro: JSON recebido não tem o formato esperado.")

        return {"message": "Dados recebidos com sucesso"}
    
class KnowledgeRequest(BaseModel):
    partner_code: str
    content: str

@app.post("/create-knowledge")
async def create_knowledge(request: KnowledgeRequest):
    """
    Cria uma pasta para o partner_code e salva o conteúdo em um arquivo document.txt.
    """
    # Caminho da pasta do parceiro
    partner_path = Path(f"knowledge/partners/{request.partner_code}")
    document_path = partner_path / "document.txt"

    try:
        # Criar a pasta se ela não existir
        partner_path.mkdir(parents=True, exist_ok=True)

        # Escrever o conteúdo no arquivo document.txt
        with document_path.open("w", encoding="utf-8") as file:
            file.write(request.content)

        # Log de sucesso
        await log_queue.put(f"Pasta criada: {partner_path}, Arquivo criado: {document_path}")
        return {"message": f"Arquivo document.txt criado com sucesso para o parceiro '{request.partner_code}'."}

    except Exception as e:
        # Log de erro
        await log_queue.put(f"Erro ao criar o arquivo para o parceiro '{request.partner_code}': {str(e)}")
        return {"error": f"Erro ao criar o arquivo: {str(e)}"}

class PromptRequest(BaseModel):
    partner_code: str
    role: str
    goal: str
    backstory: str
    name: str
    task_description: str


@app.post("/create-prompt")
async def create_prompt(request: PromptRequest):
    """
    Cria uma pasta para o partner_code e salva o conteúdo em um arquivo document.txt.
    """
    # Caminho da pasta do parceiro
    partner_path = Path(f"knowledge/partners/{request.partner_code}")
    role_path = partner_path / "role.txt"
    goal_path = partner_path / "goal.txt"
    backstory_path = partner_path / "backstory.txt"
    name_path = partner_path / "name.txt"
    task_description_path = partner_path / "task_description.txt"

    try:
        # Criar a pasta se ela não existir
        partner_path.mkdir(parents=True, exist_ok=True)

        # Escrever o conteúdo no arquivo role.txt
        with role_path.open("w", encoding="utf-8") as file:
            file.write(request.role)

        # Escrever o conteúdo no arquivo goal.txt
        with goal_path.open("w", encoding="utf-8") as file:
            file.write(request.goal)

        # Escrever o conteúdo no arquivo backstory.txt
        with backstory_path.open("w", encoding="utf-8") as file:
            file.write(request.backstory)

        # Escrever o conteúdo no arquivo name.txt
        with name_path.open("w", encoding="utf-8") as file:
            file.write(request.name)

        # Escrever o conteúdo no arquivo task_description.txt
        with task_description_path.open("w", encoding="utf-8") as file:
            file.write(request.task_description)

        # Log de sucesso
        await log_queue.put(f"Pasta atualizada: {partner_path}, Arquivos criado.")
        return {"message": f"Arquivos name, role, goal, backstory e task_description criado com sucesso para o parceiro '{request.partner_code}'."}

    except Exception as e:
        # Log de erro
        await log_queue.put(f"Erro ao criar o arquivo para o parceiro '{request.partner_code}': {str(e)}")
        return {"error": f"Erro ao criar o arquivo: {str(e)}"}