
import pandas as pd
import sqlite3
import os

# Defina o nome do arquivo do banco de dados
DB_FILE = "database.db"

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Conexão com o banco de dados {db_file} estabelecida.")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """ Cria a tabela para armazenar os dados de jogos """
    try:
        sql_create_matches_table = """ CREATE TABLE IF NOT EXISTS matches (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        country TEXT,
                                        league TEXT,
                                        season TEXT,
                                        date TEXT,
                                        time TEXT,
                                        home_team TEXT,
                                        away_team TEXT,
                                        home_goals INTEGER,
                                        away_goals INTEGER,
                                        result TEXT,
                                        psc_home_odds REAL,
                                        psc_draw_odds REAL,
                                        psc_away_odds REAL,
                                        max_c_home_odds REAL,
                                        max_c_draw_odds REAL,
                                        max_c_away_odds REAL,
                                        avg_c_home_odds REAL,
                                        avg_c_draw_odds REAL,
                                        avg_c_away_odds REAL
                                    ); """
        cursor = conn.cursor()
        cursor.execute(sql_create_matches_table)
        print("Tabela 'matches' criada com sucesso.")
    except sqlite3.Error as e:
        print(e)

def ingest_csv_to_db(conn, csv_file):
    """ Ingestiona dados de um arquivo CSV para o banco de dados SQLite """
    try:
        df = pd.read_csv(csv_file)
        # Renomeia as colunas para corresponder à tabela do banco de dados
        df.rename(columns={
            'Country': 'country',
            'League': 'league',
            'Season': 'season',
            'Date': 'date',
            'Time': 'time',
            'Home': 'home_team',
            'Away': 'away_team',
            'HG': 'home_goals',
            'AG': 'away_goals',
            'Res': 'result',
            'PSCH': 'psc_home_odds',
            'PSCD': 'psc_draw_odds',
            'PSCA': 'psc_away_odds',
            'MaxCH': 'max_c_home_odds',
            'MaxCD': 'max_c_draw_odds',
            'MaxCA': 'max_c_away_odds',
            'AvgCH': 'avg_c_home_odds',
            'AvgCD': 'avg_c_draw_odds',
            'AvgCA': 'avg_c_away_odds'
        }, inplace=True)

        # Seleciona apenas as colunas que correspondem à tabela
        df_to_ingest = df[[
            'country', 'league', 'season', 'date', 'time', 'home_team', 'away_team',
            'home_goals', 'away_goals', 'result', 'psc_home_odds', 'psc_draw_odds',
            'psc_away_odds', 'max_c_home_odds', 'max_c_draw_odds', 'max_c_away_odds',
            'avg_c_home_odds', 'avg_c_draw_odds', 'avg_c_away_odds'
        ]]

        df_to_ingest.to_sql('matches', conn, if_exists='append', index=False)
        print(f"Dados do arquivo {csv_file} inseridos na tabela 'matches'.")
    except Exception as e:
        print(f"Erro ao processar o arquivo {csv_file}: {e}")

if __name__ == '__main__':
    # Cria a conexão com o banco de dados
    conn = create_connection(DB_FILE)

    if conn is not None:
        # Cria a tabela
        create_table(conn)

        # Ingestiona o arquivo CSV
        ingest_csv_to_db(conn, 'BRA.csv')

        # Fecha a conexão
        conn.close()
        print("Conexão com o banco de dados fechada.")


