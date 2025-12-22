import json
import calendar
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from .models import Produto, Venda, ItensVenda, Categoria, Fornecedor
from .forms import ProdutoForm, CategoriaForm, CadastroFuncionarioForm, FornecedorForm
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import TruncDay
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.db import transaction
from django.db.models.functions import TruncDay, TruncHour

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
@user_passes_test(checar_gerente, login_url='/pdv/')
def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(User, id=funcionario_id)
    
    # Segurança: Impede excluir superusuários (Admin)
    if funcionario.is_superuser:
        messages.error(request, "Não é permitido excluir um Administrador do sistema.")
        return redirect('catalogo_funcionarios')
    
    # Segurança: Impede excluir a si mesmo
    if funcionario == request.user:
        messages.error(request, "Você não pode excluir seu próprio usuário.")
        return redirect('catalogo_funcionarios')

    try:
        nome = funcionario.username
        funcionario.delete()
        messages.success(request, f"Funcionário '{nome}' excluído com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro ao excluir: {e}")
        
    return redirect('catalogo_funcionarios')

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
def catalogo_fornecedores(request):
    # Lógica de Adicionar (POST)
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Fornecedor cadastrado com sucesso!")
                return redirect('catalogo_fornecedores')
            except Exception as e:
                messages.error(request, f"Erro ao cadastrar: {e}")
        else:
            messages.error(request, "Erro no formulário. Verifique os dados.")
    else:
        form = FornecedorForm()

    # Listagem (Ordem alfabética por Empresa)
    fornecedores = Fornecedor.objects.all().order_by('empresa')

    return render(request, 'loja/fornecedores.html', {
        'fornecedores': fornecedores,
        'form': form
    })

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
def editar_fornecedor(request, fornecedor_id):
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dados de '{fornecedor.empresa}' atualizados!")
            return redirect('catalogo_fornecedores')
    else:
        form = FornecedorForm(instance=fornecedor)
    
    return render(request, 'loja/editar_fornecedor.html', {
        'form': form,
        'fornecedor': fornecedor
    })

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
def excluir_fornecedor(request, fornecedor_id):
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
    nome = fornecedor.empresa
    fornecedor.delete()
    messages.success(request, f"Fornecedor '{nome}' removido.")
    return redirect('catalogo_fornecedores')


@login_required
def home_pdv(request):
    """
    Função 1: O porteiro Inteligente.
    """
    usuario = request.user

    # 1. Busca qualquer venda pendente deste usuário
    venda_pendente = Venda.objects.filter(vendedor=usuario, status='P').first()

    if venda_pendente:
        # Se achou uma pendente, usa ela mesma (não cria outra)
        return redirect('frente_caixa', venda_id=venda_pendente.id)
    
    # 2. Se não tem nenhuma pendente, cria uma nova
    nova_venda = Venda.objects.create(vendedor=usuario, status='P')
    return redirect('frente_caixa', venda_id=nova_venda.id)

@login_required
def frente_caixa(request, venda_id):
    """
    Função 2: A tela do Caixa.
    OBRIGATORIAMENTE recebe um ID.
    """
    # Garante que a venda existe
    venda = get_object_or_404(Venda, id=venda_id)
    
    # --- TRAVA DE SEGURANÇA ---
    # Se a venda já foi Concluída ('C') ou Cancelada ('X'), 
    # não permite abrir o PDV para edição.
    if venda.status in ['C', 'X']:
        messages.warning(request, f"A Venda #{venda.id} já foi finalizada e não pode ser alterada.")
        # Redireciona para o relatório (onde ele pode ver os detalhes, mas não editar)
        return redirect('relatorio_vendas')

    # Verifica se pertence ao usuário (opcional, dependendo da sua regra de negócio)
    # Se quiser que gerente edite venda de caixa, remova o "vendedor=request.user" abaixo
    if not checar_gerente(request.user) and venda.vendedor != request.user:
         messages.error(request, "Você não tem permissão para acessar esta venda.")
         return redirect('home_pdv')

    itens = venda.itensvenda_set.all()

    context = {
        'venda': venda,
        'itens': itens,
        'venda_id': venda.id
    }
    
    return render(request, 'loja/pdv.html', context)




