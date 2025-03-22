from typing import Optional

import asgi_sitemaps
from asgi_sitemaps._types import ItemsTypes, T
from sqlalchemy import select

from db.models import Rout
from db.database import get_session


class Sitemap(asgi_sitemaps.Sitemap):

    def items(self) -> ItemsTypes:
        return ["/", "/for-creators"]

    def location(self, item: T) -> str:
        return item

    def changefreq(self, item: T) -> Optional[str]:
        return "monthly"

    def priority(self, item: T) -> float:
        return 1

class SitemapUtils(asgi_sitemaps.Sitemap):
    def items(self) -> ItemsTypes:
        return ["/shop", "/login", "/register"]

    def location(self, item: T) -> str:
        return item

    def changefreq(self, item: T) -> Optional[str]:
        return "monthly"


    def priority(self, item: T) -> float:
        return 0.8

class SitemapTours(asgi_sitemaps.Sitemap):
    async def items(self) -> list[dict]:
        async for session in get_session():
            async with session.begin():
                query = select(Rout.id).where(Rout.is_displayed == True).order_by(Rout.updated_at.desc())
                result = await session.execute(query)
                tours = result.scalars().all()
        return tours

    def location(self, item: T) -> str:
        return f'tour/{item}'

    def changefreq(self, item: T) -> Optional[str]:
        return "monthly"

sitemap = asgi_sitemaps.SitemapApp([Sitemap(), SitemapUtils(), SitemapTours()], domain='pocketour.online')