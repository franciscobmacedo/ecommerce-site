from django.contrib import admin
from django.urls import path

from ecommerce import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("purchase", views.purchase, name="purchase"),
    path("purchase_success", views.purchase_success, name="purchase_success"),
    path("webhook", views.webhook, name="webhook"),
]
