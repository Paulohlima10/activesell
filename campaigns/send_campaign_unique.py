import psycopg2
from datetime import datetime
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage, MediaMessage, MediaType
import requests
# from logs.logging_config import log_message
import os
import uuid
import base64
import asyncio
import re
import random
import time


# === CONFIGURAÇÕES ===
DB_CONFIG = {
    "host": "aws-0-us-east-1.pooler.supabase.com",
    "port": 6543,
    "dbname": "postgres",
    "user": "postgres.gzzvydiznhwaxrahzkjt",
    "password": "Activesell@01"
}

# === CONEXÃO COM O BANCO ===
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def normalize_phone(phone):
    """
    Normaliza o telefone para o formato 553491704671.
    Remove um '9' extra após o DDD se houver.
    Retorna None se o telefone não estiver no formato esperado.
    """
    # Remove caracteres não numéricos
    phone = re.sub(r'\D', '', phone)
    # Verifica se começa com 55 e tem 13 dígitos (com o 9 extra)
    if re.fullmatch(r'55\d{2}9\d{8}', phone):
        # Remove o 9 após o DDD
        return phone[:4] + phone[5:]
    # Verifica se já está no formato correto (12 dígitos após 55)
    elif re.fullmatch(r'55\d{10}', phone):
        return phone
    else:
        return None

# === ENVIO DE MENSAGEM WHATSAPP ===
async def send_message_via_http(
    phone_number,
    msg=None,
    image_url=None,
    msg_id=None,
    context_info=None,
    variables=None,
    token="9C84DC7EBCC6-4B17-8625-A4A60018AC03",
    text_url=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/text",
    image_url_api=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/image"
):
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }

    # Substitui variáveis no texto da mensagem
    if msg and variables:
        try:
            msg = msg.format(**variables)
        except KeyError as e:
            raise Exception(f"Variável não encontrada na mensagem: {e}")

    results = {}

    # Se ambos msg e image_url forem fornecidos, envie a imagem primeiro e depois o texto
    if msg and image_url:
        # Envia imagem
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar imagem: {response.status_code}")
        content_type = response.headers.get("Content-Type", "image/jpeg")
        img_base64 = base64.b64encode(response.content).decode("utf-8")
        if content_type == "image/png":
            img_data = f"data:image/png;base64,{img_base64}"
        else:
            img_data = f"data:image/jpeg;base64,{img_base64}"

        payload_img = {
            "Phone": phone_number,
            "Image": img_data
        }
        resp_img = requests.post(image_url_api, headers=headers, json=payload_img)
        print(f"Resposta ao enviar imagem: {resp_img.status_code} - {resp_img.text}")
        results["image"] = resp_img.json()

        # Envia mensagem de texto
        if msg_id is None:
            msg_id = uuid.uuid4().hex.upper()
        payload_text = {
            "Phone": phone_number,
            "Body": msg,
            "Id": msg_id
        }
        if context_info:
            payload_text["ContextInfo"] = context_info
        resp_text = requests.post(text_url, headers=headers, json=payload_text)
        print(f"Resposta ao enviar mensagem de texto: {resp_text.status_code} - {resp_text.text}")
        results["text"] = resp_text.json()
        return results

    # Se apenas imagem
    elif image_url:
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar imagem: {response.status_code}")
        content_type = response.headers.get("Content-Type", "image/jpeg")
        img_base64 = base64.b64encode(response.content).decode("utf-8")
        if content_type == "image/png":
            img_data = f"data:image/png;base64,{img_base64}"
        else:
            img_data = f"data:image/jpeg;base64,{img_base64}"

        payload = {
            "Phone": phone_number,
            "Image": img_data
        }
        resp = requests.post(image_url_api, headers=headers, json=payload)
        print(f"Resposta ao enviar imagem: {resp.status_code} - {resp.text}")
        return resp.json()

    # Se apenas texto
    else:
        if msg_id is None:
            msg_id = uuid.uuid4().hex.upper()
        payload = {
            "Phone": phone_number,
            "Body": msg,
            "Id": msg_id
        }
        if context_info:
            payload["ContextInfo"] = context_info
        response = requests.post(text_url, headers=headers, json=payload)
        print(f"Resposta ao enviar mensagem de texto: {response.status_code} - {response.text}")
        return response.json()


