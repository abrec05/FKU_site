from django.db import models

class CheckedExcel(models.Model):
    sha256 = models.CharField(max_length=64, unique=True)
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="checked_excels/%Y/%m/%d/")
    size = models.BigIntegerField(default=0)

    # откуда взяли
    source = models.CharField(
        max_length=32,
        choices=[
            ("diagram", "Проверка диаграммы (Excel-заказ)"),
            ("order_params", "Проверка заказа → Проверка параметров"),
        ],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_name} ({self.source})"
