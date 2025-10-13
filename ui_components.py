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
            'imagem': produto_imagem,
            'PRECO_FINAL': produto_preco 
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

def render_product_image(link_imagem):
    placeholder_html = """<div class="product-image-container" style="background-color: #f0f0f0; border-radius: 8px;"><span style="color: #a0a0a0; font-size: 1.1rem; font-weight: bold;">Sem Imagem</span></div>"""
    if link_imagem and str(link_imagem).strip().startswith('http'):
        st.markdown(f'<div class="product-image-container"><img src="{link_imagem}" alt="Imagem do produto"></div>', unsafe_allow_html=True)
    else:
        st.markdown(placeholder_html, unsafe_allow_html=True)


# --- FUNÇÃO DO CARD DE PRODUTO (ATUALIZADA PARA LINK DE PÁGINA) ---
def render_product_card(prod_id, row, key_prefix, df_catalogo_indexado, i):
    """Renderiza um card de produto que, ao ser clicado, navega para a página de detalhes."""
    
    produto_nome = str(row['NOME'])
    descricao_curta = str(row.get('DESCRICAOCURTA', '')).strip()
    
    try:
        estoque_atual = int(pd.to_numeric(row.get('QUANTIDADE', 999999), errors='coerce'))
    except (ValueError, TypeError):
        estoque_atual = 999999
        
    esgotado = estoque_atual <= 0
    estoque_baixo = 0 < estoque_atual <= ESTOQUE_BAIXO_LIMITE
    
    preco_final = row['PRECO_FINAL']
    preco_original = row['PRECO']
    is_promotion = pd.notna(row.get('PRECO_PROMOCIONAL'))
    
    # URL para a nova página de detalhes, passando o ID como query parameter
    detail_url = f"produto_detalhe?id={prod_id}"
    
    # Prepara os elementos HTML
    html_status = ""
    if esgotado:
        html_status = '<span class="esgotado-badge">🚫 ESGOTADO</span>'
    elif estoque_baixo:
        html_status = f'<span class="estoque-baixo-badge">⚠️ Últimas {estoque_atual} Unidades!</span>'

    html_promocao = ""
    if is_promotion:
        html_promocao = f"""
        <div style="margin-bottom: 0.5rem;">
            <span style="background-color: #D32F2F; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem;">
                🔥 PROMOÇÃO
            </span>
        </div>
        """
        html_precos = f"""
        <div style="line-height: 1.2;">
            <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {preco_original:.2f}</span>
            <h4 style='color: #D32F2F; margin:0;'>R$ {preco_final:.2f}</h4>
        </div>
        """
    else:
        html_precos = f"<h4 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final:.2f}</h4>"
        
    condicao_pagamento = row.get('CONDICAOPAGAMENTO', 'Preço à vista')
    html_condicao = f"<span style='color: #757575; font-size: 0.85rem; font-weight: normal;'>({condicao_pagamento})</span>"
    
    # Renderiza a imagem 
    placeholder_html = """<div class="product-image-container" style="background-color: #f0f0f0; border-radius: 8px;"><span style="color: #a0a0a0; font-size: 1.1rem; font-weight: bold;">Sem Imagem</span></div>"""
    link_imagem = row.get('LINKIMAGEM')
    if link_imagem and str(link_imagem).strip().startswith('http'):
        image_html = f'<div class="product-image-container"><img src="{link_imagem}" alt="Imagem do produto"></div>'
    else:
        image_html = placeholder_html

    # O conteúdo do card é estilizado e embrulhado na tag <a> para navegação nativa
    # CORREÇÃO: Usamos o st.markdown com o HTML/CSS do cartão, permitindo unsafe_allow_html=True
    st.markdown(f"""
        <a href="{detail_url}" style="text-decoration: none; color: inherit; display: block; height: 100%;">
            <div style="cursor: pointer; padding: 10px; border-radius: 8px; border: 1px solid #E0E0E0; background-color: white; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: left;">
                {html_status}
                {image_html}
                {html_promocao}
                <div style="min-height: 80px;">
                    <p style="font-weight: bold; margin-bottom: 0.3rem; color: #262626 !important;">{produto_nome}</p>
                    <p style="font-size: 0.85rem; color: #757575 !important; margin-top: 0;">{descricao_curta}</p>
                </div>
                <div style="border-top: 1px solid #eee; padding-top: 0.5rem; margin-top: 0.5rem;">
                    {html_precos}
                    {html_condicao}
                </div>
                <p style="color: #E91E63; font-weight: bold; margin-top: 1rem; text-align: center;">VER DETALHES</p>
            </div>
        </a>
    """, unsafe_allow_html=True)
    
    # Adiciona um CSS de hover (precisa ser feito via st.markdown pois não é um widget Streamlit)
    st.markdown(f"""
    <style>
        a[href*="{detail_url}"]:hover > div {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            transform: translateY(-2px);
            transition: all 0.2s;
        }}
    </style>
    """, unsafe_allow_html=True)
