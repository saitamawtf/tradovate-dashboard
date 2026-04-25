"""
Tradovate Dashboard - Advanced Analytics Module
Métricas y análisis avanzado de trading con features tipo TradeZella/FXReplay
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json
import random
import math


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
    # Nuevos campos para análisis avanzado
    risk_amount: float = 0.0  # Cuánto arriesgaste en el trade
    setup_name: str = ""  # Nombre del setup (ORB, breakout, etc)
    notes: str = ""  # Notas del trade
    entry_time: datetime = None
    exit_time: datetime = None
    rating: int = 0  # 1-5 rating del trade


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
    # Nuevas métricas
    expectancy: float = 0.0  # Win rate × avg win - loss rate × avg loss
    r_multiple_avg: float = 0.0  # Promedio de R-multiple
    best_trade: float = 0.0
    worst_trade: float = 0.0
    consecutive_wins_value: float = 0.0
    consecutive_losses_value: float = 0.0


@dataclass
class DrawdownInfo:
    current_drawdown: float
    max_drawdown: float
    max_drawdown_pct: float
    drawdown_duration_minutes: float
    current_streak: int = 0


@dataclass
class CalendarDay:
    date: str
    trades: int
    pnl: float
    wins: int
    losses: int
    is_profitable: bool
    is_trading_day: bool


@dataclass
class TimeAnalytics:
    best_hours: List[Dict]  # Horas con mejor rendimiento
    best_days: List[Dict]  # Días de la semana con mejor rendimiento
    worst_hours: List[Dict]
    worst_days: List[Dict]
    hourly_stats: Dict[int, Dict]
    daily_stats: Dict[int, Dict]


@dataclass
class MonteCarloResult:
    final_equity: List[float]
    median_equity: float
    percentile_10: float
    percentile_90: float
    probability_of_ruin: float
    avg_final_equity: float


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
        
        # Calcular R-múltiples
        r_multiples = []
        for t in self.trades:
            if t.risk_amount > 0:
                r = t.pnl / t.risk_amount
                r_multiples.append(r)
            elif t.pnl > 0:
                r_multiples.append(1.0)  # Default
        
        # Calcular expectancy
        win_rate = (len(winning) / len(self.trades)) if self.trades else 0
        avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0
        avg_loss = abs(sum(t.pnl for t in losing) / len(losing)) if losing else 0
        loss_rate = 1 - win_rate
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        # Calcular rachas
        consecutive_wins, max_wins = 0, 0
        consecutive_losses, max_losses = 0, 0
        current_streak = 0
        
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
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=abs(sum(t.pnl for t in winning) / sum(t.pnl for t in losing)) if losing and sum(t.pnl for t in losing) != 0 else 0,
            largest_win=max(t.pnl for t in winning) if winning else 0,
            largest_loss=min(t.pnl for t in losing) if losing else 0,
            avg_trade=total_pnl / len(self.trades) if self.trades else 0,
            max_consecutive_wins=max_wins,
            max_consecutive_losses=max_losses,
            total_pnl=total_pnl,
            total_commission=total_commission,
            avg_duration_minutes=avg_duration,
            expectancy=expectancy,
            r_multiple_avg=sum(r_multiples) / len(r_multiples) if r_multiples else 0,
            best_trade=max(t.pnl for t in self.trades) if self.trades else 0,
            worst_trade=min(t.pnl for t in self.trades) if self.trades else 0
        )
    
    def _empty_performance(self) -> PerformanceMetrics:
        return PerformanceMetrics(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, avg_win=0, avg_loss=0, profit_factor=0,
            largest_win=0, largest_loss=0, avg_trade=0,
            max_consecutive_wins=0, max_consecutive_losses=0,
            total_pnl=0, total_commission=0, avg_duration_minutes=0,
            expectancy=0, r_multiple_avg=0, best_trade=0, worst_trade=0
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
        peak = equity_curve[0] if equity_curve else 0
        max_drawdown = 0
        max_drawdown_pct = 0
        
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
        
        # Calcular racha actual
        current_streak = 0
        for t in reversed(self.trades):
            if t.pnl < 0:
                break
            if t.pnl > 0:
                current_streak += 1
        
        return DrawdownInfo(
            current_drawdown=current_drawdown,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            drawdown_duration_minutes=max_duration,
            current_streak=current_streak
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
    
    def get_hourly_performance(self) -> TimeAnalytics:
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
            data['hour'] = h
            data['win_rate'] = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            data['avg_pnl'] = data['pnl'] / data['trades'] if data['trades'] > 0 else 0
        
        # Ordenar por PnL
        sorted_by_pnl = sorted(hourly.values(), key=lambda x: x['pnl'], reverse=True)
        best_hours = sorted_by_pnl[:3]
        worst_hours = sorted_by_pnl[-3:]
        
        # Stats por día de la semana
        daily = {d: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0, 'day_name': ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][d]} for d in range(7)}
        
        for t in self.trades:
            day = t.timestamp.weekday()
            daily[day]['trades'] += 1
            daily[day]['pnl'] += t.pnl
            if t.pnl > 0:
                daily[day]['wins'] += 1
            elif t.pnl < 0:
                daily[day]['losses'] += 1
        
        for d, data in daily.items():
            data['day'] = d
            data['win_rate'] = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            data['avg_pnl'] = data['pnl'] / data['trades'] if data['trades'] > 0 else 0
        
        sorted_by_pnl_days = sorted(daily.values(), key=lambda x: x['pnl'], reverse=True)
        
        return TimeAnalytics(
            best_hours=best_hours,
            worst_hours=worst_hours,
            best_days=sorted_by_pnl_days[:3],
            worst_days=sorted_by_pnl_days[-3:],
            hourly_stats=hourly,
            daily_stats=daily
        )
    
    def get_performance_calendar(self) -> Dict[str, CalendarDay]:
        """Calendario de rendimiento (para heatmap)"""
        calendar = {}
        
        for t in self.trades:
            date = t.timestamp.date().isoformat()
            if date not in calendar:
                calendar[date] = CalendarDay(
                    date=date,
                    trades=0,
                    pnl=0,
                    wins=0,
                    losses=0,
                    is_profitable=False,
                    is_trading_day=True
                )
            calendar[date].trades += 1
            calendar[date].pnl += t.pnl
            if t.pnl > 0:
                calendar[date].wins += 1
            elif t.pnl < 0:
                calendar[date].losses += 1
        
        # Marcar días rentables
        for day in calendar.values():
            day.is_profitable = day.pnl > 0
        
        return calendar
    
    def get_best_and_worst_days(self) -> Dict:
        """Mejores y peores días de trading"""
        daily = self.get_daily_stats()
        
        if not daily:
            return {'best': [], 'worst': []}
        
        sorted_by_pnl = sorted(daily, key=lambda x: x['pnl'], reverse=True)
        
        return {
            'best': sorted_by_pnl[:5],  # Top 5 mejores días
            'worst': sorted_by_pnl[-5:]  # Top 5 peores días
        }
    
    def get_expectancy_breakdown(self) -> Dict:
        """Desglose de expectancy"""
        winning = [t for t in self.trades if t.pnl > 0]
        losing = [t for t in self.trades if t.pnl < 0]
        
        total_trades = len(self.trades)
        if total_trades == 0:
            return {'expectancy': 0, 'probability': 0, 'avg_win': 0, 'avg_loss': 0}
        
        win_rate = len(winning) / total_trades
        loss_rate = len(losing) / total_trades
        avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0
        avg_loss = abs(sum(t.pnl for t in losing) / len(losing)) if losing else 0
        
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        return {
            'expectancy': expectancy,
            'expectancy_per_dollar': expectancy,  # Por cada dólar arriesgado
            'win_rate': win_rate * 100,
            'loss_rate': loss_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'risk_reward_ratio': avg_win / avg_loss if avg_loss > 0 else 0,
            'total_trades': total_trades,
            'quality_score': self._calculate_quality_score()
        }
    
    def _calculate_quality_score(self) -> float:
        """Calcula un score de calidad 0-100 basado en múltiples factores"""
        if not self.trades:
            return 0
        
        score = 0
        
        # Win rate (30 puntos máx)
        win_rate = len([t for t in self.trades if t.pnl > 0]) / len(self.trades)
        score += min(30, win_rate * 30)
        
        # Profit factor (25 puntos máx)
        winning = sum(t.pnl for t in self.trades if t.pnl > 0)
        losing = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        if losing > 0:
            pf = winning / losing
            score += min(25, pf * 10)
        
        # Expectancy (25 puntos máx)
        metrics = self.calculate_performance_metrics()
        if metrics.expectancy > 0:
            score += min(25, metrics.expectancy * 5)
        
        # Consistencia (20 puntos máx)
        dd = self.calculate_drawdown()
        if dd.max_drawdown_pct < 10:
            score += 20
        elif dd.max_drawdown_pct < 20:
            score += 10
        
        return min(100, score)
    
    def run_monte_carlo_simulation(self, num_simulations: int = 1000) -> MonteCarloResult:
        """Simulación Monte Carlo para proyectar resultados futuros"""
        if not self.trades:
            return MonteCarloResult([], 0, 0, 0, 0, 0)
        
        # Obtener distribución de resultados
        returns = [t.pnl for t in self.trades]
        mean_return = sum(returns) / len(returns)
        std_return = math.sqrt(sum((r - mean_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
        
        # Starting equity (assume $10,000)
        starting_equity = 10000
        num_trades = len(self.trades)
        
        final_equities = []
        ruin_count = 0
        
        for _ in range(num_simulations):
            equity = starting_equity
            
            for _ in range(num_trades):
                # Random sample from returns
                random_return = random.choice(returns)
                equity += random_return
                
                # Check for ruin (equity < $1000)
                if equity < 1000:
                    ruin_count += 1
                    break
            
            final_equities.append(equity)
        
        final_equities.sort()
        
        percentile_10 = final_equities[int(len(final_equities) * 0.1)]
        percentile_90 = final_equities[int(len(final_equities) * 0.9)]
        median_equity = final_equities[int(len(final_equities) * 0.5)]
        avg_equity = sum(final_equities) / len(final_equities)
        
        return MonteCarloResult(
            final_equity=final_equities,
            median_equity=median_equity,
            percentile_10=percentile_10,
            percentile_90=percentile_90,
            probability_of_ruin=(ruin_count / num_simulations * 100),
            avg_final_equity=avg_equity
        )
    
    def get_r_multiple_analysis(self) -> Dict:
        """Análisis de R-múltiplos (risk-adjusted returns)"""
        if not self.trades:
            return {'avg_r': 0, 'r_distribution': {}, 'best_r': 0, 'worst_r': 0}
        
        r_multiples = []
        for t in self.trades:
            if t.risk_amount > 0:
                r = t.pnl / t.risk_amount
            else:
                r = t.pnl / 100  # Default risk de $100
            r_multiples.append(r)
        
        # Distribución de R-múltiplos
        distribution = {
            'excellent': len([r for r in r_multiples if r >= 3]),  # R >= 3
            'good': len([r for r in r_multiples if 1 <= r < 3]),   # R 1-3
            'breakeven': len([r for r in r_multiples if -1 < r < 1]),  # -1 < R < 1
            'poor': len([r for r in r_multiples if -3 <= r < -1]),  # R -3 to -1
            'terrible': len([r for r in r_multiples if r < -3])   # R < -3
        }
        
        return {
            'avg_r': sum(r_multiples) / len(r_multiples) if r_multiples else 0,
            'best_r': max(r_multiples) if r_multiples else 0,
            'worst_r': min(r_multiples) if r_multiples else 0,
            'r_distribution': distribution,
            'r_values': r_multiples
        }
    
    def get_full_report(self) -> Dict:
        """Reporte completo con todas las métricas"""
        metrics = self.calculate_performance_metrics()
        drawdown = self.calculate_drawdown()
        time_analytics = self.get_hourly_performance()
        expectancy = self.get_expectancy_breakdown()
        r_analysis = self.get_r_multiple_analysis()
        monte_carlo = self.run_monte_carlo_simulation(500)
        best_worst = self.get_best_and_worst_days()
        
        return {
            'summary': {
                'total_trades': metrics.total_trades,
                'total_pnl': metrics.total_pnl,
                'win_rate': f"{metrics.win_rate:.1f}%",
                'profit_factor': f"{metrics.profit_factor:.2f}",
                'expectancy': f"${metrics.expectancy:.2f}",
                'quality_score': f"{self._calculate_quality_score():.0f}/100"
            },
            'performance': {
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'avg_win': f"${metrics.avg_win:.2f}",
                'avg_loss': f"${metrics.avg_loss:.2f}",
                'largest_win': f"${metrics.largest_win:.2f}",
                'largest_loss': f"${metrics.largest_loss:.2f}",
                'avg_trade': f"${metrics.avg_trade:.2f}",
                'total_commission': f"${metrics.total_commission:.2f}"
            },
            'streaks': {
                'max_consecutive_wins': metrics.max_consecutive_wins,
                'max_consecutive_losses': metrics.max_consecutive_losses,
                'current_drawdown': f"${drawdown.current_drawdown:.2f}",
                'max_drawdown': f"${drawdown.max_drawdown:.2f} ({drawdown.max_drawdown_pct:.1f}%)"
            },
            'time_analytics': {
                'best_hours': time_analytics.best_hours,
                'best_days': time_analytics.best_days,
                'worst_hours': time_analytics.worst_hours,
                'worst_days': time_analytics.worst_days
            },
            'expectancy': expectancy,
            'r_multiple': r_analysis,
            'monte_carlo': {
                'median_equity': f"${monte_carlo.median_equity:,.2f}",
                'percentile_10': f"${monte_carlo.percentile_10:,.2f}",
                'percentile_90': f"${monte_carlo.percentile_90:,.2f}",
                'probability_of_ruin': f"{monte_carlo.probability_of_ruin:.1f}%",
                'avg_projected': f"${monte_carlo.avg_final_equity:,.2f}"
            },
            'best_days': best_worst['best'],
            'worst_days': best_worst['worst'],
            'symbols': self.get_symbol_performance()[:5],
            'equity_curve': self.get_equity_curve()
        }
    
    def get_summary(self) -> Dict:
        """Resumen para el dashboard (método de compatibilidad)"""
        metrics = self.calculate_performance_metrics()
        drawdown = self.calculate_drawdown()
        
        return {
            'performance': {
                'total_trades': metrics.total_trades,
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'win_rate': metrics.win_rate,
                'avg_win': metrics.avg_win,
                'avg_loss': metrics.avg_loss,
                'profit_factor': metrics.profit_factor,
                'largest_win': metrics.largest_win,
                'largest_loss': metrics.largest_loss,
                'avg_trade': metrics.avg_trade,
                'max_consecutive_wins': metrics.max_consecutive_wins,
                'max_consecutive_losses': metrics.max_consecutive_losses,
                'total_pnl': metrics.total_pnl,
                'total_commission': metrics.total_commission,
                'avg_duration_minutes': metrics.avg_duration_minutes,
                'expectancy': metrics.expectancy,
                'r_multiple_avg': metrics.r_multiple_avg,
                'best_trade': metrics.best_trade,
                'worst_trade': metrics.worst_trade
            },
            'drawdown': {
                'current_drawdown': drawdown.current_drawdown,
                'max_drawdown': drawdown.max_drawdown,
                'max_drawdown_pct': drawdown.max_drawdown_pct,
                'drawdown_duration_minutes': drawdown.drawdown_duration_minutes,
                'current_streak': drawdown.current_streak
            }
        }