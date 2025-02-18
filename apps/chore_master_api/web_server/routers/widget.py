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


@router.get("/transaction-inspector/transactions/{tx_hash}")
async def get_transaction_inspector_transactions_tx_hash(tx_hash: str):
    if tx_hash == "0x593fa3f2a232d1799225baf7d2ac7e33c5051cbe6ff55b8b6e3ada41bc7ef581":
        return ResponseSchema[dict](
            status=StatusEnum.SUCCESS,
            data={
                "hash": "0x593fa3f2a232d1799225baf7d2ac7e33c5051cbe6ff55b8b6e3ada41bc7ef581",
                "status": "Success",
                "block": 21791814,
                "confirmations": 60010,
                "timestamp": "2025-02-07T05:01:47Z",
                "confirmation_time": "within 30 secs",
                "action": {
                    "type": "Swap",
                    "from_amount": "6893.653596587094938899",
                    "from_token": "USDe",
                    "to_amount": "127925.305094317346311985",
                    "to_token": "YT-USDe-27MAR2025",
                    "platform": "Pendle",
                },
                "from": "0x23392278f49b3a19bb26489acd9126d202d336f",
                "interacted_with": {
                    "address": "0x888888888889758f76e7103c6cbf23abbf58f946",
                    "label": "Pendle: RouterV4",
                },
                "transfers": [
                    {
                        "token": "USDe",
                        "from": "0x233922784f49b3a19bb26489acd9126d202d336f",
                        "from_label": "Unknown",
                        "to": "0x888888888889758f76e7103c6cbf23abbf58f946",
                        "to_label": "Pendle: RouterV4",
                        "amount": "6893.653596587094938899",
                        "icon_address": "/token/images/ethenausde_32.svg",
                    },
                    {
                        "token": "USDe",
                        "from": "0x888888888889758f76e7103c6cbf23abbf58f946",
                        "from_label": "Pendle: RouterV4",
                        "to": "0x4db99b79361f98865230f5702de024c69f629fec",
                        "to_label": "Pendle: SY-USDe Token 5",
                        "amount": "6893.653596587094938899",
                        "icon_address": "/token/images/ethenausde_32.svg",
                    },
                    {
                        "token": "USDe",
                        "from": "0x4db99b79361f98865230f5702de024c69f629fec",
                        "from_label": "Pendle: SY-USDe Token 5",
                        "to": "0x313359c1c2a466516980cbdd7b3ea38bce64e4ca",
                        "to_label": "alexzhuang.eth",
                        "amount": "2423.608948578301828257",
                        "icon_address": "/token/images/ethenausde_32.svg",
                    },
                    {
                        "token": "SY-USDe",
                        "from": "0x0000000000000000000000000000000000000000",
                        "from_label": "Null: 0x000...000",
                        "to": "0x888888888889758f76e7103c6cbf23abbf58f946",
                        "to_label": "Pendle: RouterV4",
                        "amount": "6893.653596587094938899",
                        "icon_address": "/token/images/syusde.png",
                    },
                    {
                        "token": "SY-USDe",
                        "from": "0x888888888889758f76e7103c6cbf23abbf58f946",
                        "from_label": "Pendle: RouterV4",
                        "to": "0x000000000000c9b3e2c3ec88b1b4c0cd853f4321",
                        "to_label": "Unknown",
                        "amount": "2489.304097141301482667",
                        "icon_address": "/token/images/syusde.png",
                    },
                    {
                        "token": "SY-USDe",
                        "from": "0x000000000000c9b3e2c3ec88b1b4c0cd853f4321",
                        "from_label": "Unknown",
                        "to": "0x0000000000000000000000000000000000000000",
                        "to_label": "Null: 0x000...000",
                        "amount": "2423.608948578301828257",
                        "icon_address": "/token/images/syusde.png",
                    },
                    {
                        "token": "SY-USDe",
                        "from": "0x000000000000c9b3e2c3ec88b1b4c0cd853f4321",
                        "from_label": "Unknown",
                        "to": "0x8270400d528c34e1596ef367eedec99080a1b592",
                        "to_label": "Unknown",
                        "amount": "65.69514856299965441",
                        "icon_address": "/token/images/syusde.png",
                    },
                    {
                        "token": "SY-USDe",
                        "from": "0x888888888889758f76e7103c6cbf23abbf58f946",
                        "from_label": "Pendle: RouterV4",
                        "to": "0x4a8036efa1307f1ca82d932c0895faa18db0c9ee",
                        "to_label": "Pendle: YT-USDe-27MAR2025 Token",
                        "amount": "4404.349499445793456232",
                        "icon_address": "/token/images/syusde.png",
                    },
                    {
                        "token": "SY-USDe",
                        "from": "0xb451a36c8b6b2eac77ad0737ba732818143a0e25",
                        "from_label": "Pendle: PENDLE-LPT Token 90",
                        "to": "0x4a8036efa1307f1ca82d932c0895faa18db0c9ee",
                        "to_label": "Pendle: YT-USDe-27MAR2025 Token",
                        "amount": "223657.257767574847382579",
                        "icon_address": "/token/images/syusde.png",
                    },
                    {
                        "token": "SY-USDe",
                        "from": "0xb451a36c8b6b2eac77ad0737ba732818143a0e25",
                        "from_label": "Pendle: PENDLE-LPT Token 90",
                        "to": "0x8270400d528c34e1596ef367eedec99080a1b592",
                        "to_label": "Unknown",
                        "amount": "23.457897339557544186",
                        "icon_address": "/token/images/syusde.png",
                    },
                    {
                        "token": "YT-USDe",
                        "from": "0x313359c1c2a466516980cbdd7b3ea38bce64e4ca",
                        "from_label": "alexzhuang.eth",
                        "to": "0x233922784f49b3a19bb26489acd9126d202d336f",
                        "to_label": "Unknown",
                        "amount": "127925.305094317346311985",
                        "icon_address": "/token/images/ytusde27mar2025.png",
                    },
                    {
                        "token": "YT-USDe",
                        "from": "0x0000000000000000000000000000000000000000",
                        "from_label": "Null: 0x000...000",
                        "to": "0x233922784f49b3a19bb26489acd9126d202d336f",
                        "to_label": "Unknown",
                        "amount": "228061.607267020640838811",
                        "icon_address": "/token/images/ytusde27mar2025.png",
                    },
                    {
                        "token": "PT-USDe",
                        "from": "0x0000000000000000000000000000000000000000",
                        "from_label": "Null: 0x000...000",
                        "to": "0xb451a36c8b6b2eac77ad0737ba732818143a0e25",
                        "to_label": "Pendle: PENDLE-LPT Token 90",
                        "amount": "228061.607267020640838811",
                        "icon_address": "/token/images/ptusde27mar2025.png",
                    },
                ],
            },
        )

    async with httpx.AsyncClient(timeout=None) as client:
        etherscan_scraper = EtherscanScraper(
            client=client, cf_clearance="", user_agent=""
        )
        html = await etherscan_scraper.get_tx_advanced_html(tx_hash)

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
                "token": address_map[token_address]["label"],
                "from": from_address,
                "from_label": address_map[from_address]["label"],
                "to": to_address,
                "to_label": address_map[to_address]["label"],
                "amount": f"{amount}",
            }
        )

    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "from": "",
            "interacted_with": {
                "address": "",
                "label": "",
            },
            "transfers": transfers,
        },
    )


@router.get("/tx_hash/{tx_hash}/logs")
async def get_tx_logs(tx_hash: str):
    async with httpx.AsyncClient(timeout=None) as client:
        etherscan_scraper = EtherscanScraper(
            client=client, cf_clearance="", user_agent=""
        )
        html = await etherscan_scraper.get_tx_advanced_html(tx_hash)

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

    # for transfer in transfers:
    #     from_address = transfer["from_address"]
    #     from_label = address_map[from_address]["label"]
    #     to_address = transfer["to_address"]
    #     to_label = address_map[to_address]["label"]
    #     token_address = transfer["token_address"]
    #     token_label = address_map[token_address]["label"]
    #     amount = transfer["amount"]
    #     value = transfer["value"]
    #     print(
    #         f'"{from_label}" -> "{to_label}": {amount} {token_label}{f" ({value})" if value is not None else ""}'
    #     )

    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "address_map": address_map,
            "transfers": transfers,
        },
    )
