from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def conect(tipo_banco: str, string_conexao: str):
    """
    Testa a conexão com o banco de dados informado e retorna o status e a conexão.

    Parâmetros:
        tipo_banco (str): Tipo do banco (ex: 'postgresql', 'mysql', 'sqlite', etc.)
        string_conexao (str): String de conexão completa (sem o driver).

    Retorna:
        Tuple[bool, sqlalchemy.engine.base.Connection | None]: 
            (True, conexão) se bem-sucedido, (False, None) em caso de erro.
    """
    try:
        if tipo_banco == "sqlite":
            engine = create_engine(f"sqlite:///{string_conexao}")
        else:
            # A string_conexao já deve conter o driver apropriado, ex: 'pymysql://user:pass@host/db'
            engine = create_engine(f"{string_conexao}")

        conexao = engine.connect()
        conexao.execute(text("SELECT 1"))  # Teste simples
        return True, conexao

    except SQLAlchemyError as e:
        print(f"[ERRO] Falha ao conectar: {e}")
        return False, None

# Exemplo de uso
if __name__ == "__main__":
    check, conn = conect("sqlite", "db_farmacia.db")
    if check:
        print("Conexão bem-sucedida!")
        conn.close()
    else:
        print("Falha na conexão.")  