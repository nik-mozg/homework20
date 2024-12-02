# shopapp/views.py
from timeit import default_timer

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from .forms import ProductForm
from .models import Order, Product, User
from .serializers import OrderSerializer, ProductSerializer


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ["name", "description"]
    filterset_fields = [
        "name",
        "description",
        "price",
        "discount",
        "archived",
    ]
    ordering_fields = [
        "name",
        "price",
        "discount",
    ]


class ShopIndexView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ("Laptop", 1999),
            ("Desktop", 2999),
            ("Smartphone", 999),
        ]
        context = {
            "time_running": default_timer(),
            "products": products,
        }
        return render(request, "shopapp/shop-index.html", context=context)


class ProductDetailsView(DetailView):
    template_name = "shopapp/products-details.html"
    queryset = Product.objects.prefetch_related("images")
    context_object_name = "product"


class ProductsListView(ListView):
    template_name = "shopapp/products-list.html"
    context_object_name = "products"
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(CreateView):
    model = Product
    fields = "name", "price", "description", "discount", "preview"
    success_url = reverse_lazy("shopapp:products_list")


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse(
            "shopapp:product_details",
            kwargs={"pk": self.object.pk},
        )


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class OrdersListView(LoginRequiredMixin, ListView):
    queryset = Order.objects.select_related("user").prefetch_related("products")


class OrderDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "shopapp.view_order"
    queryset = Order.objects.select_related("user").prefetch_related("products")


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        products = Product.objects.order_by("pk").all()
        products_data = [
            {
                "pk": product.pk,
                "name": product.name,
                "price": product.price,
                "archived": product.archived,
            }
            for product in products
        ]
        return JsonResponse({"products": products_data})


class LatestProductsFeed(Feed):
    title = "Latest Products"
    link = "/products/latest/feed/"
    description = "Updates on the latest products in the shop."

    def items(self):
        return Product.objects.order_by("-id")[:5]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return item.get_absolute_url()


class UserOrdersListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "shopapp/user_orders_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        self.owner = get_object_or_404(User, pk=self.kwargs["user_id"])
        return Order.objects.filter(user=self.owner).order_by("pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner
        return context


class UserOrdersExportView(LoginRequiredMixin, View):
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        cache_key = f"user_orders_{user_id}"
        data = cache.get(cache_key)

        if not data:
            orders = Order.objects.filter(user=user).order_by("pk")
            serializer = OrderSerializer(orders, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=60)  # Кеш на 1 минуту

        return JsonResponse(data, safe=False)
