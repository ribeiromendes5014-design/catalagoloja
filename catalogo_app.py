# catalogo_app.py

import streamlit as st
import pandas as pd
import json
import time
from streamlit_autorefresh import st_autorefresh
import requests


# --- 1. CONFIGURAÇÃO DE PÁGINA (Deve ser a primeira chamada Streamlit) ---
st.set_page_config(page_title="Catálogo Doce&Bella", layout="wide", initial_sidebar_state="collapsed")


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
from detalhes_produto_ui import mostrar_detalhes_produto # <--- FIM DAS IMPORTAÇÕES


# --- Inicialização do Carrinho de Compras e Estado --- <--- DEVE COMEÇAR AQUI, SEM LINHAS INÚTEIS
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

    /* === REGRAS DE OTIMIZAÇÃO DE GRADE (NOVO) === */
    /* Força as colunas individuais a serem flexíveis e encolherem */
    div[data-testid="stColumns"] > div {
        flex-basis: 0 !important;
        min-width: 0 !important;
        flex-shrink: 1 !important;
    }
    
    /* Garante que o conteúdo interno (imagem/preço) também possa encolher */
    .product-image-container, .price-action-flex {
        min-width: 0 !important;
    }
    /* =========================================== */

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

div[data-testid="stButton"] > button { 
    background-color: #D32F2F; 
    color: white; 
    border-radius: 10px; 
    border: 1px solid #000000; 
    font-weight: bold; 
}
div[data-testid="stButton"] > button:hover { 
    background-color: #000000; 
    color: white; 
    border: 1px solid #FF4500; 
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

col_filtro_cat, col_select_ordem, col_grade_opcoes, _ = st.columns([1, 1, 1, 2])
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
    
    # ----------------------------------------------------
    # --- NOVO: Adiciona a opção de Grade na coluna criada ---
    opcoes_grade = [4, 3, 2] # Opções de colunas
    
    # IMPORTANTE: Coloque o selectbox na nova coluna col_grade_opcoes
    colunas_por_linha = col_grade_opcoes.selectbox(
        "Produtos por linha:",
        opcoes_grade, 
        index=0, # 4 será o padrão
        key='grade_produtos'
    )
    # ----------------------------------------------------
    
    opcoes_ordem = ['Lançamento', 'Promoção', 'Menor Preço', 'Maior Preço', 'Nome do Produto (A-Z)']
    
    # IMPORTANTE: Mantenha o selectbox na coluna original col_select_ordem
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

    # ----------------------------------------------------
    # --- NOVO: Usa a variável colunas_por_linha (Ex: 4, 3 ou 2) ---
    cols = st.columns(colunas_por_linha)
    
    for i, row in df_filtrado.reset_index(drop=True).iterrows():
        product_id = row['ID']
        unique_key = f'prod_{product_id}_{i}'
        
        # NOVO: Usa colunas_por_linha no operador módulo
        with cols[i % colunas_por_linha]:
            render_product_card(product_id, row, key_prefix=unique_key, df_catalogo_indexado=st.session_state.df_catalogo_indexado)
    # ----------------------------------------------------








