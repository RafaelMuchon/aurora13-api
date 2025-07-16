
import sqlite3

DB_FILE = "database.db"

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

def verify_data(conn):
    """ Verifica se os dados foram inseridos corretamente, incluindo as odds médias """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM matches")
        count = cursor.fetchone()[0]
        print(f"Número de registros na tabela matches: {count}")

        cursor.execute("PRAGMA table_info(matches)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Colunas na tabela matches: {columns}")

        cursor.execute("SELECT id, home_team, away_team, avg_home_odds, avg_draw_odds, avg_away_odds FROM matches LIMIT 5")
        rows = cursor.fetchall()
        print("Primeiros 5 registros com odds médias:")
        for row in rows:
            print(row)

    except sqlite3.Error as e:
        print(e)

if __name__ == '__main__':
    conn = create_connection(DB_FILE)
    if conn:
        verify_data(conn)
        conn.close()


