from typing import Optional, TypedDict


class ParsedInstrument(TypedDict):
    base_asset: str
    quote_asset: str
    settlement_asset: Optional[str]
    period: Optional[str]
    is_spot: bool
    is_perpetual: bool
    is_term: bool
    is_aggregated_term: bool


class SymbolUtils:
    @staticmethod
    def parse_instrument(instrument_symbol: str) -> ParsedInstrument:
        components = instrument_symbol.split("_")
        if len(components) < 2:
            raise ValueError(f"Invalid instrument symbol: {instrument_symbol}")
        base_asset = components[0]
        quote_asset = components[1]
        settlement_asset = components[2] if len(components) > 2 else None
        period = components[3] if len(components) > 3 else None

        is_spot = None
        is_perpetual = None
        is_term = None
        is_aggregated_term = None

        if settlement_asset is None:
            is_spot = True
            is_perpetual = False
            is_term = False
            is_aggregated_term = False
        else:
            is_spot = False
            if period is None:
                is_perpetual = True
                is_term = False
                is_aggregated_term = False
            else:
                is_perpetual = False
                is_term = True
                if period.isdigit():
                    is_aggregated_term = False
                else:
                    is_aggregated_term = True

        return ParsedInstrument(
            base_asset=base_asset,
            quote_asset=quote_asset,
            settlement_asset=settlement_asset,
            period=period,
            is_spot=is_spot,
            is_perpetual=is_perpetual,
            is_term=is_term,
            is_aggregated_term=is_aggregated_term,
        )
