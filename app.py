import os
import csv 
from datetime import datetime
from flask import Flask, request, jsonify, render_template 
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

# --- CONFIGURAÇÃO DO BANCO DE DADOS (POSTGRESQL) ---
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        # Conecta ao banco de dados do Render
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    else:
        raise Exception("DATABASE_URL não configurada no ambiente do Render.")

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Tabela do Painel (Motos que aparecem no telão)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entregas (
            id SERIAL PRIMARY KEY,
            num TEXT,
            data TEXT,
            hora TEXT,
            modelo TEXT,
            cor TEXT,
            chassi TEXT,
            vendedor TEXT,
            cidade TEXT,
            obs TEXT
        );
    """)
    # Tabela do Histórico (Dados permanentes para os relatórios)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            hora_sistema TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            nf TEXT,
            data_entrega TEXT,
            hora TEXT,
            modelo TEXT,
            cor TEXT,
            chassi TEXT,
            vendedor TEXT,
            cidade TEXT,
            obs TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Inicializa o banco ao iniciar o app
try:
    init_db()
except Exception as e:
    print(f"Atenção: Erro ao iniciar banco: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/relatorio')
def relatorio_page():
    return render_template('relatorios.html')

@app.route('/proximo_reg', methods=['GET'])
def proximo_reg():

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT MAX(id) FROM entregas")
        res = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({"proximo": (res + 1) if res else 1})
    except Exception as e:
        return jsonify({"proximo": 1})

@app.route('/get_entregas', methods=['GET'])
def get_entregas():
    try:
        data_sel = request.args.get('data')
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if data_sel and data_sel.strip() != "":
            cur.execute("SELECT * FROM entregas WHERE data = %s", (data_sel,))
        else:
            cur.execute("SELECT * FROM entregas")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# --- FUNÇÃO QUE ESTAVA FALTANDO: ALIMENTA O RELATÓRIO ---
@app.route('/get_historico', methods=['GET'])
def get_historico():
    try:
        mes_filtro = request.args.get('mes') 
        ano_filtro = request.args.get('ano') 
        dia_filtro = request.args.get('dia') 

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Seleciona dados da tabela de histórico
        query = "SELECT vendedor, modelo, cor, cidade, data_entrega as data FROM historico WHERE 1=1"
        params = []

        if ano_filtro:
            query += " AND data_entrega LIKE %s"
            params.append(f"{ano_filtro}%")
            
        if mes_filtro:
            query += " AND data_entrega LIKE %s"
            params.append(f"%-{mes_filtro}-%")
            
        if dia_filtro:
            query += " AND data_entrega = %s"
            params.append(dia_filtro)

        cur.execute(query, params)
        historico = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(historico)
    except Exception as e:
        print(f"Erro no relatório: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/salvar', methods=['POST'])
def salvar():
    try:
        dados = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO entregas (num, data, hora, modelo, cor, chassi, vendedor, cidade, obs)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (dados.get('nf',''), dados.get('data',''), dados.get('hora',''), 
              dados.get('modelo',''), dados.get('cor',''), dados.get('chassi',''), 
              dados.get('vendedor',''), dados.get('cidade',''), dados.get('obs','')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/registrar_historico', methods=['POST'])
def registrar_historico():
    try:
        dados = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO historico (nf, data_entrega, hora, modelo, cor, chassi, vendedor, cidade, obs)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (dados.get('nf', ''), dados.get('data', ''), dados.get('hora', ''), 
              dados.get('modelo', ''), dados.get('cor', ''), dados.get('chassi', ''), 
              dados.get('vendedor', ''), dados.get('cidade', ''), dados.get('obs', '')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/deletar/<int:id>', methods=['DELETE'])
def deletar_entrega(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM entregas WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/limpar_painel', methods=['POST'])
def limpar_painel():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM entregas")
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
