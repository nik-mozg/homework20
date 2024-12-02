from django.contrib.sitemaps import Sitemap

from .models import Product


class ShopSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.all()

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, "updated_at") else None
