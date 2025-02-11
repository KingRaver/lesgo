import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from ..config.settings import DATA_STORAGE_PATH
from ..analysis.rotation_detector import RotationSignal

class TableauExporter:
    def __init__(self, output_path: str = DATA_STORAGE_PATH):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def prepare_tier_view(self, 
                         market_data: pd.DataFrame, 
                         signals: List[RotationSignal]) -> pd.DataFrame:
        """
        Prepare tier analysis data for Tableau visualization
        
        Parameters:
            market_data (pd.DataFrame): Market data with tier assignments
            signals (List[RotationSignal]): Detected rotation signals
            
        Returns:
            pd.DataFrame: Processed data for Tableau
        """
        # Create base dataframe
        tableau_data = market_data.copy()
        
        # Add tier names for better visualization
        tier_names = {
            0: 'Top Tier',
            1: 'High Cap',
            2: 'Mid Cap',
            3: 'Lower Cap'
        }
        tableau_data['tier_name'] = tableau_data['tier'].map(tier_names)
        
        # Add signal information
        signal_df = pd.DataFrame([{
            'timestamp': s.timestamp,
            'from_tier': s.from_tier,
            'to_tier': s.to_tier,
            'confidence': s.confidence,
            'signal_type': s.signal_type
        } for s in signals])
        
        if not signal_df.empty:
            tableau_data = tableau_data.merge(
                signal_df,
                how='left',
                on='timestamp'
            )
        
        return tableau_data

    def prepare_flow_view(self, signals: List[RotationSignal]) -> pd.DataFrame:
        """
        Prepare capital flow visualization data
        
        Parameters:
            signals (List[RotationSignal]): Rotation signals
            
        Returns:
            pd.DataFrame: Flow data for Tableau
        """
        flow_data = []
        
        for signal in signals:
            flow_data.append({
                'timestamp': signal.timestamp,
                'from_tier': signal.from_tier,
                'to_tier': signal.to_tier,
                'confidence': signal.confidence,
                'flow_strength': signal.metrics.get('volume_factor', 0),
                'correlation': signal.metrics.get('correlation', 0)
            })
            
        return pd.DataFrame(flow_data)

    def prepare_performance_view(self, backtest_results: Dict) -> pd.DataFrame:
        """
        Prepare trading performance data
        
        Parameters:
            backtest_results (Dict): Results from backtesting
            
        Returns:
            pd.DataFrame: Performance data for Tableau
        """
        trades = backtest_results.get('trades', [])
        metrics = backtest_results.get('metrics', {})
        
        # Prepare trade history
        trade_data = pd.DataFrame([{
            'entry_time': t.entry_time,
            'exit_time': t.exit_time,
            'coin_id': t.coin_id,
            'tier': t.tier,
            'entry_price': t.entry_price,
            'exit_price': t.exit_price,
            'position_size': t.position_size,
            'pnl': t.pnl,
            'status': t.status
        } for t in trades])
        
        # Add performance metrics
        metric_data = pd.DataFrame([{
            'metric': key,
            'value': value
        } for key, value in metrics.items()])
        
        return trade_data, metric_data

    def export_for_tableau(self, 
                          market_data: pd.DataFrame,
                          signals: List[RotationSignal],
                          backtest_results: Optional[Dict] = None) -> Dict[str, str]:
        """
        Export all analysis data for Tableau
        
        Parameters:
            market_data (pd.DataFrame): Market data
            signals (List[RotationSignal]): Rotation signals
            backtest_results (Optional[Dict]): Backtesting results
            
        Returns:
            Dict[str, str]: Paths to exported files
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        exported_files = {}
        
        # Export tier analysis
        tier_data = self.prepare_tier_view(market_data, signals)
        tier_path = self.output_path / f'tier_analysis_{timestamp}.csv'
        tier_data.to_csv(tier_path, index=False)
        exported_files['tier_analysis'] = str(tier_path)
        
        # Export flow analysis
        flow_data = self.prepare_flow_view(signals)
        flow_path = self.output_path / f'flow_analysis_{timestamp}.csv'
        flow_data.to_csv(flow_path, index=False)
        exported_files['flow_analysis'] = str(flow_path)
        
        # Export performance data if available
        if backtest_results:
            trade_data, metric_data = self.prepare_performance_view(backtest_results)
            
            trade_path = self.output_path / f'trade_history_{timestamp}.csv'
            trade_data.to_csv(trade_path, index=False)
            exported_files['trade_history'] = str(trade_path)
            
            metric_path = self.output_path / f'performance_metrics_{timestamp}.csv'
            metric_data.to_csv(metric_path, index=False)
            exported_files['performance_metrics'] = str(metric_path)
        
        return exported_files

    def create_tableau_instructions(self) -> str:
        """
        Generate instructions for Tableau dashboard creation
        
        Returns:
            str: Instructions for creating visualizations
        """
        instructions = """
        Tableau Dashboard Setup Instructions:
        
        1. Tier Analysis Dashboard:
           - Create a scatter plot of market cap vs. volume
           - Color code by tier_name
           - Size points by volume_to_mcap ratio
           - Add tier transition arrows using flow analysis data
        
        2. Capital Flow Dashboard:
           - Create a Sankey diagram using flow analysis data
           - Use confidence for flow width
           - Color code by flow strength
        
        3. Performance Dashboard:
           - Create trade history timeline
           - Add PnL distribution by tier
           - Display key performance metrics
           - Add tier performance comparison
        
        4. Recommended Calculations:
           - Tier Performance: AVG([pnl]) by [tier_name]
           - Flow Strength: SUM([flow_strength]) by [from_tier], [to_tier]
           - Success Rate: COUNT([status]='closed') / COUNT([status])
        """
        
        return instructions
