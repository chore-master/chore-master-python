from typing import Type

from chore_master_api.logical_sheets.some_module import some_entity_logical_sheet
from chore_master_api.models.some_module import SomeEntity
from modules.google_service.models.logical_sheet import LogicalSheet
from modules.repositories.base_sheet_repository import BaseSheetRepository


class SomeEntityRepository(BaseSheetRepository[SomeEntity]):
    @property
    def entity_class(self) -> Type[SomeEntity]:
        return SomeEntity

    @property
    def logical_sheet(self) -> LogicalSheet:
        return some_entity_logical_sheet
