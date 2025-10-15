# detalhes_produto_ui.py
# Implementação da Tela de Detalhes do Produto - Layout de E-commerce

import streamlit as st
import pandas as pd
import time

# Importações CRÍTICAS para a lógica de compra e estado (Do seu projeto)
from ui_components import adicionar_qtd_ao_carrinho
from data_handler import ESTOQUE_BAIXO_LIMITE 


def mostrar_detalhes_produto(df_catalogo_indexado):
    """
    Renderiza a tela de detalhes de um único produto, puxando dados do CSV (df_catalogo_indexado),
    com layout de e-commerce (colunas, simulação de vendedor/frete, carrossel e barra de ações).
    """
    
    # 1. BUSCA E VALIDA O PRODUTO CLICADO
    produto_id_clicado = st.session_state.get('produto_detalhe_id')
    
    if not produto_id_clicado or produto_id_clicado not in df_catalogo_indexado.index:
        st.error("Produto não encontrado ou ID de detalhe ausente.")
        st.session_state.produto_detalhe_id = None
        st.rerun() 
        return 

    # --- LÓGICA DE VARIAÇÕES (PRODUTO PAI) ---
    row_clicada = df_catalogo_indexado.loc[produto_id_clicado].copy()
    
    # Identifica o ID Principal e o Produto Principal
    id_pai = row_clicada.get('PAIID', produto_id_clicado)
    id_principal_para_info = id_pai if pd.notna(id_pai) and id_pai in df_catalogo_indexado.index else produto_id_clicado
    row_principal = df_catalogo_indexado.loc[id_principal_para_info].copy()

    # Busca todas as variações 
    df_variacoes = df_catalogo_indexado[
        (df_catalogo_indexado['PAIID'] == id_principal_para_info) | 
        (df_catalogo_indexado.index == id_principal_para_info)
    ].sort_values(by='NOME').copy()

    # Variáveis iniciais (o produto clicado é o selecionado por padrão)
    id_variacao_selecionada = produto_id_clicado
    produto_selecionado_row = row_clicada

    # --- 2. LAYOUT INICIAL E BOTÃO VOLTAR ---
    
    # st.set_page_config não pode ser chamado aqui, pois já foi chamado em catalogo_app.py
    
    if st.button("⬅️ Voltar ao Catálogo"):
        st.session_state.produto_detalhe_id = None
        st.rerun()
    
    # Título Principal Dinâmico
    st.title(row_principal['NOME'])
    st.markdown("---") 

    # --- 3. ESTRUTURA PRINCIPAL: COLUNAS [Imagem, Detalhes/Compra] ---
    col_img_variacao, col_detalhes_compra = st.columns([1, 2])
    

    # =================================================================
    # --- COLUNA ESQUERDA: IMAGEM E OPÇÕES (VARIAÇÃO) ---
    # =================================================================
    with col_img_variacao:
        # Imagem Principal (Dinâmica do CSV)
        st.image(row_principal.get('LINKIMAGEM'), use_container_width=True)
        
        # Lógica de Seleção de Variação (Dinâmica do CSV)
        if not df_variacoes.empty and len(df_variacoes) > 1:
            st.markdown("---")
            mapa_variacoes = {
                f"{row['NOME']} ({row.get('DESCRICAOCURTA', '')})" : row.name
                for _, row in df_variacoes.iterrows()
            }
            try:
                indice_selecionado = list(mapa_variacoes.values()).index(produto_id_clicado)
            except ValueError:
                 indice_selecionado = 0
            
            opcao_selecionada_nome = st.radio(
                "Selecione a Variação:", options=list(mapa_variacoes.keys()), index=indice_selecionado, key='seletor_variacao_radio', label_visibility="visible"
            )
            
            id_variacao_selecionada = mapa_variacoes[opcao_selecionada_nome]
            produto_selecionado_row = df_catalogo_indexado.loc[id_variacao_selecionada]
            
        elif len(df_variacoes) == 1:
             st.info("Este produto é uma variação única.")
        else:
             st.info("Este produto não possui variações.")

    
    # =================================================================
    # --- COLUNA DIREITA: DETALHES, PREÇO, VENDEDOR E COMPRA ---
    # =================================================================
    with col_detalhes_compra:
        
        # --- Detalhes de Preço (Dinâmico do CSV) ---
        preco_original = produto_selecionado_row['PRECO']
        preco_final_variacao = produto_selecionado_row['PRECO_FINAL']
        is_promotion = pd.notna(produto_selecionado_row.get('PRECO_PROMOCIONAL'))
        condicao_pagamento = produto_selecionado_row.get('CONDICAOPAGAMENTO', 'Preço à vista')
        cashback_percent = pd.to_numeric(produto_selecionado_row.get('CASHBACKPERCENT'), errors='coerce')
        
        if is_promotion:
            # Preço com desconto (layout e-commerce)
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

        st.markdown("---")
        
        # --- Frete Simulado (Fixo, conforme briefing) ---
        st.info(
            """
            🚛 **Frete de R$ 89,99** <span style='text-decoration: line-through; color: #E91E63;'>R$ 89,99</span> 
            **R$ 49,99** com cupom  
            *Prazo: 10 a 15 dias úteis*
            """,
            icon="📦"
        )
        
        # --- Simulação de Opções do Vendedor (Fixo, conforme briefing) ---
        with st.expander("Vendido e Entregue por:"):
            st.subheader("Doce&Bella Cosméticos")
            st.caption("Ativo há 5 minutos atrás")
            st.button("Ver página da Loja", key="btn_ver_loja", use_container_width=True)

            st.markdown("<br>Métricas da Loja (Simulação):", unsafe_allow_html=True)
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Produtos", "104,2MIL")
            col_m2.metric("Avaliação", "4.8 ⭐")
            col_m3.metric("Resposta Chat", "95%")


        # --- Descrição em Expander (Dinâmico do CSV) ---
        with st.expander("Descrição Detalhada e Especificações", expanded=True):
            st.markdown(f"**Marca:** {row_principal.get('MARCA', 'N/A')}")
            st.markdown(f"**Descrição:** {row_principal.get('DESCRICAOLONGA', row_principal.get('DESCRICAOCURTA', 'Sem descrição detalhada'))}")

        st.markdown("---")
        
        # --- ÁREA DE COMPRA (Quantidae e Botão Adicionar - Dinâmico) ---
        
        estoque_atual_variacao = int(pd.to_numeric(produto_selecionado_row.get('QUANTIDADE', 999999), errors='coerce'))
        
        col_qtd, col_add = st.columns([1, 2])
        
        qtd_a_adicionar = col_qtd.number_input(
            'Qtd',
            min_value=1,
            max_value=estoque_atual_variacao,
            value=1,
            step=1,
            key='qtd_detalhes',
            label_visibility="visible"
        )
        
        if estoque_atual_variacao <= 0:
             col_add.error("🚫 ESGOTADO")
        elif col_add.button(f"🛒 Adicionar R$ {preco_final_variacao * qtd_a_adicionar:.2f}", 
                            key='btn_add_detalhes', use_container_width=True, type="primary"):
            
            adicionar_qtd_ao_carrinho(id_variacao_selecionada, produto_selecionado_row, qtd_a_adicionar)
            st.rerun()

    
    st.markdown("---")
    
    # =================================================================
    # --- 4. Seção "Produtos do Mesmo Vendedor" (SIMULADO) ---
    # =================================================================
    st.header("PRODUTOS RELACIONADOS")
    st.markdown("Ver tudo >", unsafe_allow_html=True)

    # Usa produtos reais (os primeiros do DF) como simulação de relacionados, 
    # se houver mais de um produto no catálogo.
    df_amostra = df_catalogo_indexado.head(4).reset_index()
    
    if not df_amostra.empty:
        cols_cards = st.columns(len(df_amostra))

        for i, col in enumerate(cols_cards):
            if i < len(df_amostra):
                row_card = df_amostra.loc[i]
                with col:
                    st.image(row_card['LINKIMAGEM'], use_container_width=True)
                    st.caption(f"**{row_card['NOME']}**")
                    st.markdown("⭐⭐⭐⭐ (342)", unsafe_allow_html=True) # Avaliação Fixa
                    st.subheader(f"R$ {row_card['PRECO_FINAL']:.2f}")
                    st.markdown("---")
    else:
        st.info("Simulação de produtos relacionados indisponível.")

    st.markdown("<br><br>", unsafe_allow_html=True)


    # =================================================================
    # --- 5. BARRA DE AÇÕES (RODAPÉ SIMULADO) ---
    # =================================================================
    
    # Esta seção é apenas uma simulação visual extra, 
    # a funcionalidade principal de compra já está na coluna da direita.
    st.subheader("Ações Rápidas (Simulação de Rodapé)")

    col_chat, col_add, col_buy = st.columns(3)

    col_chat.button("💬 Conversar agora", key="btn_chat_detalhes", use_container_width=True)
    
    # O botão de Adicionar aqui é puramente estético ou precisaria de mais lógica complexa
    # para sincronizar com a quantidade selecionada acima. Usamos o principal acima.
    col_add.button("Adicionar ao carrinho", key="btn_add_cart_sim", use_container_width=True)
    
    col_buy.button("🔥 Compre agora", key="btn_buy_now_detalhes", use_container_width=True, type="primary")


    st.markdown("<br><br>", unsafe_allow_html=True)

