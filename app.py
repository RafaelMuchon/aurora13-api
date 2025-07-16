from flask import Flask, request, jsonify, render_template_string
import os
import pandas as pd
import sqlite3
import json
import logging
from flask_cors import CORS

# Importa as funções dos modelos
from dixon_coles_model import predict_dixon_coles, MODEL_PARAMS_FILE
from skellam_bayesian_model import predict_skellam_bayesian, train_skellam_bayesian_model
from xg_differential_model import predict_xg_differential
from calculate_bet_value import calculate_value_bet

app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads'
PARQUET_FOLDER = 'parquets'
DB_FILE = 'database.db'

# Cria os diretórios se não existirem
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PARQUET_FOLDER, exist_ok=True)

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info(f"Conexão com o banco de dados {db_file} estabelecida.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar com o banco de dados: {e}")
    return conn

@app.route('/')
def home():
    """Página inicial da API"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aurora13 API - Sistema de Predição Esportiva</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .endpoint { background-color: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #007bff; }
        </style>
    </head>
    <body>
        <h1>Aurora13 API - Sistema de Predição Esportiva</h1>
        <p>Bem-vindo à API de predição esportiva Aurora13. Esta API oferece modelos preditivos avançados para apostas esportivas.</p>
        
        <h2>Endpoints Disponíveis:</h2>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/predict/dixon-coles</strong>
            <p>Predição usando o modelo Dixon-Coles</p>
            <p>Parâmetros: home_team, away_team</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/predict/skellam-bayesian</strong>
            <p>Predição usando o modelo Skellam Bayesiano</p>
            <p>Parâmetros: home_team, away_team</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/predict/xg-differential</strong>
            <p>Predição usando o modelo XG Diferencial</p>
            <p>Parâmetros: home_team, away_team</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/value-bets</strong>
            <p>Lista de apostas de valor identificadas pelo sistema</p>
            <p>Parâmetros opcionais: min_value (padrão: 0.05)</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <strong>/teams</strong>
            <p>Lista de times disponíveis no banco de dados</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/predict/dixon-coles')
def predict_dixon_coles_endpoint():
    """Endpoint para predição usando o modelo Dixon-Coles"""
    home_team = request.args.get('home_team')
    away_team = request.args.get('away_team')
    
    if not home_team or not away_team:
        return jsonify({"error": "Parâmetros 'home_team' e 'away_team' são obrigatórios"}), 400
    
    try:
        with open(MODEL_PARAMS_FILE, 'r') as f:
            dixon_coles_params = json.load(f)
        
        prediction = predict_dixon_coles(home_team, away_team, dixon_coles_params)
        
        if prediction:
            return jsonify({
                "model": "Dixon-Coles",
                "home_team": home_team,
                "away_team": away_team,
                "predictions": prediction
            })
        else:
            return jsonify({"error": "Time(s) não encontrado(s) no modelo"}), 404
            
    except FileNotFoundError:
        return jsonify({"error": "Modelo Dixon-Coles não treinado"}), 500
    except Exception as e:
        logger.error(f"Erro na predição Dixon-Coles: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route('/predict/skellam-bayesian')
def predict_skellam_bayesian_endpoint():
    """Endpoint para predição usando o modelo Skellam Bayesiano"""
    home_team = request.args.get('home_team')
    away_team = request.args.get('away_team')
    
    if not home_team or not away_team:
        return jsonify({"error": "Parâmetros 'home_team' e 'away_team' são obrigatórios"}), 400
    
    try:
        conn = create_connection(DB_FILE)
        if not conn:
            return jsonify({"error": "Erro de conexão com o banco de dados"}), 500
        
        team_stats = train_skellam_bayesian_model(conn)
        prediction = predict_skellam_bayesian(home_team, away_team, team_stats)
        conn.close()
        
        if prediction:
            return jsonify({
                "model": "Skellam Bayesiano",
                "home_team": home_team,
                "away_team": away_team,
                "predictions": prediction
            })
        else:
            return jsonify({"error": "Time(s) não encontrado(s) no modelo"}), 404
            
    except Exception as e:
        logger.error(f"Erro na predição Skellam Bayesiano: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route('/predict/xg-differential')
def predict_xg_differential_endpoint():
    """Endpoint para predição usando o modelo XG Diferencial"""
    home_team = request.args.get('home_team')
    away_team = request.args.get('away_team')
    
    if not home_team or not away_team:
        return jsonify({"error": "Parâmetros 'home_team' e 'away_team' são obrigatórios"}), 400
    
    try:
        conn = create_connection(DB_FILE)
        if not conn:
            return jsonify({"error": "Erro de conexão com o banco de dados"}), 500
        
        prediction = predict_xg_differential(home_team, away_team, conn)
        conn.close()
        
        if prediction:
            return jsonify({
                "model": "XG Diferencial",
                "home_team": home_team,
                "away_team": away_team,
                "predictions": prediction
            })
        else:
            return jsonify({"error": "Time(s) não encontrado(s) no modelo"}), 404
            
    except Exception as e:
        logger.error(f"Erro na predição XG Diferencial: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route('/value-bets')
def value_bets_endpoint():
    """Endpoint para listar apostas de valor"""
    min_value = float(request.args.get('min_value', 0.05))  # 5% por padrão
    
    try:
        conn = create_connection(DB_FILE)
        if not conn:
            return jsonify({"error": "Erro de conexão com o banco de dados"}), 500
        
        with open(MODEL_PARAMS_FILE, 'r') as f:
            dixon_coles_params = json.load(f)
        
        cursor = conn.cursor()
        cursor.execute("SELECT home_team, away_team, avg_home_odds, avg_draw_odds, avg_away_odds FROM matches WHERE season = '2025' AND avg_home_odds IS NOT NULL AND avg_draw_odds IS NOT NULL AND avg_away_odds IS NOT NULL")
        matches = cursor.fetchall()
        
        value_bets = []
        
        for match in matches:
            home_team, away_team, avg_home_odds, avg_draw_odds, avg_away_odds = match
            
            prediction = predict_dixon_coles(home_team, away_team, dixon_coles_params)
            
            if prediction:
                real_prob_home_win = prediction["home_win"]
                real_prob_draw = prediction["draw"]
                real_prob_away_win = prediction["away_win"]
                
                value_home_win = calculate_value_bet(real_prob_home_win, avg_home_odds)
                value_draw = calculate_value_bet(real_prob_draw, avg_draw_odds)
                value_away_win = calculate_value_bet(real_prob_away_win, avg_away_odds)
                
                if value_home_win > min_value:
                    value_bets.append({
                        "match": f"{home_team} vs {away_team}",
                        "outcome": "Home Win",
                        "real_prob": real_prob_home_win,
                        "bookie_odds": avg_home_odds,
                        "value": value_home_win
                    })
                if value_draw > min_value:
                    value_bets.append({
                        "match": f"{home_team} vs {away_team}",
                        "outcome": "Draw",
                        "real_prob": real_prob_draw,
                        "bookie_odds": avg_draw_odds,
                        "value": value_draw
                    })
                if value_away_win > min_value:
                    value_bets.append({
                        "match": f"{home_team} vs {away_team}",
                        "outcome": "Away Win",
                        "real_prob": real_prob_away_win,
                        "bookie_odds": avg_away_odds,
                        "value": value_away_win
                    })
        
        # Ordena por valor decrescente
        value_bets.sort(key=lambda x: x["value"], reverse=True)
        
        conn.close()
        
        return jsonify({
            "min_value_threshold": min_value,
            "total_value_bets": len(value_bets),
            "value_bets": value_bets
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular apostas de valor: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route('/teams')
def teams_endpoint():
    """Endpoint para listar times disponíveis"""
    try:
        conn = create_connection(DB_FILE)
        if not conn:
            return jsonify({"error": "Erro de conexão com o banco de dados"}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT home_team FROM matches WHERE season = '2025' UNION SELECT DISTINCT away_team FROM matches WHERE season = '2025' ORDER BY home_team")
        teams = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            "total_teams": len(teams),
            "teams": teams
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar times: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    logger.info("Iniciando a aplicação Aurora13 API...")
    app.run(host='0.0.0.0', port=5000, debug=True)


