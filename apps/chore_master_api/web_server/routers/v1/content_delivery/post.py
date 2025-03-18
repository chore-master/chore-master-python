from typing import Annotated

from fastapi import APIRouter, Header, Path

from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()

PROJECT_API_KEY = "DfuhFarHVvRKPt2y7doapje5"

posts = [
    {
        "reference": "post-1",
        "project_api_key": PROJECT_API_KEY,
        "title": "Post 1",
        "content": "Content 1",
    },
    {
        "reference": "post-2",
        "project_api_key": PROJECT_API_KEY,
        "title": "Post 2",
        "content": "Content 2",
    },
    {
        "reference": "post-3",
        "project_api_key": PROJECT_API_KEY,
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
async def get_posts(x_project_api_key: Annotated[str | None, Header()] = None):
    return ResponseSchema[list[ReadPostSummaryResponse]](
        status=StatusEnum.SUCCESS,
        data=[
            ReadPostSummaryResponse(
                reference=post["reference"],
                title=post["title"],
            )
            for post in posts
            if post["project_api_key"] == x_project_api_key
        ],
    )


@router.get("/posts/{post_reference}")
async def get_posts_post_reference(
    post_reference: Annotated[str, Path()],
    x_project_api_key: Annotated[str | None, Header()] = None,
):
    post = next(
        (
            post
            for post in posts
            if post["reference"] == post_reference
            and post["project_api_key"] == x_project_api_key
        ),
        None,
    )
    if not post:
        raise BadRequestError("Post not found")
    return ResponseSchema[ReadPostDetailResponse](status=StatusEnum.SUCCESS, data=post)
