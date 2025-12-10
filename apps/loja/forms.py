from django import forms
from .models import Produto, Categoria, Funcionario
from django.contrib.auth.models import User

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


class CadastroFuncionarioForm(forms.ModelForm):
    nome_completo = forms.CharField(label="Nome Completo", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # CAMPO NOVO: TELEFONE
    telefone = forms.CharField(
        label="Telefone / WhatsApp",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'})
    )
    
    senha = forms.CharField(label="Senha", required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    CARGO_CHOICES = (
        ('Caixa', 'Caixa (Acesso apenas PDV)'),
        ('Gerente', 'Gerente (Acesso Total)'),
    )
    cargo = forms.ChoiceField(choices=CARGO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'email'] # O telefone NÃO entra aqui, pois é de outra tabela
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(CadastroFuncionarioForm, self).__init__(*args, **kwargs)
        # Se estiver editando, carrega os dados
        if self.instance and self.instance.pk:
            self.fields['nome_completo'].initial = f"{self.instance.first_name} {self.instance.last_name}".strip()
            self.fields['senha'].widget.attrs['placeholder'] = "Deixe em branco para manter a atual"
            
            # Carrega o Cargo
            if self.instance.groups.filter(name='Gerente').exists():
                self.fields['cargo'].initial = 'Gerente'
            else:
                self.fields['cargo'].initial = 'Caixa'
            
            # Carrega o Telefone (se existir)
            if hasattr(self.instance, 'funcionario'):
                self.fields['telefone'].initial = self.instance.funcionario.telefone

    def save(self, commit=True):
        user = super(CadastroFuncionarioForm, self).save(commit=False)
        
        # Salva senha
        if self.cleaned_data.get('senha'):
            user.set_password(self.cleaned_data['senha'])
            
        # Salva nome
        nomes = self.cleaned_data['nome_completo'].split()
        user.first_name = nomes[0]
        if len(nomes) > 1:
            user.last_name = " ".join(nomes[1:])
        
        if commit:
            user.save()
            # SALVA O TELEFONE NA TABELA NOVA
            func_profile, created = Funcionario.objects.get_or_create(usuario=user)
            func_profile.telefone = self.cleaned_data['telefone']
            func_profile.save()
            
        return user