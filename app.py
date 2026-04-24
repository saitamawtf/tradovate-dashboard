"""
Tradovate Trading Dashboard - Web Application
Flask app con dashboard para visualizar estadísticas de trading
"""

from flask import Flask, render_template, jsonify, request
import os
import json
from datetime import datetime, timedelta
from tradovate_api import TradovateDashboard, TradovateAPI
from analytics import AnalyticsEngine, Trade, TradeDirection

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
    
    # Usar el motor de análisis
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    
    return jsonify(analytics.get_summary())


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


@app.route('/api/analytics/symbols')
def symbol_performance():
    """Rendimiento por símbolo"""
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_symbol_performance())


@app.route('/api/analytics/daily')
def daily_stats():
    """Estadísticas diarias"""
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_daily_stats())


@app.route('/api/analytics/hourly')
def hourly_performance():
    """Rendimiento por hora"""
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_hourly_performance())


@app.route('/api/analytics/direction')
def direction_performance():
    """Rendimiento BUY vs SELL"""
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_direction_performance())


@app.route('/api/analytics/equity')
def equity_curve():
    """Curva de equity"""
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_equity_curve())


@app.route('/api/analytics/full')
def full_analytics():
    """Análisis completo para gráficos avanzados"""
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    
    return jsonify({
        'summary': analytics.get_summary(),
        'symbols': analytics.get_symbol_performance(),
        'daily': analytics.get_daily_stats(),
        'hourly': analytics.get_hourly_performance(),
        'direction': analytics.get_direction_performance(),
        'equity_curve': analytics.get_equity_curve()
    })


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Desconecta y limpia sesión"""
    global dashboard
    if 'dashboard' in globals():
        del dashboard
    return jsonify({"success": True})


def _get_trades_for_analytics():
    """Convierte trades del dashboard al formato del analytics engine"""
    if 'dashboard' not in globals():
        return []
    
    # Crear trades de ejemplo para demo (reemplazar con datos reales)
    trades = []
    from datetime import datetime
    
    # Demo data si no hay trades reales
    if not dashboard.trades:
        # Generar datos de ejemplo para demostración
        import random
        symbols = ['MNQ', 'MES', 'NQ', 'ES']
        directions = [TradeDirection.BUY, TradeDirection.SELL]
        
        base_time = datetime.now()
        for i in range(100):
            direction = random.choice(directions)
            symbol = random.choice(symbols)
            pnl = random.uniform(-500, 800)
            commission = random.uniform(2, 5)
            
            trade = Trade(
                id=f"trade_{i}",
                symbol=symbol,
                direction=direction,
                quantity=random.randint(1, 5),
                price=random.uniform(4000, 5000),
                timestamp=base_time - timedelta(hours=random.randint(0, 720)),
                pnl=round(pnl, 2),
                commission=round(commission, 2)
            )
            trades.append(trade)
    else:
        for t in dashboard.trades:
            direction = TradeDirection.BUY if t.direction.value == "Buy" else TradeDirection.SELL
            trade = Trade(
                id=t.id,
                symbol=t.symbol,
                direction=direction,
                quantity=t.quantity,
                price=t.price,
                timestamp=t.timestamp,
                pnl=t.pnl,
                commission=t.commission
            )
            trades.append(trade)
    
    return trades


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              TRADOVATE TRADING DASHBOARD                    ║
    ║                    Advanced Analytics                        ║
    ║                                                              ║
    ║  🚀 Servidor iniciando en http://localhost:5000             ║
    ║                                                              ║
    ║  Características:                                            ║
    ║  → Métricas avanzadas de rendimiento                         ║
    ║  → Análisis por símbolo                                     ║
    ║  → Estadísticas horarias                                     ║
    ║  → Drawdown y curva de equity                                ║
    ║  → Rendimiento BUY vs SELL                                   ║
    ║                                                              ║
    ║  Abre tu navegador y vai a:                                  ║
    ║  → http://localhost:5000                                     ║
    ║                                                              ║
    ║  Para detener: Ctrl+C                                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True)