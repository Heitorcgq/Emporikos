from django import forms
from .models import Produto, Categoria

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'tipo_venda', 'codigo', 'preco_compra', 'preco_venda', 'estoque_atual', 'detalhes']
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tipo_venda': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_venda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estoque_atual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'detalhes': forms.TextInput(attrs={'class': 'form-control'}),
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
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }

        