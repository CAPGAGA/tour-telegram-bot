from typing import Optional

import asgi_sitemaps
from asgi_sitemaps._types import ItemsTypes, T


class Sitemap(asgi_sitemaps.Sitemap):

    def items(self) -> ItemsTypes:
        return ["/"]

    def location(self, item: T) -> str:
        return item

    def changefreq(self, item: T) -> Optional[str]:
        return "monthly"

    def priority(self, item: T) -> float:
        return 1

sitemap = asgi_sitemaps.SitemapApp(Sitemap(), domain='pocketour.online')