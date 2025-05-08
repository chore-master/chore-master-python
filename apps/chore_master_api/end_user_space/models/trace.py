from apps.chore_master_api.end_user_space.models.base import Entity


class Quota(Entity):
    user_reference: str
    limit: int
    used: int
