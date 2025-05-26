import psycopg2
from datetime import datetime
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage, MediaMessage, MediaType
import requests

# === CONFIGURAÇÕES ===
DB_CONFIG = {
    "host": "aws-0-us-east-1.pooler.supabase.com",
    "port": 6543,
    "dbname": "postgres",
    "user": "postgres.gzzvydiznhwaxrahzkjt",
    "password": "Activesell@01"
}

API_TOKEN = "429683C4C977415CAAFCCE10F7D57E11"
INSTANCE_ID = "vendasai"
WHATSAPP_API_KEY = "3FECACA8A982-4B10-A363-7B291D432708"
WHATSAPP_URL = "http://localhost:8080"


# === CONEXÃO COM O BANCO ===
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# === ENVIO DE MENSAGEM WHATSAPP ===
client = EvolutionClient(base_url=WHATSAPP_URL, api_token=API_TOKEN)


def send_message(phone_number, message, image_url=None, variables=None):
    if not phone_number:
        return {"status": "fail", "reason": "telefone vazio"}

    try:
        phone_number = phone_number.strip().replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
        if not phone_number.startswith("+"):
            phone_number = phone_number  # Assumindo Brasil

        # Substitui variáveis na mensagem, se fornecidas
        if variables:
            message = message.format(**variables)

        if image_url:
            url = "http://localhost:8080/message/sendMedia/vendasai"
            payload = {
                "number": phone_number,
                "mediatype": "image",
                "mimetype": "image/png",
                "caption": message,
                "media": image_url,
                "fileName": "Imagem.png"
            }
            headers = {
                "apikey": WHATSAPP_API_KEY,
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        else:
            msg = TextMessage(number=phone_number, text=message, delay=1000)
            return client.messages.send_text(instance_id=INSTANCE_ID, message=msg, instance_token=WHATSAPP_API_KEY)
    except Exception as e:
        return {"status": "fail", "reason": str(e)}

# === PROCESSAMENTO DE CAMPANHAS ===
def process_campaigns():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Seleciona campanhas ativas
        cursor.execute("""
            SELECT id, message FROM campaigns
            WHERE status = 'active' AND start_date <= NOW() AND end_date >= NOW()
        """)
        campaigns = cursor.fetchall()

        for campaign_id, message in campaigns:
            print(f"📢 Processando campanha {campaign_id}")

            # 2. Busca clientes da campanha ainda não enviados, incluindo nome_cliente e produto_recomendado
            cursor.execute("""
                SELECT cc.client_id, cl."TELEFONE", cl.nome_cliente, cl.produto_recomendado
                FROM campaign_clients cc
                JOIN clientes_classificados cl ON cl.id = cc.client_id
                WHERE cc.campaign_id = %s AND cc.status IS DISTINCT FROM 'sent'
            """, (campaign_id,))
            clients = cursor.fetchall()

            # 3. Verifica se há imagem vinculada
            cursor.execute("""
                SELECT file_url FROM campaign_files
                WHERE campaign_id = %s AND file_type = 'image'
                ORDER BY created_at DESC LIMIT 1
            """, (campaign_id,))
            image = cursor.fetchone()
            image_url = image[0] if image else None

            # 4. Envia mensagens
            for client_id, phone, nome_cliente, produto_recomendado in clients:
                primeiro_nome = nome_cliente.split()[0] if nome_cliente else ""
                variables = {
                    "nome_cliente": primeiro_nome,
                    "produto": produto_recomendado or "",
                    "link_personalizado": f"https://seusite.com/compra/{client_id}"
                }
                response = send_message(phone, message, image_url, variables=variables)
                print(f"→ Enviado para {phone}: {response}")

                # Atualiza status da campanha
                cursor.execute("""
                    UPDATE campaign_clients
                    SET status = 'sent', sent_at = %s, updated_at = %s
                    WHERE client_id = %s AND campaign_id = %s
                """, (datetime.now(), datetime.now(), client_id, campaign_id))

        conn.commit()
        print("✅ Todas as campanhas foram processadas.")
    except Exception as e:
        print(f"⚠️ ERRO ao processar campanhas: {e}")
    finally:
        cursor.close()
        conn.close()

# === EXECUÇÃO ===
if __name__ == "__main__":
    process_campaigns()
