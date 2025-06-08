from typing import Optional
from fastapi import Request


async def get_user(request: Request) -> Optional[dict]:
    return request.state.user

def template_context(request: Request):
    """Global template context processor"""
    return {
        "user": request.state.user,
        "is_authenticated": request.state.user is not None
    }
