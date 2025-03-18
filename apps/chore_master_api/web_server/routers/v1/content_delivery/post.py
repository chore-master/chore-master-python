from typing import Annotated

from fastapi import APIRouter, Path

from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()

posts = [
    {
        "reference": "post-1",
        "title": "Post 1",
        "content": "Content 1",
    },
    {
        "reference": "post-2",
        "title": "Post 2",
        "content": "Content 2",
    },
    {
        "reference": "post-3",
        "title": "Post 3",
        "content": """
# Test

~~yo~~

```python
print("Hello, world!")
```

<SampleComponent>Click me</SampleComponent>

""",
    },
]


class ReadPostSummaryResponse(BaseQueryEntityResponse):
    title: str


class ReadPostDetailResponse(BaseQueryEntityResponse):
    title: str
    content: str


@router.get("/posts")
async def get_posts():
    return ResponseSchema[list[ReadPostSummaryResponse]](
        status=StatusEnum.SUCCESS,
        data=[
            ReadPostSummaryResponse(
                reference=post["reference"],
                title=post["title"],
            )
            for post in posts
        ],
    )


@router.get("/posts/{post_reference}")
async def get_posts_post_reference(
    post_reference: Annotated[str, Path()],
):
    post = next((post for post in posts if post["reference"] == post_reference), None)
    if not post:
        raise BadRequestError("Post not found")
    return ResponseSchema[ReadPostDetailResponse](status=StatusEnum.SUCCESS, data=post)
