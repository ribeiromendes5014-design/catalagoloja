# ui_components.py

import streamlit as st
import pandas as pd
import time
import ast
import requests
import json
from data_handler import ESTOQUE_BAIXO_LIMITE # Importa a constante de limite

# --- Funções de Manipulação do Carrinho e Estado ---

def calcular_cashback_total(carrinho, df_catalogo_indexado):
    """Calcula o total de cashback a ser ganho pelos itens no carrinho."""
    cashback_total = 0.0
    for prod_id, item in carrinho.items():
        if prod_id in df_catalogo_indexado.index:
            row = df_catalogo_indexado.loc[prod_id]
            cashback_percent = pd.to_numeric(row.get('CASHBACKPERCENT'), errors='coerce') 
            preco_final = item['preco'] 
            
            if pd.notna(cashback_percent) and cashback_percent > 0:
                cashback_valor_unitario = (cashback_percent / 100) * preco_final
                cashback_total += cashback_valor_unitario * item['quantidade']
    return cashback_total


def adicionar_qtd_ao_carrinho(produto_id, produto_row, quantidade):
    produto_nome = produto_row['NOME']
    produto_preco = produto_row['PRECO_FINAL']
    produto_imagem = produto_row.get('LINKIMAGEM', '')
    
    df_catalogo = st.session_state.df_catalogo_indexado
    
    # Garante que a quantidade seja um número inteiro
    try:
        quantidade_max_raw = df_catalogo.loc[produto_id, 'QUANTIDADE']
        quantidade_max = int(pd.to_numeric(quantidade_max_raw, errors='coerce'))
    except (KeyError, ValueError):
        quantidade_max = 999999
    
    if quantidade_max <= 0:
         st.warning(f"⚠️ Produto '{produto_nome}' está esgotado.")
         return

    if produto_id in st.session_state.carrinho:
        nova_quantidade = st.session_state.carrinho[produto_id]['quantidade'] + quantidade
        
        if nova_quantidade > quantidade_max:
            disponivel = quantidade_max - st.session_state.carrinho[produto_id]['quantidade']
            st.warning(f"⚠️ Você só pode adicionar mais {disponivel} unidades. Total disponível: {quantidade_max}.")
            return
            
        st.session_state.carrinho[produto_id]['quantidade'] = nova_quantidade
    else:
        if quantidade > quantidade_max:
             st.warning(f"⚠️ Quantidade solicitada ({quantidade}) excede o estoque ({quantidade_max}) para '{produto_nome}'.")
             return
        st.session_state.carrinho[produto_id] = {
            'nome': produto_nome,
            'preco': produto_preco,
            'quantidade': quantidade,
            'imagem': produto_imagem
        }
    st.toast(f"✅ {quantidade}x {produto_nome} adicionado(s)!", icon="🛍️"); time.sleep(0.1)


def remover_do_carrinho(produto_id):
    if produto_id in st.session_state.carrinho:
        nome = st.session_state.carrinho[produto_id]['nome']
        del st.session_state.carrinho[produto_id]
        st.toast(f"❌ {nome} removido.", icon="🗑️")


def limpar_carrinho():
    st.session_state.carrinho = {}
    st.session_state.cupom_aplicado = None
    st.session_state.desconto_cupom = 0.0
    st.session_state.cupom_mensagem = ""
    st.toast("🗑️ Pedido limpo!", icon="🧹")
    st.rerun()

# --- Funções de Renderização de UI ---

