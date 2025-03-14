from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional, Union

import httpx

from apps.chore_master_api.modules.base_discriminated_operator import (
    BaseDiscriminatedOperator,
)
from modules.utils.symbol_utils import SymbolUtils


class IntervalEnum(Enum):
    PER_1_DAY = "1d"


def binary_search_lte_from_ascendingly_ordered_items(
    items: list, target: Any, key: Optional[Callable[[Any], Union[int, float]]] = None
) -> Optional[int]:
    if key is None:
        get_key = lambda x: x
    else:
        get_key = key

    left, right = 0, len(items) - 1
    matched_idx = -1
    while left <= right:
        mid = (left + right) // 2
        current_item = items[mid]
        current_key = get_key(current_item)
        if current_key <= target:
            matched_idx = mid
            left = mid + 1
        else:
            right = mid - 1

    if matched_idx != -1:
        return matched_idx
    else:
        return None


class FeedDiscriminatedOperator(BaseDiscriminatedOperator):
    async def fetch_prices(
        self,
        instrument_symbol: str,
        target_interval: IntervalEnum,
        target_datetimes: list[datetime],
    ) -> list[dict]:
        raise NotImplementedError


class OandaFeedDiscriminatedOperator(FeedDiscriminatedOperator):
    async def fetch_prices(
        self,
        instrument_symbol: str,
        target_interval: IntervalEnum,
        target_datetimes: list[datetime],
    ) -> list[dict]:
        # https://fxds-public-exchange-rates-api.oanda.com/cc-api/currencies?base=USD&quote=TWD&data_type=general_currency_pair&start_date=2024-11-30&end_date=2024-12-01
        raise NotImplementedError


class YahooFinanceFeedDiscriminatedOperator(FeedDiscriminatedOperator):
    async def fetch_prices(
        self,
        instrument_symbol: str,
        target_interval: IntervalEnum,
        target_datetimes: list[datetime],
    ) -> list[dict]:
        parsed_instrument = SymbolUtils.parse_instrument(instrument_symbol)
        base_asset = parsed_instrument["base_asset"]
        quote_asset = parsed_instrument["quote_asset"]

        if target_interval == IntervalEnum.PER_1_DAY:
            price_dicts = []
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{base_asset.upper()}{quote_asset.upper()}=X",
                    params={
                        "period1": f"{int((min(target_datetimes) - timedelta(days=1)).timestamp())}",
                        "period2": f"{int(max(target_datetimes).timestamp())}",
                        "interval": "1d",
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
                    },
                )
                response.raise_for_status()
                response_dict = response.json()
                timestamps = response_dict["chart"]["result"][0]["timestamp"]
                close_prices = response_dict["chart"]["result"][0]["indicators"][
                    "adjclose"
                ][0]["adjclose"]

                for target_datetime in target_datetimes:
                    matched_idx = binary_search_lte_from_ascendingly_ordered_items(
                        items=timestamps, target=target_datetime.timestamp()
                    )
                    if matched_idx is not None:
                        matched_datetime = datetime.fromtimestamp(
                            timestamps[matched_idx]
                        )
                        matched_price = close_prices[matched_idx]
                        # print(str(target_datetime - matched_datetime))
                        price_dicts.append(
                            {
                                "instrument_symbol": instrument_symbol,
                                "target_interval": target_interval.value,
                                "target_datetime": target_datetime,
                                "matched_datetime": matched_datetime,
                                "matched_price": matched_price,
                            }
                        )
                    else:
                        price_dicts.append(
                            {
                                "instrument_symbol": instrument_symbol,
                                "target_interval": target_interval.value,
                                "target_datetime": target_datetime,
                                "matched_datetime": None,
                                "matched_price": None,
                            }
                        )
            return price_dicts
        else:
            raise ValueError(f"Unsupported interval: {target_interval}")


class CoingeckoFeedDiscriminatedOperator(FeedDiscriminatedOperator):
    async def fetch_prices(
        self,
        instrument_symbol: str,
        target_interval: IntervalEnum,
        target_datetimes: list[datetime],
    ) -> list[dict]:
        # https://www.coingecko.com/en/coins/usd/twd
        # https://www.coingecko.com/en/coins/overnight-fi-usd/twd
        # https://www.coingecko.com/price_charts/usd/twd/24_hours.json
        # https://www.coingecko.com/price_charts/overnight-fi-usd/twd/24_hours.json
        parsed_instrument = SymbolUtils.parse_instrument(instrument_symbol)
        base_asset = parsed_instrument["base_asset"]
        quote_asset = parsed_instrument["quote_asset"]
        if target_interval == IntervalEnum.PER_1_DAY:
            price_dicts = []
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.get(
                    f"https://www.coingecko.com/price_charts/{base_asset.lower()}/{quote_asset.lower()}/max.json",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
                    },
                )
                response.raise_for_status()
                response_dict = response.json()
                stats = response_dict["stats"]

                for target_datetime in target_datetimes:
                    matched_idx = binary_search_lte_from_ascendingly_ordered_items(
                        items=stats,
                        target=target_datetime.timestamp() * 1000,
                        key=lambda item: item[0],
                    )
                    if matched_idx is not None:
                        matched_stat = stats[matched_idx]
                        matched_datetime = datetime.fromtimestamp(
                            matched_stat[0] / 1000
                        )
                        # print(str(target_datetime - matched_datetime))
                        price_dicts.append(
                            {
                                "instrument_symbol": instrument_symbol,
                                "target_interval": target_interval.value,
                                "target_datetime": target_datetime,
                                "matched_datetime": matched_datetime,
                                "matched_price": matched_stat[1],
                            }
                        )
                    else:
                        price_dicts.append(
                            {
                                "instrument_symbol": instrument_symbol,
                                "target_interval": target_interval.value,
                                "target_datetime": target_datetime,
                                "matched_datetime": None,
                                "matched_price": None,
                            }
                        )
            return price_dicts
        else:
            raise ValueError(f"Unsupported interval: {target_interval}")
