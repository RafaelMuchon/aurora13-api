
import json
import sqlite3
import pandas as pd

DB_FILE = "database.db"
MATCHES_JSON_FILE = "../matches_copa_america_2024.json" # Ainda não usaremos este para xG

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Conexão com o banco de dados {db_file} estabelecida.")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_xg_table(conn):
    """ Cria a tabela xg_data no banco de dados. """
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS xg_data (
                match_id INTEGER PRIMARY KEY,
                home_team TEXT,
                away_team TEXT,
                home_xg REAL,
                away_xg REAL
            );
        """)
        conn.commit()
        print("Tabela xg_data criada ou já existente.")
    except sqlite3.Error as e:
        print(e)

def calculate_and_insert_simplified_xg(conn):
    """ Calcula estimativas simplificadas de xG e insere na tabela xg_data. """
    df_matches = pd.read_sql_query("SELECT id, home_team, away_team, home_goals, away_goals, season FROM matches WHERE season = '2025'", conn)
    
    # Remove linhas com valores NaN nas colunas de gols
    df_matches.dropna(subset=["home_goals", "away_goals"], inplace=True)

    teams = pd.concat([df_matches["home_team"], df_matches["away_team"]]).unique()
    team_avg_goals = {}

    for team in teams:
        # Gols marcados
        scored_home = df_matches[df_matches["home_team"] == team]["home_goals"].sum()
        scored_away = df_matches[df_matches["away_team"] == team]["away_goals"].sum()
        total_scored = scored_home + scored_away

        # Gols sofridos
        conceded_home = df_matches[df_matches["home_team"] == team]["away_goals"].sum()
        conceded_away = df_matches[df_matches["away_team"] == team]["home_goals"].sum()
        total_conceded = conceded_home + conceded_away

        # Número de jogos
        num_games_home = len(df_matches[df_matches["home_team"] == team])
        num_games_away = len(df_matches[df_matches["away_team"] == team])
        total_games = num_games_home + num_games_away

        team_avg_goals[team] = {
            "avg_scored": total_scored / total_games if total_games > 0 else 0,
            "avg_conceded": total_conceded / total_games if total_games > 0 else 0
        }

    c = conn.cursor()
    for index, row in df_matches.iterrows():
        match_id = row["id"]
        home_team = row["home_team"]
        away_team = row["away_team"]

        # Estimativa simplificada de xG
        home_xg = team_avg_goals[home_team]["avg_scored"]
        away_xg = team_avg_goals[away_team]["avg_scored"]

        c.execute("INSERT OR REPLACE INTO xg_data (match_id, home_team, away_team, home_xg, away_xg) VALUES (?, ?, ?, ?, ?)",
                  (match_id, home_team, away_team, home_xg, away_xg))
    conn.commit()
    print("Estimativas simplificadas de xG inseridas na tabela xg_data.")

if __name__ == '__main__':
    conn = create_connection(DB_FILE)
    if conn:
        create_xg_table(conn)
        calculate_and_insert_simplified_xg(conn)
        conn.close()



