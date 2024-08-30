import asyncio
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pandas as pd

from apps.trading_bot.okx_funding_fee_arbitrage import close_positions, open_positions
from apps.trading_bot.okx_funding_fee_arbitrage.initialize_account import (
    set_account_configs,
    set_market_leverages,
)
from apps.trading_bot.okx_funding_fee_arbitrage.logger import Logger
from apps.trading_bot.okx_funding_fee_arbitrage.report_cash_flow_and_fee_balance import (
    get_cash_flow_df_and_fee_balance_df,
)
from apps.trading_bot.okx_funding_fee_arbitrage.report_tickers import (
    get_discount_rate_map,
    get_tickers_df,
)
from modules.strategy.base_strategy import BaseStrategy
from modules.strategy.strategy_utils import StrategyUtils


class OKXFundingFeeArbitrage(BaseStrategy):
    async def initialize_account(self):
        """
        Prerequisite:
        - 必須手動將帳戶模式切換為`跨幣種保證金模式`
        """
        async with StrategyUtils.okx_context_manager(
            "./apps/trading_bot/.okx-gocreating3.demo.env", sandbox_mode=True
        ) as exchange:
            await set_account_configs(exchange)
            print("Account configs ok.")
            await set_market_leverages(
                exchange, max_margin_leverage=5, max_perp_leverage=10
            )
            print("Market leverages ok.")

    async def report_tickers(self):
        float_format = "{:.16g}".format  # remove scientific notation
        async with StrategyUtils.okx_context_manager(
            "./apps/trading_bot/.okx-gocreating3.env"
        ) as exchange:
            now_datetime = datetime.now(tz=timezone.utc)
            tickers_df_path = f"./apps/trading_bot/okx_funding_fee_arbitrage/build/tickers/{now_datetime.isoformat()}.csv"
            StrategyUtils.ensure_directory(
                "./apps/trading_bot/okx_funding_fee_arbitrage/build/tickers"
            )
            discount_rate_map = await get_discount_rate_map(
                source="https://www.okx.com/priapi/v5/public/discount-rate"
            )
            tickers_df = await get_tickers_df(
                exchange=exchange,
                discount_rate_map=discount_rate_map,
                window_size=21,
            )
            tickers_df.to_csv(tickers_df_path, float_format=float_format, index=False)

    async def open_positions(
        self,
        base: str,
        max_single_side_position_notional_str: str = "100",
        sandbox_mode: bool = True,
    ):
        logger = Logger(name="activities")
        logger.enable_stdout_handler()
        logger.enable_file_handler(
            root_dir="./apps/trading_bot/okx_funding_fee_arbitrage/build/activities"
        )
        if sandbox_mode:
            cm = StrategyUtils.okx_context_manager(
                "./apps/trading_bot/.okx-gocreating3.demo.env", sandbox_mode=True
            )
        else:
            cm = StrategyUtils.okx_context_manager(
                "./apps/trading_bot/.okx-gocreating3.env"
            )
        async with cm as exchange:
            context = await open_positions.get_context(
                logger=logger,
                exchange=exchange,
                side="long_margin_short_perp",
                # side="short_margin_long_perp",
                base=base,
                quote="USDT",
            )
            done_tasks, _pending_tasks = await asyncio.wait(
                [
                    asyncio.create_task(
                        open_positions.watch(exchange=exchange, context=context)
                    ),
                    asyncio.create_task(
                        open_positions.place_orders(
                            exchange=exchange,
                            context=context,
                            max_single_side_position_notional=Decimal(
                                max_single_side_position_notional_str
                            ),
                        )
                    ),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            done_task = list(done_tasks)[0]
            try:
                done_task.result()
            except Exception as e:
                context.logger.error(f"Unknown error", exc_info=e)

    async def close_positions(self, base: str, sandbox_mode: bool = True):
        logger = Logger(name="activities")
        logger.enable_stdout_handler()
        logger.enable_file_handler(
            root_dir="./apps/trading_bot/okx_funding_fee_arbitrage/build/activities"
        )
        if sandbox_mode:
            cm = StrategyUtils.okx_context_manager(
                "./apps/trading_bot/.okx-gocreating3.demo.env", sandbox_mode=True
            )
        else:
            cm = StrategyUtils.okx_context_manager(
                "./apps/trading_bot/.okx-gocreating3.env"
            )
        async with cm as exchange:
            context = await close_positions.get_context(
                logger=logger,
                exchange=exchange,
                side="close_long_margin_short_perp",
                base=base,
                quote="USDT",
            )
            done_tasks, _pending_tasks = await asyncio.wait(
                [
                    asyncio.create_task(
                        close_positions.watch(exchange=exchange, context=context)
                    ),
                    asyncio.create_task(
                        close_positions.place_orders(exchange=exchange, context=context)
                    ),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            done_task = list(done_tasks)[0]
            try:
                done_task.result()
            except Exception as e:
                context.logger.error(f"Unknown error", exc_info=e)

    async def report_cash_flow_and_fee_balance(self):
        since_datetime = datetime(2024, 3, 11, tzinfo=timezone.utc)
        until_datetime = datetime.max.replace(tzinfo=timezone.utc)
        now_datetime = datetime.now(tz=timezone.utc)
        window_size = timedelta(days=1)

        float_format = "{:.16g}".format  # remove scientific notation

        async with StrategyUtils.okx_context_manager(
            "./apps/trading_bot/.okx-gocreating3.env"
        ) as exchange:
            StrategyUtils.ensure_directory(
                "./apps/trading_bot/okx_funding_fee_arbitrage/build/daily_cash_flow"
            )
            StrategyUtils.ensure_directory(
                "./apps/trading_bot/okx_funding_fee_arbitrage/build/daily_fee_balance"
            )

            current_window_start_time = since_datetime

            while current_window_start_time < until_datetime:
                current_window_end_time = current_window_start_time + window_size
                current_window_start_time_str = current_window_start_time.isoformat()
                current_window_end_time_str = min(
                    current_window_end_time, now_datetime
                ).isoformat()
                current_cash_flow_df_path = f"./apps/trading_bot/okx_funding_fee_arbitrage/build/daily_cash_flow/from_{current_window_start_time_str}_to_{current_window_end_time_str}.csv"
                since_fee_balance_df_path = f"./apps/trading_bot/okx_funding_fee_arbitrage/build/daily_fee_balance/until_{current_window_start_time_str}.csv"
                current_fee_balance_df_path = f"./apps/trading_bot/okx_funding_fee_arbitrage/build/daily_fee_balance/until_{current_window_end_time_str}.csv"

                if not os.path.exists(current_cash_flow_df_path) or not os.path.exists(
                    current_fee_balance_df_path
                ):
                    if os.path.exists(since_fee_balance_df_path):
                        since_fee_balance_df = pd.read_csv(since_fee_balance_df_path)
                    else:
                        since_fee_balance_df = pd.DataFrame(
                            columns=["balance", "currency"]
                        )
                    (
                        current_cash_flow_df,
                        current_fee_balance_df,
                    ) = await get_cash_flow_df_and_fee_balance_df(
                        exchange=exchange,
                        account="trading",
                        since_fee_balance_df=since_fee_balance_df,
                        since_datetime=current_window_start_time,
                        until_datetime=current_window_end_time,
                    )
                    if current_cash_flow_df is None or current_fee_balance_df is None:
                        break
                    current_cash_flow_df.to_csv(
                        current_cash_flow_df_path,
                        float_format=float_format,
                        index=False,
                        columns=[
                            "timestamp",
                            "datetime",
                            "balance",
                            "balance_change",
                            "currency",
                            "summary",
                        ],
                    )
                    current_fee_balance_df.to_csv(
                        current_fee_balance_df_path,
                        float_format=float_format,
                        index=False,
                        columns=[
                            "balance",
                            "currency",
                        ],
                    )

                current_window_start_time = current_window_end_time

    async def report_pnl_breakdown(self):
        since_datetime = datetime(2024, 3, 11, tzinfo=timezone.utc)
        until_datetime = datetime.max.replace(tzinfo=timezone.utc)
        now_datetime = datetime.now(tz=timezone.utc)
        window_size = timedelta(days=1)

        current_window_start_time = since_datetime

        cash_flow_df = pd.DataFrame()
        while current_window_start_time < until_datetime:
            current_window_end_time = current_window_start_time + window_size
            current_window_start_time_str = current_window_start_time.isoformat()
            current_window_end_time_str = min(
                current_window_end_time, now_datetime
            ).isoformat()
            current_window_cash_flow_df_path = f"./apps/trading_bot/okx_funding_fee_arbitrage/build/daily_cash_flow/from_{current_window_start_time_str}_to_{current_window_end_time_str}.csv"
            if not os.path.exists(current_window_cash_flow_df_path):
                break
            # fee_balance_df_path = f"./apps/trading_bot/okx_funding_fee_arbitrage/build/daily_fee_balance/until_{current_window_end_time_str}.csv"
            current_window_cash_flow_df = pd.read_csv(current_window_cash_flow_df_path)
            cash_flow_df = pd.concat([cash_flow_df, current_window_cash_flow_df])
            current_window_start_time = current_window_end_time

        result_df = pd.DataFrame(
            columns=[
                "currency",
                "contribution_count",
                "balance_change_last_cumulative_sum",
                "balance_change_min_cumulative_sum",
                "balance_change_max_cumulative_sum",
                "balance_change_per_contribution",
            ]
        )
        grouped = cash_flow_df[
            cash_flow_df["summary"].str.startswith("funding fee expense/income")
        ].groupby("summary")
        for summary, cash_flow_by_summary_df in grouped:
            currency = summary.split("(")[1].split("-")[0]
            contribution_count = len(cash_flow_by_summary_df)
            cum_sum = cash_flow_by_summary_df["balance_change"].cumsum()
            result_df.loc[len(result_df)] = {
                "currency": currency,
                "contribution_count": contribution_count,
                "balance_change_last_cumulative_sum": cum_sum.iloc[-1],
                "balance_change_min_cumulative_sum": cum_sum.min(),
                "balance_change_max_cumulative_sum": cum_sum.max(),
                "balance_change_per_contribution": cum_sum.iloc[-1]
                / contribution_count,
            }
        result_df.sort_values(
            by=["balance_change_per_contribution"], ascending=[False]
        ).to_csv(
            f"./apps/trading_bot/okx_funding_fee_arbitrage/build/pnl_breakdown.csv",
            index=False,
        )
