from typing import AsyncIterator

from apps.chore_master_api.modules.base_discriminated_resource import (
    BaseDiscriminatedResource,
)


class FeedDiscriminatedResource(BaseDiscriminatedResource):
    async def fetch_kline_dicts(
        self, instrument_symbol: str, interval_symbol: str
    ) -> AsyncIterator[list[dict]]:
        raise NotImplementedError


class CoingeckoFeedDiscriminatedResource(FeedDiscriminatedResource):
    async def fetch_kline_dicts(
        self, instrument_symbol: str, interval_symbol: str
    ) -> AsyncIterator[list[dict]]:
        # TODO: Implement
        # https://www.coingecko.com/en/coins/usd/twd
        # https://www.coingecko.com/en/coins/overnight-fi-usd/twd
        # https://www.coingecko.com/price_charts/overnight-fi-usd/twd/24_hours.json
        yield []
