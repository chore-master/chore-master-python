import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter

from modules.scraper.etherscan_scraper import EtherscanScraper
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.get("/sankey")
async def get_sankey():
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "nodes": [
                {"id": "A"},
                {"id": "B"},
                {"id": "C"},
                {"id": "D"},
                {"id": "E"},
                {"id": "F"},
            ],
            "links": [
                {"source": "A", "target": "B", "value": 10},
                {"source": "A", "target": "C", "value": 20},
                {"source": "B", "target": "D", "value": 30},
                {"source": "C", "target": "D", "value": 40},
                {"source": "E", "target": "F", "value": 2},
            ],
        },
    )


@router.get("/tx_hash/{tx_hash}/logs")
async def get_tx_logs(tx_hash: str):
    async with httpx.AsyncClient(timeout=None) as client:
        etherscan_scraper = EtherscanScraper(
            client=client, cf_clearance="", user_agent=""
        )
        html = await etherscan_scraper.get_tx_advanced_html(tx_hash)
        print(html)

    soup = BeautifulSoup(html, "html.parser")

    table_row_divs = soup.select(
        "#ContentPlaceHolder1_maintable > div.card:nth-child(1) > div.row"
    )
    erc20_transfer_spans = table_row_divs[7].select(
        "#nav_tabcontent_erc20_transfer div.row-count > span:nth-child(2)"
    )

    address_map = {}
    transfers = []
    for erc20_transfer_span in erc20_transfer_spans:
        parts = list(erc20_transfer_span.children)
        from_a = parts[1]
        to_a = parts[3]
        amount_span = parts[5]
        if len(parts) == 7:
            value = None
        elif len(parts) == 8:
            value_span = parts[6]
            value = EtherscanScraper.parse_float(value_span.text[2:-1])
        else:
            raise NotImplementedError(f"Unsupported: {erc20_transfer_span.text}")
        token_a = parts[-1]

        from_address = from_a.attrs["data-highlight-target"]
        if from_address not in address_map:
            address_map[from_address] = {
                "label": from_a.text,
            }
        to_address = to_a.attrs["data-highlight-target"]
        if to_address not in address_map:
            address_map[to_address] = {
                "label": to_a.text,
            }
        token_address = token_a.attrs["data-highlight-target"]
        if token_address not in address_map:
            address_map[token_address] = {
                "label": token_a.text,
            }
        amount = EtherscanScraper.parse_float(amount_span.text)
        transfers.append(
            {
                "from_address": from_address,
                "to_address": to_address,
                "amount": amount,
                "value": value,
                "token_address": token_address,
            }
        )
    # divs = soup.select('div[id^="logI_"]')

    # address_map = {}
    # logs = []
    # for div in divs:
    #     dls = div.select("dl")
    #     topic = dls[2].select_one("dd").select_one("ul > li > span:nth-child(2)").text
    #     if (
    #         topic
    #         != "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    #     ):
    #         continue
    #     address_dd = dls[0].select_one("dd")
    #     contract_address = address_dd.select_one("a").attrs["data-highlight-target"]
    #     address_label_span = address_dd.select_one("span")
    #     if address_label_span is None:
    #         address_label = None
    #     else:
    #         address_label = address_label_span.text
    #     if contract_address not in address_map:
    #         address_map[contract_address] = {
    #             "address": contract_address,
    #             "label": address_label,
    #         }

    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "address_map": address_map,
            "transfers": transfers,
        },
    )
