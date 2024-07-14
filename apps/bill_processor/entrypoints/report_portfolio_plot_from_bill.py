import asyncio
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator
from matplotlib.ticker import FuncFormatter


@contextmanager
def portfolio_plot(subplots_kwargs: Optional[dict] = None):
    merged_subplots_kwargs = {
        "nrows": 2,
        "ncols": 1,
        "sharex": True,
    }
    if subplots_kwargs is not None:
        merged_subplots_kwargs.update(subplots_kwargs)

    def comma_formatter(x, pos):
        return f"{x:,.0f}"

    custom_color_cycle = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    plt.rcParams["axes.prop_cycle"] = plt.cycler(color=custom_color_cycle)
    fig, axs = plt.subplots(**merged_subplots_kwargs)
    axs[-1].tick_params(axis="x", rotation=30)
    ax_settlement, ax_inventory = axs
    ax_inventory.xaxis.set_major_formatter(DateFormatter("%Y-%m"))
    ax_inventory.yaxis.get_major_formatter().set_scientific(False)
    ax_settlement.yaxis.get_major_formatter().set_scientific(False)
    ax_inventory.yaxis.set_major_formatter(FuncFormatter(comma_formatter))
    ax_inventory.xaxis.set_major_locator(MonthLocator())
    ax_settlement.yaxis.set_major_formatter(FuncFormatter(comma_formatter))
    ax_settlement.set_ylabel("Settlement Amount ($)")
    ax_settlement.axhline(0, color="gray", linestyle="--")
    ax_inventory.set_ylabel("Inventory Amount (Shares)")
    ax_inventory.grid(True)
    yield fig, axs
    plt.close()


async def plot_equity_curve(symbol: str, symbol_df: pd.DataFrame, ax: plt.Axes):
    grouped_by_time = symbol_df.groupby(["_utc_time"])
    aggregated_df = (grouped_by_time["amount_change"].sum().reset_index()).sort_values(
        by=["_utc_time"], ascending=[True]
    )
    aggregated_df["equity_amount"] = aggregated_df["amount_change"].cumsum()
    ax.bar(
        aggregated_df["_utc_time"],
        aggregated_df["amount_change"],
        label=f"{symbol} (change)",
        width=1,
    )
    ax.plot(
        aggregated_df["_utc_time"],
        aggregated_df["equity_amount"],
        label=f"{symbol} (balance)",
        linewidth=0.8,
        marker=".",
        markersize=2,
        linestyle="dotted",
    )


async def plot_portfolio(
    portofolio_name: str,
    settlement_symbol: str,
    session_reference_set: set[str],
    bill_df: pd.DataFrame,
):
    portofolio_bill_df = bill_df[
        bill_df["session_reference"].isin(session_reference_set)
    ]
    settlement_bill_df = portofolio_bill_df[
        portofolio_bill_df["symbol"] == settlement_symbol
    ]
    inventory_bill_df = portofolio_bill_df[
        portofolio_bill_df["symbol"] != settlement_symbol
    ]
    x_min = inventory_bill_df["_utc_time"].min()
    x_max = inventory_bill_df["_utc_time"].max() + relativedelta(months=1)
    x_delta = x_max - x_min

    with portfolio_plot(
        subplots_kwargs={"figsize": (max(4, x_delta.days / 80), 6)}
    ) as (
        fig,
        (ax_settlement, ax_inventory),
    ):
        fig.suptitle(f"{portofolio_name}")

        await plot_equity_curve(settlement_symbol, settlement_bill_df, ax_settlement)
        grouped_by_symbol = inventory_bill_df.groupby(["symbol"])
        for (symbol,), symbol_df in grouped_by_symbol:
            await plot_equity_curve(symbol, symbol_df, ax_inventory)

        ax_inventory.set_xlim(
            datetime(x_min.year, x_min.month, 1), datetime(x_max.year, x_max.month, 1)
        )

        ax_settlement.legend(loc="upper left", bbox_to_anchor=(1.04, 1))
        ax_inventory.legend(loc="upper left", bbox_to_anchor=(1.04, 1))
        fig.savefig(
            f"apps/bill_processor/build/portofolio_{portofolio_name}.png",
            bbox_inches="tight",
            dpi=300,
        )


async def plot_portfolios(bill_df: pd.DataFrame):
    grouped_by_symbol = bill_df.groupby(["symbol"])
    for (symbol,), symbol_df in grouped_by_symbol:
        session_reference_set = set(symbol_df["session_reference"].unique())
        await plot_portfolio(
            portofolio_name=symbol,
            settlement_symbol="TWD",
            session_reference_set=session_reference_set,
            bill_df=bill_df,
        )


async def main():
    input_root_dir_path = "apps/bill_processor/build"
    file_path = os.path.join(input_root_dir_path, "bill.csv")
    bill_df = pd.read_csv(file_path)
    bill_df["_utc_time"] = pd.to_datetime(bill_df["utc_time"])
    await plot_portfolios(bill_df)
    # await plot_portfolio(
    #     portofolio_name="隨便亂抓",
    #     settlement_symbol="TWD",
    #     session_reference_set={
    #         "ef329618-5d0a-419b-9ca4-2d1e89f06dcf",
    #         "c0460277-5c37-4164-b9a8-9e2255075850",
    #         "17ca8776-62fd-4d59-a706-8a1252e9eb7e",
    #         "1b8982e6-7182-43ba-87d8-58405cfa977f",
    #     },
    #     bill_df=bill_df,
    # )


asyncio.run(main())
