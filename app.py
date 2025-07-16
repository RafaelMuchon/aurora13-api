
from flask import Flask, request, jsonify
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PARQUET_FOLDER = 'parquets'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PARQUET_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Aurora13 API da Vovó Chica está rodando!"})

@app.route('/upload-parquet', methods=['POST'])
def upload_parquet():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome do arquivo está vazio."}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{file.filename}")
    file.save(csv_path)

    try:
        df = pd.read_csv(csv_path)
        parquet_filename = f"{timestamp}_{os.path.splitext(file.filename)[0]}.parquet"
        parquet_path = os.path.join(PARQUET_FOLDER, parquet_filename)
        df.to_parquet(parquet_path, index=False)
        return jsonify({"message": "Arquivo convertido com sucesso.", "parquet_file": parquet_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

    hotfix: forcing deploy
    
