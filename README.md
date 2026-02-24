# Emporikos - Sistema de Gestão & PDV

O **Emporikos** é uma solução completa de gestão empresarial que une a robustez de um ERP com a agilidade de um **Ponto de Venda (PDV)**. Desenvolvido para facilitar o fluxo de caixa, controle de estoque e a administração geral de negócios.

## ✨ Funcionalidades Principais

* **PDV (Frente de Caixa):** Interface otimizada para realização de vendas rápidas.
* **Controle de Estoque:** Gestão detalhada de produtos e entradas/saídas.
* **Administração:** Gerenciamento de usuários e níveis de acesso.
* **Automação de Dados:** Scripts inclusos para setup rápido e geração de produtos.

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3.x & Django Framework
* **Frontend:** HTML5, CSS3 e JavaScript (Interface dinâmica para o PDV)
* **Banco de Dados:** SQLite / PostgreSQL

## 🚀 Como Executar o Projeto

1. Clone o repositório:
   ```bash
   git clone [https://github.com/Heitorcgq/Emporikos.git](https://github.com/Heitorcgq/Emporikos.git)
Instale as dependências:

   ```bash

   pip install -r requirements.txt

```
Configure o banco de dados:

```bash

python manage.py migrate

```
Crie o administrador e inicie o sistema:
```Bash

python create_admin.py
python manage.py runserver

```
Desenvolvido por Heitorcgq


---

### 3. Opção de README (Visual e Moderna)

```markdown
# 📦 Emporikos

![Django](https://img.shields.io/badge/django-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![PDV](https://img.shields.io/badge/Funcionalidade-PDV_Integrado-orange?style=for-the-badge)

**Emporikos** é um sistema focado na experiência do lojista, integrando a retaguarda administrativa diretamente com o **Ponto de Venda**.

### ⚙️ Destaques do Sistema
- **Frente de Caixa (PDV):** Processamento de vendas com interface amigável.
- **Gestão de Produtos:** Organização por categorias e controle de inventário.
- **Scripts de Agilidade:** - `python create_admin.py`: Criação imediata de acesso master.
    - `python gerar_produtos.py`: População automática para testes no PDV.

---
