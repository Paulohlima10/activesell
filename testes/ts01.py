import requests

def send_text_via_http(phone_number, msg, msg_id="90B2F8B13FAC8A9CF6B06E99C7834DC5", token="9C84DC7EBCC6-4B17-8625-A4A60018AC03", url="http://18.205.29.7:8080/chat/send/text"):
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    payload = {
        "Phone": phone_number,
        "Body": msg,
        "Id": msg_id
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


telefone = "553491704671"
mensagem = "Olá, este é um teste de mensagem de texto via HTTP!"
resposta = send_text_via_http(telefone, mensagem)
print("Resposta ao enviar mensagem via HTTP:")
print(resposta)     
