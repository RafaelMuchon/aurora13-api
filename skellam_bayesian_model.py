
import pandas as pd
import numpy as np
import sqlite3
from scipy.stats import poisson

# Para uma implementação bayesiana mais completa, seria necessário usar bibliotecas como PyMC3 ou Stan.
# No entanto, para manter a complexidade e o tempo de execução gerenciáveis no ambiente do sandbox,
# faremos uma abordagem simplificada que se aproxima do conceito Bayesiano.

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

def train_skellam_bayesian_model(conn):
    """ Treina um modelo Skellam Bayesiano simplificado.
    Esta é uma abordagem simplificada, pois uma implementação Bayesiana completa
    geralmente envolve inferência via MCMC, que é computacionalmente intensiva.
    Aqui, vamos estimar as taxas de gols médias para cada time e usar isso para
    prever a diferença de gols.
    """
    df = pd.read_sql_query("SELECT home_team, away_team, home_goals, away_goals, season FROM matches", conn)

    # Filtra os dados para a temporada de 2025
    df = df[df["season"] == "2025"]

    # Remove linhas com valores NaN nas colunas de gols
    df.dropna(subset=["home_goals", "away_goals"], inplace=True)

    # Calcula a média de gols marcados e sofridos por cada time
    teams = pd.concat([df["home_team"], df["away_team"]]).unique()
    team_stats = {}

    for team in teams:
        # Gols marcados em casa
        home_scored = df[df["home_team"] == team]["home_goals"].sum()
        home_matches = len(df[df["home_team"] == team])

        # Gols marcados fora
        away_scored = df[df["away_team"] == team]["away_goals"].sum()
        away_matches = len(df[df["away_team"] == team])

        # Gols sofridos em casa
        home_conceded = df[df["home_team"] == team]["away_goals"].sum()

        # Gols sofridos fora
        away_conceded = df[df["away_team"] == team]["home_goals"].sum()

        total_scored = home_scored + away_scored
        total_conceded = home_conceded + away_conceded
        total_matches = home_matches + away_matches

        team_stats[team] = {
            "avg_scored": total_scored / total_matches if total_matches > 0 else 0,
            "avg_conceded": total_conceded / total_matches if total_matches > 0 else 0
        }

    return team_stats

def predict_skellam_bayesian(home_team, away_team, team_stats):
    """ Faz previsões de gols para um jogo usando o modelo Skellam Bayesiano simplificado. """
    if home_team not in team_stats or away_team not in team_stats:
        print(f"Erro: Time(s) não encontrado(s) nas estatísticas do modelo.")
        return None

    # Estimativa das taxas de gols para o jogo
    # Abordagem simplificada: taxa de gols do time da casa = avg_scored do time da casa
    # taxa de gols do time visitante = avg_scored do time visitante
    # Para uma abordagem mais sofisticada, considerar avg_conceded do adversário

    # Taxa de gols esperados para o time da casa
    lambda_home = team_stats[home_team]["avg_scored"]
    # Taxa de gols esperados para o time visitante
    mu_away = team_stats[away_team]["avg_scored"]

    # Calcula as probabilidades para cada placar (até um certo limite de gols)
    max_goals = 5 # Limite de gols para calcular as probabilidades
    prob_matrix = np.zeros((max_goals + 1, max_goals + 1))

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob_home = poisson.pmf(i, lambda_home)
            prob_away = poisson.pmf(j, mu_away)
            prob_matrix[i, j] = prob_home * prob_away

    # Probabilidades de resultado (Vitória Casa, Empate, Vitória Fora)
    prob_home_win = np.sum(np.array([prob_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i > j]))
    prob_draw = np.sum(np.array([prob_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i == j]))
    prob_away_win = np.sum(np.array([prob_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i < j]))

    # Normaliza as probabilidades para garantir que somem 1
    total_prob = prob_home_win + prob_draw + prob_away_win
    if total_prob > 0:
        prob_home_win /= total_prob
        prob_draw /= total_prob
        prob_away_win /= total_prob
    else:
        # Caso não haja probabilidade, atribui 0 a todos
        prob_home_win, prob_draw, prob_away_win = 0, 0, 0

    return {
        "home_win": prob_home_win,
        "draw": prob_draw,
        "away_win": prob_away_win,
        "lambda_home": lambda_home,
        "mu_away": mu_away
    }

if __name__ == '__main__':
    conn = create_connection(DB_FILE)
    if conn:
        print("Treinando o modelo Skellam Bayesiano simplificado...")
        team_stats = train_skellam_bayesian_model(conn)
        print("Modelo Skellam Bayesiano simplificado treinado com sucesso!")
        
        # Exemplo de previsão
        print("\n--- Exemplo de Previsão ---")
        # Substitua por times da temporada 2025
        prediction = predict_skellam_bayesian("Corinthians", "Flamengo RJ", team_stats)
        if prediction:
            print(f"Probabilidade de Vitória do Corinthians: {prediction['home_win']:.2f}")
            print(f"Probabilidade de Empate: {prediction['draw']:.2f}")
            print(f"Probabilidade de Vitória do Flamengo RJ: {prediction['away_win']:.2f}")
            print(f"Gols esperados para Corinthians (casa): {prediction['lambda_home']:.2f}")
            print(f"Gols esperados para Flamengo RJ (fora): {prediction['mu_away']:.2f}")

        conn.close()



