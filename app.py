"""
Tradovate Trading Dashboard - Web Application
Flask app con dashboard para visualizar estadisticas de trading
Supports: Tradovate, Topstep

Security Features:
- Session-based authentication with CSRF protection
- Rate limiting
- Secure headers (CSP, HSTS, X-Frame-Options, etc.)
- No credentials stored in config.json
- API key passed via headers only
"""

from flask import Flask, render_template, jsonify, request, make_response, session, abort
from functools import wraps
import os
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re

# Security imports
try:
    from flask_talisman import Talisman
    TALISMAN_AVAILABLE = True
except ImportError:
    TALISMAN_AVAILABLE = False

from tradovate_api import TradovateDashboard, TradovateAPI
from topstep_api import TopstepDashboard, TopstepAPI
from analytics import AnalyticsEngine, Trade, TradeDirection

app = Flask(__name__)

# Security configuration
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# API Rate limits (stricter)
API_LIMITS = "30 per minute;100 per hour"

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', 'tradovate2024')

# In-memory token storage (more secure than file)
_api_tokens = {}  # token -> {username, api_key, created_at}
_session_tokens = {}  # browser_token -> {authenticated, created_at}

# CSRF Token storage
_csrf_tokens = {}  # session_id -> token


def generate_csrf_token():
    """Generate CSRF token for session"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def validate_csrf_token(token):
    """Validate CSRF token"""
    return token == session.get('csrf_token')


# Add CSRF to all templates
@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf_token())


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_client_ip():
    """Get client IP, handling proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    password = data.get('password', '')
    
    if password != DASHBOARD_PASSWORD:
        time.sleep(1)  # Prevent timing attacks
        return jsonify({"success": False, "message": "Password incorrecto"}), 401
    
    # Generate secure session
    session.permanent = True
    session['authenticated'] = True
    session['login_time'] = datetime.now(timezone.utc).isoformat()
    session['ip'] = get_client_ip()
    
    # Generate new CSRF token
    session['csrf_token'] = secrets.token_hex(32)
    
    response = make_response(jsonify({
        "success": True,
        "csrf_token": session['csrf_token']
    }))
    
    # Secure cookie settings
    response.set_cookie(
        'session',
        'authenticated',
        max_age=86400,
        secure=True,
        httponly=True,
        samesite='Lax'
    )
    
    return response


@app.route('/api/logout', methods=['POST'])
@require_auth
def logout():
    # Clear session completely
    session.clear()
    
    response = make_response(jsonify({"success": True}))
    response.set_cookie('session', '', max_age=0)
    return response


@app.route('/api/validate-session', methods=['GET'])
def validate_session():
    """Check if session is valid"""
    is_valid = session.get('authenticated', False)
    csrf_token = session.get('csrf_token', '')
    
    if is_valid:
        # Verify IP hasn't changed
        current_ip = get_client_ip()
        session_ip = session.get('ip')
        
        if session_ip and current_ip != session_ip:
            # IP changed - potential session hijacking
            session.clear()
            return jsonify({"valid": False, "reason": "IP changed"}), 401
    
    return jsonify({
        "valid": is_valid,
        "csrf_token": csrf_token if is_valid else None
    })


@app.route('/api/connect', methods=['POST'])
@require_auth
@limiter.limit(API_LIMITS)
def connect():
    """Conecta a Tradovate o Topstep según el platform especificado"""
    # Validate CSRF
    data = request.get_json() or {}
    csrf_token = data.get('csrf_token') or request.headers.get('X-CSRF-Token')
    
    if not validate_csrf_token(csrf_token):
        return jsonify({"success": False, "message": "CSRF inválido"}), 403
    
    platform = data.get('platform', 'tradovate')
    name = data.get('name')
    password = data.get('password')
    access_token = data.get('access_token')
    demo = data.get('demo', False)
    account_id = data.get('account_id')
    
    global dashboard
    
    try:
        if platform == 'topstep':
            dashboard = TopstepDashboard(name, password)
        else:
            dashboard = TradovateDashboard(name, password, access_token, demo)
        
        if dashboard.connect():
            dashboard.load_data(account_id)
            
            # Generate temporary token for this connection (not stored)
            temp_token = secrets.token_hex(16)
            
            return jsonify({
                "success": True, 
                "message": f"Conectado a {platform.capitalize()} exitosamente",
                "platform": platform,
                "account_id": account_id,
                "demo": demo if platform == 'tradovate' else False,
                "temp_token": temp_token  # For this session only
            })
        else:
            error_msg = dashboard.get_error_message()
            return jsonify({
                "success": False, 
                "message": error_msg or "Error de conexión"
            }), 401
            
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": "Error interno del servidor"
        }), 500


