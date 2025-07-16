
import sqlite3
import pandas as pd

DB_FILE = "database.db"

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

def calculate_average_odds(conn):
    """ Calcula as odds médias e as adiciona à tabela de jogos """
    try:
        df = pd.read_sql_query("SELECT id, psc_home_odds, psc_draw_odds, psc_away_odds, max_c_home_odds, max_c_draw_odds, max_c_away_odds, avg_c_home_odds, avg_c_draw_odds, avg_c_away_odds FROM matches", conn)

        # Calcula a média das odds de casa
        df["avg_home_odds"] = df[["psc_home_odds", "max_c_home_odds", "avg_c_home_odds"]].mean(axis=1)
        # Calcula a média das odds de empate
        df["avg_draw_odds"] = df[["psc_draw_odds", "max_c_draw_odds", "avg_c_draw_odds"]].mean(axis=1)
        # Calcula a média das odds de fora
        df["avg_away_odds"] = df[["psc_away_odds", "max_c_away_odds", "avg_c_away_odds"]].mean(axis=1)

        # Atualiza o banco de dados com as novas colunas
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE matches ADD COLUMN avg_home_odds REAL")
        cursor.execute("ALTER TABLE matches ADD COLUMN avg_draw_odds REAL")
        cursor.execute("ALTER TABLE matches ADD COLUMN avg_away_odds REAL")
        conn.commit()

        for index, row in df.iterrows():
            cursor.execute("UPDATE matches SET avg_home_odds = ?, avg_draw_odds = ?, avg_away_odds = ? WHERE id = ?",
                           (row["avg_home_odds"], row["avg_draw_odds"], row["avg_away_odds"], row["id"]))
        conn.commit()
        print("Odds médias calculadas e adicionadas à tabela matches.")

    except sqlite3.Error as e:
        print(f"Erro ao calcular odds médias: {e}")

if __name__ == '__main__':
    conn = create_connection(DB_FILE)
    if conn:
        calculate_average_odds(conn)
        conn.close()


