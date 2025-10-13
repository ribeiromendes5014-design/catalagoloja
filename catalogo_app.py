# catalogo_app.py

import streamlit as st
import pandas as pd
import json
import time
from streamlit_autorefresh import st_autorefresh
import requests

# Importa as funções e constantes dos novos módulos
# CERTIFIQUE-SE DE QUE data_handler.py E ui_components.py EXISTEM NO MESMO DIRETÓRIO
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

# --- Cálculos iniciais do carrinho ---
total_acumulado = sum(item['preco'] * item['quantidade'] for item in st.session_state.carrinho.values())
num_itens = sum(item['quantidade'] for item in st.session_state.carrinho.values())
carrinho_vazio = not st.session_state.carrinho
df_catalogo_completo = st.session_state.df_catalogo_indexado
cashback_a_ganhar = calcular_cashback_total(st.session_state.carrinho, df_catalogo_completo)

# --- CONTROLE DE FLUXO PRINCIPAL ---

# Se um ID de detalhe estiver definido, pare o script e mostre APENAS a tela de detalhes.
if st.session_state.produto_detalhe_id:
    # Chama a nova função (usando df_catalogo_completo que é o df_catalogo_indexado)
    mostrar_detalhes_produto(st.session_state.df_catalogo_indexado) 
    st.stop() # CRUCIAL: Impede que o resto do catálogo seja desenha
# --- Funções Auxiliares de UI ---

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
                        alert("⚠️ Não foi possível abrir o carrinho automaticamente.\nToque no botão 'Conteúdo do Carrinho' no topo da página.");
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


# --- Layout do Aplicativo (INÍCIO DO SCRIPT PRINCIPAL) ---
st.set_page_config(page_title="Catálogo Doce&Bella", layout="wide", initial_sidebar_state="collapsed")

