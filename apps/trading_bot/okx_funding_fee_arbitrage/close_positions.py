import asyncio
import json
from decimal import Decimal
from typing import Literal, Optional

import ccxt.pro
from pydantic import BaseModel

from apps.trading_bot.okx_funding_fee_arbitrage.logger import Logger
from apps.trading_bot.okx_funding_fee_arbitrage.number import decimalize

Side = Literal["close_long_margin_short_perp", "close_short_margin_long_perp"]


class Context(BaseModel, arbitrary_types_allowed=True):
    logger: Logger

    side: Side

    margin_market_unified_symbol: str
    margin_market: dict
    _margin_market_order_book: Optional[dict] = None
    margin_market_best_ask_price: Optional[Decimal] = None
    margin_market_best_bid_price: Optional[Decimal] = None
    margin_market_max_order_amount: Optional[Decimal] = None
    margin_market_base_token_balance_amount: Decimal

    perp_market_unified_symbol: str
    perp_market: dict
    _perp_market_order_book: Optional[dict] = None
    perp_market_best_ask_price: Optional[Decimal] = None
    perp_market_best_bid_price: Optional[Decimal] = None
    perp_market_max_order_amount: Optional[Decimal] = None
    perp_market_contract_position_amount: Decimal

    cross_market_spread: Optional[Decimal] = None
    cross_market_last_spread: Optional[Decimal] = None
    cross_market_is_converging: Optional[bool] = None

    @property
    def margin_market_order_book(self) -> Optional[dict]:
        return self._margin_market_order_book

    @margin_market_order_book.setter
    def margin_market_order_book(self, value):
        self._margin_market_order_book = value
        self.margin_market_best_ask_price = decimalize(
            self.margin_market_order_book["asks"][0][0]
        )
        self.margin_market_best_bid_price = decimalize(
            self.margin_market_order_book["bids"][0][0]
        )
        if not self.is_order_books_ready:
            return
        self._update_spreads()

    @property
    def perp_market_order_book(self) -> Optional[dict]:
        return self._perp_market_order_book

    @perp_market_order_book.setter
    def perp_market_order_book(self, value):
        self._perp_market_order_book = value
        self.perp_market_best_ask_price = decimalize(
            self.perp_market_order_book["asks"][0][0]
        )
        self.perp_market_best_bid_price = decimalize(
            self.perp_market_order_book["bids"][0][0]
        )
        if not self.is_order_books_ready:
            return
        self._update_amounts()
        self._update_spreads()

    def _update_amounts(self):
        if self.side == "close_long_margin_short_perp":
            self.margin_market_max_order_amount = decimalize(
                self.margin_market_order_book["bids"][0][1]
            )
            self.perp_market_max_order_amount = decimalize(
                self.perp_market_order_book["asks"][0][1]
            )
        elif self.side == "close_short_margin_long_perp":
            self.margin_market_max_order_amount = decimalize(
                self.margin_market_order_book["asks"][0][1]
            )
            self.perp_market_max_order_amount = decimalize(
                self.perp_market_order_book["bids"][0][1]
            )

    def _update_spreads(self):
        self.cross_market_last_spread = self.cross_market_spread

        if self.side == "close_long_margin_short_perp":
            self.cross_market_spread = abs(
                (self.perp_market_best_ask_price - self.margin_market_best_bid_price)
                / self.margin_market_best_bid_price
            )
        elif self.side == "close_short_margin_long_perp":
            self.cross_market_spread = abs(
                (self.margin_market_best_ask_price - self.perp_market_best_bid_price)
                / self.perp_market_best_bid_price
            )

        if self.cross_market_last_spread is None:
            return

        if self.cross_market_spread > self.cross_market_last_spread:
            self.cross_market_is_converging = False
        elif self.cross_market_spread < self.cross_market_last_spread:
            self.cross_market_is_converging = True

    @property
    def is_order_books_ready(self) -> bool:
        if self.margin_market_order_book is None or self.perp_market_order_book is None:
            return False
        if (
            len(self.margin_market_order_book["bids"]) == 0
            or len(self.margin_market_order_book["asks"]) == 0
            or len(self.perp_market_order_book["bids"]) == 0
            or len(self.perp_market_order_book["asks"]) == 0
        ):
            return False
        return True

    @property
    def is_spread_ready(self) -> bool:
        if self.cross_market_is_converging is None:
            return False
        return True

    def report_spreads(self):
        if self.cross_market_last_spread is None:
            return

        chunks = []

        sign = " "
        if self.cross_market_is_converging == False:
            sign = "▲"
        elif self.cross_market_is_converging == True:
            sign = "▼"
        chunk = sign + " {:.4f}%".format(self.cross_market_spread * 100)

        chunks.append(chunk)

        self.logger.info("[Spread] " + "\t".join(chunks))


