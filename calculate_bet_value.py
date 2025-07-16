
import sqlite3
import json
import numpy as np
from dixon_coles_model import predict_dixon_coles, DB_FILE, MODEL_PARAMS_FILE

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Conexão com o banco de dados {db_file} estabelecida.")
    except sqlite3.Error as e:
        print(e)
    return conn

def calculate_value_bet(real_prob, bookie_odds):
    """ Calcula o valor de uma aposta. """
    # Probabilidade implícita da casa de apostas
    implied_prob = 1 / bookie_odds
    
    # Valor = (Probabilidade Real * Odds) - 1
    # Ou, para um cálculo mais direto de valor:
    # Valor = (Probabilidade Real / Probabilidade Implícita) - 1
    value = (real_prob / implied_prob) - 1
    return value

if __name__ == '__main__':
    conn = create_connection(DB_FILE)
    if conn:
        try:
            with open(MODEL_PARAMS_FILE, 'r') as f:
                dixon_coles_params = json.load(f)
            print("Parâmetros do modelo Dixon-Coles carregados com sucesso.")
        except FileNotFoundError:
            print(f"Erro: Arquivo de parâmetros do modelo Dixon-Coles não encontrado em {MODEL_PARAMS_FILE}")
            conn.close()
            exit()

        cursor = conn.cursor()
        # Seleciona jogos da temporada 2025 com odds médias
        cursor.execute("SELECT home_team, away_team, avg_home_odds, avg_draw_odds, avg_away_odds FROM matches WHERE season = '2025' AND avg_home_odds IS NOT NULL AND avg_draw_odds IS NOT NULL AND avg_away_odds IS NOT NULL")
        matches = cursor.fetchall()

        print("\n--- Análise de Valor de Apostas ---")
        value_bets = []

        for match in matches:
            home_team, away_team, avg_home_odds, avg_draw_odds, avg_away_odds = match

            # Previsão do modelo Dixon-Coles
            prediction = predict_dixon_coles(home_team, away_team, dixon_coles_params)
            
            if prediction:
                real_prob_home_win = prediction["home_win"]
                real_prob_draw = prediction["draw"]
                real_prob_away_win = prediction["away_win"]

                # Calcula o valor para cada resultado
                value_home_win = calculate_value_bet(real_prob_home_win, avg_home_odds)
                value_draw = calculate_value_bet(real_prob_draw, avg_draw_odds)
                value_away_win = calculate_value_bet(real_prob_away_win, avg_away_odds)

                # Define um limiar para considerar uma aposta de valor (ex: > 0%)
                if value_home_win > 0.05: # 5% de valor esperado
                    value_bets.append({
                        "match": f"{home_team} vs {away_team}",
                        "outcome": "Home Win",
                        "real_prob": f"{real_prob_home_win:.2%}",
                        "bookie_odds": avg_home_odds,
                        "value": f"{value_home_win:.2%}"
                    })
                if value_draw > 0.05:
                    value_bets.append({
                        "match": f"{home_team} vs {away_team}",
                        "outcome": "Draw",
                        "real_prob": f"{real_prob_draw:.2%}",
                        "bookie_odds": avg_draw_odds,
                        "value": f"{value_draw:.2%}"
                    })
                if value_away_win > 0.05:
                    value_bets.append({
                        "match": f"{home_team} vs {away_team}",
                        "outcome": "Away Win",
                        "real_prob": f"{real_prob_away_win:.2%}",
                        "bookie_odds": avg_away_odds,
                        "value": f"{value_away_win:.2%}"
                    })
        
        if value_bets:
            print("Apostas de Valor Encontradas (Valor Esperado > 5%):")
            for bet in value_bets:
                print(f"  Jogo: {bet['match']}\n    Resultado: {bet['outcome']}\n    Probabilidade Real: {bet['real_prob']}\n    Odds da Casa: {bet['bookie_odds']}\n    Valor: {bet['value']}\n")
        else:
            print("Nenhuma aposta de valor encontrada com o limiar atual.")

        conn.close()



