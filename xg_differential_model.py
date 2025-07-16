
import sqlite3
import pandas as pd
import numpy as np

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

def predict_xg_differential(home_team, away_team, conn):
    """ Faz previsões de resultado com base no XG diferencial. """
    # Recupera os xG médios dos times da tabela xg_data
    # Como o xg_data é por partida, vamos calcular a média de xG para cada time
    # a partir dos dados da temporada 2025.
    df_xg = pd.read_sql_query("SELECT home_team, away_team, home_xg, away_xg FROM xg_data", conn)

    # Calcula o xG médio para cada time (marcado e sofrido)
    team_xg_stats = {}
    all_teams = pd.concat([df_xg["home_team"], df_xg["away_team"]]).unique()

    for team in all_teams:
        home_matches = df_xg[df_xg["home_team"] == team]
        away_matches = df_xg[df_xg["away_team"] == team]

        avg_xg_scored = (home_matches["home_xg"].sum() + away_matches["away_xg"].sum()) / \
                        (len(home_matches) + len(away_matches)) if (len(home_matches) + len(away_matches)) > 0 else 0
        
        avg_xg_conceded = (home_matches["away_xg"].sum() + away_matches["home_xg"].sum()) / \
                          (len(home_matches) + len(away_matches)) if (len(home_matches) + len(away_matches)) > 0 else 0
        
        team_xg_stats[team] = {
            "avg_xg_scored": avg_xg_scored,
            "avg_xg_conceded": avg_xg_conceded
        }

    if home_team not in team_xg_stats or away_team not in team_xg_stats:
        print(f"Erro: Time(s) não encontrado(s) nas estatísticas de xG. Times disponíveis: {list(team_xg_stats.keys())}")
        return None

    # Calcula o XG diferencial para o jogo
    # XG diferencial = (XG do time da casa - XG sofrido pelo time visitante) - (XG do time visitante - XG sofrido pelo time da casa)
    # Uma abordagem mais simples é: XG_home_ataque - XG_away_defesa
    # Usaremos uma abordagem mais comum: xG_marcado_home - xG_sofrido_away

    # XG esperado para o time da casa (marcado pelo time da casa vs. sofrido pelo time visitante)
    expected_xg_home = team_xg_stats[home_team]["avg_xg_scored"]
    # XG esperado para o time visitante (marcado pelo time visitante vs. sofrido pelo time da casa)
    expected_xg_away = team_xg_stats[away_team]["avg_xg_scored"]

    # O diferencial de xG é a diferença entre o xG esperado do time da casa e do time visitante
    xg_differential = expected_xg_home - expected_xg_away

    # Traduz o XG diferencial em probabilidades de resultado
    # Esta é uma simplificação. Em um modelo real, usaríamos regressão logística ou similar.
    # Para fins de demonstração, vamos usar limiares simples.
    prob_home_win = 0.0
    prob_draw = 0.0
    prob_away_win = 0.0

    if xg_differential > 0.5: # Time da casa tem XG significativamente maior
        prob_home_win = 0.7
        prob_draw = 0.2
        prob_away_win = 0.1
    elif xg_differential < -0.5: # Time visitante tem XG significativamente maior
        prob_home_win = 0.1
        prob_draw = 0.2
        prob_away_win = 0.7
    else: # XG diferencial equilibrado
        prob_home_win = 0.3
        prob_draw = 0.4
        prob_away_win = 0.3

    return {
        "home_win": prob_home_win,
        "draw": prob_draw,
        "away_win": prob_away_win,
        "expected_xg_home": expected_xg_home,
        "expected_xg_away": expected_xg_away,
        "xg_differential": xg_differential
    }

if __name__ == '__main__':
    conn = create_connection(DB_FILE)
    if conn:
        print("Realizando previsão com o modelo de XG Diferencial...")
        
        # Exemplo de previsão
        # Substitua por times da temporada 2025
        prediction = predict_xg_differential("Corinthians", "Flamengo RJ", conn)
        if prediction:
            print(f"Probabilidade de Vitória do Corinthians: {prediction['home_win']:.2f}")
            print(f"Probabilidade de Empate: {prediction['draw']:.2f}")
            print(f"Probabilidade de Vitória do Flamengo RJ: {prediction['away_win']:.2f}")
            print(f"XG Esperado para Corinthians (casa): {prediction['expected_xg_home']:.2f}")
            print(f"XG Esperado para Flamengo RJ (fora): {prediction['expected_xg_away']:.2f}")
            print(f"XG Diferencial: {prediction['xg_differential']:.2f}")

        conn.close()



