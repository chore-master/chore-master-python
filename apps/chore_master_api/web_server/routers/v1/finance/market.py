# import asyncio
# import json
# import os
# from collections import defaultdict
# from datetime import datetime, timezone
# from typing import Mapping

# import httpx
# import pandas as pd
# from bs4 import BeautifulSoup
from fastapi import APIRouter, Query

# from apps.chore_master_api.web_server.dependencies.concurrency import get_mutex
# from modules.scraper.cloud_flare_solver import CloudflareSolver
# from modules.scraper.etherscan_scraper import EtherscanScraper
# from modules.utils.cache_utils import FileSystemCache
# from modules.utils.file_system_utils import FileSystemUtils
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/market")


@router.get("/ecosystem")
async def get_ecosystem():
    color_map = {
        "person": "blue",
        "organiation": "red",
        "network": "grey",
        "project": "green",
        "token": "yellow",
    }

    networks = [
        {
            "id": "network_ethereum",
            "name": "Ethereum",
            "to_token": ["token_eth"],
        },
        {
            "id": "network_solana",
            "name": "Solana",
            "to_token": ["token_sol"],
        },
        {
            "id": "network_tron",
            "name": "Tron",
        },
        {
            "id": "network_bsc",
            "name": "BSC",
        },
        {
            "id": "network_base",
            "name": "Base",
            "from_person": ["person_jesse_pollak"],
        },
        {
            "id": "network_bitcoin",
            "name": "Bitcoin",
            "to_token": ["token_btc"],
        },
        {
            "id": "network_arbitrum",
            "name": "Arbitrum",
        },
        {
            "id": "network_avalanche",
            "name": "Avalanche",
        },
        {
            "id": "network_sui",
            "name": "Sui",
        },
        {
            "id": "network_hyperliquid",
            "name": "Hyperliquid",
        },
        {
            "id": "network_aptos",
            "name": "Aptos",
        },
        {
            "id": "network_ton",
            "name": "TON",
            "full_name": "The Open Network",
            "to_token": ["token_ton"],
        },
        {
            "id": "network_tron",
            "name": "TRON",
            "full_name": "TRON（波場）",
            "from_person": ["person_justin_sun"],
            "to_token": ["token_trx"],
        },
        {
            "id": "network_ape_chain",
            "name": "Ape Chain",
            "to_token": ["token_ape"],
        },
    ]

    people = [
        {
            "id": "person_shaw",
            "name": "Shaw",
        },
        {
            "id": "person_jesse_pollak",
            "name": "Jesse Pollak",
            "avatar_url": "https://s3.amazonaws.com/finn--production/uploads/public_8f3e472e-bac5-4913-bfc4-f80ef8d27ceb_image.jpeg",
        },
        {
            "id": "person_michael_egorov",
            "name": "Michael Egorov",
            "avatar_url": "https://media.licdn.com/dms/image/v2/C5603AQEqg8W79nphvA/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1516508038501?e=2147483647&v=beta&t=ge60gZwH8Pd3b5IDVQhLHTnZzeq_1qblKJER1Ye3N5Y",
        },
        {
            "id": "person_jerry_li",
            "name": "Jerry Li",
        },
        {
            "id": "person_corey_caplan",
            "name": "Corey Caplan",
            "avatar_url": "https://www.shirleywachtel.com/wp-content/uploads/2023/02/Corey-Caplan.jpg",
        },
        {
            "id": "person_guy_young",
            "name": "Guy Young",
            "avatar_url": "https://cdn.prod.website-files.com/645edd8f8709e3387ae97c68/663b7d7ab6281c3238157f72_2099_Guy-Young%20(1).jpeg",
        },
        {
            "id": "person_pierre_person",
            "name": "Pierre PERSON",
            "avatar_url": "https://pbs.twimg.com/profile_images/1792630849612976129/8Qdeh-Yb_400x400.jpg",
        },
        {
            "id": "person_pavel_durov",
            "name": "Pavel Durov",
        },
        {
            "id": "person_nikolai_durov",
            "name": "Nikolai Durov",
        },
        {
            "id": "person_justin_sun",
            "name": "Justin Sun",
            "full_name": "Justin Sun（孫宇晨）",
        },
        {
            "id": "person_konstantin_lomashuk",
            "name": "Konstantin Lomashuk",
        },
        {
            "id": "person_vasiliy_shapovalov",
            "name": "Vasiliy Shapovalov",
        },
        {
            "id": "person_jordan_fish",
            "name": "Jordan Fish",
        },
        {
            "id": "person_robert_leshner",
            "name": "Robert Leshner",
        },
        {
            "id": "person_stani_kulechov",
            "name": "Stani Kulechov",
        },
        {
            "id": "person_rune_christensen",
            "name": "Rune Christensen",
        },
        {
            "id": "person_mike_silagadze",
            "name": "Mike Silagadze",
            "avatar_url": "https://www.ether.fi/_next/image?url=%2Fimages%2Fabout%2Fprofiles%2Fmike.webp&w=256&q=75",
        },
        {
            "id": "person_greg_solano",
            "name": "Greg Solano",
        },
        {
            "id": "person_wylie_aronow",
            "name": "Wylie Aronow",
        },
    ]

    organiations = [
        {
            "id": "org_iosg",
            "name": "IOSG Ventures",
        },
        {
            "id": "org_eliza_labs",
            "name": "Eliza Labs",
        },
        {
            "id": "org_ai16z",
            "name": "ai16z DAO",
            "from_org": ["org_eliza_labs"],
            "from_person": ["person_shaw"],
        },
        {
            "id": "org_term_structure_labs",
            "name": "Term Structure Labs",
            "from_person": ["person_jerry_li"],
        },
        {
            "id": "org_usual_money",
            "name": "Usual Money",
            "from_person": ["person_pierre_person"],
            "to_token": ["token_usual"],
        },
        {
            "id": "org_ethena_labs",
            "name": "Ethena Labs",
            "from_person": ["person_guy_young"],
            "to_token": ["token_ena"],
        },
        {
            "id": "org_leavitt_innovations",
            "name": "Leavitt Innovations",
            "from_person": ["person_corey_caplan"],
        },
        {
            "id": "org_ton_foundation",
            "name": "TON Foundation",
            "from_person": ["person_pavel_durov", "person_nikolai_durov"],
        },
        {
            "id": "org_tron_foundation",
            "name": "TRON Foundation",
            "from_person": ["person_justin_sun"],
        },
        {
            "id": "org_curve_dao",
            "name": "Curve DAO",
            "from_person": ["person_michael_egorov"],
            "to_token": ["token_crv"],
        },
        {
            "id": "org_lido_dao",
            "name": "Lido DAO",
            "from_person": [
                "person_konstantin_lomashuk",
                "person_vasiliy_shapovalov",
                "person_jordan_fish",
            ],
            "to_token": ["token_ldo"],
        },
        {
            "id": "org_compound_labs",
            "name": "Compound Labs",
            "from_person": ["person_robert_leshner"],
            "to_token": ["token_comp"],
        },
        {
            "id": "org_aave_labs",
            "name": "Aave Labs",
            "from_person": ["person_stani_kulechov"],
            "to_token": ["token_aave"],
        },
        {
            "id": "org_maker_dao",
            "name": "MakerDAO",
            "from_person": ["person_rune_christensen"],
            "to_token": ["token_mkr", "token_dai"],
        },
        {
            "id": "org_phoenix_labs",
            "name": "Phoenix Labs",
            "from_org": ["org_maker_dao"],
        },
        {
            "id": "org_spark_protocol",
            "name": "Spark Protocol",
            "from_org": ["org_phoenix_labs"],
        },
        {
            "id": "org_ether_fi_dao",
            "name": "Ether.Fi DAO",
            "from_person": ["person_mike_silagadze"],
            "to_token": ["token_ethfi"],
        },
        {
            "id": "org_yuga_labs",
            "name": "Yuga Labs",
            "from_person": ["person_greg_solano", "person_wylie_aronow"],
        },
        {
            "id": "org_ape_coin_dao",
            "name": "ApeCoin DAO",
            "to_token": ["token_ape"],
            "to_network": ["network_bsc"],
        },
    ]

    apps = [
        {
            "id": "app_termstructure",
            "name": "Term Structure",
            "from_org": ["org_term_structure_labs"],
            "to_network": ["network_ethereum", "network_arbitrum"],
        },
        {
            "id": "app_termmax",
            "name": "TermMax",
            "from_org": ["org_term_structure_labs"],
            "to_network": ["network_ethereum", "network_arbitrum"],
        },
        {
            "id": "app_ethena",
            "name": "Ethena",
            "from_org": ["org_ethena_labs"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "app_usual",
            "name": "Usual",
            "from_org": ["org_usual_money"],
            "to_network": ["network_ethereum", "network_arbitrum"],
        },
        {
            "id": "app_dolomite",
            "name": "Dolomite",
            "from_org": ["org_leavitt_innovations"],
            "to_network": ["network_arbitrum"],
        },
        {
            "id": "app_pump_fun",
            "name": "Pump.fun",
            "to_network": ["network_solana"],
        },
        {
            "id": "app_telegram",
            "name": "Telegram",
            "from_person": ["person_pavel_durov"],
            "to_network": ["network_ton"],
        },
        {
            "id": "app_curve_finance",
            "name": "Curve Finance",
            "from_person": ["person_michael_egorov"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "app_lido",
            "name": "Lido",
            "from_org": ["org_lido_dao"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "app_compound_finance",
            "name": "Compound Finance",
            "from_org": ["org_compound_labs"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "app_aave",
            "name": "Aave",
            "from_org": ["org_aave_labs"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "app_spark_lend",
            "name": "Spark Lend",
            "from_org": ["org_spark_protocol"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "app_ether_fi",
            "name": "ether.fi",
            "from_org": ["org_ether_fi_dao"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "app_ape_express",
            "name": "Ape Express",
            "from_org": ["org_yuga_labs"],
            "to_network": ["network_ape_chain"],
        },
    ]

    tokens = [
        {
            "id": "token_btc",
            "name": "BTC",
            "full_name": "Bitcoin",
        },
        {
            "id": "token_eth",
            "name": "ETH",
            "full_name": "Ethereum",
        },
        {
            "id": "token_sol",
            "name": "SOL",
            "full_name": "Solana",
        },
        {
            "id": "token_usual",
            "name": "USUAL",
        },
        {
            "id": "token_usd0",
            "name": "USD0",
            "from_app": ["app_usual"],
        },
        {
            "id": "token_usd0++",
            "name": "USD0++",
            "from_token": ["token_usd0"],
        },
        {
            "id": "token_ena",
            "name": "ENA",
        },
        {
            "id": "token_usde",
            "name": "USDe",
            "from_app": ["app_ethena"],
        },
        {
            "id": "token_susde",
            "name": "sUSDe",
            "from_token": ["token_usde"],
        },
        {
            "id": "token_dolo",
            "name": "DOLO",
            "from_app": ["app_dolomite"],
        },
        {
            "id": "token_odolo",
            "name": "oDOLO",
            "from_token": ["token_dolo"],
        },
        {
            "id": "token_vedolo",
            "name": "veDOLO",
            "from_token": ["token_odolo"],
        },
        {
            "id": "token_ton",
            "name": "TON",
            "full_name": "Toncoin",
        },
        {
            "id": "token_trx",
            "name": "TRX",
            "full_name": "Tronix",
        },
        {
            "id": "token_crv",
            "name": "CRV",
            "full_name": "Curve DAO Token",
        },
        {
            "id": "token_vecrv",
            "name": "veCRV",
            "from_token": ["token_crv"],
        },
        {
            "id": "token_ldo",
            "name": "LDO",
            "full_name": "Lido DAO Token",
        },
        {
            "id": "token_steth",
            "name": "stETH",
            "full_name": "Lido Staked ETH",
            "from_app": ["app_lido"],
        },
        {
            "id": "token_wsteth",
            "name": "wstETH",
            "full_name": "Wrapped stETH",
            "from_token": ["token_steth"],
        },
        {
            "id": "token_comp",
            "name": "COMP",
            "full_name": "Compound",
        },
        {
            "id": "token_aave",
            "name": "AAVE",
            "full_name": "Aave",
        },
        {
            "id": "token_mkr",
            "name": "MKR",
            "full_name": "MakerDAO",
        },
        {
            "id": "token_dai",
            "name": "DAI",
            "full_name": "Dai",
        },
        {
            "id": "token_sdai",
            "name": "sDAI",
            "full_name": "Savings Dai",
            "from_token": ["token_dai"],
        },
        {
            "id": "token_ethfi",
            "name": "ETHFI",
            "full_name": "Ether.fi",
        },
        {
            "id": "token_eeth",
            "name": "eETH",
            "from_app": ["app_ether_fi"],
        },
        {
            "id": "token_bayc",
            "name": "BAYC",
            "full_name": "Bored Ape Yacht Club",
            "from_org": ["org_yuga_labs"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "token_mayc",
            "name": "MAYC",
            "full_name": "Mutant Ape Yacht Club",
            "from_org": ["org_yuga_labs"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "token_bakc",
            "name": "BAKC",
            "full_name": "Bored Ape Kennel Club",
            "from_org": ["org_yuga_labs"],
            "to_network": ["network_ethereum"],
        },
        {
            "id": "token_ape",
            "name": "APE",
            "full_name": "ApeCoin",
            "to_network": ["network_ape_chain"],
        },
    ]

    links = []
    entities = [*people, *organiations, *networks, *apps, *tokens]
    dimensions = ["person", "org", "network", "app", "token"]
    for dimension in dimensions:
        for entity in entities:
            key = f"from_{dimension}"
            if key in entity:
                for fromEntityId in entity[key]:
                    links.append([fromEntityId, entity["id"]])
            key = f"to_{dimension}"
            if key in entity:
                for toEntityId in entity[key]:
                    links.append([entity["id"], toEntityId])
    nodes = [
        *[
            {
                **item,
                "color": color_map["person"],
            }
            for item in people
        ],
        *[
            {
                **item,
                "color": color_map["organiation"],
            }
            for item in organiations
        ],
        *[
            {
                **item,
                "color": color_map["network"],
            }
            for item in networks
        ],
        *[
            {
                **item,
                "color": color_map["project"],
            }
            for item in apps
        ],
        *[
            {
                **item,
                "color": color_map["token"],
            }
            for item in tokens
        ],
    ]
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "nodes": nodes,
            "links": links,
        },
    )


@router.get("/interest-rate-inspect")
async def get_interest_rate_inspect(cap_amount: int = Query(default=800000)):
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "policies": [
                {
                    "platform_name": "聯邦銀行",
                    "references": [
                        "https://www.ubot.com.tw/rates/twd/deposit_rate",
                        "https://newnewbank.com.tw/deposits10.htm",
                    ],
                    "end_time": "2025-07-20T00:00:00Z",
                    "entries": [
                        {
                            "min_amount": 0,
                            "max_amount": 150000,
                            "rate": 0.1,
                        },
                        {
                            "min_amount": 150001,
                            "max_amount": cap_amount,
                            "rate": 0.0063500,
                        },
                    ],
                },
                {
                    "platform_name": "王道銀行",
                    "references": [
                        "https://www.o-bank.com/web/event/cm_integration_page/index.html#event",
                        "https://www.o-bank.com/retail/cm/ratemain/cm-deprate",
                    ],
                    "end_time": "2025-08-18T00:00:00Z",
                    "entries": [
                        {
                            "min_amount": 0,
                            "max_amount": 200000,
                            "rate": 0.021,
                        },
                        {
                            "min_amount": 200001,
                            "max_amount": 500000,
                            "rate": 0.015,
                        },
                        {
                            "min_amount": 500001,
                            "max_amount": cap_amount,
                            "rate": 0.008750,
                        },
                    ],
                },
                {
                    "platform_name": "永豐銀行",
                    "references": [
                        "https://bank.sinopac.com/MMA8/bank/html/rate/bank_Interest.html",
                    ],
                    "end_time": "2025-06-30T00:00:00Z",
                    "entries": [
                        {
                            "min_amount": 0,
                            "max_amount": 300000,
                            "rate": 0.015,
                        },
                        {
                            "min_amount": 300001,
                            "max_amount": cap_amount,
                            "rate": 0.00705,
                        },
                    ],
                },
                {
                    "platform_name": "將來銀行",
                    "references": [
                        "https://www.nextbank.com.tw/announcement/4b262cbb0600000005db69481a78b4a4/news57",
                        "https://nebweb.nextbank.com.tw/corp/rates",
                    ],
                    "end_time": "2025-03-31T00:00:00Z",
                    "entries": [
                        {
                            "min_amount": 0,
                            "max_amount": 50000,
                            "rate": 0.01,
                        },
                        {
                            "min_amount": 50001,
                            "max_amount": cap_amount,
                            "rate": 0.015,
                        },
                        # {
                        #     "min_amount": 300001,
                        #     "max_amount": cap_amount,
                        #     "rate": 0.00875,
                        # },
                    ],
                },
            ],
        },
    )


# @router.get("/a_token_transactions")
# async def get_a_token_transactions(mutex: asyncio.Lock = Depends(get_mutex)):
#     cloudflare_cache = FileSystemCache(base_dir=".cache/cloudflare")
#     cloudflare_context_text = cloudflare_cache.get(keys=["context.json"])
#     if cloudflare_context_text is None:
#         async with CloudflareSolver() as cf_solver:
#             user_agent = cf_solver.user_agent
#             cf_clearance = await cf_solver.get_clearance_token(
#                 url="https://etherscan.io/tokenholdings?a=0xc049f307dc4db93747c943c33eb99d5ac2164b45"
#             )
#             cloudflare_cache.set(
#                 keys=["context.json"],
#                 value=json.dumps(
#                     {
#                         "user_agent": user_agent,
#                         "cf_clearance": cf_clearance,
#                     }
#                 ),
#             )
#     else:
#         cloudflare_context = json.loads(cloudflare_context_text)
#         user_agent = cloudflare_context["user_agent"]
#         cf_clearance = cloudflare_context["cf_clearance"]

#     series = []
#     token_symbol_to_token_map = json.load(
#         open(os.path.join(os.path.dirname(__file__), "token_symbol_to_token_map.json"))
#     )
#     # token_symbol_cache = FileSystemCache(base_dir=".cache/token_symbols")
#     for token_symbol, token_dict in token_symbol_to_token_map.items():
#         # keys = [f"{token_symbol}.json"]
#         # token_symbol_cache_text = token_symbol_cache.get(keys=keys)
#         # if token_symbol_cache_text is not None:
#         #     token_symbol_cache_dict = json.loads(token_symbol_cache_text)
#         #     from_node_set = set(token_symbol_cache_dict["from_node_set"])
#         #     to_node_set = set(token_symbol_cache_dict["to_node_set"])
#         #     node_to_weight_map = {
#         #         tuple(k.split("|")): v
#         #         for k, v in token_symbol_cache_dict[
#         #             "node_to_weight_map"
#         #         ].items()
#         #     }
#         # else:

#         async with httpx.AsyncClient(timeout=None) as client:
#             etherscan_scraper = EtherscanScraper(
#                 client=client,
#                 cf_clearance=cf_clearance,
#                 user_agent=user_agent,
#                 is_debugging=True,
#             )
#             from_node_set = set()
#             to_node_set = set()
#             node_to_weight_map: Mapping[str, float] = defaultdict(lambda: 0.0)
#             df_dir_path = f"./data/csv/{datetime.now(timezone.utc).strftime('%Y_%m_%d')}/token_symbols/{token_symbol}/sender_addresses"
#             df_columns = [
#                 "transaction_hash",
#                 "method",
#                 "transaction_time",
#                 "from_address",
#                 "to_address",
#                 "to_address_name",
#                 "to_address_icon_title",
#                 "quantity",
#                 "notional",
#                 "token_symbol",
#             ]
#             FileSystemUtils.ensure_directory(df_dir_path)
#             for sender_address in token_dict.get("sender_addresses", []):
#                 df_file_path = f"{df_dir_path}/{sender_address}.csv"
#                 if os.path.exists(df_file_path):
#                     df = pd.read_csv(df_file_path, keep_default_na=False)
#                 else:
#                     advanced_filter_htmls = (
#                         await etherscan_scraper.get_advanced_filter_htmls(
#                             from_address=sender_address,
#                             token_address=token_dict["address"],
#                         )
#                     )
#                     row_dicts = []
#                     for html in advanced_filter_htmls:
#                         soup = BeautifulSoup(html, "html.parser")
#                         trs = soup.find_all("tr")[1:]
#                         for tr in trs:
#                             tds = tr.find_all("td")
#                             if (
#                                 len(tds) == 1
#                                 and tds[0].text.strip()
#                                 == "There are no matching entriesPlease try again later"
#                             ):
#                                 break
#                             transaction_hash = tds[0].text.strip()
#                             transaction_type = tds[1].text.strip()
#                             method = tds[2].text.strip()
#                             transaction_time_str = (
#                                 datetime.strptime(
#                                     tds[4].text.strip(), "%Y-%m-%d %H:%M:%S"
#                                 ).isoformat()
#                                 + "Z"
#                             )
#                             to_address = EtherscanScraper.parse_address(
#                                 tds[9].find("a")["href"]
#                             )
#                             to_address_name = tds[9].text.strip()
#                             quantity = EtherscanScraper.parse_float(tds[10].text)
#                             notional = EtherscanScraper.parse_float(
#                                 tds[11].find("span")["data-bs-title"][1:]
#                             )
#                             to_address_icon = tds[9].find("img")
#                             if to_address_icon is None:
#                                 to_address_icon_title = None
#                             else:
#                                 to_address_icon_title = to_address_icon["data-bs-title"]
#                             row_dict = {
#                                 "transaction_hash": transaction_hash,
#                                 "type": transaction_type,
#                                 "method": method,
#                                 "transaction_time": transaction_time_str,
#                                 "from_address": sender_address,
#                                 "to_address": to_address,
#                                 "to_address_name": to_address_name,
#                                 "to_address_icon_title": to_address_icon_title,
#                                 "quantity": quantity,
#                                 "notional": notional,
#                                 "token_symbol": token_symbol,
#                             }
#                             row_dicts.append(row_dict)
#                     if len(row_dicts) > 0:
#                         df = pd.DataFrame.from_records(
#                             row_dicts,
#                             columns=df_columns,
#                         )
#                     else:
#                         df = pd.DataFrame(columns=df_columns)
#                     df.to_csv(df_file_path, index=False)

#                 for _, row in df.iterrows():
#                     from_node = row["from_address"]
#                     from_node_set.add(from_node)
#                     to_node = row["to_address_name"]
#                     if row["to_address_icon_title"]:
#                         to_node = f"{to_node} ({row['to_address_icon_title']})"
#                     to_node_set.add(to_node)
#                     node_to_weight_map[(from_node, to_node)] += row["notional"]

#             # token_symbol_cache.set(
#             #     keys=keys,
#             #     value=json.dumps(
#             #         {
#             #             "from_node_set": list(from_node_set),
#             #             "to_node_set": list(to_node_set),
#             #             "node_to_weight_map": {
#             #                 "|".join(k): v
#             #                 for k, v in node_to_weight_map.items()
#             #             },
#             #         }
#             #     ),
#             # )

#         nodes = [{"id": node, "column": 0} for node in from_node_set] + [
#             {"id": node, "column": 1} for node in to_node_set
#         ]
#         token_symbol_to_threshold_map = {
#             "ETH": 100_000_000,
#             "weETH": 1_000_000,
#             "wstETH": 1_000_000,
#             "USDT": 50_000_000,
#             "WBTC": 10_000_000,
#             "USDC": 50_000_000,
#         }
#         threshold = token_symbol_to_threshold_map.get(token_symbol, 0)
#         links = [
#             [from_node, to_node, weight]
#             for (
#                 from_node,
#                 to_node,
#             ), weight in node_to_weight_map.items()
#             if weight > threshold
#         ]
#         series.append(
#             {
#                 "name": token_symbol,
#                 "nodes": nodes,
#                 "links": links,
#             }
#         )
#     return ResponseSchema[dict](
#         status=StatusEnum.SUCCESS,
#         data={
#             "series": series,
#         },
#     )
