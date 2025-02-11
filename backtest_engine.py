import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..config.settings import TIER_PARAMS
from ..analysis.rotation_detector import RotationSignal

@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    coin_id: str
    tier: int
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    stop_loss: float
    take_profit: float
    signal_confidence: float
    status: str  # 'open', 'closed', 'stopped'
    pnl: Optional[float]

class BacktestEngine:
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 max_position_size: float = 0.1):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = max_position_size
        self.positions: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.performance_metrics: Dict = {}

    def calculate_position_size(self, tier: int, signal_confidence: float) -> float:
        """
        Calculate position size based on tier and signal confidence
        
        Parameters:
            tier (int): Market tier (0-3)
            signal_confidence (float): Signal confidence score
            
        Returns:
            float: Position size in base currency
        """
        tier_adjustment = TIER_PARAMS[tier]['position_size_adjustment']
        confidence_adjustment = min(max(signal_confidence, 0.3), 1.0)
        
        position_size = (
            self.current_capital * 
            self.max_position_size * 
            tier_adjustment * 
            confidence_adjustment
        )
        
        return position_size

    def calculate_risk_levels(self, 
                            tier: int, 
                            entry_price: float, 
                            volatility: float) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels
        
        Parameters:
            tier (int): Market tier
            entry_price (float): Entry price
            volatility (float): Price volatility
            
        Returns:
            Tuple[float, float]: (stop_loss, take_profit) prices
        """
        tier_params = TIER_PARAMS[tier]
        
        # Adjust stops based on volatility
        volatility_adjustment = min(max(volatility, 0.02), 0.15)
        
        stop_loss = entry_price * (1 - (tier_params['stop_loss_multiplier'] * volatility_adjustment))
        take_profit = entry_price * (1 + (tier_params['take_profit_multiplier'] * volatility_adjustment))
        
        return stop_loss, take_profit

    def enter_position(self, 
                      timestamp: datetime,
                      coin_id: str,
                      tier: int,
                      entry_price: float,
                      volatility: float,
                      signal_confidence: float) -> Optional[Trade]:
        """
        Enter a new trading position
        
        Parameters:
            timestamp (datetime): Entry timestamp
            coin_id (str): Cryptocurrency identifier
            tier (int): Market tier
            entry_price (float): Entry price
            volatility (float): Price volatility
            signal_confidence (float): Signal confidence score
            
        Returns:
            Optional[Trade]: New trade if entered, None if invalid
        """
        # Calculate position parameters
        position_size = self.calculate_position_size(tier, signal_confidence)
        stop_loss, take_profit = self.calculate_risk_levels(tier, entry_price, volatility)
        
        # Validate position size
        if position_size > self.current_capital:
            return None
            
        # Create and record trade
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            coin_id=coin_id,
            tier=tier,
            entry_price=entry_price,
            exit_price=None,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            signal_confidence=signal_confidence,
            status='open',
            pnl=None
        )
        
        self.positions.append(trade)
        self.current_capital -= position_size
        
        return trade

    def update_positions(self, 
                        timestamp: datetime,
                        market_data: pd.DataFrame) -> List[Trade]:
        """
        Update open positions based on new market data
        
        Parameters:
            timestamp (datetime): Current timestamp
            market_data (pd.DataFrame): Latest market data
            
        Returns:
            List[Trade]: List of updated trades
        """
        closed_positions = []
        
        for trade in self.positions:
            if trade.status != 'open':
                continue
                
            # Get current price
            current_price = market_data[
                market_data['coin_id'] == trade.coin_id
            ]['close'].iloc[0]
            
            # Check stop loss and take profit
            if current_price <= trade.stop_loss:
                trade.exit_price = current_price
                trade.exit_time = timestamp
                trade.status = 'stopped'
                trade.pnl = self.calculate_pnl(trade)
                closed_positions.append(trade)
                
            elif current_price >= trade.take_profit:
                trade.exit_price = current_price
                trade.exit_time = timestamp
                trade.status = 'closed'
                trade.pnl = self.calculate_pnl(trade)
                closed_positions.append(trade)
        
        # Remove closed positions from active positions
        for trade in closed_positions:
            self.positions.remove(trade)
            self.closed_trades.append(trade)
            self.current_capital += trade.position_size * (1 + trade.pnl)
            
        return closed_positions

    def calculate_pnl(self, trade: Trade) -> float:
        """
        Calculate profit/loss for a trade
        
        Parameters:
            trade (Trade): Trade to calculate PnL for
            
        Returns:
            float: Profit/loss percentage
        """
        if trade.exit_price is None:
            return 0.0
            
        return (trade.exit_price - trade.entry_price) / trade.entry_price

    def calculate_performance_metrics(self) -> Dict:
        """
        Calculate backtest performance metrics
        
        Returns:
            Dict: Performance metrics
        """
        if not self.closed_trades:
            return {}
            
        pnls = [trade.pnl for trade in self.closed_trades if trade.pnl is not None]
        
        metrics = {
            'total_trades': len(self.closed_trades),
            'win_rate': sum(1 for pnl in pnls if pnl > 0) / len(pnls),
            'average_return': np.mean(pnls),
            'return_std': np.std(pnls),
            'sharpe_ratio': np.mean(pnls) / np.std(pnls) if np.std(pnls) > 0 else 0,
            'max_drawdown': min(pnls) if pnls else 0,
            'final_capital': self.current_capital,
            'total_return': (self.current_capital - self.initial_capital) / self.initial_capital
        }
        
        # Calculate metrics by tier
        for tier in range(4):
            tier_trades = [t for t in self.closed_trades if t.tier == tier]
            if tier_trades:
                tier_pnls = [t.pnl for t in tier_trades if t.pnl is not None]
                metrics[f'tier_{tier}_return'] = np.mean(tier_pnls)
                metrics[f'tier_{tier}_trades'] = len(tier_trades)
        
        self.performance_metrics = metrics
        return metrics

    def run_backtest(self, 
                    historical_data: pd.DataFrame,
                    signals: List[RotationSignal]) -> Dict:
        """
        Run backtest simulation
        
        Parameters:
            historical_data (pd.DataFrame): Historical market data
            signals (List[RotationSignal]): Trading signals
            
        Returns:
            Dict: Backtest results and metrics
        """
        # Reset backtest state
        self.current_capital = self.initial_capital
        self.positions = []
        self.closed_trades = []
        
        # Sort data and signals by timestamp
        historical_data = historical_data.sort_values('timestamp')
        signals = sorted(signals, key=lambda x: x.timestamp)
        
        # Run simulation
        for timestamp, market_data in historical_data.groupby('timestamp'):
            # Update existing positions
            self.update_positions(timestamp, market_data)
            
            # Process new signals
            current_signals = [s for s in signals if s.timestamp == timestamp]
            
            for signal in current_signals:
                # Find target coin in signal's tier
                target_coins = market_data[
                    market_data['tier'] == signal.to_tier
                ].sort_values('market_cap', ascending=False)
                
                if not target_coins.empty:
                    coin_data = target_coins.iloc[0]
                    
                    # Enter new position if capital available
                    if self.current_capital > 0:
                        self.enter_position(
                            timestamp=timestamp,
                            coin_id=coin_data['coin_id'],
                            tier=signal.to_tier,
                            entry_price=coin_data['close'],
                            volatility=coin_data['price_change_percentage_24h'] / 100,
                            signal_confidence=signal.confidence
                        )
        
        # Close any remaining positions at the last price
        final_market_data = historical_data.iloc[-1:]
        self.update_positions(final_market_data['timestamp'].iloc[0], final_market_data)
        
        # Calculate final metrics
        metrics = self.calculate_performance_metrics()
        
        return {
            'metrics': metrics,
            'trades': self.closed_trades,
            'final_capital': self.current_capital
        }
