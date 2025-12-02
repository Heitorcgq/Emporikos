import json
from django.shortcuts import render, redirect
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
def salvar_venda(request):
    if request.method == 'POST':
        dados = json.loads(request.body)
        carrinho = dados.get('carrinho')

        # 1. Cria a venda
        usuario = request.user if request.user.is_authenticated else None
        venda = Venda.objects.create(
            vendedor=usuario,
            valor_total=0
        )

        total_venda = 0
        
        # 2. Processa cada item do carrinho
        for item in carrinho:
            produto_id = item['id']
            quantidade = int(item['quantidade'])
            
            produto = Produto.objects.get(id=produto_id)
            preco_momento = produto.preco_venda
            
            # Cria o item da venda
            ItensVenda.objects.create(
                venda=venda,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco_momento,
                subtotal=quantidade * preco_momento
            )
            
            # Atualiza total geral
            total_venda += (quantidade * preco_momento)
            
            # 3. Baixa o Estoque
            produto.estoque_atual -= quantidade
            produto.save()
        
        # Atualiza o valor final da venda
        venda.valor_total = total_venda
        venda.save()
        
        return JsonResponse({'status': 'sucesso', 'venda_id': venda.id})
    
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
