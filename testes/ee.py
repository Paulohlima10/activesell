from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field
import sqlite3
import json
import os

# =======================
# Classe para explorar o schema do SQLite
# =======================
class SQLiteSchemaExplorer:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def get_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [col[1] for col in cursor.fetchall()]
            schema[table] = columns

        return schema


# =======================
# Inicializa ferramenta com caminho do banco
# =======================
db_path = 'db_farmacia.db'  # Substitua pelo caminho real
schema_tool = SQLiteSchemaExplorer(db_path)

# =======================
# Tools especializadas
# =======================
class SqlTool(BaseTool):
    name: str = "sql_tool"
    description: str = "Retorna o schema do banco de dados SQLite (todas as tabelas disponiveis)."

    def _run(self, *args, **kwargs):
        result = schema_tool.get_schema()
        print("=== Resultados do Schema ===", result)
        return json.dumps({"clientes": result})


# =======================
# Inicializa modelo LLM
# =======================
os.environ["OPENAI_API_KEY"] = "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"

# =======================
# Agentes especialistas
# =======================
cliente_agent = Agent(
    role="Analista de Clientes",
    goal="Identificar tabelas relacionadas a dados de clientes",
    backstory="Você é especialista em bases de dados e reconhece informações cadastrais de clientes.",
    verbose=True,
    tools=[SqlTool()]
)

compras_agent = Agent(
    role="Analista de Compras",
    goal="Identificar tabelas relacionadas ao histórico de compras",
    backstory="Você analisa bancos de dados e identifica pedidos, vendas e itens comprados.",
    verbose=True,
    tools=[SqlTool()]
)

produtos_agent = Agent(
    role="Analista de Produtos",
    goal="Identificar tabelas relacionadas ao catálogo de produtos",
    backstory="Você é especialista em produtos e reconhece tabelas de catálogo e composição.",
    verbose=True,
    tools=[SqlTool()]
)

# =======================
# Tarefas para os agentes
# =======================
cliente_task = Task(
    description=(
        "Liste as tabelas que contêm dados de clientes com base na estrutura do banco fornecida.\n"
        "Responda no formato JSON com a chave 'clientes'."
    ),
    agent=cliente_agent,
    expected_output="Um JSON com as tabelas de clientes."
)

compras_task = Task(
    description=(
        "Liste as tabelas relacionadas ao histórico de compras com base na estrutura fornecida.\n"
        "Responda no formato JSON com a chave 'compras'."
    ),
    agent=compras_agent,
    expected_output="Um JSON com as tabelas de compras."
)

produtos_task = Task(
    description=(
        "Liste as tabelas com informações de produtos e catálogo com base na estrutura fornecida.\n"
        "Responda no formato JSON com a chave 'produtos'."
    ),
    agent=produtos_agent,
    expected_output="Um JSON com as tabelas de produtos."
)

# =======================
# Crew
# =======================
crew = Crew(
    agents=[cliente_agent, compras_agent, produtos_agent],
    tasks=[cliente_task, compras_task, produtos_task],
    verbose=True
)

# =======================
# Execução
# =======================
if __name__ == "__main__":
    resultado = crew.kickoff()
    print("\n=== Resultado Final ===")
    print(resultado)
