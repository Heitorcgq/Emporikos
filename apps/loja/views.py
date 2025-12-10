import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from .models import Produto, Venda, ItensVenda, Categoria
from .forms import ProdutoForm, CategoriaForm, CadastroFuncionarioForm
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import TruncDay
from django.contrib.auth.models import Group, User
from django.contrib import messages

def checar_gerente(user):
    return user.is_superuser or user.groups.filter(name='Gerente').exists()

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
def catalogo_funcionarios(request):
    # Lógica de Cadastro (POST)
    if request.method == 'POST':
        form = CadastroFuncionarioForm(request.POST)
        if form.is_valid():
            try:
                # 1. Cria o usuário
                novo_usuario = form.save()
                
                # 2. Adiciona ao Grupo (Cargo)
                cargo_nome = form.cleaned_data['cargo']
                grupo = Group.objects.get(name=cargo_nome)
                novo_usuario.groups.add(grupo)
                
                messages.success(request, f"Funcionário {novo_usuario.username} cadastrado com sucesso!")
                return redirect('catalogo_funcionarios')
            except Exception as e:
                messages.error(request, f"Erro ao cadastrar: {e}")
        else:
            messages.error(request, "Erro no formulário. Verifique os dados.")
    else:
        form = CadastroFuncionarioForm()

    # Lógica de Listagem (GET)
    # Pega todos os usuários que não são superusuários (Admin técnico)
    funcionarios = User.objects.filter(is_superuser=False).order_by('username')

    return render(request, 'loja/funcionarios.html', {
        'funcionarios': funcionarios,
        'form': form
    })

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(User, id=funcionario_id)
    
    if request.method == 'POST':
        form = CadastroFuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            try:
                usuario_salvo = form.save()
                
                # Atualizar Cargo (Remove os antigos e adiciona o novo)
                usuario_salvo.groups.clear()
                grupo_novo = Group.objects.get(name=form.cleaned_data['cargo'])
                usuario_salvo.groups.add(grupo_novo)
                
                messages.success(request, f"Dados de {usuario_salvo.username} atualizados!")
                return redirect('catalogo_funcionarios')
            except Exception as e:
                messages.error(request, f"Erro ao atualizar: {e}")
    else:
        form = CadastroFuncionarioForm(instance=funcionario)
    
    return render(request, 'loja/editar_funcionario.html', {
        'form': form,
        'funcionario': funcionario
    })

@login_required
def frente_caixa(request):
    return render(request, 'loja/pdv.html')

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
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
            'codigo': p.codigo or '---',
            'tipo': p.tipo_venda
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
            quantidade = float(item['quantidade'])
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
@user_passes_test(checar_gerente, login_url='/pdv/')
def relatorio_vendas(request):
    # 1. Filtros Padrão (Datas)
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    vendedor_id = request.GET.get('vendedor')  # <--- NOVO: Pegamos o ID do vendedor

    vendas = Venda.objects.all().order_by('-data_venda')

    if data_inicio and data_fim:
        vendas = vendas.filter(data_venda__range=[data_inicio, data_fim])
    
    # 2. Filtro por Vendedor (NOVO)
    if vendedor_id:
        vendas = vendas.filter(vendedor_id=vendedor_id)
        vendedor_id = int(vendedor_id) # Converte para inteiro para marcar o select no HTML

    # 3. Totais
    total_faturado = vendas.aggregate(Sum('valor_final'))['valor_final__sum'] or 0
    total_vendas = vendas.count()
    ticket_medio = total_faturado / total_vendas if total_vendas > 0 else 0

    # 4. Lista de Funcionários para o Dropdown (Apenas ativos)
    funcionarios = User.objects.filter(is_active=True).order_by('username')

    return render(request, 'loja/relatorio_vendas.html', {
        'vendas': vendas,
        'total_faturado': total_faturado,
        'ticket_medio': ticket_medio,
        'total_vendas': total_vendas,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'funcionarios': funcionarios,         # <--- Enviamos a lista
        'vendedor_selecionado': vendedor_id,  # <--- Enviamos quem foi escolhido
    })

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
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
@user_passes_test(checar_gerente, login_url='/pdv/')
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
@user_passes_test(checar_gerente, login_url='/pdv/')
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
@user_passes_test(checar_gerente, login_url='/pdv/')
def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    produto.delete()
    return redirect('relatorio_estoque')

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
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
    dados_prod = [float(p['total_vendido']) for p in top_produtos]

    context = {
        'datas_grafico': json.dumps(datas_grafico),
        'valores_grafico': json.dumps(valores_grafico),
        'labels_pgto': json.dumps(labels_pgto),
        'dados_pgto': json.dumps(dados_pgto),
        'labels_prod': json.dumps(labels_prod),
        'dados_prod': json.dumps(dados_prod),
    }
    
    return render(request, 'loja/dashboard_vendas.html', context)

@login_required
def imprimir_cupom(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id)
    return render(request, 'loja/cupom.html', {'venda': venda})