@csrf_exempt
def api_adicionar_item(request, venda_id):
    if request.method == 'POST':
        venda = get_object_or_404(Venda, id=venda_id)
        
        # --- TRAVA DE SEGURANÇA ---
        if venda.status != 'P':
            return JsonResponse({'status': 'erro', 'mensagem': 'Venda fechada não pode ser alterada.'}, status=403)
            
        data = json.loads(request.body)
        produto_codigo = data.get('codigo')
        produto = get_object_or_404(Produto, codigo=produto_codigo) 
        
        # ... (restante do código igual) ...
        
        item_existente = venda.itensvenda_set.filter(produto=produto).first()
        
        if item_existente:
            item_existente.quantidade += 1
            item_existente.save()
        else:
            ItensVenda.objects.create(
                venda=venda,
                produto=produto,
                quantidade=1,
                preco_unitario=produto.preco_venda,
                subtotal=produto.preco_venda
            )
            
        venda.valor_total = sum(item.subtotal for item in venda.itensvenda_set.all())
        venda.valor_final = venda.valor_total
        venda.save()
    
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro'}, status=400)

@csrf_exempt
def api_remover_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(ItensVenda, id=item_id)
        venda = item.venda
        
        # --- TRAVA DE SEGURANÇA ---
        if venda.status != 'P':
            return JsonResponse({'status': 'erro', 'mensagem': 'Venda fechada não pode ser alterada.'}, status=403)

        item.delete()
        
        # Recalcula total da venda
        venda.valor_total = sum(i.subtotal for i in venda.itensvenda_set.all())
        venda.valor_final = venda.valor_total
        venda.save()
        
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro'}, status=400)

