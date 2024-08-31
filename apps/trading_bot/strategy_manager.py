from apps.trading_bot.okx_funding_fee_arbitrage.strategy import OKXFundingFeeArbitrage
from modules.strategy.strategy_manager import StrategyManager

strategy_manager = StrategyManager()
strategy_manager.register_strategy(OKXFundingFeeArbitrage())
strategy_manager.run_http_server()
