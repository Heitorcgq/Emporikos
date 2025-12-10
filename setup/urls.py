from django.contrib import admin
from django.urls import path
from apps.loja import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- ROTAS PRINCIPAIS (QUE FALTAVAM) ---
    # Rota da Home: Redireciona para a venda aberta ou cria uma nova
    path('', views.home_pdv, name='home_pdv'),
    # Rota da Tela de Vendas: Mostra o HTML do caixa
    path('pdv/<int:venda_id>/', views.frente_caixa, name='frente_caixa'),

    # --- NOVAS ROTAS PARA O CARRINHO (APIs) ---
    path('api/pdv/adicionar/<int:venda_id>/', views.api_adicionar_item, name='api_adicionar_item'),
    path('api/pdv/remover/<int:item_id>/', views.api_remover_item, name='api_remover_item'),
    path('api/pdv/atualizar-qtd/<int:item_id>/', views.api_atualizar_quantidade, name='api_atualizar_quantidade'),

    # --- CADASTROS E RELATÓRIOS ---
    path('produtos/novo/', views.cadastro_produto, name='cadastro_produto'),
    path('relatorios/vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    path('categorias/nova/', views.cadastro_categoria, name='cadastro_categoria'),
    path('relatorios/estoque/', views.relatorio_estoque, name='relatorio_estoque'),
    path('produtos/editar/<int:produto_id>/', views.editar_produto, name='editar_produto'),
    path('produtos/excluir/<int:produto_id>/', views.excluir_produto, name='excluir_produto'),
    path('relatorios/vendas/dashboard/', views.dashboard_vendas, name='dashboard_vendas'),
    
    # --- FUNCIONÁRIOS E CUPOM ---
    path('vendas/<int:venda_id>/cupom/', views.imprimir_cupom, name='imprimir_cupom'),
    path('gestao/funcionarios/', views.catalogo_funcionarios, name='catalogo_funcionarios'),
    path('gestao/funcionarios/editar/<int:funcionario_id>/', views.editar_funcionario, name='editar_funcionario'),
    path('gestao/funcionarios/excluir/<int:funcionario_id>/', views.excluir_funcionario, name='excluir_funcionario'),
    
    # --- BUSCA E CHECKOUT ---
    path('api/buscar-produto/', views.buscar_produto, name='buscar_produto'),    
    path('vendas/<int:venda_id>/checkout/', views.checkout, name='checkout'),
    
    # API para concluir (Deixei apenas uma vez)
    path('api/concluir-venda/<int:venda_id>/', views.concluir_venda, name='concluir_venda'),
]