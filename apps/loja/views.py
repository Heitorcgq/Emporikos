import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from .models import Produto, Venda, ItensVenda, Categoria
from .forms import ProdutoForm, CategoriaForm
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import TruncDay

@login_required
def frente_caixa(request):
    return render(request, 'loja/pdv.html')

@login_required
def cadastro_produto(request):
    if request.method == 'POST':
        # Se o usuário enviou dados (clicou em Salvar)
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            # Redireciona de volta para a mesma tela para cadastrar outro, ou para o PDV
            return redirect('cadastro_produto') 
    else:
        # Se o usuário está apenas entrando na página
        form = ProdutoForm()

    return render(request, 'loja/cadastro_produto.html', {'form': form})

def buscar_produto(request):
    termo = request.GET.get('termo')
    produtos = Produto.objects.filter(
        nome__icontains=termo
    ) | Produto.objects.filter(
        codigo__icontains=termo
    )
    
    dados = []
    for p in produtos[:10]:
        dados.append({
            'id': p.id,
            'nome': p.nome,
            'preco': float(p.preco_venda),
            'codigo': p.codigo or '---'
        })
    
    return JsonResponse(dados, safe=False)

@csrf_exempt
def iniciar_venda(request):
    """
    ETAPA 1: Recebe os itens do PDV, cria a venda PENDENTE e retorna o ID.
    NÃO baixa estoque aqui ainda.
    """
    if request.method == 'POST':
        dados = json.loads(request.body)
        carrinho = dados.get('carrinho')
        
        usuario = request.user if request.user.is_authenticated else None
        
        # Cria venda PENDENTE
        venda = Venda.objects.create(
            vendedor=usuario,
            status='P', # Pendente
            valor_total=0,
            valor_final=0
        )
        
        total_itens = 0
        
        for item in carrinho:
            produto = Produto.objects.get(id=item['id'])
            quantidade = int(item['quantidade'])
            preco = float(produto.preco_venda)
            
            ItensVenda.objects.create(
                venda=venda,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco,
                subtotal=quantidade * preco
            )
            total_itens += (quantidade * preco)
        
        venda.valor_total = total_itens
        venda.valor_final = total_itens # Inicialmente é igual, sem desconto
        venda.save()
        
        # Retorna o ID para o Javascript redirecionar
        return JsonResponse({'status': 'sucesso', 'venda_id': venda.id})
        
    return JsonResponse({'status': 'erro'}, status=400)

@login_required
def checkout(request, venda_id):
    """
    ETAPA 2: Renderiza a tela de pagamento
    """
    venda = get_object_or_404(Venda, id=venda_id)
    
    # Se já foi concluída, não deixa pagar de novo
    if venda.status == 'C':
        return redirect('frente_caixa')
        
    return render(request, 'loja/checkout.html', {'venda': venda})

@csrf_exempt
def concluir_venda(request, venda_id):
    """Finaliza a venda e BAIXA O ESTOQUE (com proteção contra negativo infinito)."""
    if request.method == 'POST':
        venda = get_object_or_404(Venda, id=venda_id)
        
        if venda.status == 'C':
            return JsonResponse({'status': 'erro', 'mensagem': 'Venda já concluída'})

        dados = json.loads(request.body)
        
        # Atualiza dados financeiros
        venda.desconto = float(dados.get('desconto', 0))
        venda.acrescimo = float(dados.get('acrescimo', 0))
        venda.valor_final = float(dados.get('valor_final', venda.valor_total))
        venda.forma_pagamento = dados.get('forma_pagamento', 'DIN')
        venda.status = 'C' # Concluída
        venda.save()
        
        # Lista para guardar nomes de produtos que já estavam zerados
        itens_sem_baixa = []

        # Baixa Estoque com Condição
        for item in venda.itensvenda_set.all():
            produto = item.produto
            
            # REGRA: Só desconta se tiver estoque positivo
            if produto.estoque_atual > 0:
                produto.estoque_atual -= item.quantidade
                produto.save()
            else:
                # Se já for 0 ou negativo, não faz nada e avisa
                itens_sem_baixa.append(produto.nome)
        
        # Prepara a resposta
        resposta = {'status': 'sucesso'}
        
        # Se houve algum item que não baixou estoque, avisamos
        if itens_sem_baixa:
            nomes = ", ".join(itens_sem_baixa)
            resposta['aviso'] = f"Venda concluída! Porém, estes itens já estavam esgotados e o estoque não foi alterado: {nomes}"
            
        return JsonResponse(resposta)
        
    return JsonResponse({'status': 'erro'}, status=400)

