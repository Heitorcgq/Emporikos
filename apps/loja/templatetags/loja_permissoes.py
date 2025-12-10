from django import template

register = template.Library()

@register.filter(name='eh_gerente')
def eh_gerente(user):
    if not user.is_authenticated:
        return False
        
    return user.is_superuser or user.groups.filter(name='Gerente').exists()