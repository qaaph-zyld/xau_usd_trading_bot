import pandas as pd
import numpy as np
from typing import Dict, Any, List, Type
from .base_strategy import BaseStrategy
import logging
from pathlib import Path
import json
import matplotlib.pyplot as plt
from datetime import datetime

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, data: pd.DataFrame, strategies: List[Type[BaseStrategy]]):
        """
        Backtesting framework for comparing multiple strategies
        
        Args:
            data: DataFrame with OHLCV data
            strategies: List of strategy classes to test
        """
        self.data = data
        self.strategies = strategies
        self.results = {}
        self.output_dir = Path("results/backtests")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run_backtest(self, 
                    strategy_params: Dict[str, Dict] = None,
                    initial_capital: float = 100000) -> Dict[str, Any]:
        """
        Run backtest for all strategies
        
        Args:
            strategy_params: Dictionary of strategy parameters
            initial_capital: Starting capital for each strategy
            
        Returns:
            Dictionary of backtest results
        """
        try:
            for strategy_class in self.strategies:
                strategy_name = strategy_class.__name__
                logger.info(f"Running backtest for {strategy_name}")
                
                # Initialize strategy with parameters if provided
                params = strategy_params.get(strategy_name, {}) if strategy_params else {}
                strategy = strategy_class(self.data.copy(), 
                                       initial_capital=initial_capital,
                                       **params)
                
                # Run backtest
                results = strategy.backtest()
                self.results[strategy_name] = {
                    'strategy': strategy,
                    'metrics': results
                }
                
            return self.results
            
        except Exception as e:
            logger.error(f"Error during backtesting: {str(e)}")
            raise
            
    def generate_report(self, save_plots: bool = True) -> str:
        """
        Generate comprehensive backtest report
        
        Returns:
            Path to saved report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.output_dir / f"report_{timestamp}"
        report_dir.mkdir(exist_ok=True)
        
        # Save performance metrics
        metrics_data = {}
        for strategy_name, result in self.results.items():
            metrics_data[strategy_name] = result['metrics']
            
            # Save strategy plot
            if save_plots:
                plot_path = report_dir / f"{strategy_name}_performance.png"
                result['strategy'].plot_performance(str(plot_path))
        
        # Save metrics to JSON
        metrics_path = report_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=4)
        
        # Generate comparison plots
        self._generate_comparison_plots(report_dir)
        
        return str(report_dir)
    
    def _generate_comparison_plots(self, report_dir: Path):
        """
        Generate plots comparing all strategies
        """
        plt.figure(figsize=(12, 6))
        
        for strategy_name, result in self.results.items():
            strategy = result['strategy']
            plt.plot(strategy.data.index, 
                    strategy.capital, 
                    label=strategy_name)
        
        plt.title('Strategy Comparison - Portfolio Value')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(report_dir / "strategy_comparison.png")
        plt.close()
        
    def get_best_strategy(self, metric: str = 'sharpe_ratio') -> str:
        """
        Get the best performing strategy based on specified metric
        
        Args:
            metric: Performance metric to compare
            
        Returns:
            Name of best performing strategy
        """
        best_value = float('-inf')
        best_strategy = None
        
        for strategy_name, result in self.results.items():
            current_value = result['metrics'][metric]
            if current_value > best_value:
                best_value = current_value
                best_strategy = strategy_name
                
        return best_strategy
