from typing import Literal

from apps.chore_master_api.end_user_space.models.base import Entity
from apps.chore_master_api.modules.base_discriminated_resource import (
    BaseDiscriminatedResource,
)

ResourceDiscriminator = Literal[
    "oanda_feed",
    "yahoo_finance_feed",
    "coingecko_feed",
]


class Resource(Entity):
    user_reference: str
    name: str
    discriminator: ResourceDiscriminator
    value: dict

    def to_discriminated_resource(self) -> BaseDiscriminatedResource:
        if self.discriminator == "oanda_feed":
            from apps.chore_master_api.modules.feed_discriminated_resource import (
                OandaFeedDiscriminatedResource,
            )

            cls = OandaFeedDiscriminatedResource
        elif self.discriminator == "yahoo_finance_feed":
            from apps.chore_master_api.modules.feed_discriminated_resource import (
                YahooFinanceFeedDiscriminatedResource,
            )

            cls = YahooFinanceFeedDiscriminatedResource
        elif self.discriminator == "coingecko_feed":
            from apps.chore_master_api.modules.feed_discriminated_resource import (
                CoingeckoFeedDiscriminatedResource,
            )

            cls = CoingeckoFeedDiscriminatedResource
        else:
            raise NotImplementedError(
                f"Unsupported discriminator: {self.discriminator}"
            )
        return cls(value=self.value)
