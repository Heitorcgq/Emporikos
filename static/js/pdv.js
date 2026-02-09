// --- 1. ELEMENTOS DA TELA ---
const inputBusca = document.getElementById('input-busca');
const listaSugestoes = document.getElementById('lista-sugestoes');
let timeoutBusca = null;

// --- 2. INICIALIZAÇÃO ---
document.addEventListener('DOMContentLoaded', () => {
    renderizarTabela();
});

// --- 3. LÓGICA DE BUSCA ---
inputBusca.addEventListener('input', function() {
    const termo = this.value.trim();
    clearTimeout(timeoutBusca);
    if (termo.length < 1) { 
        listaSugestoes.style.display = 'none'; 
        return; 
    }
    timeoutBusca = setTimeout(() => carregarSugestoes(termo), 300);
});

inputBusca.addEventListener('keypress', async function (e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const termo = this.value.trim();
        if(!termo) return;
        
        const response = await fetch(`/api/buscar-produto/?termo=${encodeURIComponent(termo)}`);
        const dados = await response.json();

        if (dados.length === 0) {
            alert("Produto não encontrado!");
            listaSugestoes.style.display = 'none';
        } else if (dados.length === 1) {
            adicionarAoCarrinho(dados[0]);
        } else {
            desenharLista(dados);
        }
    }
});

async function carregarSugestoes(termo) {
    try {
        const response = await fetch(`/api/buscar-produto/?termo=${encodeURIComponent(termo)}`);
        const dados = await response.json();
        desenharLista(dados);
    } catch (e) { console.error(e); }
}

function desenharLista(produtos) {
    listaSugestoes.innerHTML = '';
    if (produtos.length === 0) { 
        listaSugestoes.style.display = 'none'; 
        return; 
    }
    
    produtos.forEach(p => {
        const li = document.createElement('li');
        li.className = 'list-group-item list-group-item-action d-flex justify-content-between cursor-pointer';
        li.onclick = () => { adicionarAoCarrinho(p); };
        
        li.innerHTML = `
            <div>
                <strong>${p.nome}</strong> 
                <span class="badge bg-light text-secondary border ms-1" style="font-size: 0.7em;">${p.tipo || 'UN'}</span>
                <br><small>${p.codigo}</small>
            </div>
            <span class="fw-bold">R$ ${p.preco.toFixed(2)}</span>
        `;
        listaSugestoes.appendChild(li);
    });
    listaSugestoes.style.display = 'block';
}

// --- 4. FUNÇÕES DE REDE ---
async function adicionarAoCarrinho(produto) {
    try {
        const response = await fetch(`/api/pdv/adicionar/${VENDA_ID}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ codigo: produto.codigo })
        });

        if (response.ok) {
            window.location.reload(); 
        } else {
            alert('Erro ao salvar item.');
        }
    } catch (error) { alert("Erro de conexão."); }
}

async function removerNoServidor(itemVendaId) {
    const response = await fetch(`/api/pdv/remover/${itemVendaId}/`, {
        method: 'POST', headers: {'X-CSRFToken': CSRF_TOKEN}
    });
    if (response.ok) window.location.reload();
}

async function atualizarQtdServidor(itemVendaId, novaQtd) {
    try {
        await fetch(`/api/pdv/atualizar-qtd/${itemVendaId}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ quantidade: novaQtd }),
            keepalive: true
        });
    } catch (e) {
        console.error("Erro ao salvar quantidade:", e);
    }
}

async function limparVenda() {
    const response = await fetch(`/api/pdv/limpar/${VENDA_ID}/`, {
        method: 'POST', headers: {'X-CSRFToken': CSRF_TOKEN}
    });
    if (response.ok) window.location.reload();
}

// --- 5. RENDERIZAÇÃO ---
function renderizarTabela() {
    const tbody = document.getElementById('tabela-itens');
    if(!tbody) return;
    tbody.innerHTML = '';
    let total = 0;
    let qtdItens = 0;

    carrinho.forEach(item => {
        const subtotal = item.preco * item.quantidade;
        total += subtotal;
        qtdItens += 1;

        let step = item.tipo === 'UN' ? '1' : '0.001';
        let min = item.tipo === 'UN' ? '1' : '0.001';

        tbody.innerHTML += `
        <tr>
            <td class="ps-4 fw-bold text-secondary font-monospace">${item.codigo}</td>
            <td>
                <div class="d-flex align-items-center">
                    <span class="fw-bold text-dark me-2">${item.nome}</span>
                    <span class="badge bg-light text-secondary border" style="font-size: 0.7em;">${item.tipo}</span>
                </div>
            </td>
            <td class="text-center">
                <input type="number" step="${step}" min="${min}"
                       class="form-control form-control-sm text-center d-inline-block" 
                       style="width: 80px;"
                       value="${item.quantidade}"
                       onchange="atualizarLocalEBackend(${item.id_item_venda}, this.value, '${item.tipo}')">
            </td>
            <td class="text-end">R$ ${item.preco.toFixed(2)}</td>
            <td class="text-end fw-bold text-primary">R$ ${subtotal.toFixed(2)}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-light text-danger" onclick="removerNoServidor(${item.id_item_venda})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>`;
    });

    document.getElementById('visor-total').innerText = total.toLocaleString('pt-BR', {style:'currency', currency:'BRL'});
    document.getElementById('total-itens-badge').innerText = `${qtdItens} itens`;
}

function atualizarLocalEBackend(id, qtd, tipo) {
    let novaQtd = parseFloat(qtd);
    const item = carrinho.find(i => i.id_item_venda === id);
    if(item) {
        item.quantidade = novaQtd;
        renderizarTabela(); 
        atualizarQtdServidor(id, novaQtd);
    }
}

function irParaCheckout() {
    if (carrinho.length === 0) {
        alert("O carrinho está vazio!");
        return;
    }
    window.location.href = URL_CHECKOUT;
}

// Atalhos de teclado
document.addEventListener('keydown', e => {
    if (e.key === 'F2') {
        e.preventDefault();
        irParaCheckout();
    }
});