import pandas as pd
import logging
from pathlib import Path
from typing import List, Type
from .base_strategy import BaseStrategy
from .sma_crossover import SMACrossoverStrategy
from .rsi_mean_reversion import RSIMeanReversionStrategy
from .backtester import Backtester
from ..data.collector import ForexDataCollector
import json

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyRunner:
    def __init__(self, data_collector: ForexDataCollector):
        """
        Strategy Runner for managing strategy execution and optimization
        
        Args:
            data_collector: Instance of ForexDataCollector
        """
        self.data_collector = data_collector
        self.strategies: List[Type[BaseStrategy]] = [
            SMACrossoverStrategy,
            RSIMeanReversionStrategy
        ]
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
    def run_optimization(self, data: pd.DataFrame) -> dict:
        """
        Run optimization for all strategies
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with optimal parameters for each strategy
        """
        optimal_params = {}
        
        try:
            # Optimize SMA Crossover
            sma_strategy = SMACrossoverStrategy(data.copy())
            sma_params = sma_strategy.optimize_parameters(
                short_range=(10, 50),
                long_range=(100, 200)
            )
            optimal_params['SMACrossoverStrategy'] = sma_params
            
            # Optimize RSI Mean Reversion
            rsi_strategy = RSIMeanReversionStrategy(data.copy())
            rsi_params = rsi_strategy.optimize_parameters(
                rsi_range=(10, 20),
                oversold_range=(20, 40),
                overbought_range=(60, 80)
            )
            optimal_params['RSIMeanReversionStrategy'] = rsi_params
            
            # Save optimization results
            self._save_optimization_results(optimal_params)
            
            return optimal_params
            
        except Exception as e:
            logger.error(f"Error during optimization: {str(e)}")
            raise
            
    def run_backtest(self, data: pd.DataFrame, 
                    optimal_params: dict = None) -> str:
        """
        Run backtest with optimal parameters
        
        Args:
            data: DataFrame with OHLCV data
            optimal_params: Dictionary with optimal parameters for each strategy
            
        Returns:
            Path to backtest report
        """
        try:
            backtester = Backtester(data, self.strategies)
            results = backtester.run_backtest(
                strategy_params=optimal_params,
                initial_capital=100000
            )
            
            # Generate and save report
            report_path = backtester.generate_report()
            
            # Log best strategy
            best_strategy = backtester.get_best_strategy()
            logger.info(f"Best performing strategy: {best_strategy}")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Error during backtesting: {str(e)}")
            raise
            
    def _save_optimization_results(self, results: dict):
        """
        Save optimization results to file
        """
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.results_dir / f"optimization_results_{timestamp}.json"
        
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=4)
            
        logger.info(f"Optimization results saved to {file_path}")
        
def main():
    """
    Main function to run strategy optimization and backtesting
    """
    try:
        # Initialize data collector
        collector = ForexDataCollector()
        
        # Get historical data
        data = collector.fetch_intraday_data()
        
        # Initialize strategy runner
        runner = StrategyRunner(collector)
        
        # Run optimization
        logger.info("Starting strategy optimization...")
        optimal_params = runner.run_optimization(data)
        
        # Run backtest with optimal parameters
        logger.info("Starting backtest with optimal parameters...")
        report_path = runner.run_backtest(data, optimal_params)
        
        logger.info(f"Backtest report generated at: {report_path}")
        
    except Exception as e:
        logger.error(f"Error in strategy runner: {str(e)}")
        raise
        
if __name__ == "__main__":
    main()
