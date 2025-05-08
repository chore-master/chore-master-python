from fastapi import Depends

from apps.chore_master_api.end_user_space.models.trace import Quota
from apps.chore_master_api.end_user_space.unit_of_works.trace import (
    TraceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import get_current_user
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_trace_uow
from apps.chore_master_api.web_server.schemas.dto import CurrentUser


class Counter:
    def __init__(self, initial_count: int):
        self._current_count = initial_count

    @property
    def current_count(self):
        return self._current_count

    def increase(self, delta: int):
        self._current_count += delta

    def decrease(self, delta: int):
        self._current_count -= delta


async def get_quota_counter(
    current_user: CurrentUser = Depends(get_current_user),
    uow: TraceSQLAlchemyUnitOfWork = Depends(get_trace_uow),
):
    async with uow:
        quotas = await uow.quota_repository.find_many(
            filter={
                "user_reference": current_user.reference,
            }
        )
        is_quota_exists = len(quotas) > 0
        initial_count = 0
        if is_quota_exists:
            initial_count = quotas[0].used
        quota_counter = Counter(initial_count)

        yield quota_counter

        if quota_counter.current_count != initial_count:
            if is_quota_exists:
                await uow.quota_repository.update_many(
                    filter={
                        "reference": quotas[0].reference,
                        "user_reference": current_user.reference,
                    },
                    values={
                        "used": quota_counter.current_count,
                    },
                )
            else:
                await uow.quota_repository.insert_one(
                    Quota(
                        user_reference=current_user.reference,
                        used=quota_counter.current_count,
                        limit=0,
                    ),
                )
        await uow.commit()
