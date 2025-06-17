import os
import json
from crewai import Agent, Task, Crew
from agents.ChatHistory import ChatHistoryManager
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai import Knowledge
from logs.logging_config import log_queue
import asyncio
# from crewai_tools import MySQLSearchTool
import mysql.connector
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDatabaseTool, InfoSQLDatabaseTool

class SalesAssistant:
    def __init__(self, partner_code):
        # Configurar chave de API
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

        # Inicializar o gerenciador de histórico de chat
        self.chat_history = ChatHistoryManager()

        # Configurar a base de conhecimento inicial
        self.partner_code = partner_code
        self.update_knowledge(partner_code)

        # Inicializar conexão com banco de dados
        self.db_tools = self.configure_db_tools()

        # Carregar os arquivos da base de conhecimento
        self.role = self.load_file(partner_code, "role.txt")
        self.goal = self.load_file(partner_code, "goal.txt")
        self.backstory = self.load_file(partner_code, "backstory.txt")
        self.name = self.load_file(partner_code, "name.txt")
        self.task_description = self.load_file(partner_code, "task_description.txt")

        # Configurar agentes
        self.sale_agent = self.create_sale_agent()

        # Configurar tarefas
        self.sale_task = self.create_sale_task()

        # Configurar CrewAI
        self.crew = Crew(
            agents=[self.sale_agent],
            tasks=[self.sale_task],
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

    def configure_db_tools(self):
        """Configura a ferramenta de acesso ao banco de dados MySQL."""
        # Initialize the tool with the database URI and the target table name
        tool = MySQLSearchTool(
            db_uri=(
                os.getenv("AIVEN_BASE_URL")
            ),
            table_name='PEDIDOS'
        )
        return [tool]

    def create_sale_agent(self):
        return Agent(
            name=self.name,
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.db_tools,
            knowledge=self.knowledge,
            verbose=True
        )

    
    def create_sale_task(self):
        return Task(
            description=self.task_description,
            expected_output=json.dumps({
                "Resposta": "Resposta do agente baseada na pergunta do usuário"
            }),
            agent=self.sale_agent
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
    
    def ask_question(self, question, client_id):
        # Executar a tarefa do CrewAI
        result = self.crew.kickoff(inputs={
            "question": question,
            "historico": self.chat_history.get_history_string(client_id),
            "contexto": "contexto"
        })

        # Processar a resposta
        resposta_json = json.loads(str(result))
        resposta = resposta_json.get("Resposta", "Erro ao obter resposta")

        # Atualizar o histórico de chat
        self.chat_history.add_message(client_id, "user", question)
        self.chat_history.add_message(client_id, "assistant", resposta)

        return resposta
    
    def load_file(self, partner_code, file_name):
        """
        Lê um arquivo específico da base de conhecimento do parceiro e retorna o conteúdo.
        """
        knowledge_path = os.path.join("assets", "partners", partner_code)
        file_path = os.path.join(knowledge_path, file_name)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                asyncio.create_task(log_queue.put(f"Conteúdo do arquivo '{file_name}' carregado para o parceiro '{partner_code}'"))
                return content
        else:
            asyncio.create_task(log_queue.put(f"O arquivo '{file_name}' não foi encontrado para o parceiro '{partner_code}'.")) 
            return f"Arquivo padrão: {file_name} não encontrado."


# Exemplo de uso
if __name__ == "__main__":
    import asyncio

    async def main():

        while True:
            assistant = SalesAssistant("00002")
            if assistant:
                question = input("Digite sua pergunta: ")
                resposta = assistant.process_question(question, "1234")
                print("\nResposta:", resposta)
            

    asyncio.run(main())