# === PROCESSAMENTO DE CAMPANHAS ===
async def process_campaigns(campaign_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Busca dados da campanha específica
        cursor.execute("""
            SELECT id, message, start_date, end_date, daily_limit
            FROM campaigns
            WHERE id = %s
        """, (campaign_id,))
        campaign = cursor.fetchone()

        if not campaign:
            print(f"⚠️ Campanha {campaign_id} não encontrada.")
            return

        campaign_id, message, start_date, end_date, daily_limit = campaign

        # Corrige timezone para garantir comparação correta
        if start_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=None)
        if end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)

        while True:
            now = datetime.now()
            if now < start_date:
                print(f"⏳ Campanha {campaign_id} ainda não começou. Aguardando início.")
                await asyncio.sleep(60)
                continue
            if now > end_date:
                print(f"⏹️ Campanha {campaign_id} finalizada (data limite atingida).")
                break

            # Busca clientes ainda não enviados para hoje
            cursor.execute("""
                SELECT cc.client_id, cl."TELEFONE", cl.nome_cliente, cl.produto_recomendado
                FROM campaign_clients cc
                JOIN clientes_classificados cl ON cl.id = cc.client_id
                WHERE cc.campaign_id = %s AND cc.status IS DISTINCT FROM 'sent'
                ORDER BY RANDOM()
                LIMIT %s
            """, (campaign_id, daily_limit))
            clients = cursor.fetchall()

            if not clients:
                print(f"✅ Todas as mensagens da campanha {campaign_id} já foram enviadas.")
                break

            # Busca imagem vinculada
            cursor.execute("""
                SELECT file_url FROM campaign_files
                WHERE campaign_id = %s AND file_type = 'image'
                ORDER BY created_at DESC LIMIT 1
            """, (campaign_id,))
            image = cursor.fetchone()
            image_url = image[0] if image else None

            # Calcula intervalo aleatório entre envios
            seconds_in_day = 60 * 60 * 12  # 12 horas úteis para disparo
            interval = seconds_in_day // max(1, len(clients))
            min_interval = max(10, interval // 2)
            max_interval = max(20, interval)

            sent_today = 0

            for client_id, phone, nome_cliente, produto_recomendado in clients:
                if sent_today >= daily_limit:
                    print(f"🔒 Limite diário atingido para campanha {campaign_id}.")
                    break

                normalized_phone = normalize_phone(phone)
                if not normalized_phone:
                    # log_message(f"Telefone inválido para client_id {client_id}: {phone}")
                    continue

                primeiro_nome = nome_cliente.split()[0] if nome_cliente else ""
                variables = {
                    "nome_cliente": primeiro_nome,
                    "produto": produto_recomendado or "",
                    "link_personalizado": f"https://seusite.com/compra/{client_id}"
                }

                response = await send_message_via_http(normalized_phone, message, image_url, variables=variables)
                print(f"→ Enviado para {normalized_phone}: {response}")

                cursor.execute("""
                    UPDATE campaign_clients
                    SET status = 'sent', sent_at = %s, updated_at = %s
                    WHERE client_id = %s AND campaign_id = %s
                """, (datetime.now(), datetime.now(), client_id, campaign_id))
                conn.commit()
                sent_today += 1

                # Aguarda intervalo aleatório antes do próximo envio
                sleep_seconds = random.randint(min_interval, max_interval)
                await asyncio.sleep(sleep_seconds)

            # Após o loop, verifica se ainda há clientes para enviar amanhã
            if sent_today < daily_limit:
                print(f"✅ Todas as mensagens possíveis do dia foram enviadas para campanha {campaign_id}.")
                break

            # Aguarda até o próximo dia para continuar
            now = datetime.now()
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)
            wait_seconds = (tomorrow - now).total_seconds()
            print(f"⏳ Aguardando até o próximo dia para continuar campanha {campaign_id}...")
            await asyncio.sleep(wait_seconds)

    except Exception as e:
        print(f"⚠️ ERRO ao processar campanha {campaign_id}: {e}")
    finally:
        cursor.close()
        conn.close()

# === EXECUÇÃO ===
if __name__ == "__main__":
    campaign_id = "14c2d3c6-c9ba-43e3-9ffb-bcf858d7e6de"
    asyncio.run(process_campaigns(campaign_id))