@csrf_exempt
def api_atualizar_quantidade(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(ItensVenda, id=item_id)
        venda = item.venda
        
        # --- TRAVA DE SEGURANÇA ---
        if venda.status != 'P':
            return JsonResponse({'status': 'erro', 'mensagem': 'Venda fechada não pode ser alterada.'}, status=403)
            
        data = json.loads(request.body)
        nova_qtd = Decimal(str(data.get('quantidade')))
        
        item.quantidade = nova_qtd
        item.save()
        
        venda.valor_total = sum(i.subtotal for i in venda.itensvenda_set.all())
        venda.valor_final = venda.valor_total
        venda.save()
        
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro'}, status=400)

@csrf_exempt
def api_limpar_venda(request, venda_id):
    if request.method == 'POST':
        venda = get_object_or_404(Venda, id=venda_id)
        
        # --- TRAVA DE SEGURANÇA ---
        if venda.status != 'P':
            return JsonResponse({'status': 'erro', 'mensagem': 'Venda fechada não pode ser limpa.'}, status=403)
        
        # Apaga todos os itens desta venda
        venda.itensvenda_set.all().delete()
        
        # Zera os totais
        venda.valor_total = 0
        venda.valor_final = 0
        venda.save()
        
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro'}, status=400)

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
        return redirect('frente_caixa', venda_id=venda.id)
    
    # [NOVO] Se não tem itens, chuta de volta para o caixa
    if not venda.itensvenda_set.exists():
        # Opcional: Adicionar mensagem de erro (requer configurar messages no template)
        return redirect('frente_caixa', venda_id=venda.id)
        
    return render(request, 'loja/checkout.html', {'venda': venda})

@transaction.atomic
@csrf_exempt
def concluir_venda(request, venda_id):
    """Finaliza a venda, BAIXA O ESTOQUE e avisa se algo zerou."""
    if request.method == 'POST':
        venda = get_object_or_404(Venda, id=venda_id)
        
        if venda.status == 'C':
            return JsonResponse({'status': 'erro', 'mensagem': 'Venda já concluída'})

        dados = json.loads(request.body)
        
        # 1. Captura e Valida Valores
        novo_valor_final = float(dados.get('valor_final', venda.valor_total))
        valor_recebido = float(dados.get('valor_recebido', 0))
        desconto = float(dados.get('desconto', 0))
        acrescimo = float(dados.get('acrescimo', 0))
        forma_pagamento = dados.get('forma_pagamento', 'DIN')

        # Trava de Segurança (Backend)
        if forma_pagamento == 'DIN':
            if valor_recebido < (novo_valor_final - 0.01):
                return JsonResponse({
                    'status': 'erro', 
                    'mensagem': f'Valor recebido (R$ {valor_recebido:.2f}) é menor que o total.'
                }, status=400)

        # 2. Atualiza Venda
        venda.desconto = desconto
        venda.acrescimo = acrescimo
        venda.valor_final = novo_valor_final
        venda.valor_recebido = valor_recebido
        venda.forma_pagamento = forma_pagamento
        venda.data_venda = timezone.now()
        venda.status = 'C'
        venda.save()
        
        # Listas para notificações
        itens_sem_baixa = []   # Já estava zerado antes
        itens_que_zeraram = [] # Zerou AGORA com essa venda

        # 3. Baixa Estoque
        for item in venda.itensvenda_set.all():
            produto = item.produto
            
            if produto.estoque_atual > 0:
                # Salva o estoque antigo para comparação (opcional, mas bom pra debug)
                estoque_antigo = produto.estoque_atual
                
                # Baixa normal
                produto.estoque_atual -= item.quantidade 
                produto.save()
                
                # --- NOVA LÓGICA DE NOTIFICAÇÃO ---
                # Se após a baixa o estoque ficou <= 0, avisa que acabou!
                if produto.estoque_atual <= 0:
                    itens_que_zeraram.append(produto.nome)
                    
            else:
                # Se já era 0 ou negativo antes de começar
                itens_sem_baixa.append(produto.nome)
        
        # 4. Prepara a Resposta com os Avisos
        resposta = {'status': 'sucesso'}
        avisos = []

        if itens_sem_baixa:
            nomes = ", ".join(itens_sem_baixa)
            avisos.append(f"⛔ ESTOQUE INALTERADO: Os seguintes itens já estavam esgotados: {nomes}")
        
        if itens_que_zeraram:
            nomes = ", ".join(itens_que_zeraram)
            avisos.append(f"⚠️ ESTOQUE ACABOU: Os seguintes itens esgotaram nesta venda: {nomes}")

        if avisos:
            resposta['aviso'] = "\n\n".join(avisos)
            
        return JsonResponse(resposta)
        
    return JsonResponse({'status': 'erro'}, status=400)

@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
def relatorio_vendas(request):
    # 1. Captura os parâmetros do formulário
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    vendedor_id = request.GET.get('vendedor')
    venda_id = request.GET.get('venda_id') # <--- Novo campo

    # 2. Base: Apenas vendas concluídas
    vendas = Venda.objects.filter(status='C').order_by('-data_venda')

    # 3. Lógica de Filtragem (Prioridade para o ID)
    if venda_id:
        # Se digitou um ID, filtramos EXATAMENTE ele e ignoramos datas/vendedor
        vendas = vendas.filter(id=venda_id)
    else:
        # Se NÃO digitou ID, aplicamos os filtros normais de período e vendedor
        if data_inicio and data_fim:
            vendas = vendas.filter(data_venda__range=[data_inicio, data_fim])
        
        if vendedor_id:
            vendas = vendas.filter(vendedor_id=vendedor_id)
            vendedor_id = int(vendedor_id)

    # 4. Totais (Calculados sobre o resultado filtrado)
    total_faturado = vendas.aggregate(Sum('valor_final'))['valor_final__sum'] or 0
    total_vendas = vendas.count()
    ticket_medio = total_faturado / total_vendas if total_vendas > 0 else 0

    # 5. Lista para o Dropdown
    funcionarios = User.objects.filter(is_active=True).order_by('username')

    return render(request, 'loja/relatorio_vendas.html', {
        'vendas': vendas,
        'total_faturado': total_faturado,
        'ticket_medio': ticket_medio,
        'total_vendas': total_vendas,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'funcionarios': funcionarios,
        'vendedor_selecionado': vendedor_id,
        'venda_id_busca': venda_id,
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

    # 1. Filtro por Categoria
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)
    
    # 2. Filtro por Termo (Nome ou Código)
    termo = request.GET.get('termo')
    if termo:
        produtos = produtos.filter(
            Q(nome__icontains=termo) | Q(codigo__icontains=termo)
        )

    # 3. Filtros de Status (Baixo ou Esgotado)
    esgotado = request.GET.get('esgotado') 
    baixo_estoque = request.GET.get('baixo')
    
    if esgotado and baixo_estoque:
        produtos = produtos.filter(estoque_atual__lte=10)
    
    elif esgotado:
        produtos = produtos.filter(estoque_atual__lte=0)
        
    elif baixo_estoque:
        produtos = produtos.filter(estoque_atual__lte=10, estoque_atual__gt=0)
    # Totais
    valor_total_estoque = 0
    for p in produtos:
        valor_total_estoque += (p.preco_compra * p.estoque_atual)

    context = {
        'produtos': produtos,
        'categorias': categorias,
        'valor_total_estoque': valor_total_estoque,
        'total_itens': produtos.count(),
        'filtro_categoria': int(categoria_id) if categoria_id else None,
        'filtro_baixo': baixo_estoque,
        'filtro_esgotado': esgotado,
        'termo_busca': termo
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
    # 1. Definição do Período (Filtros)
    hoje = timezone.now()
    
    # Captura parâmetros da URL
    mes_filtro = request.GET.get('mes', hoje.month) 
    ano_filtro = request.GET.get('ano', hoje.year)
    dia_filtro = request.GET.get('dia', '') # Padrão vazio = Todos

    # Validação e Conversão
    try:
        mes_filtro = int(mes_filtro)
        ano_filtro = int(ano_filtro)
    except ValueError:
        mes_filtro = hoje.month
        ano_filtro = hoje.year
        
    # Valida o dia (se foi informado)
    dia_selecionado = None
    if dia_filtro and dia_filtro.isdigit():
        dia_selecionado = int(dia_filtro)

    # 2. Filtragem Base (Ano e Mês são obrigatórios)
    vendas_periodo = Venda.objects.filter(
        data_venda__year=ano_filtro,
        data_venda__month=mes_filtro,
        status='C'
    )
    
    # Se escolheu um dia específico, filtra também pelo dia
    if dia_selecionado:
        vendas_periodo = vendas_periodo.filter(data_venda__day=dia_selecionado)

    # --- GRÁFICO 1: EVOLUÇÃO (LINHA) ---
    # Lógica Inteligente: Se filtrou por DIA, mostra por HORA. Se é MÊS, mostra por DIA.
    
    if dia_selecionado:
        # Agrupa por HORA
        vendas_timeline = vendas_periodo.annotate(
            periodo=TruncHour('data_venda')
        ).values('periodo').annotate(
            total=Sum('valor_final')
        ).order_by('periodo')
        
        # Formato: 08:00, 09:00...
        datas_grafico = [v['periodo'].strftime('%H:00') for v in vendas_timeline]
        titulo_grafico1 = f"Vendas por Hora ({dia_selecionado}/{mes_filtro})"
    else:
        # Agrupa por DIA (Padrão)
        vendas_timeline = vendas_periodo.annotate(
            periodo=TruncDay('data_venda')
        ).values('periodo').annotate(
            total=Sum('valor_final')
        ).order_by('periodo')
        
        # Formato: 01/12, 02/12...
        datas_grafico = [v['periodo'].strftime('%d/%m') for v in vendas_timeline]
        titulo_grafico1 = "Evolução Diária"

    valores_grafico = [float(v['total']) for v in vendas_timeline]

    # --- GRÁFICO 2: FORMAS DE PAGAMENTO (Rosca) ---
    vendas_pagamento = vendas_periodo.values('forma_pagamento').annotate(
        qtd=Count('id')
    )
    
    dict_pgto = dict(Venda.FORMA_PAGAMENTO_CHOICES)
    labels_pgto = [dict_pgto.get(v['forma_pagamento'], v['forma_pagamento']) for v in vendas_pagamento]
    dados_pgto = [v['qtd'] for v in vendas_pagamento]

    # --- GRÁFICO 3: TOP PRODUTOS (Barras) ---
    top_produtos = ItensVenda.objects.filter(
        venda__in=vendas_periodo
    ).values(
        'produto__nome'
    ).annotate(
        total_vendido=Sum('quantidade')
    ).order_by('-total_vendido')[:5]
    
    labels_prod = [p['produto__nome'] for p in top_produtos]
    dados_prod = [float(p['total_vendido']) for p in top_produtos]

    # --- GRÁFICO 4: TOP VENDEDORES (R$) ---
    top_vendedores = vendas_periodo.values('vendedor__username').annotate(
        total_faturado=Sum('valor_final')
    ).order_by('-total_faturado')[:5]

    labels_vend = [v['vendedor__username'] for v in top_vendedores]
    dados_vend = [float(v['total_faturado']) for v in top_vendedores]

    # --- DADOS PARA O SELECT DE DIAS ---
    # Descobre quantos dias tem o mês selecionado (ex: Fevereiro 2024 = 29)
    _, qtd_dias_mes = calendar.monthrange(ano_filtro, mes_filtro)
    lista_dias = range(1, qtd_dias_mes + 1)

    context = {
        'datas_grafico': json.dumps(datas_grafico),
        'valores_grafico': json.dumps(valores_grafico),
        'titulo_grafico1': titulo_grafico1, # Título dinâmico
        
        'labels_pgto': json.dumps(labels_pgto),
        'dados_pgto': json.dumps(dados_pgto),
        'labels_prod': json.dumps(labels_prod),
        'dados_prod': json.dumps(dados_prod),
        'labels_vend': json.dumps(labels_vend), 
        'dados_vend': json.dumps(dados_vend),
        
        # Filtros
        'mes_selecionado': mes_filtro,
        'ano_selecionado': ano_filtro,
        'dia_selecionado': dia_selecionado, # Novo
        
        'lista_meses': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'lista_anos': range(hoje.year, hoje.year - 5, -1),
        'lista_dias': lista_dias, # Novo
    }
    
    return render(request, 'loja/dashboard_vendas.html', context)

@login_required
def imprimir_cupom(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id)
    return render(request, 'loja/cupom.html', {'venda': venda})


@login_required
@user_passes_test(checar_gerente, login_url='/pdv/')
def notificacoes(request):
    # 1. Produtos Esgotados (Estoque <= 0)
    esgotados = Produto.objects.filter(estoque_atual__lte=0).order_by('nome')
    
    # 2. Produtos com Estoque Baixo (Entre 0.001 e 10)
    baixo_estoque = Produto.objects.filter(
        estoque_atual__gt=0, 
        estoque_atual__lte=10
    ).order_by('estoque_atual')

    # Contagem total de alertas
    total_alertas = esgotados.count() + baixo_estoque.count()

    context = {
        'esgotados': esgotados,
        'baixo_estoque': baixo_estoque,
        'total_alertas': total_alertas
    }
    
    return render(request, 'loja/notificacoes.html', context)