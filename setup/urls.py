from django.contrib import admin
from django.urls import path
from apps.loja import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota da tela principal do caixa
    path('', views.frente_caixa, name='frente_caixa'),
    path('produtos/novo/', views.cadastro_produto, name='cadastro_produto'),
    path('relatorios/vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    # Rotas "invisíveis" que o JavaScript vai chamar
    path('api/buscar-produto/', views.buscar_produto, name='buscar_produto'),
    path('api/salvar-venda/', views.salvar_venda, name='salvar_venda'),
]