from fastapi import Request

async def get_auth_token(request: Request):
    return request.cookies.get('auth_token')