# --- CSS (COM CORREÇÃO DE LAYOUT) ---
st.markdown(f"""
<style>
MainMenu, footer, [data-testid="stSidebar"] {{visibility: hidden;}}
[data-testid="stSidebarHeader"], [data-testid="stToolbar"],
[data-testid="stAppViewBlockContainer"], [data-testid="stDecoration"] {{
    margin: 0 !important;
    padding: 0 !important;
}}

/* --- Mantém o botão invisível mas clicável (para abrir o carrinho) --- */
div[data-testid="stPopover"] > div:first-child > button {{
    position: fixed !important;
    bottom: 110px; /* mesmo nível do botão flutuante */
    right: 40px;
    width: 60px !important;
    height: 60px !important;
    opacity: 0 !important; /* invisível mas clicável */
    z-index: 1001 !important;
    pointer-events: auto !important;
}}

.stApp {{
    background-image: url({BACKGROUND_IMAGE_URL}) !important;
    background-size: cover;
    background-attachment: fixed;
}}

div.block-container {{
    background-color: rgba(255,255,255,0.95);
    border-radius: 10px;
    padding: 2rem;
    margin-top: 1rem;
    color: #262626;
}}

div[data-testid="stAppViewBlockContainer"] {{
    padding-top: 0 !important;
}}

.fullwidth-banner {{
    position: relative;
    width: 100vw;
    left: 50%;
    right: 50%;
    margin-left: -50vw;
    margin-right: -50vw;
    overflow: hidden;
    z-index: 9999;
}}

.fullwidth-banner img {{
    display: block;
    width: 100%;
    height: auto;
    object-fit: cover;
    margin: 0;
    padding: 0;
}}

/* --- CSS para o Botão Flutuante do Carrinho --- */
.cart-float {{
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
}}
.whatsapp-float img {{  <-- CORRIGIDO
    width: 60px;
    height: 60px;
    cursor: pointer;
    display: block;
}}  <-- CORRIGIDO

/* --- CSS para o Botão Flutuante do Carrinho --- */
.cart-float {{  <-- CORRIGIDO
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
}}  <-- CORRIGIDO
.cart-float-count {{  <-- CORRIGIDO
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
}}  <-- CORRIGIDO

/* === BLACK FRIDAY CORES INÍCIO (ANTIGO .pink-bar-container) === */
.pink-bar-container {{ 
    /* Cor de fundo da barra de busca alterada para Preto */
    background-color: #000000; 
    padding: 10px 0; 
    width: 100vw; 
    position: relative; 
    left: 50%; right: 50%; 
    margin-left: -50vw; 
    margin-right: -50vw; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.4); 
}}
.pink-bar-content {{ width: 100%; max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; align-items: center; }}

.cart-badge-button {{ 
    /* Botão de resumo no topo e checkout */
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
}}
.cart-badge-button:hover {{ 
    background-color: #FF4500; 
}}
.cart-count {{ 
    /* Contador de itens no carrinho */
    background-color: white; 
    color: #D32F2F; 
    border-radius: 50%; 
    padding: 2px 7px; 
    margin-left: 8px; 
    font-size: 14px; 
    line-height: 1; 
}}

div[data-testid="stButton"] > button {{ 
    /* Botões 'Adicionar ao Carrinho' e 'Aplicar Cupom' */
    background-color: #D32F2F; 
    color: white; 
    border-radius: 10px; 
    border: 1px solid #000000; 
    font-weight: bold; 
}}
div[data-testid="stButton"] > button:hover {{ 
    /* Cor de hover preta */
    background-color: #000000; 
    color: white; 
    border: 1px solid #FF4500; 
}}

/* === Estilos de Produtos e Estoque === */

.product-image-container {{ height: 220px; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; overflow: hidden; }}
.product-image-container img {{ max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px; }}

.esgotado-badge {{ background-color: #757575; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem; margin-bottom: 0.5rem; display: block; }}
.estoque-baixo-badge {{ background-color: #FFC107; color: black; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem; margin-bottom: 0.5rem; display: block; }}

.price-action-flex {{
    display: flex;
    justify-content: space-between; 
    align-items: flex-end; 
    margin-top: 1rem;
    gap: 10px; 
}}
.action-buttons-container {{
    flex-shrink: 0;
    width: 45%; 
}}
.action-buttons-container div[data-testid="stNumberInput"] {{
    width: 100%;
}}

/* --- CSS para o Botão Flutuante do WhatsApp --- */
.whatsapp-float {{
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
}}
.whatsapp-float img {{
    width: 60px;
    height: 60px;
    cursor: pointer;
    display: block;
}}

/* --- CSS para o Botão Flutuante do Carrinho --- */
.cart-float {{
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
}}
.cart-float-count {{
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
}}
</style>
""", unsafe_allow_html=True)



