from typing import Type

from chore_master_api.logical_sheets.financial_management import (
    account_logical_sheet,
    passbook_logical_sheet,
)
from chore_master_api.models.financial_management import Account, Passbook
from modules.google_service.models.logical_sheet import LogicalSheet
from modules.repositories.base_sheet_repository import BaseSheetRepository


class AccountRepository(BaseSheetRepository[Account]):
    @property
    def entity_class(self) -> Type[Account]:
        return Account

    @property
    def logical_sheet(self) -> LogicalSheet:
        return account_logical_sheet


class PassbookRepository(BaseSheetRepository[Passbook]):
    @property
    def entity_class(self) -> Type[Passbook]:
        return Passbook

    @property
    def logical_sheet(self) -> LogicalSheet:
        return passbook_logical_sheet
