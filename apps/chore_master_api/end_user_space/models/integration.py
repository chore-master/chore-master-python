from typing import Literal

from apps.chore_master_api.end_user_space.models.base import Entity

ResourceDiscriminator = Literal[
    "s3_feed",
    "s3_account",
    "okx_feed",
    "okx_account",
    "process_executor",
    "s3_storage",
]


class Resource(Entity):
    end_user_reference: str
    name: str
    discriminator: ResourceDiscriminator
    value: dict
