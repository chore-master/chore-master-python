from typing import Type

from apps.chore_master_api.logical_sheets.financial_management import (
    account_logical_sheet,
    asset_logical_sheet,
    net_value_logical_sheet,
)
from apps.chore_master_api.models.financial_management import Account, Asset, NetValue
from modules.google_service.models.logical_sheet import LogicalSheet
from modules.repositories.base_sheet_repository import BaseSheetRepository


class AccountRepository(BaseSheetRepository[Account]):
    @property
    def entity_class(self) -> Type[Account]:
        return Account

    @property
    def logical_sheet(self) -> LogicalSheet:
        return account_logical_sheet


class AssetRepository(BaseSheetRepository[Asset]):
    @property
    def entity_class(self) -> Type[Asset]:
        return Asset

    @property
    def logical_sheet(self) -> LogicalSheet:
        return asset_logical_sheet


class NetValueRepository(BaseSheetRepository[NetValue]):
    @property
    def entity_class(self) -> Type[NetValue]:
        return NetValue

    @property
    def logical_sheet(self) -> LogicalSheet:
        return net_value_logical_sheet
