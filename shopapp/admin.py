# shopapp/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import path

from .admin_mixins import ExportAsCSVMixin
from .forms import OrderImportForm
from .models import Order, Product, ProductImage


class OrderInline(admin.TabularInline):
    model = Product.orders.through


class ProductInline(admin.StackedInline):
    model = ProductImage


@admin.action(description="Archive products")
def mark_archived(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
):
    queryset.update(archived=True)


@admin.action(description="Unarchive products")
def mark_unarchived(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
):

    queryset.update(archived=False)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin, ExportAsCSVMixin):
    actions = [
        mark_archived,
        mark_unarchived,
        "export_csv",
    ]
    inlines = [
        OrderInline,
        ProductInline,
    ]
    list_display = "pk", "name", "description_short", "price", "discount", "archived"
    list_display_links = "pk", "name"
    ordering = "-name", "pk"
    search_fields = "name", "description"
    fieldsets = [
        (
            None,
            {
                "fields": ("name", "description"),
            },
        ),
        (
            "Price options",
            {
                "fields": ("price", "discount"),
                "classes": ("wide", "collapse"),
            },
        ),
        (
            "Images",
            {
                "fields": ("preview",),
            },
        ),
        (
            "Extra options",
            {
                "fields": ("archived",),
                "classes": ("collapse",),
                "description": "Extra options. Field 'archived' is for soft delete",
            },
        ),
    ]

    def description_short(self, obj: Product) -> str:
        if len(obj.description) < 48:
            return obj.description
        return obj.description[:48] + "..."


class ProductInline(admin.StackedInline):
    model = Order.products.through


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/shopapp/order_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_orders),
                name="shopapp_order_import",
            ),
        ]
        return custom_urls + urls

    def import_orders(self, request):
        if request.method == "POST":
            form = OrderImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data["file"]
                self.process_file(file)
                self.message_user(request, "Orders imported successfully.")
                return redirect("..")
        else:
            form = OrderImportForm()

        context = {"form": form}
        return render(request, "admin/csv_form.html", context)

    def process_file(self, file):
        import csv
        from io import TextIOWrapper

        csv_reader = csv.DictReader(TextIOWrapper(file, encoding="utf-8"))
        for row in csv_reader:
            if "username" not in row:
                raise KeyError(f"Missing 'username' in row: {row}")
            user = User.objects.get(username=row["username"])
            order = Order.objects.create(
                user=user,
                delivery_address=row["delivery_address"],
                promocode=row["promocode"],
            )
            product_ids = row["product_ids"].split(",")
            for product_id in product_ids:
                product = Product.objects.get(id=product_id)
                order.products.add(product)