# --- CORREÇÃO: ÂNCORA E CONTEÚDO DO POPOVER ---
# Definimos o popover e todo o seu conteúdo dentro de um container no início do código.
# Isso garante que ele sempre exista no DOM para ser encontrado pelo JavaScript do botão flutuante.
with st.container():
    with st.popover("Conteúdo do Carrinho"):
        st.header("🛒 Detalhes do Pedido")
        if carrinho_vazio:
            st.info("Seu carrinho está vazio.")
        else:
            desconto_cupom = st.session_state.get('desconto_cupom', 0.0)
            total_com_desconto = total_acumulado - desconto_cupom
            if total_com_desconto < 0:
                total_com_desconto = 0

            st.markdown(f"Subtotal: `R$ {total_acumulado:.2f}`")
            if desconto_cupom > 0:
                st.markdown(f"Desconto (`{st.session_state.cupom_aplicado}`): <span style='color: #D32F2F;'>- R$ {desconto_cupom:.2f}</span>", unsafe_allow_html=True)

            st.markdown(f"<span style='color: #2E7D32; font-weight: bold;'>Cashback a Ganhar: R$ {cashback_a_ganhar:.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: #E91E63; margin-top: 0;'>Total: R$ {total_com_desconto:.2f}</h3>", unsafe_allow_html=True)
            st.markdown("---")

            col_h1, col_h2, col_h3, col_h4 = st.columns([3, 1.5, 2.5, 1])
            col_h2.markdown("**Qtd**")
            col_h3.markdown("**Subtotal**")
            col_h4.markdown("")
            st.markdown('<div style="margin-top: -10px; border-top: 1px solid #ccc;"></div>', unsafe_allow_html=True)

            for prod_id, item in list(st.session_state.carrinho.items()):
                c1, c2, c3, c4 = st.columns([3, 1.5, 2.5, 1])
                c1.write(f"*{item['nome']}*")

                max_qtd = int(df_catalogo_completo.loc[prod_id, 'QUANTIDADE']) if (df_catalogo_completo is not None and prod_id in df_catalogo_completo.index) else 999999

                if item['quantidade'] > max_qtd:
                    st.session_state.carrinho[prod_id]['quantidade'] = max_qtd
                    item['quantidade'] = max_qtd
                    st.toast(f"Ajustado: {item['nome']} ao estoque máximo de {max_qtd}.", icon="⚠️")
                    st.rerun()

                nova_quantidade = c2.number_input(label=f'Qtd_{prod_id}', min_value=1, max_value=max_qtd, value=item['quantidade'], step=1, key=f'qtd_{prod_id}_popover', label_visibility="collapsed")

                if nova_quantidade != item['quantidade']:
                    st.session_state.carrinho[prod_id]['quantidade'] = nova_quantidade
                    st.rerun()

                subtotal_item = item['preco'] * item['quantidade']
                preco_unitario = item['preco']
                c3.markdown(f"<div style='text-align: left; white-space: nowrap;'><strong>R$ {subtotal_item:.2f}</strong><br><span style='font-size: 0.8rem; color: #757575;'>(R$ {preco_unitario:.2f} un.)</span></div>", unsafe_allow_html=True)

                if c4.button("X", key=f'rem_{prod_id}_popover'):
                    remover_do_carrinho(prod_id)
                    st.rerun()

            st.markdown("---")
            st.subheader("🎟️ Cupom de Desconto")
            cupom_col1, cupom_col2 = st.columns([3, 1])
            codigo_cupom_input = cupom_col1.text_input("Código do Cupom", key="cupom_input", label_visibility="collapsed").upper()

            if cupom_col2.button("Aplicar", key="aplicar_cupom_btn", use_container_width=True):
                if codigo_cupom_input:
                    df_cupons_validos = carregar_cupons()
                    cupom_encontrado = df_cupons_validos[df_cupons_validos['NOME_CUPOM'] == codigo_cupom_input]
                    if not cupom_encontrado.empty:
                        cupom_info = cupom_encontrado.iloc[0]
                        valor_minimo = cupom_info['VALOR_MINIMO_PEDIDO']
                        if float(total_acumulado) >= float(valor_minimo):
                            tipo = cupom_info['TIPO_DESCONTO']
                            valor = cupom_info['VALOR_DESCONTO']
                            desconto = (valor / 100) * total_acumulado if tipo == 'PERCENTUAL' else valor
                            st.session_state.cupom_aplicado = codigo_cupom_input
                            st.session_state.desconto_cupom = desconto
                            st.session_state.cupom_mensagem = f"✅ Cupom '{codigo_cupom_input}' aplicado!"
                        else:
                            st.session_state.cupom_aplicado = None
                            st.session_state.desconto_cupom = 0.0
                            st.session_state.cupom_mensagem = f"❌ O valor mínimo para este cupom é de R$ {valor_minimo:.2f}."
                    else:
                        st.session_state.cupom_aplicado = None
                        st.session_state.desconto_cupom = 0.0
                        st.session_state.cupom_mensagem = "❌ Cupom inválido, expirado ou esgotado."
                else:
                    st.session_state.cupom_mensagem = "⚠️ Digite um código de cupom."
                st.rerun()

            if st.session_state.cupom_mensagem:
                if "✅" in st.session_state.cupom_mensagem:
                    st.success(st.session_state.cupom_mensagem)
                else:
                    st.error(st.session_state.cupom_mensagem)

            st.markdown("---")
            st.button("🗑️ Limpar Pedido", on_click=limpar_carrinho, use_container_width=True)
            st.markdown("---")

            st.subheader("Finalizar Pedido")
            nome_input = st.text_input("Seu Nome Completo:", key='checkout_nome_dynamic')
            contato_input = st.text_input("Seu Contato (WhatsApp - apenas números, com DDD):", key='checkout_contato_dynamic')

            nivel_cliente, saldo_cashback = 'N/A', 0.00
            if nome_input and contato_input and DF_CLIENTES_CASH is not None and not DF_CLIENTES_CASH.empty:
                existe, nome_encontrado, saldo_cashback, nivel_cliente = buscar_cliente_cashback(contato_input, DF_CLIENTES_CASH)
                if existe:
                    st.success(f"🎉 **Bem-vindo(a) de volta, {nome_encontrado}!** Nível: **{nivel_cliente.upper()}**. Saldo de Cashback: **R$ {saldo_cashback:.2f}**.")
                elif contato_input.strip():
                    st.info("👋 **Novo Cliente!** Você começará a acumular cashback após este pedido.")

            with st.form("form_finalizar_pedido", clear_on_submit=True):
                st.text_input("Nome (Preenchido)", value=nome_input, disabled=True, label_visibility="collapsed")
                st.text_input("Contato (Preenchido)", value=contato_input, disabled=True, label_visibility="collapsed")
                if st.form_submit_button("✅ Enviar Pedido", type="primary", use_container_width=True):
                    if nome_input and contato_input:
                        contato_limpo = ''.join(filter(str.isdigit, contato_input))
                        detalhes = {
                            "subtotal": total_acumulado,
                            "desconto_cupom": st.session_state.desconto_cupom,
                            "cupom_aplicado": st.session_state.cupom_aplicado,
                            "total": total_com_desconto,
                            "itens": [
                                {"id": int(k), "nome": v['nome'], "preco": v['preco'], "quantidade": v['quantidade'], "imagem": v.get('imagem', '')}
                                for k, v in st.session_state.carrinho.items()
                            ],
                            "nome": nome_input,
                            "contato": contato_limpo,
                            "cliente_nivel_atual": nivel_cliente,
                            "cliente_saldo_cashback": saldo_cashback,
                            "cashback_a_ganhar": cashback_a_ganhar
                        }
                        
                        sucesso, id_pedido = salvar_pedido(nome_input, contato_limpo, total_com_desconto, json.dumps(detalhes, ensure_ascii=False), detalhes)
                        
                        if sucesso:
                            # 1. Mensagem de Opt-in com o ID do Pedido
                            mensagem_optin = (
                                f"Olá! Acabei de fazer um pedido (ID: {id_pedido}) pelo catálogo da Doce&Bella. "
                                f"Confirmo meu Opt-in e desejo prosseguir com a compra. Meu nome é {nome_input}."
                            )
                            
                            # 2. Gera o Link do WhatsApp e codifica o texto
                            link_whats = f"https://wa.me/{NUMERO_WHATSAPP}?text={requests.utils.quote(mensagem_optin)}"
                            
                            # 3. EXECUTA O JAVASCRIPT PARA REDIRECIONAMENTO IMEDIATO
                            js_redirect = f"""
                            <script>
                            window.location.href = '{link_whats}';
                            </script>
                            """
                            st.markdown(js_redirect, unsafe_allow_html=True)

                            # 4. Limpa states para a PRÓXIMA sessão do usuário (Após o redirecionamento)
                            st.session_state.carrinho = {}
                            st.session_state.cupom_aplicado = None
                            st.session_state.desconto_cupom = 0.0
                            st.session_state.cupom_mensagem = ""
                            
                           
                            
                        else:
                             st.error("❌ Erro ao salvar o pedido. Tente novamente.")
                    else:
                        st.warning("Preencha seu nome e contato.")



# --- Tela de Pedido Confirmado ---
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
    # Se você ainda quiser mostrar o resumo em um formato simples (sem o botão copiar),
    # você pode usar st.markdown ou st.info. Vamos remover tudo que duplicava.

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
        
    st.stop() 
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

    cols = st.columns(4)
    for i, row in df_filtrado.reset_index(drop=True).iterrows():
        product_id = row['ID']
        unique_key = f'prod_{product_id}_{i}'
        with cols[i % 4]:
            render_product_card(product_id, row, key_prefix=unique_key, df_catalogo_indexado=st.session_state.df_catalogo_indexado)


                               






































