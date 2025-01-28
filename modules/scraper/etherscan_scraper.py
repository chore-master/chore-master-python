import asyncio
from datetime import datetime, timezone
from typing import Optional, TypedDict

import httpx
from bs4 import BeautifulSoup

from modules.utils.cache_utils import FileSystemCache


class EtherscanScraper:
    class AdvancedFilterDict(TypedDict):
        to_address: str
        to_address_name: Optional[str]
        quantity: float

    @staticmethod
    def parse_float(text: str) -> float:
        """
        Input: '597,839.482281'
        Output: 597839.482281
        """
        return float(text.strip().replace(",", ""))

    @staticmethod
    def parse_address(path: Optional[str] = None) -> str:
        """
        Input:
            path='/address/0xed80e4cca763de95000d915dd4b89d7092640128'
        Output: '0xed80e4cca763de95000d915dd4b89d7092640128'
        """
        if path is None:
            raise NotImplementedError
        return path.split("/")[-1]

    def __init__(
        self,
        client: httpx.AsyncClient,
        cf_clearance: str,
        user_agent: str,
        is_debugging: bool = False,
    ) -> None:
        self.client = client
        self.cf_clearance = cf_clearance
        self.user_agent = user_agent
        self.is_debugging = is_debugging
        self._file_system_cache = FileSystemCache(base_dir=".cache/etherscan_scraper")

    async def get_advanced_filter(
        self, from_address: str, token_address: str, page_count: Optional[int] = None
    ) -> list[AdvancedFilterDict]:
        # https://etherscan.io/advanced-filter?fadd=0xed80e4cca763de95000d915dd4b89d7092640128&tkn=0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee&ps=100&p=1
        current_page = 1
        advanced_filter_dicts = []
        ctx = [
            "[get_advanced_filter]",
            f"[from_address={from_address}, token_address={token_address}]",
        ]
        self._log(*ctx)
        while True:
            self._log(*ctx, f"[page={current_page}]")
            keys = [
                datetime.now(timezone.utc).strftime("%Y_%m_%d"),
                "advanced_filter",
                "from_addresses",
                from_address,
                "token_addresses",
                token_address,
                "pages",
                f"{current_page}.html",
            ]
            response_html = self._file_system_cache.get(keys=keys)
            if response_html is None:
                response = await self.client.get(
                    "https://etherscan.io/advanced-filter",
                    headers={
                        "User-Agent": self.user_agent,
                    },
                    cookies={
                        "cf_clearance": self.cf_clearance,
                    },
                    params={
                        "fadd": from_address,
                        "tkn": token_address,
                        "ps": 100,
                        "p": current_page,
                    },
                )
                response.raise_for_status()
                response_html = response.text
                self._file_system_cache.set(keys=keys, value=response_html)
                await asyncio.sleep(0.8)  # cool down
            soup = BeautifulSoup(response_html, "html.parser")
            if page_count is None:
                page_element = soup.select_one(
                    "#ContentPlaceHolder1_pageRecords > nav > ul > li:nth-child(3) > span"
                )
                if page_element is None:
                    break
                page_count = int(page_element.text.split(" ")[3])
            rows = soup.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                advanced_filter_dict = self.AdvancedFilterDict(
                    to_address=self.parse_address(cols[9].find("a")["href"]),
                    to_address_name=cols[9].text.strip(),
                    quantity=self.parse_float(cols[10].text),
                )
                advanced_filter_dicts.append(advanced_filter_dict)
            if current_page == page_count:
                break
            current_page += 1
        return advanced_filter_dicts

    def _log(self, *args):
        if self.is_debugging:
            print(f"[{self.__class__.__name__}]", *args)
