import re
import uuid
import asyncpg
from fastapi import APIRouter, Request
from datetime import datetime, timezone

router = APIRouter()

DB_CONFIG = {
    "host": "aws-0-us-east-1.pooler.supabase.com",
    "port": 6543,
    "database": "postgres",
    "user": "postgres.gzzvydiznhwaxrahzkjt",
    "password": "Activesell@01"
}

async def get_db_conn():
    return await asyncpg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

async def get_or_create_conversation(conn, client_id, client_name):
    row = await conn.fetchrow(
        "SELECT id FROM conversations WHERE client_id = $1", client_id
    )
    if row:
        return row["id"]
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await conn.execute(
        """
        INSERT INTO conversations (id, client_id, client_name, status, last_seen, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        conv_id, client_id, client_name, "online", now, now, now
    )
    return conv_id

@router.post("/webhook_chat")
async def webhook_chat(request: Request):
    data = await request.json()
    if data.get("event") == "messages.upsert":
        msg_data = data.get("data", {})
        remote_jid = msg_data.get("key", {}).get("remoteJid", "")
        phone_number = re.sub(r"@s\.whatsapp\.net$", "", remote_jid)
        client_name = msg_data.get("pushName", "Desconhecido")
        raw_type = msg_data.get("messageType", "conversation")
        
        # Mapeamento para os tipos aceitos pelo banco
        if raw_type == "conversation":
            message_type = "text"
        elif raw_type == "imageMessage":
            message_type = "image"
        else:
            message_type = "text"  # padrão para evitar erro

        message_timestamp = msg_data.get("messageTimestamp")
        if message_timestamp:
            msg_dt = datetime.fromtimestamp(message_timestamp, tz=timezone.utc)
        else:
            msg_dt = datetime.now(timezone.utc)

        msg = msg_data.get("message", {})
        if "conversation" in msg:
            content = msg.get("conversation", "")
            file_url = None
            file_name = None
        elif "imageMessage" in msg:
            img = msg["imageMessage"]
            content = img.get("caption", "")
            file_url = img.get("url")
            file_name = "imagem.jpg"
        else:
            content = ""
            file_url = None
            file_name = None

        conn = await get_db_conn()
        try:
            conversation_id = await get_or_create_conversation(conn, phone_number, client_name)
            msg_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO messages (
                    id, conversation_id, content, sender, read, type, file_url, file_name, message_timestamp
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                msg_id, conversation_id, content, "client", True, message_type, file_url, file_name, msg_dt
            )
        finally:
            await conn.close()
    return {"message": "Dados recebidos com sucesso"}