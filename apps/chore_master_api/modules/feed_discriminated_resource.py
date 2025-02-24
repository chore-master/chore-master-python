from datetime import datetime
from enum import Enum

import httpx

from apps.chore_master_api.modules.base_discriminated_resource import (
    BaseDiscriminatedResource,
)
from modules.utils.symbol_utils import SymbolUtils


class IntervalEnum(Enum):
    PER_1_DAY = "1d"


class FeedDiscriminatedResource(BaseDiscriminatedResource):
    async def fetch_prices(
        self,
        instrument_symbol: str,
        target_interval: IntervalEnum,
        target_datetimes: list[datetime],
    ) -> list[dict]:
        raise NotImplementedError


class YahooFinanceFeedDiscriminatedResource(FeedDiscriminatedResource):
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
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{base_asset}{quote_asset}=X",
                    params={
                        # "period1": "1080086400",
                        "period1": f"{int(datetime.fromisoformat('2024-01-01').timestamp())}",  # 1704067200
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
                    target_timestamp = target_datetime.timestamp() * 1000

                    # Binary search implementation
                    left, right = 0, len(timestamps) - 1
                    matched_idx = -1

                    while left <= right:
                        mid = (left + right) // 2
                        current_timestamp = timestamps[mid]

                        if current_timestamp <= target_timestamp:
                            matched_idx = mid
                            left = mid + 1
                        else:
                            right = mid - 1

                    if matched_idx != -1:
                        matched_timestamp = timestamps[matched_idx]
                        matched_price = close_prices[matched_idx]
                        price_dicts.append(
                            {
                                "instrument_symbol": instrument_symbol,
                                "target_interval": target_interval.value,
                                "target_datetime": target_datetime,
                                "matched_datetime": datetime.fromtimestamp(
                                    matched_timestamp
                                ),
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


class CoingeckoFeedDiscriminatedResource(FeedDiscriminatedResource):
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
                # with open("response.html", "w") as f:
                #     f.write(response.text)
                response.raise_for_status()
                response_dict = response.json()
                stats = response_dict["stats"]

                for target_datetime in target_datetimes:
                    target_timestamp = target_datetime.timestamp() * 1000

                    # Binary search implementation
                    left, right = 0, len(stats) - 1
                    matched_idx = -1

                    while left <= right:
                        mid = (left + right) // 2
                        current_timestamp = stats[mid][0]

                        if current_timestamp <= target_timestamp:
                            matched_idx = mid
                            left = mid + 1
                        else:
                            right = mid - 1

                    if matched_idx != -1:
                        matched_stat = stats[matched_idx]
                        price_dicts.append(
                            {
                                "instrument_symbol": instrument_symbol,
                                "target_interval": target_interval.value,
                                "target_datetime": target_datetime,
                                "matched_datetime": datetime.fromtimestamp(
                                    matched_stat[0] / 1000
                                ),
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
