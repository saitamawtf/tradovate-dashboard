"""
Tradovate Trading Dashboard - Web Application
Flask app con dashboard para visualizar estadísticas de trading
"""

from flask import Flask, render_template, jsonify, request
import os
import json
from tradovate_api import TradovateDashboard, TradovateAPI

app = Flask(__name__)

# Credenciales desde variables de entorno o archivo config
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')


def load_config():
    """Carga configuración desde archivo"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_config(config):
    """Guarda configuración"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('index.html')


@app.route('/api/connect', methods=['POST'])
def connect():
    """Conecta a Tradovate"""
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')
    access_token = data.get('access_token')
    
    global dashboard
    dashboard = TradovateDashboard(name, password, access_token)
    
    if dashboard.connect():
        dashboard.load_data()
        
        # Guardar token para futuras conexiones
        config = load_config()
        if access_token:
            config['access_token'] = access_token
        save_config(config)
        
        return jsonify({"success": True, "message": "Conectado exitosamente"})
    else:
        return jsonify({"success": False, "message": "Error de conexión"}), 401


@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtiene configuración guardada (sin password)"""
    config = load_config()
    config.pop('password', None)  # No enviar password
    return jsonify(config)


@app.route('/api/dashboard/summary')
def summary():
    """Resumen del dashboard"""
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    return jsonify(dashboard.get_summary())


@app.route('/api/dashboard/performance')
def performance():
    """Métricas de rendimiento"""
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    return jsonify(dashboard.get_performance())


@app.route('/api/dashboard/trades')
def trades():
    """Trades recientes"""
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    
    limit = request.args.get('limit', 20, type=int)
    return jsonify(dashboard.get_recent_trades(limit))


@app.route('/api/dashboard/positions')
def positions():
    """Posiciones abiertas"""
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    
    positions = dashboard.api.get_positions()
    return jsonify(positions)


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Desconecta y limpia sesión"""
    global dashboard
    if 'dashboard' in globals():
        del dashboard
    return jsonify({"success": True})


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              TRADOVATE TRADING DASHBOARD                    ║
    ║                                                              ║
    ║  🚀 Servidor iniciando en http://localhost:5000             ║
    ║                                                              ║
    ║  Abre tu navegador y vai a:                                  ║
    ║  → http://localhost:5000                                     ║
    ║                                                              ║
    ║  Para detener: Ctrl+C                                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True)