def render_product_image_clickable(link_imagem, prod_id):
    """
    Renderiza a imagem do produto. Ao clicar, define o st.session_state.produto_detalhe_id
    e força o rerun para ir para a tela de detalhes.
    """
    import streamlit as st # Garante que st está disponível aqui
    
    if link_imagem and str(link_imagem).strip().startswith('http'):
        image_url = link_imagem
    else:
        # Imagem placeholder
        image_url = "https://via.placeholder.com/300x220?text=Sem+Imagem" 

    # --- HTML DO CONTAINER CLICÁVEL ---
    # Envolvemos tudo em um div com um ID único para facilitar a localização do botão Streamlit.
    st.markdown(f'<div id="container-clicavel-{prod_id}">', unsafe_allow_html=True)
    
    html_content = f"""
    <div class="product-image-container clickable-image" 
         onclick="
            // 1. Encontra o botão de clique invisível para este produto.
            const btn = document.getElementById('details_btn_{prod_id}');
            // 2. Simula o clique no botão.
            if (btn) {{
                btn.click();
            }}
         "
         style="cursor: pointer;">
        <img src="{image_url}" alt="Imagem do produto" style="max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px;">
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
    
    # --- BOTÃO INVISÍVEL DE ACIONAMENTO (HIDDEN BUTTON) ---
    
    # É CRUCIAL que o botão Streamlit seja renderizado APÓS o markdown da imagem.
    
    # O Streamlit Button que o JS vai "clicar".
    # Sem 'label_visibility' devido à compatibilidade.
    if st.button(
        "Definir ID", 
        key=f'details_btn_{prod_id}' # Este ID é usado no JavaScript e no CSS
    ):
        st.session_state.produto_detalhe_id = prod_id
        st.rerun()
        
    # --- FECHANDO O CONTÊINER DO BOTÃO E INJETANDO O CSS ---
    st.markdown('</div>', unsafe_allow_html=True)

    # CSS AGRESSIVO: Tenta esconder o botão por fora do container do próprio st.button.
    # O CSS tenta encontrar o botão pelo ID e aplica display: none.
    st.markdown(
        f"""
        <style>
        /* Oculta o botão 'Definir ID' por ser um truque de click-handler */
        div[data-testid="stVerticalBlock"] > div > div > div:has(> button#details_btn_{prod_id}) {{
            display: none !important;
            height: 0 !important;
            width: 0 !important;
            overflow: hidden !important;
        }}
        /* Se o seletor acima não funcionar, tenta o contêiner direto */
        #container-clicavel-{prod_id} + div button#details_btn_{prod_id} {{
            display: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def render_product_card(prod_id, row, key_prefix, df_catalogo_indexado):
    """Renderiza um card de produto simplificado e clicável para abrir a tela de detalhes."""
    with st.container(border=True):
        
        produto_nome = str(row['NOME'])
        descricao_curta = str(row.get('DESCRICAOCURTA', '')).strip()
        
        try:
            estoque_atual = int(pd.to_numeric(row.get('QUANTIDADE', 999999), errors='coerce'))
        except (ValueError, TypeError):
            estoque_atual = 999999
            
        esgotado = estoque_atual <= 0
        estoque_baixo = 0 < estoque_atual <= ESTOQUE_BAIXO_LIMITE
        
        if esgotado:
            st.markdown('<span class="esgotado-badge">🚫 ESGOTADO</span>', unsafe_allow_html=True)
        elif estoque_baixo:
            st.markdown(f'<span class="estoque-baixo-badge">⚠️ Últimas {estoque_atual} Unidades!</span>', unsafe_allow_html=True)

        
        # -----------------------------------------------------------------
        render_product_image_clickable(row.get('LINKIMAGEM'), prod_id)
        # -----------------------------------------------------------------


        preco_final = row['PRECO_FINAL']
        preco_original = row['PRECO']
        is_promotion = pd.notna(row.get('PRECO_PROMOCIONAL'))

        if is_promotion:
            st.markdown(f"""
            <div style="margin-bottom: 0.5rem;">
                <span style="background-color: #D32F2F; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem;">
                    🔥 PROMOÇÃO
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**{produto_nome}**")
        if descricao_curta:
            st.caption(descricao_curta)

        # REMOVEMOS O st.expander("Ver detalhes") AQUI

        # --- SEÇÃO CORRIGIDA: Preço e Ação agora estão juntos ---
        st.markdown('<div class="price-action-flex">', unsafe_allow_html=True)
        
        # Lado Esquerdo: Preços e Cashback
        with st.container():
            condicao_pagamento = row.get('CONDICAOPAGAMENTO', 'Preço à vista')
            cashback_percent = pd.to_numeric(row.get('CASHBACKPERCENT'), errors='coerce')
            
            # Formata o preço e as condições
            if is_promotion:
                st.markdown(f"""
                <div style="line-height: 1.2;">
                    <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {preco_original:.2f}</span>
                    <h4 style='color: #D32F2F; margin:0;'>R$ {preco_final:.2f}</h4>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<h4 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final:.2f}</h4>", unsafe_allow_html=True)
            
            st.markdown(f"<span style='color: #757575; font-size: 0.85rem; font-weight: normal;'>({condicao_pagamento})</span>", unsafe_allow_html=True)

            if pd.notna(cashback_percent) and cashback_percent > 0:
                cashback_valor = (cashback_percent / 100) * preco_final
                st.markdown(f"<span style='color: #2E7D32; font-size: 0.8rem; font-weight: bold;'>Cashback: R$ {cashback_valor:.2f}</span>", unsafe_allow_html=True)

        # Lado Direito: Botões de Ação
        st.markdown('<div class="action-buttons-container">', unsafe_allow_html=True)
        with st.container():
            # REMOVEMOS O INPUT DE QUANTIDADE E O BOTÃO "ADICIONAR" AQUI,
            # POIS A COMPRA DEVE SER FEITA NA TELA DE DETALHES
            
            # COLOCAMOS UM BOTÃO SIMPLES DE "VER DETALHES" COMO SEGUNDA OPÇÃO, 
            # CASO O CLIQUE NA IMAGEM FALHE EM ALGUM NAVEGADOR
            if st.button("👁️ Ver Detalhes", key=f'btn_details_card_{key_prefix}', use_container_width=True):
                 st.session_state.produto_detalhe_id = prod_id
                 st.rerun()

        st.markdown('</div>', unsafe_allow_html=True) # Fecha action-buttons-container
        st.markdown('</div>', unsafe_allow_html=True) # Fecha price-action-flex