async def get_context(
    logger: Logger, exchange: ccxt.pro.okx, side: Side, base: str, quote: str
) -> Context:
    margin_market_symbol = f"{base}/{quote}"
    perp_market_symbol = f"{base}/{quote}:{quote}"
    symbol_to_market_map = await exchange.load_markets()
    margin_market = symbol_to_market_map[margin_market_symbol]
    perp_market = symbol_to_market_map[perp_market_symbol]

    symbol_to_balance_map, perp_market_position = await asyncio.gather(
        exchange.fetch_balance(),
        exchange.fetch_position(symbol=perp_market_symbol),
    )
    margin_market_base_token_balance_amount = decimalize(
        symbol_to_balance_map[base]["free"]
    )
    perp_market_contract_position_amount = decimalize(perp_market_position["contracts"])

    context = Context(
        logger=logger,
        side=side,
        margin_market_unified_symbol=margin_market_symbol,
        margin_market=margin_market,
        margin_market_base_token_balance_amount=margin_market_base_token_balance_amount,
        perp_market_unified_symbol=perp_market_symbol,
        perp_market=perp_market,
        perp_market_contract_position_amount=perp_market_contract_position_amount,
    )
    return context


async def watch(exchange: ccxt.pro.okx, context: Context):

    async def _watch_margin_market_order_book():
        while True:
            response = await exchange.watch_order_book(
                symbol=context.margin_market_unified_symbol
            )
            context.margin_market_order_book = response
            context.report_spreads()

    async def _watch_perp_market_order_book():
        while True:
            response = await exchange.watch_order_book(
                symbol=context.perp_market_unified_symbol
            )
            context.perp_market_order_book = response
            context.report_spreads()

    await asyncio.gather(
        _watch_margin_market_order_book(),
        _watch_perp_market_order_book(),
    )


async def place_orders(exchange: ccxt.pro.okx, context: Context):
    while not context.is_spread_ready:
        await asyncio.sleep(0)

    while True:
        if context.side == "close_long_margin_short_perp":
            margin_market_order_side = "sell"
            perp_market_order_side = "buy"
        elif context.side == "close_short_margin_long_perp":
            margin_market_order_side = "buy"
            perp_market_order_side = "sell"

        if (
            context.margin_market_base_token_balance_amount
            < context.margin_market["limits"]["amount"]["min"]
            or context.perp_market_contract_position_amount
            < context.perp_market["limits"]["amount"]["min"]
        ):
            raise ValueError(f"The amount is too small to place an order.")
        elif (
            context.margin_market_base_token_balance_amount
            > context.margin_market_max_order_amount
            or context.perp_market_contract_position_amount
            > context.perp_market_max_order_amount
        ):
            await asyncio.sleep(0.1)
            continue
        elif context.cross_market_is_converging == False:
            await asyncio.sleep(0.1)
            continue
        else:
            break

    context.logger.info("[Position] [Margin & Perp] Closing...")

    margin_order, perp_order = await asyncio.gather(
        exchange.create_order(
            symbol=context.margin_market_unified_symbol,
            type="market",
            side=margin_market_order_side,
            amount=float(context.margin_market_base_token_balance_amount),
            params={"tdMode": "cross"},
        ),
        exchange.create_order(
            symbol=context.perp_market_unified_symbol,
            type="market",
            side=perp_market_order_side,
            amount=float(context.perp_market_contract_position_amount),
            params={"tdMode": "cross", "posSide": "net"},
        ),
    )

    context.logger.info("[Position] [Margin & Perp] Closed.")
    context.logger.info(json.dumps(margin_order, indent=2))
    context.logger.info(json.dumps(perp_order, indent=2))
