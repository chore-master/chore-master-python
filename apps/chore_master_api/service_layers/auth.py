import httpx


async def get_is_turnstile_token_valid(
    verify_url: str, secret_key: str, token: str
) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            verify_url,
            data={
                "secret": secret_key,
                "response": token,
            },
        )
        result = response.json()
        return result.get("success", False)