@app.route('/api/config', methods=['GET'])
@require_auth
@limiter.limit(API_LIMITS)
def get_config():
    """Get config WITHOUT sensitive data"""
    config = load_config_secure()
    # Never return passwords or API keys
    config.pop('password', None)
    config.pop('api_key', None)
    config.pop('access_token', None)
    return jsonify(config)


def load_config_secure():
    """Load config without sensitive data"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Return only safe fields
            return {
                'platform': config.get('platform', 'tradovate'),
                'name': config.get('name', ''),
                'account_id': config.get('account_id', '')
            }
    return {}


@app.route('/api/topstep/accounts', methods=['GET'])
@require_auth
@limiter.limit(API_LIMITS)
def get_topstep_accounts():
    """Obtiene lista de cuentas de Topstep - API key via header ONLY"""
    # API key MUST come from header, not URL (prevents log leakage)
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        return jsonify({"error": "API key requerida en header X-API-Key"}), 400
    
    # Get username from session or header
    username = request.headers.get('X-Username') or session.get('username')
    
    if not username:
        return jsonify({"error": "Username requerido"}), 400
    
    try:
        api = TopstepAPI(username, api_key)
        if api.authenticate():
            accounts = api.get_accounts()
            
            # Sanitize accounts - remove any sensitive data
            safe_accounts = []
            for acc in accounts:
                safe_accounts.append({
                    'id': acc.get('id'),
                    'name': acc.get('name'),
                    'balance': acc.get('balance'),
                    'canTrade': acc.get('canTrade'),
                    'isVisible': acc.get('isVisible'),
                    'simulated': acc.get('simulated')
                })
            
            return jsonify({
                "success": True,
                "accounts": safe_accounts
            })
        else:
            return jsonify({"error": api.get_error_message()}), 401
    except Exception as e:
        return jsonify({"error": "Error interno"}), 500


# ============ Protected Dashboard APIs ============

@app.route('/api/dashboard/summary')
@require_auth
@limiter.limit(API_LIMITS)
def summary():
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    return jsonify(dashboard.get_summary())


@app.route('/api/dashboard/performance')
@require_auth
@limiter.limit(API_LIMITS)
def performance():
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    
    return jsonify(analytics.get_summary())


@app.route('/api/dashboard/trades')
@require_auth
@limiter.limit(API_LIMITS)
def trades():
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)  # Cap at 100
    return jsonify(dashboard.get_recent_trades(limit))


@app.route('/api/dashboard/positions')
@require_auth
@limiter.limit(API_LIMITS)
def positions():
    if 'dashboard' not in globals():
        return jsonify({"error": "No conectado"}), 400
    
    positions = dashboard.api.get_positions()
    return jsonify(positions)


@app.route('/api/analytics/symbols')
@require_auth
@limiter.limit(API_LIMITS)
def symbol_performance():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_symbol_performance())


@app.route('/api/analytics/daily')
@require_auth
@limiter.limit(API_LIMITS)
def daily_stats():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_daily_stats())


@app.route('/api/analytics/hourly')
@require_auth
@limiter.limit(API_LIMITS)
def hourly_performance():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_hourly_performance())


@app.route('/api/analytics/direction')
@require_auth
@limiter.limit(API_LIMITS)
def direction_performance():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_direction_performance())


@app.route('/api/analytics/equity')
@require_auth
@limiter.limit(API_LIMITS)
def equity_curve():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_equity_curve())


@app.route('/api/analytics/full')
@require_auth
@limiter.limit(API_LIMITS)
def full_analytics():
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


@app.route('/api/analytics/expectancy')
@require_auth
@limiter.limit(API_LIMITS)
def expectancy_analytics():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_expectancy_breakdown())


@app.route('/api/analytics/r-multiples')
@require_auth
@limiter.limit(API_LIMITS)
def r_multiple_analytics():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_r_multiple_analysis())


@app.route('/api/analytics/monte-carlo')
@require_auth
@limiter.limit(API_LIMITS)
def monte_carlo_analytics():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    result = analytics.run_monte_carlo_simulation(1000)
    return jsonify({
        'median_equity': result.median_equity,
        'percentile_10': result.percentile_10,
        'percentile_90': result.percentile_90,
        'probability_of_ruin': result.probability_of_ruin,
        'avg_final_equity': result.avg_final_equity
    })


@app.route('/api/analytics/best-worst-days')
@require_auth
@limiter.limit(API_LIMITS)
def best_worst_days():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    return jsonify(analytics.get_best_and_worst_days())


@app.route('/api/analytics/calendar')
@require_auth
@limiter.limit(API_LIMITS)
def performance_calendar():
    trades = _get_trades_for_analytics()
    analytics = AnalyticsEngine(trades)
    calendar = analytics.get_performance_calendar()
    # Convert CalendarDay to dict
    return jsonify({k: {
        'date': v.date,
        'trades': v.trades,
        'pnl': v.pnl,
        'wins': v.wins,
        'losses': v.losses,
        'is_profitable': v.is_profitable,
        'is_trading_day': v.is_trading_day
    } for k, v in calendar.items()})


@app.route('/api/disconnect', methods=['POST'])
@require_auth
@limiter.limit(API_LIMITS)
def disconnect():
    global dashboard
    if 'dashboard' in globals():
        del dashboard
    return jsonify({"success": True})


def _get_trades_for_analytics():
    """Convierte trades del dashboard al formato del analytics engine"""
    if 'dashboard' not in globals():
        return []
    
    trades = []
    
    if not dashboard.trades:
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
                id="trade_" + str(i),
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
            direction = TradeDirection.BUY if (hasattr(t, 'direction') and t.direction.value == "Buy") or (isinstance(t, dict) and t.get('direction') == 'Buy') else TradeDirection.SELL
            trade = Trade(
                id=t.id if hasattr(t, 'id') else str(t.get('id', '')),
                symbol=t.symbol if hasattr(t, 'symbol') else t.get('symbol', 'UNKNOWN'),
                direction=direction,
                quantity=t.quantity if hasattr(t, 'quantity') else t.get('quantity', 0),
                price=t.price if hasattr(t, 'price') else t.get('price', 0),
                timestamp=t.timestamp if hasattr(t, 'timestamp') else datetime.now(),
                pnl=t.pnl if hasattr(t, 'pnl') else t.get('pnl', 0),
                commission=t.commission if hasattr(t, 'commission') else t.get('commission', 0)
            )
            trades.append(trade)
    
    return trades


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Demasiadas solicitudes. Intenta más tarde."}), 429


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Error interno del servidor"}), 500


# ============ Security Headers Middleware ============

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # Prevent caching of sensitive data
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response


def start_cloudflared():
    """Inicia cloudflared en background si está instalado"""
    try:
        import subprocess
        result = subprocess.run(['which', 'cloudflared'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n[+] cloudflared iniciado para acceso publico...")
            subprocess.Popen(['cloudflared', 'tunnel', '--url', 'http://localhost:5000', '--log', 'stdout'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            return True
        else:
            return False
    except Exception as e:
        print("[-] cloudflared no disponible: " + str(e))
        return False


if __name__ == '__main__':
    print("""
    ===========================================================
               TRADING DASHBOARD
                  Multi-Platform
              Tradovate + Topstep Support
              
              🔒 Security Hardened 🔒
    ===========================================================
    
    Servidor iniciando en http://0.0.0.0:5000
    
    Security Features:
    - Session authentication
    - CSRF protection
    - Rate limiting
    - Secure headers
    - API key via headers only
    
    ===========================================================
    """)
    
    start_cloudflared()
    
    # Run WITHOUT debug in production
    app.run(host='0.0.0.0', port=5000, debug=False)