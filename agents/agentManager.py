import os
import json
from crewai import Agent, Task, Crew
from agents.ChatHistory import ChatHistoryManager
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai import Knowledge
from logs.logging_config import log_queue
import asyncio


class SalesAssistant:
    def __init__(self, partner_code):
        # Configurar chave de API
        os.environ["OPENAI_API_KEY"] = "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"

        # Inicializar o gerenciador de histórico de chat
        self.chat_history = ChatHistoryManager()

        # Configurar a base de conhecimento inicial
        self.partner_code = partner_code
        self.update_knowledge(partner_code)

        # Carregar os arquivos da base de conhecimento
        self.role = self.load_file(partner_code, "role.txt")
        self.goal = self.load_file(partner_code, "goal.txt")
        self.backstory = self.load_file(partner_code, "backstory.txt")
        self.name = self.load_file(partner_code, "name.txt")
        self.task_description = self.load_file(partner_code, "task_description.txt")

        # Configurar agentes
        self.sale_agent = self.create_sale_agent()
        self.classification_agent = self.create_classification_agent()

        # Configurar tarefas
        self.sale_task = self.create_sale_task()
        self.classification_task = self.create_classification_task()

        # Configurar CrewAI
        self.crew = Crew(
            agents=[self.sale_agent, self.classification_agent],
            tasks=[self.sale_task, self.classification_task],
            language="pt",
            knowledge=self.knowledge,
            verbose=False
        )

    def update_knowledge(self, partner_code):
        """
        Atualiza a base de conhecimento com base no código do parceiro.
        """
        knowledge_path = os.path.join("partners", partner_code)
        document_path = os.path.join(knowledge_path, "document.txt")

        knowledge_path2 = os.path.join("knowledge", "partners", partner_code)
        document_path2 = os.path.join(knowledge_path2, "document.txt")

        if os.path.exists(document_path2):
            asyncio.create_task(log_queue.put(f"Atualizando base de conhecimento com o arquivo: {document_path}"))
            text_source = TextFileKnowledgeSource(file_paths=[document_path])
            self.knowledge = Knowledge(
                collection_name=f"vendas_farmacia_{partner_code}",
                sources=[text_source]
            )
        else:
            asyncio.create_task(log_queue.put(f"O arquivo de conhecimento '{document_path}' não foi encontrado. Usando base de conhecimento vazia."))
            self.knowledge = Knowledge(
                collection_name=f"vendas_farmacia_{partner_code}",
                sources=[]
            )

    def create_sale_agent(self):
        return Agent(
            name=self.name,
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            knowledge=self.knowledge,
            verbose=False
        )

    def create_classification_agent(self):
        return Agent(
            name="Classificador de Estágio",
            role="Analisa o histórico da conversa e classifica o cliente no funil de vendas.",
            goal="Determinar se o cliente está na fase de prospecção, consideração ou decisão de compra.",
            backstory="Especialista em analisar comportamento do cliente.",
            verbose=False
        )

    def create_sale_task(self):
        return Task(
            description=self.task_description,
            expected_output=json.dumps({
                "Resposta": "resposta do agente Vendedor",
                "Classificacao": "Prospecção"
            }),
            agent=self.sale_agent
        )

    def create_classification_task(self):
        return Task(
            description="Receber o histórico da conversa e classificar o estágio do cliente no funil de vendas. Historico: {historico}",
            expected_output=json.dumps({
                "Resposta": "resposta do agente apropriado",
                "Classificacao": "Prospecção"
            }),
            agent=self.classification_agent
        )

    def process_question(self, question, phone_number):
        # Executar a tarefa do CrewAI
        result = self.crew.kickoff(inputs={
            "question": question,
            "historico": self.chat_history.get_history_string(phone_number),
            "contexto": "contexto"
        })

        # Processar a resposta
        resposta_json = json.loads(str(result))
        resposta = resposta_json.get("Resposta", "Erro ao obter resposta")

        # Atualizar o histórico de chat
        self.chat_history.add_message(phone_number, "user", question)
        self.chat_history.add_message(phone_number, "assistant", resposta)

        return resposta
    
    def load_file(self, partner_code, file_name):
        """
        Lê um arquivo específico da base de conhecimento do parceiro e retorna o conteúdo.
        """
        knowledge_path = os.path.join("knowledge", "partners", partner_code)
        file_path = os.path.join(knowledge_path, file_name)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                asyncio.create_task(log_queue.put(f"Conteúdo do arquivo '{file_name}' carregado para o parceiro '{partner_code}'"))
                return content
        else:
            asyncio.create_task(log_queue.put(f"O arquivo '{file_name}' não foi encontrado para o parceiro '{partner_code}'.")) 
            return f"Arquivo padrão: {file_name} não encontrado."

class SalesAssistantManager:
    def __init__(self):
        self.assistants = {}

    def add_assistant(self, partner_code):
        if partner_code not in self.assistants:
            self.assistants[partner_code] = SalesAssistant(partner_code)
            asyncio.create_task(log_queue.put(f"Assistente para o parceiro '{partner_code}' foi adicionado."))
        else:
            asyncio.create_task(log_queue.put(f"Assistente para o parceiro '{partner_code}' já existe."))

    def get_assistant(self, partner_code):
        return self.assistants.get(partner_code, None)
    
    def delete_assistant(self, partner_code):
        """
        Remove um assistente da lista com base no partner_code.
        """
        if partner_code in self.assistants:
            del self.assistants[partner_code]
            asyncio.create_task(log_queue.put(f"Assistente para o parceiro '{partner_code}' foi removido."))
        else:
            asyncio.create_task(log_queue.put(f"Nenhum assistente encontrado para o parceiro '{partner_code}'."))

# Exemplo de uso
if __name__ == "__main__":
    import asyncio

    async def main():
        manager = SalesAssistantManager()

        while True:
            action = input("\nDigite 'add' para adicionar um assistente, 'ask' para fazer uma pergunta, 'delete' para remover um assistente ou 'sair' para encerrar: ").lower()

            if action == "add":
                partner_code = input("Digite o código do parceiro: ")
                manager.add_assistant(partner_code)

            elif action == "ask":
                partner_code = input("Digite o código do parceiro: ")
                assistant = manager.get_assistant(partner_code)
                if assistant:
                    question = input("Digite sua pergunta: ")
                    resposta = assistant.process_question(question, "1234")
                    print("\nResposta:", resposta)
                else:
                    print(f"Nenhum assistente encontrado para o parceiro '{partner_code}'.")

            elif action == "delete":
                partner_code = input("Digite o código do parceiro que deseja remover: ")
                manager.delete_assistant(partner_code)

            elif action == "sair":
                print("Encerrando o programa...")
                break

            else:
                print("Ação inválida. Tente novamente.")

    asyncio.run(main())