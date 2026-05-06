import os
import sqlite3
import csv 
from datetime import datetime
from flask import Flask, request, jsonify, render_template  # Adicionado render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Ajuste de Caminhos para o Render
DB_PATH = 'oficina.db'
CSV_PATH = 'historico_entregas.csv'

# --- NOVA ROTA PRINCIPAL ---
@app.route('/')
def home():
    # Isso busca automaticamente o arquivo dentro da pasta /templates
    return render_template('index.html')

@app.route('/relatorio')
def relatorio_page():
    # Rota para abrir a página de relatórios
    return render_template('relatorios.html')
# ---------------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    return conn

@app.route('/proximo_reg', methods=['GET'])
def proximo_reg():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM entregas")
        resultado = cursor.fetchone()[0]
        conn.close()
        return jsonify({"proximo": (resultado + 1) if resultado else 1})
    except:
        return jsonify({"proximo": 1})

@app.route('/get_entregas', methods=['GET'])
def get_entregas():
    try:
        data_sel = request.args.get('data')
        conn = get_db_connection()
        cursor = conn.cursor()
        if data_sel and data_sel.strip() != "":
            cursor.execute("SELECT * FROM entregas WHERE data = ?", (data_sel,))
        else:
            cursor.execute("SELECT * FROM entregas")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(ix) for ix in rows])
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/get_historico', methods=['GET'])
def get_historico():
    try:
        mes_filtro = request.args.get('mes') 
        ano_filtro = request.args.get('ano') 
        dia_filtro = request.args.get('dia') 

        if not os.path.exists(CSV_PATH):
            return jsonify([])

        historico = []
        with open(CSV_PATH, mode='r', encoding='utf-8-sig') as file:
            leitor = csv.DictReader(file, delimiter=';')
            for linha in leitor:
                data_entrega = linha.get('DATA_ENTREGA', '') 
                if ano_filtro and ano_filtro not in data_entrega: continue
                if mes_filtro and (len(data_entrega) < 7 or data_entrega[5:7] != mes_filtro): continue
                if dia_filtro and data_entrega != dia_filtro: continue

                historico.append({
                    "vendedor": linha.get('VENDEDOR', ''),
                    "modelo": linha.get('MODELO', ''),
                    "cor": linha.get('COR', ''),
                    "cidade": linha.get('CIDADE', ''),
                    "data": data_entrega
                })
        return jsonify(historico)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/salvar', methods=['POST'])
def salvar():
    try:
        dados = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entregas (num, data, hora, modelo, cor, chassi, vendedor, cidade, obs)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (dados.get('nf',''), dados.get('data',''), dados.get('hora',''), 
              dados.get('modelo',''), dados.get('cor',''), dados.get('chassi',''), 
              dados.get('vendedor',''), dados.get('cidade',''), dados.get('obs','')))
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/registrar_historico', methods=['POST'])
def registrar_historico():
    try:
        dados = request.json
        arquivo_existe = os.path.exists(CSV_PATH)
        arquivo_vazio = os.stat(CSV_PATH).st_size == 0 if arquivo_existe else True
        
        with open(CSV_PATH, mode='a', newline='', encoding='utf-8-sig') as file:
            escritor = csv.writer(file, delimiter=';')
            if arquivo_vazio:
                escritor.writerow(['HORA_SISTEMA', 'NF', 'DATA_ENTREGA', 'HORA', 'MODELO', 'COR', 'CHASSI', 'VENDEDOR', 'CIDADE', 'OBS'])
            
            escritor.writerow([
                datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                dados.get('nf', ''), dados.get('data', ''), dados.get('hora', ''), 
                dados.get('modelo', ''), dados.get('cor', ''), dados.get('chassi', ''), 
                dados.get('vendedor', ''), dados.get('cidade', ''), dados.get('obs', '')
            ])
        return jsonify({"status": "sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/deletar/<int:id>', methods=['DELETE'])
def deletar_entrega(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entregas WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/limpar_painel', methods=['POST'])
def limpar_painel():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entregas")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='entregas'")
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
