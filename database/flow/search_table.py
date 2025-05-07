from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from typing import List
from database.flow.conection_db import conect

def listar_tabelas(conexao: Connection) -> List[str]:
    """
    Retorna uma lista com os nomes das tabelas do banco de dados conectado.

    Parâmetros:
        conexao (sqlalchemy.engine.Connection): Objeto de conexão válido.

    Retorna:
        List[str]: Lista com os nomes das tabelas.
    """
    try:
        inspetor = inspect(conexao)
        tabelas = inspetor.get_table_names()
        
        # Verificação adicional para debug
        if not tabelas:
            print("Nenhuma tabela encontrada. Verificando via SQL direto...")
            # No SQLite podemos consultar a tabela sqlite_master
            result = conexao.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            if result:
                print(f"Tabelas encontradas via SQL direto: {[r[0] for r in result]}")
            else:
                print("Banco realmente vazio...")
                
        return tabelas
    except Exception as e:
        print(f"[ERRO] Não foi possível listar as tabelas: {e}")
        return []

# 🎯 Teste com SQLite
if __name__ == "__main__":
    tipo = "sqlite"
    string_conexao = "db_farmacia.db"  # ou o caminho completo se estiver em outra pasta

    conectado, conexao = conect(tipo, string_conexao)

    if conectado:
        print("✅ Conectado com sucesso ao SQLite!")

        tabelas = listar_tabelas(conexao)
        print("📋 Tabelas encontradas:")
        for tabela in tabelas:
            print(f"- {tabela}")

        conexao.close()
    else:
        print("❌ Não foi possível conectar ao banco.")