"""
Tradovate Dashboard - Analytics Module
Métricas y análisis avanzado de trading
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import json


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
class PerformanceMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    largest_win: float
    largest_loss: float
    avg_trade: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    total_pnl: float
    total_commission: float
    avg_duration_minutes: float


@dataclass
class DrawdownInfo:
    current_drawdown: float
    max_drawdown: float
    max_drawdown_pct: float
    drawdown_duration_minutes: float


class AnalyticsEngine:
    """Motor de análisis para estadísticas avanzadas de trading"""
    
    def __init__(self, trades: List[Trade]):
        self.trades = sorted(trades, key=lambda t: t.timestamp)
    
    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calcula métricas completas de rendimiento"""
        if not self.trades:
            return self._empty_performance()
        
        winning = [t for t in self.trades if t.pnl > 0]
        losing = [t for t in self.trades if t.pnl < 0]
        total_pnl = sum(t.pnl for t in self.trades)
        total_commission = sum(t.commission for t in self.trades)
        
        # Calcular rachas
        consecutive_wins, max_wins = 0, 0
        consecutive_losses, max_losses = 0, 0
        
        for t in self.trades:
            if t.pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_wins = max(max_wins, consecutive_wins)
            elif t.pnl < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                max_losses = max(max_losses, consecutive_losses)
        
        # Calcular duración promedio de trades
        avg_duration = 0
        if len(self.trades) > 1:
            durations = []
            for i in range(1, len(self.trades)):
                delta = (self.trades[i].timestamp - self.trades[i-1].timestamp).total_seconds() / 60
                durations.append(delta)
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        return PerformanceMetrics(
            total_trades=len(self.trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=(len(winning) / len(self.trades) * 100) if self.trades else 0,
            avg_win=sum(t.pnl for t in winning) / len(winning) if winning else 0,
            avg_loss=abs(sum(t.pnl for t in losing) / len(losing)) if losing else 0,
            profit_factor=abs(sum(t.pnl for t in winning) / sum(t.pnl for t in losing)) if losing and sum(t.pnl for t in losing) != 0 else 0,
            largest_win=max(t.pnl for t in winning) if winning else 0,
            largest_loss=min(t.pnl for t in losing) if losing else 0,
            avg_trade=total_pnl / len(self.trades) if self.trades else 0,
            max_consecutive_wins=max_wins,
            max_consecutive_losses=max_losses,
            total_pnl=total_pnl,
            total_commission=total_commission,
            avg_duration_minutes=avg_duration
        )
    
    def calculate_drawdown(self) -> DrawdownInfo:
        """Calcula drawdown actual y máximo"""
        if not self.trades:
            return DrawdownInfo(0, 0, 0, 0)
        
        equity_curve = []
        running_equity = 0
        
        for t in self.trades:
            running_equity += t.pnl
            equity_curve.append(running_equity)
        
        # Encontrar máximo equity
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        current_drawdown = 0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0
        
        # Drawdown actual
        current_drawdown = peak - equity_curve[-1] if equity_curve else 0
        
        # Duración del drawdown
        drawdown_start = None
        max_duration = 0
        
        for i, equity in enumerate(equity_curve):
            if peak - equity > 0:
                if drawdown_start is None:
                    drawdown_start = self.trades[i].timestamp
            else:
                if drawdown_start is not None:
                    duration = (self.trades[i].timestamp - drawdown_start).total_seconds() / 60
                    max_duration = max(max_duration, duration)
                    drawdown_start = None
        
        return DrawdownInfo(
            current_drawdown=current_drawdown,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            drawdown_duration_minutes=max_duration
        )
    
    def get_symbol_performance(self) -> List[Dict]:
        """Agrupación de métricas por símbolo"""
        symbols = {}
        for t in self.trades:
            if t.symbol not in symbols:
                symbols[t.symbol] = {
                    'symbol': t.symbol,
                    'trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'total_pnl': 0,
                    'avg_pnl': 0
                }
            symbols[t.symbol]['trades'] += 1
            symbols[t.symbol]['total_pnl'] += t.pnl
            if t.pnl > 0:
                symbols[t.symbol]['wins'] += 1
            elif t.pnl < 0:
                symbols[t.symbol]['losses'] += 1
        
        # Calcular promedios y win rate
        for symbol in symbols.values():
            symbol['win_rate'] = (symbol['wins'] / symbol['trades'] * 100) if symbol['trades'] > 0 else 0
            symbol['avg_pnl'] = symbol['total_pnl'] / symbol['trades'] if symbol['trades'] > 0 else 0
        
        # Ordenar por total PnL
        return sorted(symbols.values(), key=lambda x: x['total_pnl'], reverse=True)
    
    def get_daily_stats(self) -> List[Dict]:
        """Estadísticas diarias"""
        daily = {}
        for t in self.trades:
            date = t.timestamp.date().isoformat()
            if date not in daily:
                daily[date] = {
                    'date': date,
                    'trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'pnl': 0,
                    'volume': 0
                }
            daily[date]['trades'] += 1
            daily[date]['pnl'] += t.pnl
            daily[date]['volume'] += abs(t.price * t.quantity)
            if t.pnl > 0:
                daily[date]['wins'] += 1
            elif t.pnl < 0:
                daily[date]['losses'] += 1
        
        # Calcular win rate diario
        for day in daily.values():
            day['win_rate'] = (day['wins'] / day['trades'] * 100) if day['trades'] > 0 else 0
        
        return sorted(daily.values(), key=lambda x: x['date'], reverse=True)
    
    def get_equity_curve(self) -> List[Dict]:
        """Curva de equity para gráficos"""
        curve = []
        running_pnl = 0
        
        for t in self.trades:
            running_pnl += t.pnl
            curve.append({
                'date': t.timestamp.isoformat(),
                'equity': running_pnl,
                'trade_pnl': t.pnl
            })
        
        return curve
    
    def get_hourly_performance(self) -> Dict[int, Dict]:
        """Rendimiento por hora del día (para encontrar mejores horarios)"""
        hourly = {h: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0} for h in range(24)}
        
        for t in self.trades:
            hour = t.timestamp.hour
            hourly[hour]['trades'] += 1
            hourly[hour]['pnl'] += t.pnl
            if t.pnl > 0:
                hourly[hour]['wins'] += 1
            elif t.pnl < 0:
                hourly[hour]['losses'] += 1
        
        # Calcular win rate y avg por hora
        for h, data in hourly.items():
            data['win_rate'] = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            data['avg_pnl'] = data['pnl'] / data['trades'] if data['trades'] > 0 else 0
        
        return hourly
    
    def get_direction_performance(self) -> Dict:
        """Rendimiento区分 BUY vs SELL"""
        buy_trades = [t for t in self.trades if t.direction == TradeDirection.BUY]
        sell_trades = [t for t in self.trades if t.direction == TradeDirection.SELL]
        
        return {
            'buy': {
                'trades': len(buy_trades),
                'wins': len([t for t in buy_trades if t.pnl > 0]),
                'losses': len([t for t in buy_trades if t.pnl < 0]),
                'total_pnl': sum(t.pnl for t in buy_trades),
                'win_rate': (len([t for t in buy_trades if t.pnl > 0]) / len(buy_trades) * 100) if buy_trades else 0
            },
            'sell': {
                'trades': len(sell_trades),
                'wins': len([t for t in sell_trades if t.pnl > 0]),
                'losses': len([t for t in sell_trades if t.pnl < 0]),
                'total_pnl': sum(t.pnl for t in sell_trades),
                'win_rate': (len([t for t in sell_trades if t.pnl > 0]) / len(sell_trades) * 100) if sell_trades else 0
            }
        }
    
    def get_summary(self) -> Dict:
        """Resumen completo para el dashboard"""
        performance = self.calculate_performance_metrics()
        drawdown = self.calculate_drawdown()
        
        return {
            'performance': {
                'total_trades': performance.total_trades,
                'winning_trades': performance.winning_trades,
                'losing_trades': performance.losing_trades,
                'win_rate': round(performance.win_rate, 1),
                'avg_win': round(performance.avg_win, 2),
                'avg_loss': round(performance.avg_loss, 2),
                'profit_factor': round(performance.profit_factor, 2),
                'largest_win': round(performance.largest_win, 2),
                'largest_loss': round(performance.largest_loss, 2),
                'avg_trade': round(performance.avg_trade, 2),
                'max_consecutive_wins': performance.max_consecutive_wins,
                'max_consecutive_losses': performance.max_consecutive_losses,
                'total_pnl': round(performance.total_pnl, 2),
                'total_commission': round(performance.total_commission, 2),
                'avg_duration_minutes': round(performance.avg_duration_minutes, 1)
            },
            'drawdown': {
                'current': round(drawdown.current_drawdown, 2),
                'max': round(drawdown.max_drawdown, 2),
                'max_pct': round(drawdown.max_drawdown_pct, 1),
                'duration_minutes': round(drawdown.drawdown_duration_minutes, 0)
            }
        }
    
    def _empty_performance(self) -> PerformanceMetrics:
        return PerformanceMetrics(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, avg_win=0, avg_loss=0, profit_factor=0,
            largest_win=0, largest_loss=0, avg_trade=0,
            max_consecutive_wins=0, max_consecutive_losses=0,
            total_pnl=0, total_commission=0, avg_duration_minutes=0
        )