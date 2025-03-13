from typing import Literal

from apps.chore_master_api.end_user_space.models.base import Entity
from apps.chore_master_api.modules.base_discriminated_operator import (
    BaseDiscriminatedOperator,
)

OperatorDiscriminator = Literal[
    "oanda_feed",
    "yahoo_finance_feed",
    "coingecko_feed",
]


class Operator(Entity):
    user_reference: str
    name: str
    discriminator: OperatorDiscriminator
    value: dict

    def to_discriminated_operator(self) -> BaseDiscriminatedOperator:
        if self.discriminator == "oanda_feed":
            from apps.chore_master_api.modules.feed_discriminated_operator import (
                OandaFeedDiscriminatedOperator,
            )

            cls = OandaFeedDiscriminatedOperator
        elif self.discriminator == "yahoo_finance_feed":
            from apps.chore_master_api.modules.feed_discriminated_operator import (
                YahooFinanceFeedDiscriminatedOperator,
            )

            cls = YahooFinanceFeedDiscriminatedOperator
        elif self.discriminator == "coingecko_feed":
            from apps.chore_master_api.modules.feed_discriminated_operator import (
                CoingeckoFeedDiscriminatedOperator,
            )

            cls = CoingeckoFeedDiscriminatedOperator
        else:
            raise NotImplementedError(
                f"Unsupported discriminator: {self.discriminator}"
            )
        return cls(value=self.value)
