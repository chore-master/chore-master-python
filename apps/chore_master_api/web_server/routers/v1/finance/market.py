import asyncio
import json
import os
from collections import defaultdict
from typing import Mapping

import httpx
from fastapi import APIRouter, Depends

from apps.chore_master_api.web_server.dependencies.concurrency import get_mutex
from modules.scraper.cloud_flare_solver import CloudflareSolver
from modules.scraper.etherscan_scraper import EtherscanScraper
from modules.utils.cache_utils import FileSystemCache
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


@router.get("/a_token_transactions")
async def get_a_token_transactions(mutex: asyncio.Lock = Depends(get_mutex)):
    cloudflare_cache = FileSystemCache(base_dir=".cache/cloudflare")
    cloudflare_context_text = cloudflare_cache.get(keys=["context.json"])
    if cloudflare_context_text is None:
        async with CloudflareSolver() as cf_solver:
            user_agent = cf_solver.user_agent
            cf_clearance = await cf_solver.get_clearance_token(
                url="https://etherscan.io/tokenholdings?a=0xc049f307dc4db93747c943c33eb99d5ac2164b45"
            )
            cloudflare_cache.set(
                keys=["context.json"],
                value=json.dumps(
                    {
                        "user_agent": user_agent,
                        "cf_clearance": cf_clearance,
                    }
                ),
            )
    else:
        cloudflare_context = json.loads(cloudflare_context_text)
        user_agent = cloudflare_context["user_agent"]
        cf_clearance = cloudflare_context["cf_clearance"]

    series = []
    token_symbol_to_token_map = json.load(
        open(os.path.join(os.path.dirname(__file__), "token_symbol_to_token_map.json"))
    )
    token_symbol_cache = FileSystemCache(base_dir=".cache/token_symbols")
    for token_symbol, token_dict in token_symbol_to_token_map.items():
        keys = [f"{token_symbol}.json"]
        token_symbol_cache_text = token_symbol_cache.get(keys=keys)
        if token_symbol_cache_text is not None:
            token_symbol_cache_dict = json.loads(token_symbol_cache_text)
            from_identifier_set = set(token_symbol_cache_dict["from_identifier_set"])
            to_identifier_set = set(token_symbol_cache_dict["to_identifier_set"])
            identifier_to_quantity_map = {
                tuple(k.split("|")): v
                for k, v in token_symbol_cache_dict[
                    "identifier_to_quantity_map"
                ].items()
            }
        else:
            from_identifier_set = set()
            to_identifier_set = set()
            identifier_to_quantity_map: Mapping[str, float] = defaultdict(lambda: 0.0)
            async with httpx.AsyncClient(timeout=None) as client:
                etherscan_scraper = EtherscanScraper(
                    client=client,
                    cf_clearance=cf_clearance,
                    user_agent=user_agent,
                    is_debugging=True,
                )
                for sender_address in token_dict.get("sender_addresses", []):
                    advanced_filter_dicts = await etherscan_scraper.get_advanced_filter(
                        from_address=sender_address,
                        token_address=token_dict["address"],
                    )
                    for advanced_filter_dict in advanced_filter_dicts:
                        from_identifier_set.add(sender_address)
                        to_identifier = advanced_filter_dict["to_address_name"]
                        if advanced_filter_dict["to_address_icon_title"] is not None:
                            to_identifier = f"{to_identifier} ({advanced_filter_dict['to_address_icon_title']})"
                        to_identifier_set.add(to_identifier)
                        identifier_to_quantity_map[
                            (sender_address, to_identifier)
                        ] += advanced_filter_dict["quantity"]
            token_symbol_cache.set(
                keys=keys,
                value=json.dumps(
                    {
                        "from_identifier_set": list(from_identifier_set),
                        "to_identifier_set": list(to_identifier_set),
                        "identifier_to_quantity_map": {
                            "|".join(k): v
                            for k, v in identifier_to_quantity_map.items()
                        },
                    }
                ),
            )

        token_price = token_dict["price"]
        nodes = [
            {"id": identifier, "column": 0} for identifier in from_identifier_set
        ] + [{"id": identifier, "column": 1} for identifier in to_identifier_set]
        links = [
            [from_identifier, to_identifier, quantity * token_price]
            for (
                from_identifier,
                to_identifier,
            ), quantity in identifier_to_quantity_map.items()
        ]
        series.append(
            {
                "name": token_symbol,
                "nodes": nodes,
                "links": links,
            }
        )
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "series": series,
        },
    )
