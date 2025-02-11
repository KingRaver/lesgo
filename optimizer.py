import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..config.settings import ANALYSIS_PARAMS, TIER_PARAMS
from .backtest_engine import BacktestEngine
from ..analysis.rotation_detector import RotationDetector

@dataclass
class OptimizationResult:
    parameters: Dict
    performance: Dict
    confidence: float
    tier_adjustments: Dict[int, Dict[str, float]]

class ParameterOptimizer:
    def __init__(self, backtest_engine: BacktestEngine):
        self.backtest_engine = backtest_engine
        self.parameter_ranges = {
            'volume_threshold': np.arange(1.5, 3.0, 0.25),
            'correlation_threshold': np.arange(0.5, 0.9, 0.1),
            'position_size_multiplier': np.arange(0.05, 0.2, 0.025),
            'min_confidence': np.arange(0.4, 0.8, 0.1)
        }
        
    def generate_parameter_combinations(self) -> List[Dict]:
        """Generate all possible parameter combinations"""
        combinations = []
        
        for vol_thresh in self.parameter_ranges['volume_threshold']:
            for corr_thresh in self.parameter_ranges['correlation_threshold']:
                for pos_size in self.parameter_ranges['position_size_multiplier']:
                    for min_conf in self.parameter_ranges['min_confidence']:
                        params = {
                            'volume_threshold': float(vol_thresh),
                            'correlation_threshold': float(corr_thresh),
                            'position_size_multiplier': float(pos_size),
                            'min_confidence': float(min_conf)
                        }
                        combinations.append(params)
        
        return combinations

    def optimize_tier_parameters(self, 
                               historical_data: pd.DataFrame,
                               detector: RotationDetector) -> OptimizationResult:
        """
        Optimize parameters for each tier
        
        Parameters:
            historical_data (pd.DataFrame): Historical market data
            detector (RotationDetector): Rotation detector instance
            
        Returns:
            OptimizationResult: Optimized parameters and performance
        """
        combinations = self.generate_parameter_combinations()
        best_result = None
        best_performance = float('-inf')
        
        for params in combinations:
            # Update detector parameters
            detector.volume_threshold = params['volume_threshold']
            detector.correlation_threshold = params['correlation_threshold']
            detector.min_confidence = params['min_confidence']
            
            # Generate signals with current parameters
            signals = detector.generate_rotation_signals(historical_data)
            
            # Run backtest
            result = self.backtest_engine.run_backtest(historical_data, signals)
            
            # Score this parameter set
            performance_score = self._calculate_parameter_score(result)
            
            if performance_score > best_performance:
                best_performance = performance_score
                
                # Calculate tier-specific adjustments
                tier_adjustments = self._calculate_tier_adjustments(result['metrics'])
                
                best_result = OptimizationResult(
                    parameters=params,
                    performance=result['metrics'],
                    confidence=performance_score,
                    tier_adjustments=tier_adjustments
                )
        
        return best_result

    def _calculate_parameter_score(self, backtest_result: Dict) -> float:
        """
        Calculate overall score for parameter set
        
        Parameters:
            backtest_result (Dict): Backtest performance metrics
            
        Returns:
            float: Parameter set score
        """
        metrics = backtest_result['metrics']
        
        # Weight different performance aspects
        weights = {
            'win_rate': 0.3,
            'sharpe_ratio': 0.3,
            'total_return': 0.2,
            'max_drawdown': 0.2
        }
        
        score_components = [
            metrics.get('win_rate', 0) * weights['win_rate'],
            metrics.get('sharpe_ratio', 0) * weights['sharpe_ratio'],
            metrics.get('total_return', 0) * weights['total_return'],
            (1 + metrics.get('max_drawdown', -1)) * weights['max_drawdown']  # Convert drawdown to positive score
        ]
        
        return float(np.mean(score_components))

    def _calculate_tier_adjustments(self, metrics: Dict) -> Dict[int, Dict[str, float]]:
        """
        Calculate tier-specific parameter adjustments
        
        Parameters:
            metrics (Dict): Performance metrics by tier
            
        Returns:
            Dict[int, Dict[str, float]]: Tier-specific adjustments
        """
        adjustments = {}
        
        for tier in range(4):
            tier_return = metrics.get(f'tier_{tier}_return', 0)
            tier_trades = metrics.get(f'tier_{tier}_trades', 0)
            
            # Calculate adjustment factors based on tier performance
            adjustments[tier] = {
                'position_size': 1.0 - (tier * 0.15),  # Reduce size for lower tiers
                'entry_threshold': 1.0 + (tier * 0.1),  # Higher threshold for lower tiers
                'stop_loss': 1.0 + (tier * 0.2),       # Wider stops for lower tiers
                'take_profit': 1.0 + (tier * 0.3)      # Higher targets for lower tiers
            }
            
            # Adjust based on tier performance
            if tier_trades > 0:
                performance_factor = max(min(1 + tier_return, 1.5), 0.5)
                for key in adjustments[tier]:
                    adjustments[tier][key] *= performance_factor
        
        return adjustments

    def apply_optimization_results(self, 
                                 optimization_result: OptimizationResult,
                                 detector: RotationDetector,
                                 backtest_engine: BacktestEngine) -> None:
        """
        Apply optimized parameters to detector and backtest engine
        
        Parameters:
            optimization_result (OptimizationResult): Optimization results
            detector (RotationDetector): Rotation detector instance
            backtest_engine (BacktestEngine): Backtest engine instance
        """
        # Update detector parameters
        detector.volume_threshold = optimization_result.parameters['volume_threshold']
        detector.correlation_threshold = optimization_result.parameters['correlation_threshold']
        detector.min_confidence = optimization_result.parameters['min_confidence']
        
        # Update position sizing in backtest engine
        backtest_engine.max_position_size = optimization_result.parameters['position_size_multiplier']
        
        # Apply tier-specific adjustments
        for tier, adjustments in optimization_result.tier_adjustments.items():
            TIER_PARAMS[tier].update({
                'position_size_adjustment': adjustments['position_size'],
                'stop_loss_multiplier': TIER_PARAMS[tier]['stop_loss_multiplier'] * adjustments['stop_loss'],
                'take_profit_multiplier': TIER_PARAMS[tier]['take_profit_multiplier'] * adjustments['take_profit']
            })

    def get_optimization_summary(self, optimization_result: OptimizationResult) -> str:
        """
        Generate human-readable optimization summary
        
        Parameters:
            optimization_result (OptimizationResult): Optimization results
            
        Returns:
            str: Summary of optimization results
        """
        summary = []
        summary.append("Parameter Optimization Results:")
        summary.append("\nOptimal Parameters:")
        for param, value in optimization_result.parameters.items():
            summary.append(f"- {param}: {value:.3f}")
        
        summary.append("\nPerformance Metrics:")
        for metric, value in optimization_result.performance.items():
            if isinstance(value, (int, float)):
                summary.append(f"- {metric}: {value:.3f}")
        
        summary.append("\nTier-Specific Adjustments:")
        for tier, adjustments in optimization_result.tier_adjustments.items():
            summary.append(f"\nTier {tier}:")
            for param, value in adjustments.items():
                summary.append(f"- {param}: {value:.3f}")
        
        return "\n".join(summary)
