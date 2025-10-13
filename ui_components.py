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

def render_product_image(link_imagem):
    placeholder_html = """<div class="product-image-container" style="background-color: #f0f0f0; border-radius: 8px;"><span style="color: #a0a0a0; font-size: 1.1rem; font-weight: bold;">Sem Imagem</span></div>"""
    if link_imagem and str(link_imagem).strip().startswith('http'):
        st.markdown(f'<div class="product-image-container"><img src="{link_imagem}" alt="Imagem do produto"></div>', unsafe_allow_html=True)
    else:
        st.markdown(placeholder_html, unsafe_allow_html=True)


def render_product_card(prod_id, row, key_prefix, df_catalogo_indexado):
    """Renderiza um card de produto que, ao ser clicado, abre a página de detalhes."""
    
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
    
    # Prepara o HTML do conteúdo do card
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
    
    # Renderiza a imagem usando a função existente
    placeholder_html = """<div class="product-image-container" style="background-color: #f0f0f0; border-radius: 8px;"><span style="color: #a0a0a0; font-size: 1.1rem; font-weight: bold;">Sem Imagem</span></div>"""
    link_imagem = row.get('LINKIMAGEM')
    if link_imagem and str(link_imagem).strip().startswith('http'):
        image_html = f'<div class="product-image-container"><img src="{link_imagem}" alt="Imagem do produto"></div>'
    else:
        image_html = placeholder_html

    # Usa um botão estilizado para simular o clique no card
    card_html = f"""
        <div style="cursor: pointer; padding: 10px; border-radius: 8px; border: 1px solid #E0E0E0; background-color: white; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
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
    """
    
    # O botão Streamlit fica invisível, mas ocupa o espaço do card e executa a ação
    st.button(
        card_html, 
        key=f'btn_card_click_{key_prefix}', 
        on_click=handle_card_click, 
        args=(prod_id,), 
        use_container_width=True
    )
    
    # Adicionando um CSS para forçar a renderização do botão como o container do card
    st.markdown(f"""
    <style>
        div[data-testid="stVerticalBlock"] > div:nth-child({(i % 4) + 1}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div > button {{
            background: none !important;
            border: none !important;
            padding: 0;
            box-shadow: none !important;
            height: 100%;
        }}
        div[data-testid="stVerticalBlock"] > div:nth-child({(i % 4) + 1}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div > button:hover {{
            background-color: rgba(0, 0, 0, 0.03) !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_product_details_page(prod_id, df_catalogo_indexado):
    """Renderiza a página de detalhes completa do produto."""
    
    # 1. Obter a linha completa do produto
    try:
        row = df_catalogo_indexado.loc[prod_id]
    except KeyError:
        st.error("Produto não encontrado.")
        if st.button("Voltar ao Catálogo"):
            st.session_state.visualizando_detalhes = False
            st.session_state.produto_selecionado_id = None
            st.rerun()
        return

    produto_nome = str(row['NOME'])
    preco_final = row['PRECO_FINAL']
    preco_original = row['PRECO']
    is_promotion = pd.notna(row.get('PRECO_PROMOCIONAL'))
    estoque_atual = int(pd.to_numeric(row.get('QUANTIDADE', 999999), errors='coerce'))
    esgotado = estoque_atual <= 0
    condicao_pagamento = row.get('CONDICAOPAGAMENTO', 'Preço à vista')
    cashback_percent = pd.to_numeric(row.get('CASHBACKPERCENT'), errors='coerce')
    descricao_principal = row.get('DESCRICAOLONGA')
    detalhes_str = row.get('DETALHESGRADE')
    youtube_url = row.get('YOUTUBE_URL')
    
    # 2. Botão Voltar
    if st.button("⬅️ Voltar ao Catálogo"):
        st.session_state.visualizando_detalhes = False
        st.session_state.produto_selecionado_id = None
        st.rerun()

    st.title(produto_nome)
    
    # 3. Layout da Página de Detalhes (Foto e Informações Principais)
    col_midia, col_info = st.columns([1, 1])

    with col_midia:
        if youtube_url and isinstance(youtube_url, str) and youtube_url.strip().startswith('http'):
            tab_foto, tab_video = st.tabs(["📷 Foto", "▶️ Vídeo"])
            with tab_foto:
                render_product_image(row.get('LINKIMAGEM'))
            with tab_video:
                st.video(youtube_url)
        else:
            render_product_image(row.get('LINKIMAGEM'))
            
    with col_info:
        # Preços
        if is_promotion:
            st.markdown(f"""
            <div style="line-height: 1.2;">
                <span style='text-decoration: line-through; color: #757575; font-size: 1.2rem;'>De R$ {preco_original:.2f}</span>
                <h1 style='color: #D32F2F; margin:0;'>Por R$ {preco_final:.2f}</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final:.2f}</h1>", unsafe_allow_html=True)
            
        st.markdown(f"<span style='color: #757575; font-size: 1rem; font-weight: normal;'>({condicao_pagamento})</span>", unsafe_allow_html=True)
        
        # Cashback
        if pd.notna(cashback_percent) and cashback_percent > 0:
            cashback_valor = (cashback_percent / 100) * preco_final
            st.markdown(f"<span style='color: #2E7D32; font-size: 1.1rem; font-weight: bold;'>🎉 Você ganha R$ {cashback_valor:.2f} de Cashback!</span>", unsafe_allow_html=True)

        st.markdown("---")
        
        # Status do Estoque
        if esgotado:
            st.error("🚫 Este produto está ESGOTADO.")
        elif estoque_atual <= ESTOQUE_BAIXO_LIMITE:
            st.warning(f"⚠️ Últimas {estoque_atual} unidades no estoque!")
        else:
            st.success("✅ Produto disponível em estoque.")
            
        st.markdown("---")

        # Seletor de Quantidade e Botão Adicionar
        if not esgotado:
            col_qtd, col_add = st.columns([1, 3])
            
            with col_qtd:
                qtd_a_adicionar = st.number_input(
                    'Qtd',
                    min_value=1,
                    max_value=estoque_atual,
                    value=1,
                    step=1,
                    key=f'qtd_input_details_{prod_id}',
                    label_visibility="collapsed"
                )

            with col_add:
                # O row completo é necessário para adicionar_qtd_ao_carrinho
                row_dict = row.to_dict()
                if st.button(f"🛒 Adicionar {qtd_a_adicionar} ao Pedido", key=f'btn_add_details_{prod_id}', use_container_width=True, type='primary'):
                    adicionar_qtd_ao_carrinho(prod_id, row_dict, qtd_a_adicionar)
                    # Força a página de detalhes a recarregar para atualizar o status do carrinho no popover
                    st.session_state.visualizando_detalhes = False # Volta para o catalogo para facilitar
                    st.session_state.produto_selecionado_id = None
                    st.rerun()

    st.markdown("---")
    
    # 4. Detalhes Longos e Especificações
    tab_desc, tab_specs = st.tabs(["📄 Descrição Completa", "📋 Especificações"])
    
    with tab_desc:
        if descricao_principal and descricao_principal.strip():
            st.markdown(descricao_principal)
        else:
            st.info("Descrição completa não disponível.")
            
    with tab_specs:
        if detalhes_str and detalhes_str.strip():
            if detalhes_str.strip().startswith('{'):
                try:
                    detalhes_dict = ast.literal_eval(detalhes_str)
                    texto_formatado = "\n".join([f"* **{chave.strip()}**: {str(valor).strip()}" for chave, valor in detalhes_dict.items()])
                    st.markdown(texto_formatado)
                except (ValueError, SyntaxError):
                    st.markdown(detalhes_str)
            else:
                st.markdown(detalhes_str)
        else:
            st.info("Especificações técnicas não disponíveis.")
        
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
            item_ja_no_carrinho = prod_id in st.session_state.carrinho

            if esgotado:
                st.empty() # Não mostra nada se estiver esgotado
            elif item_ja_no_carrinho:
                qtd_atual = st.session_state.carrinho[prod_id]['quantidade']
                st.button(f"✅ {qtd_atual}x NO PEDIDO", key=f'btn_in_cart_{key_prefix}', use_container_width=True, disabled=True)
            else:
                qtd_a_adicionar = st.number_input(
                    'Quantidade',
                    min_value=1,
                    max_value=estoque_atual,
                    value=1,
                    step=1,
                    key=f'qtd_input_{key_prefix}',
                    label_visibility="collapsed"
                )
                
                if st.button(f"🛒 Adicionar {qtd_a_adicionar} un.", key=f'btn_add_{key_prefix}', use_container_width=True):
                    if qtd_a_adicionar >= 1:
                        adicionar_qtd_ao_carrinho(prod_id, row, qtd_a_adicionar)
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True) # Fecha action-buttons-container
        st.markdown('</div>', unsafe_allow_html=True) # Fecha price-action-flex
