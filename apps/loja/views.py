import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Produto, Venda, ItensVenda
from .forms import ProdutoForm
from datetime import datetime, timedelta
from django.utils import timezone

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
    """
    ETAPA 3: Recebe os dados de pagamento, BAIXA O ESTOQUE e finaliza.
    """
    if request.method == 'POST':
        venda = get_object_or_404(Venda, id=venda_id)
        
        if venda.status == 'C':
            return JsonResponse({'status': 'erro', 'mensagem': 'Venda já concluída'})

        dados = json.loads(request.body)
        
        # Atualiza valores
        venda.desconto = float(dados.get('desconto', 0))
        venda.acrescimo = float(dados.get('acrescimo', 0))
        venda.valor_final = float(dados.get('valor_final', venda.valor_total))
        venda.forma_pagamento = dados.get('forma_pagamento', 'DIN')
        venda.status = 'C' # CONCLUÍDA
        venda.save()
        
        # AGORA SIM: Baixa o estoque
        for item in venda.itensvenda_set.all():
            produto = item.produto
            produto.estoque_atual -= item.quantidade
            produto.save()
            
        return JsonResponse({'status': 'sucesso'})
        
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
