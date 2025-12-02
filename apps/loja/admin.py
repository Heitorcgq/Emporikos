from django.contrib import admin
from .models import Categoria, Produto, Venda, ItensVenda

class ItensVendaInline(admin.TabularInline):
    model = ItensVenda
    extra = 1

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco_venda', 'estoque_atual')
    search_fields = ('nome', 'codigo')
    list_filter = ('categoria',)

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_venda', 'vendedor', 'valor_total')
    inlines = [ItensVendaInline]

admin.site.register(Categoria)