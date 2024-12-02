from rest_framework import serializers

from .models import Order, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "pk",
            "name",
            "description",
            "price",
            "discount",
            "created_at",
            "archived",
            "preview",
        )


class OrderSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S%z")

    class Meta:
        model = Order
        fields = ["id", "delivery_address", "promocode", "created_at", "products"]
