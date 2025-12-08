from django import forms
from .models import Produto, Categoria

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'codigo', 'preco_compra', 'preco_venda', 'estoque_atual', 'detalhes']
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Linha de Costura Branca'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escaneie ou digite'}),
            'preco_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_venda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estoque_atual': forms.NumberInput(attrs={'class': 'form-control'}),
            'detalhes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cor, Tamanho, Marca...'}),
        }

        error_messages = {
            'codigo': {
                'unique': "Já existe um produto cadastrado com este código.",
            }
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Botões, Elásticos...'}),
        }

        