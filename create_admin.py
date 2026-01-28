import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
email = 'admin@exemplo.com'
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superusuario '{username}' criado com sucesso!")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"Senha do usuario '{username}' atualizada!")