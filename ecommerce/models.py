from django.db import models


class LineOrder(models.Model):
    quantity = models.IntegerField()
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    shipping_details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.quantity} units"
