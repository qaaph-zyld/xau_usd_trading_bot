import pandas as pd
import logging
from pathlib import Path
from typing import List, Type, Dict
from .base_strategy import BaseStrategy
from .sma_crossover import SMACrossoverStrategy
from .rsi_mean_reversion import RSIMeanReversionStrategy
from .backtester import Backtester
from ..data.collector import ForexDataCollector
from ..risk_management.risk_manager import RiskManager
from ..risk_management.money_manager import MoneyManager, AllocationLimits
import json

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyRunner:
    def __init__(self, data_collector: ForexDataCollector, initial_capital: float = 100000):
        """
        Strategy Runner for managing strategy execution and optimization
        
        Args:
            data_collector: Instance of ForexDataCollector
            initial_capital: Initial trading capital
        """
        self.data_collector = data_collector
        self.initial_capital = initial_capital
        self.strategies: List[Type[BaseStrategy]] = [
            SMACrossoverStrategy,
            RSIMeanReversionStrategy
        ]
        
        # Initialize risk management components
        self.risk_manager = RiskManager(
            initial_capital=initial_capital,
            max_portfolio_risk=0.05,
            max_correlation=0.7,
            max_daily_trades=3,
            max_drawdown=0.15
        )
        
        allocation_limits = AllocationLimits(
            max_single_position=0.1,
            max_daily_risk=0.05,
            max_sector_exposure=0.2,
            max_drawdown=0.15
        )
        
        self.money_manager = MoneyManager(
            initial_capital=initial_capital,
            allocation_limits=allocation_limits
        )
        
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
    def run_optimization(self, data: pd.DataFrame) -> dict:
        """
        Run optimization for all strategies with risk management
        """
        optimal_params = {}
        
        try:
            # Calculate correlation matrix for risk management
            returns = data['close'].pct_change().dropna()
            correlation_matrix = returns.expanding().corr()
            
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
        Run backtest with optimal parameters and risk management
        """
        try:
            # Calculate correlation matrix
            returns = data['close'].pct_change().dropna()
            correlation_matrix = returns.expanding().corr()
            
            backtester = Backtester(data, self.strategies)
            results = backtester.run_backtest(
                strategy_params=optimal_params,
                initial_capital=self.initial_capital
            )
            
            # Apply risk management to results
            for strategy_name, result in results.items():
                strategy = result['strategy']
                
                # Calculate risk metrics
                returns = pd.Series(strategy.capital).pct_change().dropna()
                risk_metrics = self.risk_manager.calculate_risk_metrics(returns)
                result['risk_metrics'] = risk_metrics.__dict__
                
                # Simulate money management
                positions = strategy.positions[strategy.positions != 0]
                for timestamp, position in positions.items():
                    symbol = 'XAU/USD'  # For this specific bot
                    price = data.loc[timestamp, 'close']
                    
                    if position > 0:
                        # Simulate long position with risk management
                        can_allocate, reason = self.money_manager.can_allocate(
                            symbol=symbol,
                            risk_amount=abs(position) * price * 0.02,  # 2% risk
                            sector='Precious Metals'
                        )
                        
                        if not can_allocate:
                            strategy.positions.loc[timestamp] = 0
                            logger.info(f"Position rejected by money manager: {reason}")
            
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
    Main function to run strategy optimization and backtesting with risk management
    """
    try:
        # Initialize data collector
        collector = ForexDataCollector()
        
        # Get historical data
        data = collector.fetch_intraday_data()
        
        # Initialize strategy runner with risk management
        runner = StrategyRunner(collector)
        
        # Run optimization
        logger.info("Starting strategy optimization...")
        optimal_params = runner.run_optimization(data)
        
        # Run backtest with optimal parameters and risk management
        logger.info("Starting backtest with optimal parameters...")
        report_path = runner.run_backtest(data, optimal_params)
        
        logger.info(f"Backtest report generated at: {report_path}")
        
    except Exception as e:
        logger.error(f"Error in strategy runner: {str(e)}")
        raise
        
if __name__ == "__main__":
    main()