@login_required
def relatorio_vendas(request):
    # Datas padrão: Do dia 1 do mês atual até hoje
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    data_inicio = request.GET.get('data_inicio', inicio_mes.strftime('%Y-%m-%d'))
    data_fim = request.GET.get('data_fim', hoje.strftime('%Y-%m-%d'))

    # Filtra as vendas
    vendas = Venda.objects.filter(
        data_venda__gte=data_inicio,
        data_venda__lte=data_fim
    ).order_by('-data_venda')

    # Calcula totais
    total_faturamento = vendas.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_pedidos = vendas.count()

    context = {
        'vendas': vendas,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'total_faturamento': total_faturamento,
        'total_pedidos': total_pedidos,
    }
    
    return render(request, 'loja/relatorio_vendas.html', context)

@login_required
def cadastro_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cadastro_categoria')
    else:
        form = CategoriaForm

    categorias_existentes = Categoria.objects.all().order_by('nome')

    return render(request, 'loja/cadastro_categoria.html', {
        'form': form, 
        'categorias': categorias_existentes # Passamos a lista para o HTML
    })


@login_required
def relatorio_estoque(request):
    produtos = Produto.objects.all().order_by('nome')
    categorias = Categoria.objects.all().order_by('nome')

    categoria_id = request.GET.get('categoria')
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)
    
    baixo_estoque = request.GET.get('baixo')
    if baixo_estoque:
        produtos = produtos.filter(estoque_atual__lte=10)
    
    valor_total_estoque = 0
    for p in produtos:
        valor_total_estoque += (p.preco_compra * p.estoque_atual)

    context = {
        'produtos': produtos,
        'categorias': categorias,
        'valor_total_estoque': valor_total_estoque,
        'total_itens': produtos.count(),
        'filtro_categoria': int(categoria_id) if categoria_id else None,
        'filtro_baixo': baixo_estoque
    }
    
    return render(request, 'loja/relatorio_estoque.html', context)


@login_required
def editar_produto(request, produto_id):
    # Busca o produto ou dá erro 404 se não existir
    produto = get_object_or_404(Produto, id=produto_id)
    
    if request.method == 'POST':
        # Carrega o formulário COM os dados do produto (instance=produto)
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('relatorio_estoque') # Volta para a lista de estoque
    else:
        # Preenche o formulário com os dados atuais
        form = ProdutoForm(instance=produto)
    
    return render(request, 'loja/editar_produto.html', {'form': form, 'produto': produto})

@login_required
def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    produto.delete()
    return redirect('relatorio_estoque')

@login_required
def dashboard_vendas(request):
    # Data de corte (últimos 30 dias)
    data_limite = timezone.now() - timedelta(days=30)
    
    # 1. GRÁFICO DE VENDAS DIÁRIAS (Linha)
    # Agrupa vendas por dia e soma o valor total
    vendas_diarias = Venda.objects.filter(
        data_venda__gte=data_limite, status='C'
    ).annotate(
        dia=TruncDay('data_venda')
    ).values('dia').annotate(
        total=Sum('valor_total')
    ).order_by('dia')
    
    # Prepara listas para o Javascript
    datas_grafico = [v['dia'].strftime('%d/%m') for v in vendas_diarias]
    valores_grafico = [float(v['total']) for v in vendas_diarias]

    # 2. GRÁFICO DE FORMAS DE PAGAMENTO (Rosca)
    vendas_pagamento = Venda.objects.filter(status='C').values('forma_pagamento').annotate(
        qtd=Count('id')
    )
    
    labels_pgto = [v['forma_pagamento'] for v in vendas_pagamento]
    dict_pgto = dict(Venda.FORMA_PAGAMENTO_CHOICES)
    labels_pgto = [dict_pgto.get(l, l) for l in labels_pgto]
    
    dados_pgto = [v['qtd'] for v in vendas_pagamento]

    # 3. TOP 5 PRODUTOS MAIS VENDIDOS (Barras)
    top_produtos = ItensVenda.objects.values(
        'produto__nome'
    ).annotate(
        total_vendido=Sum('quantidade')
    ).order_by('-total_vendido')[:5]
    
    labels_prod = [p['produto__nome'] for p in top_produtos]
    dados_prod = [p['total_vendido'] for p in top_produtos]

    context = {
        'datas_grafico': json.dumps(datas_grafico),
        'valores_grafico': json.dumps(valores_grafico),
        'labels_pgto': json.dumps(labels_pgto),
        'dados_pgto': json.dumps(dados_pgto),
        'labels_prod': json.dumps(labels_prod),
        'dados_prod': json.dumps(dados_prod),
    }
    
    return render(request, 'loja/dashboard_vendas.html', context)