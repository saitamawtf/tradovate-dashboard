"""
Tradovate Dashboard - Statistics Module
Consultas a la API de Tradovate y cálculos de estadísticas
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class TradeDirection(Enum):
    BUY = "Buy"
    SELL = "Sell"


@dataclass
class Trade:
    id: str
    symbol: str
    direction: TradeDirection
    quantity: int
    price: float
    timestamp: datetime
    pnl: float = 0.0
    commission: float = 0.0


@dataclass
class AccountStats:
    account_id: str
    account_name: str
    equity: float
    balance: float
    margin_used: float
    margin_available: float
    open_pnl: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    largest_win: float
    largest_loss: float


class TradovateAPI:
    """Cliente para la API de Tradovate"""
    
    BASE_URL = "https://live.tradovateapi.com/v1"
    
    def __init__(self, name: str = None, password: str = None, access_token: str = None):
        self.name = name
        self.password = password
        self.access_token = access_token
        self.account_id = None
    
    def authenticate(self) -> bool:
        """Autentica con credenciales o token"""
        if self.access_token:
            return True
        
        url = f"{self.BASE_URL}/auth/accesstokenrequest"
        payload = {
            "name": self.name,
            "password": self.password,
            "appId": "TradovateDashboard",
            "appVersion": "1.0",
            "cid": 0,
            "sec": ""
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessToken')
                return True
            return False
        except Exception as e:
            print(f"Auth error: {e}")
            return False
    
    def get_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_accounts(self) -> List[Dict]:
        url = f"{self.BASE_URL}/account/list"
        response = requests.get(url, headers=self.get_headers())
        return response.json().get('json', []) if response.status_code == 200 else []
    
    def get_account_id(self) -> Optional[str]:
        accounts = self.get_accounts()
        if accounts:
            self.account_id = accounts[0].get('id')
            return self.account_id
        return None
    
    def get_positions(self, account_id: str = None) -> List[Dict]:
        if not account_id:
            account_id = self.account_id
        url = f"{self.BASE_URL}/position/list?accountId={account_id}"
        response = requests.get(url, headers=self.get_headers())
        return response.json().get('json', []) if response.status_code == 200 else []
    
    def get_account_info(self, account_id: str = None) -> Dict:
        if not account_id:
            account_id = self.account_id
        url = f"{self.BASE_URL}/account/{account_id}"
        response = requests.get(url, headers=self.get_headers())
        return response.json() if response.status_code == 200 else {}
    
    def get_executions(self, account_id: str = None, days: int = 30) -> List[Dict]:
        """Obtiene ejecuciones trades de los últimos N días"""
        if not account_id:
            account_id = self.account_id
        url = f"{self.BASE_URL}/execution/list?accountId={account_id}"
        response = requests.get(url, headers=self.get_headers())
        return response.json().get('json', []) if response.status_code == 200 else []
    
    def get_orders(self, account_id: str = None, status: str = "Filled") -> List[Dict]:
        if not account_id:
            account_id = self.account_id
        url = f"{self.BASE_URL}/order/list?accountId={account_id}&status={status}"
        response = requests.get(url, headers=self.get_headers())
        return response.json().get('json', []) if response.status_code == 200 else []


class StatisticsCalculator:
    """Calcula estadísticas de trading"""
    
    @staticmethod
    def calculate_stats(trades: List[Trade], account_info: Dict = None) -> AccountStats:
        if not trades:
            return AccountStats(
                account_id="N/A",
                account_name="N/A",
                equity=0, balance=0, margin_used=0, margin_available=0,
                open_pnl=0, total_pnl=0, total_trades=0,
                winning_trades=0, losing_trades=0, win_rate=0,
                avg_win=0, avg_loss=0, profit_factor=0,
                largest_win=0, largest_loss=0
            )
        
        # Calcular PnL
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in trades)
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        
        stats = AccountStats(
            account_id=trades[0].id if trades else "N/A",
            account_name=account_info.get('name', 'N/A') if account_info else 'N/A',
            equity=account_info.get(' equity', 0) if account_info else 0,
            balance=account_info.get('balance', 0) if account_info else 0,
            margin_used=account_info.get('marginUsed', 0) if account_info else 0,
            margin_available=account_info.get('marginAvailable', 0) if account_info else 0,
            open_pnl=account_info.get('openPnl', 0) if account_info else 0,
            total_pnl=total_pnl,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=(len(winning_trades) / len(trades) * 100) if trades else 0,
            avg_win=total_wins / len(winning_trades) if winning_trades else 0,
            avg_loss=total_losses / len(losing_trades) if losing_trades else 0,
            profit_factor=total_wins / total_losses if total_losses > 0 else 0,
            largest_win=max(t.pnl for t in winning_trades) if winning_trades else 0,
            largest_loss=min(t.pnl for t in losing_trades) if losing_trades else 0
        )
        
        return stats


class TradovateDashboard:
    """Dashboard principal de Tradovate"""
    
    def __init__(self, name: str = None, password: str = None, access_token: str = None):
        self.api = TradovateAPI(name, password, access_token)
        self.trades: List[Trade] = []
        self.stats: Optional[AccountStats] = None
    
    def connect(self) -> bool:
        """Conecta a Tradovate"""
        if not self.api.authenticate():
            return False
        if not self.api.get_account_id():
            return False
        return True
    
    def load_data(self):
        """Carga datos de la cuenta"""
        # Obtener info de la cuenta
        account_info = self.api.get_account_info()
        
        # Obtener órdenes ejecutadas (trades)
        orders = self.api.get_orders()
        
        # Convertir a objetos Trade
        self.trades = []
        for order in orders:
            try:
                trade = Trade(
                    id=str(order.get('id', '')),
                    symbol=order.get('symbol', 'UNKNOWN'),
                    direction=TradeDirection.BUY if order.get('side') == 'Buy' else TradeDirection.SELL,
                    quantity=order.get('quantity', 0),
                    price=order.get('price', 0),
                    timestamp=datetime.fromisoformat(order.get('timestamp', '').replace('Z', '+00:00')),
                    pnl=order.get('pnl', 0),
                    commission=order.get('commission', 0)
                )
                self.trades.append(trade)
            except Exception as e:
                print(f"Error parsing order: {e}")
                continue
        
        # Calcular estadísticas
        self.stats = StatisticsCalculator.calculate_stats(self.trades, account_info)
    
    def get_summary(self) -> Dict:
        """Obtiene resumen del dashboard"""
        return {
            "connected": True,
            "account": {
                "id": self.stats.account_id if self.stats else "N/A",
                "name": self.stats.account_name if self.stats else "N/A",
            },
            "equity": f"${self.stats.equity:,.2f}" if self.stats else "$0.00",
            "balance": f"${self.stats.balance:,.2f}" if self.stats else "$0.00",
            "open_pnl": f"${self.stats.open_pnl:,.2f}" if self.stats else "$0.00",
            "total_pnl": f"${self.stats.total_pnl:,.2f}" if self.stats else "$0.00",
            "margin_used": f"${self.stats.margin_used:,.2f}" if self.stats else "$0.00",
            "margin_available": f"${self.stats.margin_available:,.2f}" if self.stats else "$0.00",
        }
    
    def get_performance(self) -> Dict:
        """Obtiene métricas de rendimiento"""
        if not self.stats:
            return {}
        
        return {
            "total_trades": self.stats.total_trades,
            "winning_trades": self.stats.winning_trades,
            "losing_trades": self.stats.losing_trades,
            "win_rate": f"{self.stats.win_rate:.1f}%",
            "avg_win": f"${self.stats.avg_win:,.2f}",
            "avg_loss": f"${self.stats.avg_loss:,.2f}",
            "profit_factor": f"{self.stats.profit_factor:.2f}",
            "largest_win": f"${self.stats.largest_win:,.2f}",
            "largest_loss": f"${self.stats.largest_loss:,.2f}",
        }
    
    def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """Obtiene trades recientes"""
        recent = sorted(self.trades, key=lambda t: t.timestamp, reverse=True)[:limit]
        return [
            {
                "symbol": t.symbol,
                "direction": t.direction.value,
                "quantity": t.quantity,
                "price": f"${t.price:.2f}",
                "pnl": f"${t.pnl:.2f}",
                "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M")
            }
            for t in recent
        ]