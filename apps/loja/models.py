from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome
    
class Produto(models.Model):
    TIPO_VENDA_CHOICES = [
        ('UN', 'Unidade (Inteiro)'),
        ('FR', 'Fração / Metro / Kg (Decimal)'),
    ]

    nome = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    tipo_venda = models.CharField(max_length=2, choices=TIPO_VENDA_CHOICES, default='UN', verbose_name="Tipo de Venda")
    preco_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Custo")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    codigo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    detalhes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.detalhes}"
    
class Venda(models.Model):
    FORMA_PAGAMENTO_CHOICES = [
        ('DIN', 'Dinheiro'),
        ('CRE', 'Cartão de Crédito'),
        ('DEB', 'Cartão de Débito'),
        ('PIX', 'Pix'),
    ]

    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('C', 'Concluído'),
        ('X', 'Cancelado'),
    ]

    vendedor = models.ForeignKey(User, on_delete=models.PROTECT)
    data_venda = models.DateField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    acrescimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    forma_pagamento = models.CharField(max_length=3, choices=FORMA_PAGAMENTO_CHOICES, default='DIN')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')

    def __str__(self):
        return f"Venda #{self.id} - {self.get_status_display()}"
    
class ItensVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)