from django.contrib import admin
from django.urls import path
from apps.loja import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('', views.frente_caixa, name='frente_caixa'),
    path('produtos/novo/', views.cadastro_produto, name='cadastro_produto'),
    path('relatorios/vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    path('categorias/nova/', views.cadastro_categoria, name='cadastro_categoria'),
    path('relatorios/estoque/', views.relatorio_estoque, name='relatorio_estoque'),
    path('produtos/editar/<int:produto_id>/', views.editar_produto, name='editar_produto'),
    path('produtos/excluir/<int:produto_id>/', views.excluir_produto, name='excluir_produto'),
    path('relatorios/vendas/dashboard/', views.dashboard_vendas, name='dashboard_vendas'),
    
    # Rotas "invisíveis" que o JavaScript vai chamar
    path('api/buscar-produto/', views.buscar_produto, name='buscar_produto'),
    
    path('api/iniciar-venda/', views.iniciar_venda, name='iniciar_venda'),
    
    # Tela de Checkout
    path('vendas/<int:venda_id>/checkout/', views.checkout, name='checkout'),
    
    # API para concluir
    path('api/concluir-venda/<int:venda_id>/', views.concluir_venda, name='concluir_venda'),
]