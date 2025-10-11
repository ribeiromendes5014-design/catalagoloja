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
    
    quantidade_max = int(df_catalogo.loc[produto_id, 'QUANTIDADE'] if produto_id in df_catalogo.index else 999999)
    
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
        del st.session_state.carrinho[prod_id]
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
        st.markdown(f'<div class="product-image-container"><img src="{link_imagem}"></div>', unsafe_allow_html=True)
    else:
        st.markdown(placeholder_html, unsafe_allow_html=True)


def render_product_card(prod_id, row, key_prefix, df_catalogo_indexado):
    """Renderiza um card de produto com suporte para abas de foto e vídeo, seletor de quantidade e feedback de estoque."""
    with st.container(border=True):
        
        produto_nome = str(row['NOME'])
        descricao_curta = str(row.get('DESCRICAOCURTA', '')).strip()
        
        estoque_atual = int(row.get('QUANTIDADE', 999999)) 
        esgotado = estoque_atual <= 0
        estoque_baixo = estoque_atual > 0 and estoque_atual <= ESTOQUE_BAIXO_LIMITE
        
        if esgotado:
            st.markdown('<span class="esgotado-badge">🚫 ESGOTADO</span>', unsafe_allow_html=True)
        elif estoque_baixo:
            st.markdown(f'<span class="estoque-baixo-badge">⚠️ Últimas {estoque_atual} Unidades!</span>', unsafe_allow_html=True)

        youtube_url = row.get('YOUTUBE_URL')

        if youtube_url and isinstance(youtube_url, str) and youtube_url.strip().startswith('http'):
            tab_foto, tab_video = st.tabs(["📷 Foto", "▶️ Vídeo"])
            with tab_foto:
                render_product_image(row.get('LINKIMAGEM'))
            with tab_video:
                st.video(youtube_url)
        else:
            render_product_image(row.get('LINKIMAGEM'))

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
        st.caption(descricao_curta)

        with st.expander("Ver detalhes"):
            descricao_principal = row.get('DESCRICAOLONGA')
            detalhes_str = row.get('DETALHESGRADE')
            
            tem_descricao = descricao_principal and isinstance(descricao_principal, str) and descricao_principal.strip()
            tem_detalhes = detalhes_str and isinstance(detalhes_str, str) and detalhes_str.strip()
            
            if not tem_descricao and not tem_detalhes:
                st.info('Sem informações detalhadas disponíveis para este produto.')
            else:
                if tem_descricao:
                    if descricao_principal.strip() != descricao_curta:
                        st.subheader('Descrição')
                        st.markdown(descricao_principal)
                        if tem_detalhes:
                            st.markdown('---') 
                    
                if tem_detalhes:
                    st.subheader('Especificações')
                    if detalhes_str.strip().startswith('{'):
                        try:
                            detalhes_dict = ast.literal_eval(detalhes_str)
                            texto_formatado = ""
                            for chave, valor in detalhes_dict.items():
                                texto_formatado += f"* **{chave.strip()}**: {str(valor).strip()}\n"
                            st.markdown(texto_formatado)
                        except (ValueError, SyntaxError):
                            st.markdown(detalhes_str)
                    else:
                        st.markdown(detalhes_str)

        # --- SEÇÃO CORRIGIDA: Preço e Ação (Usando Flexbox via HTML/CSS) ---
        
        # Obtém os dados de preço/cashback
        condicao_pagamento = row.get('CONDICAOPAGAMENTO', 'Preço à vista')
        cashback_percent = pd.to_numeric(row.get('CASHBACKPERCENT'), errors='coerce')
        
        cashback_html = ""
        if pd.notna(cashback_percent) and cashback_percent > 0:
            cashback_valor_calculado = (cashback_percent / 100) * preco_final
            cashback_html = f"""
            <span style='color: #2E7D32; font-size: 0.8rem; font-weight: bold; display: block; margin-top: 5px;'>
                Cashback: R$ {cashback_valor_calculado:.2f}
            </span>
            """
            
        condicao_html = f"""
        <span style='color: #757575; font-size: 0.85rem; font-weight: normal; margin-top: 5px; display: block;'>
            ({condicao_pagamento})
        </span>
        """

        # Prepara o bloco de HTML do Preço (lado esquerdo)
        if is_promotion:
            preco_bloco_html = f"""
            <div style="line-height: 1.2;">
                <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {preco_original:.2f}</span>
                <h4 style='color: #D32F2F; margin:0;'>R$ {preco_final:.2f}</h4>
                {condicao_html}
                {cashback_html}
            </div>
            """
        else:
            preco_bloco_html = f"""
            <div style='display: flex; align-items: flex-end; flex-wrap: wrap; gap: 8px;'>
                <h4 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final:.2f}</h4>
            </div>
            {condicao_html}
            {cashback_html}
            """
        
        # Injeta o HTML do Preço e inicia o container da área de botões (lado direito)
        st.markdown(f'<div class="price-action-flex">{preco_bloco_html}<div class="action-buttons-container">', unsafe_allow_html=True)
        
        # --- Lógica do Botão (Dentro do container de ação) ---
        item_ja_no_carrinho = prod_id in st.session_state.carrinho
        esgotado = estoque_atual <= 0

        if esgotado:
            st.empty() 
            
        elif item_ja_no_carrinho:
            qtd_atual = st.session_state.carrinho[prod_id]['quantidade']
            st.button(
                f"✅ {qtd_atual}x NO PEDIDO", 
                key=f'btn_add_qtd_{key_prefix}', 
                use_container_width=True, 
                disabled=True 
            )
        else:
            qtd_a_adicionar = st.number_input(
                label=f'Qtd_Input_{key_prefix}',
                min_value=1,
                max_value=estoque_atual, 
                value=1,
                step=1,
                key=f'qtd_input_{key_prefix}',
                label_visibility="collapsed"
            )
            
            if st.button(f"🛒 Adicionar {qtd_a_adicionar} un.", key=f'btn_add_qtd_{key_prefix}', use_container_width=True):
                if qtd_a_adicionar >= 1:
                    adicionar_qtd_ao_carrinho(prod_id, row, qtd_a_adicionar)
                    st.rerun()
        
        # Fecha a div do container de botões e o container flex
        st.markdown('</div></div>', unsafe_allow_html=True) 
