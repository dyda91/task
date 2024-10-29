import psycopg2

try:
    connection = psycopg2.connect(
        user="warmly-inventive-bluegill.data-1.use1.tembo.io",
        password="LdG0mKwC2RwQ3Zrb",
        host="tembo.io",
        port="5432",
        database="postgres"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT 1;")
    print("[SUCESSO] Conexão com o banco de dados PostgreSQL foi bem-sucedida!")
    cursor.close()
    connection.close()
except Exception as e:
    print(f"[ERRO] Não foi possível conectar ao banco de dados: {e}")
