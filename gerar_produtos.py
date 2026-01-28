import os
import django
import random

# --- Configuração para rodar fora do manage.py ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from apps.loja.models import Produto, Categoria

# --- Início do Script ---

# 1. Garante que existe pelo menos uma categoria
cat_teste, _ = Categoria.objects.get_or_create(nome="Geral Automático")

# 2. Listas de Variações
bases = [
    ("Linha Corrente", "UN", 2.50),
    ("Botão Acrílico", "UN", 0.30),
    ("Zíper Invisível", "UN", 1.50),
    ("Tecido Tricoline", "FR", 29.90),
    ("Fita de Cetim", "FR", 1.20),
    ("Elástico Chato", "FR", 2.00),
    ("Agulha Singer", "UN", 5.90),
    ("Viés Largo", "FR", 1.50),
    ("Tesoura Pro", "UN", 45.00),
    ("Lã Mollet", "UN", 8.90),
]

cores = ["Azul", "Vermelho", "Amarelo", "Preto", "Branco", "Verde", "Roxo", "Rosa", "Cinza", "Bege"]
detalhes = ["10mm", "20mm", "Grande", "Pequeno", "Nº 12", "Nº 14", "Liso", "Estampado", "Fino", "Grosso"]

print("--- Gerando 100 Produtos Aleatórios ---")

for i in range(1, 101):
    base_nome, tipo, preco_base = random.choice(bases)
    cor = random.choice(cores)
    detalhe = random.choice(detalhes)
    
    nome_final = f"{base_nome} {cor} {detalhe}"
    
    # Preços variados
    preco_venda = round(preco_base * random.uniform(0.9, 1.1), 2)
    preco_compra = round(preco_venda * 0.5, 2)
    
    # Estoque variado
    if tipo == 'UN':
        estoque = random.randint(0, 50)
    else:
        estoque = round(random.uniform(0.5, 100.0), 3)

    # Código único
    codigo_gerado = f"{i:03d}{random.randint(10,99)}"

    Produto.objects.create(
        nome=nome_final,
        categoria=cat_teste,
        tipo_venda=tipo,
        codigo=codigo_gerado,
        preco_compra=preco_compra,
        preco_venda=preco_venda,
        estoque_atual=estoque,
        detalhes=f"Item Automático #{i}"
    )

print("--- Sucesso! Produtos criados. ---")