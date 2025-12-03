from django.contrib import admin
from django.urls import path
from apps.loja import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.frente_caixa, name='frente_caixa'),
    path('produtos/novo/', views.cadastro_produto, name='cadastro_produto'),
    path('relatorios/vendas/', views.relatorio_vendas, name='relatorio_vendas'),

    
    # Rotas "invisíveis" que o JavaScript vai chamar
    path('api/buscar-produto/', views.buscar_produto, name='buscar_produto'),
    
    path('api/iniciar-venda/', views.iniciar_venda, name='iniciar_venda'),
    
    # Tela de Checkout
    path('vendas/<int:venda_id>/checkout/', views.checkout, name='checkout'),
    
    # API para concluir
    path('api/concluir-venda/<int:venda_id>/', views.concluir_venda, name='concluir_venda'),
]