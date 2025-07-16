
import pandas as pd
import numpy as np
import sqlite3
from scipy.optimize import minimize
import math
import json

DB_FILE = "database.db"
MODEL_PARAMS_FILE = "dixon_coles_model_params.json"

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Conexão com o banco de dados {db_file} estabelecida.")
    except sqlite3.Error as e:
        print(e)
    return conn

def dixon_coles_log_likelihood(params, home_goals, away_goals, home_team_indices, away_team_indices, num_teams):
    """ Função de log-verossimilhança para o modelo Dixon-Coles. """
    attack = params[:num_teams]
    defense = params[num_teams:2*num_teams]
    home_advantage = params[2*num_teams]

    log_likelihood = 0
    for i in range(len(home_goals)):
        home_idx = home_team_indices[i]
        away_idx = away_team_indices[i]

        # Garante que os gols são inteiros para math.factorial
        # Verifica se os valores são NaN antes de converter para int
        if pd.isna(home_goals[i]) or pd.isna(away_goals[i]):
            continue # Pula linhas com valores NaN

        hg = int(home_goals[i])
        ag = int(away_goals[i])

        # Taxas de Poisson
        lambda_home = np.exp(attack[home_idx] + defense[away_idx] + home_advantage)
        mu_away = np.exp(attack[away_idx] + defense[home_idx])

        # Log-verossimilhança da distribuição de Poisson
        # Adicionando uma verificação para evitar log(0) ou log de números negativos
        if lambda_home <= 0 or mu_away <= 0:
            continue

        log_likelihood += (hg * np.log(lambda_home) - lambda_home - np.log(math.factorial(hg)))
        log_likelihood += (ag * np.log(mu_away) - mu_away - np.log(math.factorial(ag)))

    return -log_likelihood

def train_dixon_coles_model(conn):
    """ Treina o modelo Dixon-Coles com os dados históricos. """
    df = pd.read_sql_query("SELECT home_team, away_team, home_goals, away_goals, season FROM matches", conn)

    # Filtra os dados para a temporada de 2025
    df = df[df["season"] == "2025"]

    # Remove linhas com valores NaN nas colunas de gols
    df.dropna(subset=["home_goals", "away_goals"], inplace=True)

    # Mapeia os nomes dos times para índices numéricos
    all_teams = pd.concat([df["home_team"], df["away_team"]]).unique()
    team_to_index = {team: i for i, team in enumerate(all_teams)}
    num_teams = len(all_teams)

    df["home_team_index"] = df["home_team"].map(team_to_index)
    df["away_team_index"] = df["away_team"].map(team_to_index)

    home_goals = df["home_goals"].values
    away_goals = df["away_goals"].values
    home_team_indices = df["home_team_index"].values
    away_team_indices = df["away_team_index"].values

    # Inicializa os parâmetros (ataque, defesa, vantagem de casa)
    initial_params = np.zeros(2 * num_teams + 1)

    # Otimização para encontrar os melhores parâmetros
    result = minimize(dixon_coles_log_likelihood, initial_params,
                      args=(home_goals, away_goals, home_team_indices, away_team_indices, num_teams),
                      method="BFGS", options={"disp": True})

    attack_params = result.x[:num_teams]
    defense_params = result.x[num_teams:2*num_teams]
    home_advantage_param = result.x[2*num_teams]

    # Salva os parâmetros do modelo
    model_params = {
        "attack": {team: attack_params[team_to_index[team]] for team in all_teams},
        "defense": {team: defense_params[team_to_index[team]] for team in all_teams},
        "home_advantage": home_advantage_param
    }

    # Salva os parâmetros em um arquivo JSON
    with open(MODEL_PARAMS_FILE, "w") as f:
        json.dump(model_params, f, indent=4)
    print(f"Parâmetros do modelo salvos em {MODEL_PARAMS_FILE}")

    return model_params

def predict_dixon_coles(home_team, away_team, model_params):
    """ Faz previsões de gols para um jogo usando o modelo Dixon-Coles. """
    attack = model_params["attack"]
    defense = model_params["defense"]
    home_advantage = model_params["home_advantage"]

    if home_team not in attack or away_team not in attack:
        print(f"Erro: Time(s) não encontrado(s) nos parâmetros do modelo. Times disponíveis: {list(attack.keys())}")
        return None, None

    # Taxas de Poisson para gols do time da casa e do time visitante
    lambda_home = np.exp(attack[home_team] + defense[away_team] + home_advantage)
    mu_away = np.exp(attack[away_team] + defense[home_team])

    # Calcula as probabilidades para cada placar (até um certo limite de gols)
    max_goals = 5 # Limite de gols para calcular as probabilidades
    prob_matrix = np.zeros((max_goals + 1, max_goals + 1))

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob_home = (lambda_home**i * np.exp(-lambda_home)) / math.factorial(i)
            prob_away = (mu_away**j * np.exp(-mu_away)) / math.factorial(j)
            prob_matrix[i, j] = prob_home * prob_away

    # Probabilidades de resultado (Vitória Casa, Empate, Vitória Fora)
    prob_home_win = np.sum(np.array([prob_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i > j]))
    prob_draw = np.sum(np.array([prob_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i == j]))
    prob_away_win = np.sum(np.array([prob_matrix[i, j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i < j]))

    # Normaliza as probabilidades para garantir que somem 1
    total_prob = prob_home_win + prob_draw + prob_away_win
    prob_home_win /= total_prob
    prob_draw /= total_prob
    prob_away_win /= total_prob

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
        print("Treinando o modelo Dixon-Coles...")
        model_params = train_dixon_coles_model(conn)
        print("Modelo Dixon-Coles treinado com sucesso!")
        
        # Exemplo de previsão
        print("\n--- Exemplo de Previsão ---")
        # Você pode substituir \'Corinthians\' e \'Flamengo RJ\' por outros times da temporada 2025
        # Para ver a lista de times, execute: 
        # import json
        # with open("dixon_coles_model_params.json", "r") as f:
        #     params = json.load(f)
        # print(list(params["attack"].keys()))
        
        prediction = predict_dixon_coles("Corinthians", "Flamengo RJ", model_params)
        if prediction:
            print(f"Probabilidade de Vitória do Corinthians: {prediction['home_win']:.2f}")
            print(f"Probabilidade de Empate: {prediction['draw']:.2f}")
            print(f"Probabilidade de Vitória do Flamengo RJ: {prediction['away_win']:.2f}")
            print(f"Gols esperados para Corinthians (casa): {prediction['lambda_home']:.2f}")
            print(f"Gols esperados para Flamengo RJ (fora): {prediction['mu_away']:.2f}")

        conn.close()



