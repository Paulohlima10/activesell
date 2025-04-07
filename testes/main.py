from crewai import Agent, Task, Crew
from schema_tools import SQLiteSchemaExplorer
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os

# Inicializa ferramenta com caminho do banco
db_path = 'db_farmacia.db'  # Substitua pelo caminho da sua base
schema_tool = SQLiteSchemaExplorer(db_path)
os.environ["OPENAI_API_KEY"] = "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"


# Define uma função wrapper para transformar a ferramenta em callable
class ClienteTool(BaseTool):
    name: str = "cliente_tool"
    description: str = "Tool to fetch client data"
    
    def _run(self, *args, **kwargs):
        result = schema_tool.filter_tables(['cliente', 'cpf', 'nome', 'endereco'])
        return json.dumps({"clientes": result})

class ComprasTool(BaseTool):
    name: str = "compras_tool"
    description: str = "Tool to fetch purchase data"
    
    def _run(self, *args, **kwargs):
        result = schema_tool.filter_tables(['pedido', 'compra', 'venda', 'quantidade'])
        return json.dumps({"compras": result})

class ProdutosTool(BaseTool):
    name: str = "produtos_tool"
    description: str = "Tool to fetch product data"
    
    def _run(self, *args, **kwargs):
        result = schema_tool.filter_tables(['produto', 'preco', 'descricao', 'composicao'])
        return json.dumps({"produtos": result})


# Agentes
cliente_agent = Agent(
    role='Analista de Clientes',
    goal='Identificar tabelas relacionadas a dados de clientes',
    backstory='Você é responsável por identificar onde estão armazenadas as informações cadastrais dos clientes.',
    allow_delegation=False,
)

compras_agent = Agent(
    role='Analista de Compras',
    goal='Identificar tabelas relacionadas ao histórico de compras',
    backstory='Você encontra tabelas que representam pedidos, itens comprados e vendas.',
    allow_delegation=False,
)

produtos_agent = Agent(
    role='Analista de Produtos',
    goal='Identificar tabelas com informações de produtos e catálogo',
    backstory='Você identifica onde estão armazenadas as informações dos produtos da empresa.',
    allow_delegation=False,
)

# Tarefas
cliente_task = Task(
    description="Liste as tabelas que contêm dados de clientes. Retorne no formato JSON com a chave 'clientes'. Exemplo: {\"clientes\": [\"CLIENTES\"]}",
    agent=cliente_agent,
    tools=[ClienteTool()],
    expected_output="Um JSON com a chave 'clientes' e as tabelas correspondentes"
)

compras_task = Task(
    description="Liste as tabelas relacionadas ao histórico de compras. Retorne no formato JSON com a chave 'compras'. Exemplo: {\"compras\": [\"PEDIDOS\"]}",
    agent=compras_agent,
    tools=[ComprasTool()],
    expected_output="Um JSON com a chave 'compras' e as tabelas correspondentes"
)

produtos_task = Task(
    description="Liste as tabelas com informações de produtos e catálogo. Retorne no formato JSON com a chave 'produtos'. Exemplo: {\"produtos\": [\"PRODUTOS\"]}",
    agent=produtos_agent,
    tools=[ProdutosTool()],
    expected_output="Um JSON com a chave 'produtos' e as tabelas correspondentes"
)

# Cria a Crew
crew = Crew(
    agents=[cliente_agent, compras_agent, produtos_agent],
    tasks=[cliente_task, compras_task, produtos_task],
    verbose=True
)

# Executa a crew e monta o JSON final
results = crew.kickoff()

final_json = {}
for res in results:
    if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], str):
        try:
            parsed = json.loads(res[1])
            final_json.update(parsed)
        except:
            print("Erro ao interpretar resultado como JSON:", res)
    else:
        print("Erro ao interpretar resultado como JSON:", res)


# Exibe o JSON final
print(json.dumps(final_json, indent=2))
