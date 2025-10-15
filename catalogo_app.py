# catalogo_app.py

import streamlit as st
import pandas as pd
import json
import time
from streamlit_autorefresh import st_autorefresh
import requests
import streamlit_javascript as st_js


# --- 1. CONFIGURAÇÃO DE PÁGINA (Deve ser a primeira chamada Streamlit) ---
st.set_page_config(page_title="Catálogo Doce&Bella", layout="wide", initial_sidebar_state="collapsed")

# --- Detecta modo mobile simples (sem bibliotecas externas) ---
import streamlit as st






# --- 2. IMPORTAÇÕES DE MÓDULOS LOCAIS ---
# Importa a função do novo módulo
from carrinho_ui import render_carrinho_popover 

# Importa as funções e constantes dos novos módulos
from data_handler import (
    carregar_catalogo, carregar_cupons, carregar_clientes_cashback, buscar_cliente_cashback,
    salvar_pedido, BACKGROUND_IMAGE_URL, LOGO_DOCEBELLA_URL, NUMERO_WHATSAPP
)
from ui_components import (
    adicionar_qtd_ao_carrinho, remover_do_carrinho, limpar_carrinho,
    calcular_cashback_total, render_product_card
)

# --- NOVA FUNÇÃO: Tela de Detalhes do Produto ---
def mostrar_detalhes_produto(df_catalogo_indexado):
    """Renderiza a tela de detalhes de um único produto (incluindo variações)."""
    import streamlit as st
    
    produto_id_clicado = st.session_state.get('produto_detalhe_id')
    
    if not produto_id_clicado or produto_id_clicado not in df_catalogo_indexado.index:
        st.error("Produto não encontrado ou ID de detalhe ausente.")
        st.session_state.produto_detalhe_id = None
        st.rerun()

    # --- LÓGICA DE BUSCA DO PRODUTO PAI E VARIAÇÕES ---
    row_clicada = df_catalogo_indexado.loc[produto_id_clicado].copy()
    
    # Tentativa de identificar o Pai: O PaiID é o ID que agrupa, senão é ele mesmo.
    id_pai = row_clicada.get('PAIID', produto_id_clicado)
    
    # Garante que o ID Principal (para descrição e imagem) seja o PaiID ou o ID clicado
    if pd.isna(id_pai) or id_pai == produto_id_clicado:
        id_principal_para_info = produto_id_clicado
    else:
        id_principal_para_info = id_pai

    # Busca a linha do produto que contém as informações mestras (imagem/descrição)
    if id_principal_para_info in df_catalogo_indexado.index:
        row_principal = df_catalogo_indexado.loc[id_principal_para_info].copy()
    else:
        row_principal = row_clicada # Se o Pai não for encontrado, usa o próprio item clicado

    
    # 1. BUSCA TODAS AS VARIAÇÕES (PRODUTOS FILHOS)
    # Filtra: PaiID = ID Principal OU é o próprio produto Principal (se ele for o pai)
    df_variacoes = df_catalogo_indexado[
        (df_catalogo_indexado['PAIID'] == id_principal_para_info) | 
        (df_catalogo_indexado.index == id_principal_para_info)
    ].sort_values(by='NOME').copy()

    # ----------------------------------------------------
    # --- NOVO LAYOUT (SEÇÕES DO MOCKUP) ---
    # ----------------------------------------------------
    
    # --- 1. Botão Voltar (Canto Superior Esquerdo - Seta Vermelha) ---
    if st.button("⬅️ Voltar ao Catálogo"):
        st.session_state.produto_detalhe_id = None
        st.rerun()
    
    st.markdown("---") # Linha divisória para separar o botão do conteúdo

    # --- Estrutura Principal: Imagem/Variações (Esquerda) vs Detalhes/Preço (Direita) ---
    col_img_variacao, col_detalhes_compra = st.columns([1, 2])
    
    
    # =================================================================
    # --- COLUNA ESQUERDA: IMAGEM E OPÇÕES (Quadrados Imagem e Roxo) ---
    # =================================================================
    with col_img_variacao:
        # Imagem Principal (Corpo da Imagem)
        st.image(row_principal.get('LINKIMAGEM'), use_column_width=True)
        
        # --- Lógica de Seleção de Variação (Quadrado Roxo) ---
        if not df_variacoes.empty:
            
            # Formata as opções para o Selectbox
            # Criaremos um dicionário {Nome da Variação: ID do Produto}
            mapa_variacoes = {
                f"{row['NOME']} ({row['DESCRICAOCURTA']})" : row.name
                for _, row in df_variacoes.iterrows()
            }
            
            # Encontra a chave que corresponde ao produto clicado originalmente
            indice_selecionado = list(mapa_variacoes.values()).index(produto_id_clicado)
            
            opcao_selecionada_nome = st.selectbox(
                "Selecione a Variação:",
                options=list(mapa_variacoes.keys()),
                index=indice_selecionado,
                key='seletor_variacao'
            )
            
            # Pega o ID da variação REALMENTE selecionada no widget
            id_variacao_selecionada = mapa_variacoes[opcao_selecionada_nome]
            
            # Puxa o objeto (linha) da variação selecionada para usar no preço/carrinho
            produto_selecionado_row = df_catalogo_indexado.loc[id_variacao_selecionada]
            
            st.markdown("---")
            
        else:
            # Não há variações, usa o produto principal
            id_variacao_selecionada = produto_id_clicado
            produto_selecionado_row = row_principal
            st.info("Este produto não possui variações.")

        
        # --- Área de Compra e Quantidade (Quadrado Marrom) ---
        
        # Garante que o estoque seja o da variação selecionada (se houver)
        estoque_atual_variacao = int(pd.to_numeric(produto_selecionado_row.get('QUANTIDADE', 999999), errors='coerce'))
        
        # Preço da variação selecionada
        preco_final_variacao = produto_selecionado_row['PRECO_FINAL']
        
        col_qtd, col_add = st.columns([1, 2])
        
        qtd_a_adicionar = col_qtd.number_input(
            'Qtd',
            min_value=1,
            max_value=estoque_atual_variacao,
            value=1,
            step=1,
            key='qtd_detalhes',
            label_visibility="collapsed",
            disabled=estoque_atual_variacao <= 0
        )
        
        if estoque_atual_variacao <= 0:
             col_add.error("🚫 ESGOTADO")
        elif col_add.button(f"🛒 Adicionar R$ {preco_final_variacao * qtd_a_adicionar:.2f}", 
                            key='btn_add_detalhes', use_container_width=True):
            
            adicionar_qtd_ao_carrinho(id_variacao_selecionada, produto_selecionado_row, qtd_a_adicionar)
            st.rerun()
            
    # =================================================================
    # --- COLUNA DIREITA: DETALHES (Quadrado Azul) ---
    # =================================================================
    with col_detalhes_compra:
        
        # Nome do Produto (Parte do Quadrado Azul)
        st.title(row_principal['NOME'])
        
        # Descrição (Parte do Quadrado Azul)
        st.markdown(f"**Marca:** {row_principal.get('MARCA', 'N/A')}")
        st.markdown(f"**Descrição:** {row_principal.get('DESCRICAOLONGA', row_principal.get('DESCRICAOCURTA', 'Sem descrição detalhada'))}")
        
        st.markdown("---")
        
        # Detalhes de Preço (Deixado aqui para visibilidade)
        preco_original = produto_selecionado_row['PRECO']
        is_promotion = pd.notna(produto_selecionado_row.get('PRECO_PROMOCIONAL'))
        condicao_pagamento = produto_selecionado_row.get('CONDICAOPAGAMENTO', 'Preço à vista')
        cashback_percent = pd.to_numeric(produto_selecionado_row.get('CASHBACKPERCENT'), errors='coerce')
        
        if is_promotion:
            st.markdown(f"""
            <div style="line-height: 1.2;">
                <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {preco_original:.2f}</span>
                <h2 style='color: #D32F2F; margin:0;'>R$ {preco_final_variacao:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final_variacao:.2f}</h2>", unsafe_allow_html=True)
        
        st.markdown(f"<span style='color: #757575; font-size: 0.85rem; font-weight: normal;'>({condicao_pagamento})</span>", unsafe_allow_html=True)

        if pd.notna(cashback_percent) and cashback_percent > 0:
            cashback_valor = (cashback_percent / 100) * preco_final_variacao
            st.markdown(f"<span style='color: #2E7D32; font-size: 0.9rem; font-weight: bold;'>Cashback: R$ {cashback_valor:.2f}</span>", unsafe_allow_html=True)

# --- FIM DA FUNÇÃO mostrar_detalhes_produto ---
            
# --- Inicialização do Carrinho de Compras e Estado ---
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}
if 'pedido_confirmado' not in st.session_state:
    st.session_state.pedido_confirmado = None
if 'cupom_aplicado' not in st.session_state:
    st.session_state.cupom_aplicado = None
if 'desconto_cupom' not in st.session_state:
    st.session_state.desconto_cupom = 0.0
if 'cupom_mensagem' not in st.session_state:
    st.session_state.cupom_mensagem = ""
if 'processando_pedido' not in st.session_state:
    st.session_state.processando_pedido = False

# OTIMIZAÇÃO: Cache do catálogo principal no estado da sessão para evitar re-leitura constante
if 'df_catalogo_indexado' not in st.session_state:
    st.session_state.df_catalogo_indexado = None

# --- Inicializa Dados (Uma vez) ---
if st.session_state.df_catalogo_indexado is None:
    st.session_state.df_catalogo_indexado = carregar_catalogo()

DF_CLIENTES_CASH = carregar_clientes_cashback()

# --- ADICIONA O CONTROLE DE ESTADO PARA A TELA DE DETALHES ---
if 'produto_detalhe_id' not in st.session_state:
    st.session_state.produto_detalhe_id = None

# --- Cálculos iniciais do carrinho (CRUCIAIS para os botões flutuantes) ---
total_acumulado = sum(item['preco'] * item['quantidade'] for item in st.session_state.carrinho.values())
num_itens = sum(item['quantidade'] for item in st.session_state.carrinho.values())
carrinho_vazio = not st.session_state.carrinho
df_catalogo_completo = st.session_state.df_catalogo_indexado
cashback_a_ganhar = calcular_cashback_total(st.session_state.carrinho, df_catalogo_completo)


# --- REORGANIZAÇÃO: TUDO QUE PRECISA APARECER NAS DUAS TELAS VEM PRIMEIRO ---

# --- 1. CHAMADA DO POPOVER DO CARRINHO (Tem que existir no DOM) ---
with st.container():
    # Esta função está no carrinho_ui.py e renderiza o popover completo.
    render_carrinho_popover(df_catalogo_completo, DF_CLIENTES_CASH)

# --- 2. CSS (MANTIDO AQUI PARA GARANTIR ESTILO DOS FLUTUANTES) ---
st.markdown("""
<style>
MainMenu, footer, [data-testid="stSidebar"] {visibility: hidden;}
[data-testid="stSidebarHeader"], [data-testid="stToolbar"],
[data-testid="stAppViewBlockContainer"], [data-testid="stDecoration"] {
    margin: 0 !important;
    padding: 0 !important;
}

/* --- Mantém o botão invisível mas clicável (para abrir o carrinho) --- */
div[data-testid="stPopover"] > div:first-child > button {
    position: fixed !important;
    bottom: 110px;
    right: 40px;
    width: 60px !important;
    height: 60px !important;
    opacity: 0 !important;
    z-index: 1001 !important;
    pointer-events: auto !important;
}

.stApp {
    background-image: url(""" + BACKGROUND_IMAGE_URL + """) !important;
    background-size: cover;
    background-attachment: fixed;
}

div.block-container {
    background-color: rgba(255,255,255,0.95);
    border-radius: 10px;
    padding: 2rem;
    margin-top: 1rem;
    color: #262626;
}

div[data-testid="stAppViewBlockContainer"] {
    padding-top: 0 !important;
}

.fullwidth-banner {
    position: relative;
    width: 100vw;
    left: 50%;
    right: 50%;
    margin-left: -50vw;
    margin-right: -50vw;
    overflow: hidden;
    z-index: 9999;
}

.fullwidth-banner img {
    display: block;
    width: 100%;
    height: auto;
    object-fit: cover;
    margin: 0;
    padding: 0;
}

/* === BLACK FRIDAY CORES INÍCIO === */
.pink-bar-container {
    background-color: #000000; 
    padding: 10px 0; 
    width: 100vw; 
    position: relative; 
    left: 50%; right: 50%; 
    margin-left: -50vw; 
    margin-right: -50vw; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.4); 
}
.pink-bar-content { width: 100%; max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; align-items: center; }

