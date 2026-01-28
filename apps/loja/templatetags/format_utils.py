from django import template
import re

register = template.Library()

@register.filter(name='fone_br')
def fone_br(value):
    """
    Formata números de telefone para o padrão brasileiro:
    11 dígitos: (XX) XXXXX-XXXX (Celular)
    10 dígitos: (XX) XXXX-XXXX (Fixo)
    """
    if not value:
        return ""
    
    # Remove tudo que não é número
    apenas_numeros = re.sub(r'\D', '', str(value))
    
    # Formata Celular (11 números)
    if len(apenas_numeros) == 11:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"
    
    # Formata Fixo (10 números)
    elif len(apenas_numeros) == 10:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
    
    # Se não tiver o tamanho certo, retorna o original
    return value