.cart-badge-button {
    background-color: #D32F2F; 
    color: white; 
    border-radius: 12px; 
    padding: 8px 15px;
    font-size: 16px; 
    font-weight: bold; 
    cursor: pointer; 
    border: none; 
    transition: background-color 0.3s;
    display: inline-flex; 
    align-items: center; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
    min-width: 150px; 
    justify-content: center; 
}
.cart-badge-button:hover { background-color: #FF4500; }
.cart-count {
    background-color: white; 
    color: #D32F2F; 
    border-radius: 50%; 
    padding: 2px 7px; 
    margin-left: 8px; 
    font-size: 14px; 
    line-height: 1; 
}

/* Regras Padrão (para PC/Telas Grandes) */
h1 { font-size: 2.5rem; } 

/* ======================================= */
/* MEDIA QUERY: TELA PEQUENA (CELULAR) */
/* ======================================= */
@media only screen and (max-width: 600px) {
    div.block-container {
        padding: 0.5rem !important;
        margin-top: 0.5rem !important;
    }
    h1 {
        font-size: 1.8rem;
    }
    .product-image-container {
        height: 180px;
    }
}

/* ================================================================= */
/* REGRAS GERAIS PARA AJUSTE DE TELA (MEDIA QUERY) */
/* ================================================================= */
@media only screen and (max-width: 650px) {
    div.block-container {
        padding: 1rem 0.5rem !important;
    }
    
    /* 1. Altera o container principal (stColumns) para permitir a quebra de linha */
    div[data-testid="stColumns"] {
        /* CRÍTICO: Remove flex-direction: column e força a quebra */
        flex-direction: row !important;
        flex-wrap: wrap !important;
    }
    
    /* 2. CRÍTICO: Força o contêiner de cada coluna individual a ter 50% de largura. */
    /* Este seletor geralmente funciona para colunas criadas com st.columns() */
    div[data-testid="stColumns"] > div[data-testid^="stBlock"] { 
        width: 50% !important;
        min-width: 150px !important;
        /* Adicione padding lateral para não colar */
        padding-left: 5px !important; 
        padding-right: 5px !important;
    }

    h1 { font-size: 1.8rem; }
    h2 { font-size: 1.5rem; }
    .product-image-container {
        height: 200px !important;
    }
    .whatsapp-float, .cart-float {
        width: 50px !important;
        height: 50px !important;
        bottom: 20px !important;
        right: 20px !important;
    }
    .cart-float {
        bottom: 80px !important;
    }
}
/* === Estilos de Produtos e Estoque === */
.product-image-container { height: 220px; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; overflow: hidden; }
.product-image-container img { max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px; }
.esgotado-badge { background-color: #757575; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem; margin-bottom: 0.5rem; display: block; }
.estoque-baixo-badge { background-color: #FFC107; color: black; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem; margin-bottom: 0.5rem; display: block; }

.price-action-flex {
    display: flex;
    justify-content: space-between; 
    align-items: flex-end; 
    margin-top: 1rem;
    gap: 10px; 
}
.action-buttons-container {
    flex-shrink: 0;
    width: 45%; 
}
.action-buttons-container div[data-testid="stNumberInput"] {
    width: 100%;
}

/* Botão Flutuante do WhatsApp */
.whatsapp-float {
    position: fixed;
    bottom: 40px;
    right: 40px;
    background: none;
    border: none;
    width: auto;
    height: auto;
    padding: 0;
    box-shadow: none;
    z-index: 999;
}
.whatsapp-float img {
    width: 60px;
    height: 60px;
    cursor: pointer;
    display: block;
}

/* Botão Flutuante do Carrinho */
.cart-float {
    position: fixed;
    bottom: 110px; 
    right: 40px;
    background-color: #D32F2F;
    color: white;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    text-align: center;
    font-size: 28px;
    box-shadow: 2px 2px 5px #999;
    cursor: pointer;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}
.cart-float-count {
    position: absolute;
    top: -5px;
    right: -5px;
    background-color: #FFD600;
    color: black;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    font-size: 14px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid white;
}
</style>
""", unsafe_allow_html=True)


# --- 3. BOTÕES FLUTUANTES (WhatsApp e Carrinho) ---

# --- Botão Flutuante do WhatsApp ---
MENSAGEM_PADRAO = "Olá, vi o catálogo de pedidos da Doce&Bella e gostaria de ajuda!"
LINK_WHATSAPP = f"https://wa.me/{NUMERO_WHATSAPP}?text={requests.utils.quote(MENSAGEM_PADRAO)}"
whatsapp_button_html = f"""
<a href="{LINK_WHATSAPP}" class="whatsapp-float" target="_blank" title="Fale Conosco pelo WhatsApp">
    <img src="https://d2az8otjr0j19j.cloudfront.net/templates/002/838/949/twig/static/images/top-whats.png"
         alt="WhatsApp"
         style="width: 60px; height: 60px;" />
</a>
"""
st.markdown(whatsapp_button_html, unsafe_allow_html=True)


# --- Funções Auxiliares de UI (Mantidas aqui por serem JavaScript) ---
def copy_to_clipboard_js(text_to_copy):
    js_code = f"""
    <script>
    function copyTextToClipboard(text) {{
      if (navigator.clipboard) {{
        navigator.clipboard.writeText(text).then(function() {{
          alert('Resumo do pedido copiado!');
        }}, function(err) {{
          console.error('Não foi possível copiar o texto: ', err);
          alert('Erro ao copiar o texto. Tente novamente.');
        }});
      }} else {{
        const textArea = document.createElement("textarea");
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {{
          document.execCommand('copy');
          alert('Resumo do pedido copiado!');
        }} catch (err) {{
          console.error('Fallback: Não foi possível copiar o texto: ', err);
          alert('Erro ao copiar o texto. Tente novamente.');
        }}
        document.body.removeChild(textArea);
      }}
    }}
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)


# --- Botão Flutuante do Carrinho ---
if num_itens > 0:
    floating_cart_html = f"""
    <div class="cart-float" id="floating_cart_btn" title="Ver seu pedido" role="button" aria-label="Abrir carrinho">
        🛒
        <span class="cart-float-count">{num_itens}</span>
    </div>
    <script>
    (function() {{
        const waitForPopoverButton = () => {{
            const popoverButton = document.querySelector('div[data-testid="stPopover"] button');
            if (popoverButton) {{
                return popoverButton;
            }}
            // Tenta encontrar botão por outras abordagens (compatibilidade)
            const alt = Array.from(document.querySelectorAll("button")).find(b => b.innerText.includes("Conteúdo do Carrinho"));
            if (alt) return alt;
            return null;
        }};
        const floatBtn = document.getElementById("floating_cart_btn");
        if (floatBtn) {{
            floatBtn.addEventListener("click", function() {{
                try {{
                    const popBtn = waitForPopoverButton();
                    if (popBtn) {{
                        popBtn.click();
                    }} else {{
                        console.warn("Botão do popover não encontrado. Verifique o seletor.");
                        // Não usar alert() - substitua por uma mensagem Streamlit se possível, mas aqui no JS é mais difícil.
                    }}
                }} catch (err) {{
                    console.error("Erro ao tentar abrir o popover do carrinho:", err);
                }}
            }});
        }}
    }})();
    </script>
    """
    st.markdown(floating_cart_html, unsafe_allow_html=True)


# --- 4. FLUXO DE CONTROLE PRINCIPAL ---

# --- CRÍTICO: 4.1. TELA DE PEDIDO CONFIRMADO (DEVE SER A PRIMEIRA VERIFICAÇÃO) ---
if st.session_state.pedido_confirmado:
    st.balloons()
    
    # 1. MENSAGEM DE SUCESSO
    st.success("🎉 Pedido enviado com sucesso! Clique no botão abaixo para confirmar o pedido via WhatsApp.")
    
    pedido = st.session_state.pedido_confirmado
    id_pedido_display = pedido.get('id_pedido', 'N/A')
    nome_cliente = pedido['nome']
    
    # Prepara a mensagem de Opt-in para o botão do WhatsApp
    mensagem_optin = (
        f"Olá! Acabei de fazer um pedido (ID: {id_pedido_display}) pelo catálogo da Doce&Bella. "
        f"Confirmo meu Opt-in e desejo prosseguir com a compra. Meu nome é {nome_cliente}."
    )
    
    # Gera o link final do WhatsApp
    import requests
    link_whats_final = f"https://wa.me/{NUMERO_WHATSAPP}?text={requests.utils.quote(mensagem_optin)}"

    # 2. BOTÃO DE CONFIRMAÇÃO DO WHATSAPP
    st.markdown(
        f"""
        <a href="{link_whats_final}" target="_blank">
            <button style="
                background-color: #25D366; 
                color: white; 
                border-radius: 10px; 
                border: 1px solid #000000; 
                font-weight: bold; 
                font-size: 1.1rem;
                padding: 10px 20px;
                width: 100%;
                margin-top: 15px;
                margin-bottom: 30px;
                cursor: pointer;
            ">
                ✅ CLIQUE AQUI PARA CONFIRMAR O PEDIDO NO WHATSAPP
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )
    
    # --- SIMPLIFICAÇÃO: RESUMO ABAIXO FOI REMOVIDO OU SUBSTITUÍDO ---

    st.subheader(f"Resumo do Pedido (ID: {id_pedido_display})")
    
    # Conteúdo simples do resumo
    itens_formatados = '\n'.join([f"• {item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f} un.)" for item in pedido['itens']])
    
    st.markdown(f"""
    **Cliente:** {pedido['nome']} | **Contato:** {pedido['contato']}  
    **Total a Pagar:** R$ {pedido['total']:.2f}  
    **Cashback a Ganhar:** R$ {pedido.get('cashback_a_ganhar', 0.0):.2f}
    
    **Itens:**
    {itens_formatados}
    """)
    
    st.markdown("---")
    
    # 3. BOTÃO "Voltar ao Catálogo"
    if st.button("Voltar ao Catálogo"):
        st.session_state.pedido_confirmado = None
        limpar_carrinho()
        st.rerun() 
        
    st.stop() # Finaliza o script para mostrar apenas a tela de confirmação


# --- 4.2. TELA DE DETALHES DO PRODUTO (SEGUNDA VERIFICAÇÃO) ---
if st.session_state.produto_detalhe_id:
    # Chama a nova função (usando df_catalogo_completo que é o df_catalogo_indexado)
    mostrar_detalhes_produto(st.session_state.df_catalogo_indexado) 
    st.stop() # CRUCIAL: Impede que o resto do catálogo seja desenhado.


# URL do banner de Black Friday
URL_BLACK_FRIDAY = "https://i.ibb.co/5Q6vsYc/Outdoor-de-esquenta-black-friday-amarelo-e-preto.png"

# --- Banner Black Friday full width (sem margens brancas) ---
st.markdown(
    f"""
    <div class="fullwidth-banner">
        <img src="{URL_BLACK_FRIDAY}" alt="Black Friday - Doce&Bella">
    </div>
    """,
    unsafe_allow_html=True
)

# --- Barra de Busca (Movida para baixo do Banner) ---
st.markdown("<div class='pink-bar-container'><div class='pink-bar-content'>", unsafe_allow_html=True)
st.text_input("Buscar...", key='termo_pesquisa_barra', label_visibility="collapsed", placeholder="Buscar produtos...")
st.markdown("</div></div>", unsafe_allow_html=True)


# --- Filtros e Exibição dos Produtos ---
df_catalogo = st.session_state.df_catalogo_indexado.reset_index()
categorias = df_catalogo['CATEGORIA'].dropna().astype(str).unique().tolist() if 'CATEGORIA' in df_catalogo.columns else ["TODAS AS CATEGORIAS"]
categorias.sort()
categorias.insert(0, "TODAS AS CATEGORIAS")

col_filtro_cat, col_select_ordem, _ = st.columns([1, 1, 3])
termo = st.session_state.get('termo_pesquisa_barra', '').lower()

categoria_selecionada = col_filtro_cat.selectbox("Filtrar por:", categorias, key='filtro_categoria_barra')
if termo:
    col_filtro_cat.markdown(f'<div style="font-size: 0.8rem; color: #E91E63;">Busca ativa desabilita filtro.</div>', unsafe_allow_html=True)

df_filtrado = df_catalogo.copy()
if not termo and categoria_selecionada != "TODAS AS CATEGORIAS":
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA'].astype(str) == categoria_selecionada]
elif termo:
    df_filtrado = df_filtrado[df_filtrado.apply(lambda row: termo in str(row['NOME']).lower() or termo in str(row['DESCRICAOLONGA']).lower(), axis=1)]

if df_filtrado.empty:
    st.info(f"Nenhum produto encontrado com os critérios selecionados.")
else:
    st.subheader("✨ Nossos Produtos")
    opcoes_ordem = ['Lançamento', 'Promoção', 'Menor Preço', 'Maior Preço', 'Nome do Produto (A-Z)']
    ordem_selecionada = col_select_ordem.selectbox("Ordenar por:", opcoes_ordem, key='ordem_produtos')
    df_filtrado['EM_PROMOCAO'] = df_filtrado['PRECO_PROMOCIONAL'].notna()

    sort_map = {
        'Lançamento': (['RECENCIA', 'EM_PROMOCAO'], [False, False]),
        'Promoção': (['EM_PROMOCAO', 'RECENCIA'], [False, False]),
        'Menor Preço': (['EM_PROMOCAO', 'PRECO_FINAL'], [False, True]),
        'Maior Preço': (['EM_PROMOCAO', 'PRECO_FINAL'], [False, False]),
        'Nome do Produto (A-Z)': (['EM_PROMOCAO', 'NOME'], [False, True])
    }
    if ordem_selecionada in sort_map:
        by_cols, ascending_order = sort_map[ordem_selecionada]
        df_filtrado = df_filtrado.sort_values(by=by_cols, ascending=ascending_order)

    # === Grade Responsiva de Produtos (CSS + HTML) ===
import streamlit as st

# Define o número de colunas padrão (4 no PC)
num_cols = 4 if not st.session_state.get("is_mobile", False) else 2

# Aplica um estilo CSS responsivo
st.markdown("""
<style>
.catalog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
  gap: 16px;
}
@media (max-width: 768px) {
  .catalog-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 10px;
  }
}
.catalog-item {
  background-color: white;
  border-radius: 10px;
  padding: 8px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Container HTML de grade
st.markdown('<div class="catalog-grid">', unsafe_allow_html=True)

# Renderiza cada produto dentro do container
for i, row in df_filtrado.reset_index(drop=True).iterrows():
    product_id = row['ID']
    unique_key = f'prod_{product_id}_{i}'
    st.markdown('<div class="catalog-item">', unsafe_allow_html=True)
    render_product_card(
        product_id,
        row,
        key_prefix=unique_key,
        df_catalogo_indexado=st.session_state.df_catalogo_indexado
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Fecha o container
st.markdown('</div>', unsafe_allow_html=True)










