# detalhes_produto_ui.py
# Arquivo separado para a UI da Tela de Detalhes do Produto

import streamlit as st
import pandas as pd
import time
import ast

# Importações CRÍTICAS para a lógica de compra e estado (Do seu projeto)
from ui_components import adicionar_qtd_ao_carrinho, render_product_image_clickable
from data_handler import ESTOQUE_BAIXO_LIMITE 
from streamlit_carousel import carousel


def mostrar_detalhes_produto(df_catalogo_indexado):
    """
    Renderiza a tela de detalhes de um único produto, puxando dados do CSV (df_catalogo_indexado).
    Remove o bloco "Vendido e Entregue por" e mantém a estrutura de descrição.
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
    
    id_pai = row_clicada.get('PAIID', produto_id_clicado)

    # CRÍTICO: Se a linha clicada é um produto filho (tem PAIID), usamos o PAIID para agrupar.
    # Caso contrário, usamos o próprio ID do produto.
    id_principal_para_info = id_pai if pd.notna(id_pai) else produto_id_clicado
    
    # Redefine row_principal para garantir que a linha PAI seja a base para a imagem/descrição principal
    try:
        row_principal = df_catalogo_indexado.loc[id_principal_para_info].copy()
    except KeyError:
        # Se o PAIID for inválido, usa o produto clicado como principal
        row_principal = row_clicada
        id_principal_para_info = produto_id_clicado


    # GARANTE QUE df_variacoes INCLUA:
    # 1. O produto principal (id_principal_para_info)
    # 2. Todos os produtos filhos que apontam para id_principal_para_info
    df_variacoes = df_catalogo_indexado[
        (df_catalogo_indexado['PAIID'] == id_principal_para_info) | 
        (df_catalogo_indexado.index == id_principal_para_info)
    ].sort_values(by='NOME').copy()

    id_variacao_selecionada = produto_id_clicado
    produto_selecionado_row = row_clicada

    # --- 2. LAYOUT INICIAL E BOTÃO VOLTAR ---
    
    if st.button("⬅️ Voltar ao Catálogo", type="primary"):
        st.session_state.produto_detalhe_id = None
        st.rerun()
    
    st.markdown("---") 
    st.title(row_principal['NOME']) # Título do produto

    # --- 3. ESTRUTURA PRINCIPAL: COLUNAS [Imagem, Detalhes/Compra] ---
    col_img_variacao, col_detalhes_compra = st.columns([1, 2])
    

    # =================================================================
    # --- COLUNA ESQUERDA: IMAGEM E OPÇÕES (VARIAÇÃO) ---
    # =================================================================
    with col_img_variacao:
        
        # EXIBIÇÃO DINÂMICA DA IMAGEM DA VARIAÇÃO ATUALMENTE SELECIONADA/CLICADA
        # 1. Tenta pegar a foto da variação selecionada (filho)
        image_url = produto_selecionado_row.get('FotoURL')
        
        # === CORREÇÃO CRÍTICA: Verifica se a URL existe ANTES de chamar st.image ===
        if image_url and image_url.strip():
            st.image(image_url, use_container_width=True)
        else:
            # Opção 1: Deixa o espaço em branco (Melhor para UX)
            st.empty()
        # ===========================================================================

        # Lógica de Seleção de Variação (Dinâmica do CSV)
        if not df_variacoes.empty and len(df_variacoes) > 1:
            st.markdown("---")
            
            # --- NOVO: LÓGICA DE MAPA USANDO DETALHESGRADE COM PARSING SEGURO ---
            mapa_variacoes = {}
            for index, row in df_variacoes.iterrows():
                
                detalhe_grade_str = str(row.get('DetalhesGrade', '')).strip()
                detalhes_formatados = ""
                
                if detalhe_grade_str and detalhe_grade_str != '{}' and detalhe_grade_str != 'nan':
                    try:
                        # Certifique-se de que 'import ast' esteja no topo do arquivo
                        detalhes_dict = ast.literal_eval(detalhe_grade_str) 
                        
                        detalhes_formatados = ", ".join(
                            f"{k}: {v}" 
                            for k, v in detalhes_dict.items()
                        )
                    except (ValueError, SyntaxError, NameError):
                        detalhes_formatados = detalhe_grade_str
                
                # Cria o rótulo de seleção final
                if detalhes_formatados:
                     # Exemplo: "Chinelo Havaianas (Cor: Azul, Tamanho: 37/38) - R$ 49.99"
                     label = f"{row.get('Nome', 'Produto')} ({detalhes_formatados}) - R$ {row.get('PRECO_FINAL', 0.0):.2f}"
                else:
                     # Fallback 
                     label = f"{row.get('Nome', 'Produto')} - R$ {row.get('PRECO_FINAL', 0.0):.2f}"

                mapa_variacoes[label] = index
            # --- FIM DA LÓGICA DE MAPA COM DETALHESGRADE ---

            try:
                indice_selecionado = list(mapa_variacoes.values()).index(produto_id_clicado)
            except ValueError:
                 indice_selecionado = 0
            
            # ESTE BLOCO USA mapa_variacoes, DEVE ESTAR DENTRO DO IF
            opcao_selecionada_nome = st.radio(
                "Selecione a Variação:", options=list(mapa_variacoes.keys()), index=indice_selecionado, key='seletor_variacao_radio', label_visibility="visible"
            )
            
            id_variacao_selecionada = mapa_variacoes[opcao_selecionada_nome]
            
            # Redefine produto_selecionado_row com base na seleção do rádio (CRÍTICO)
            produto_selecionado_row = df_catalogo_indexado.loc[id_variacao_selecionada]
            
        elif len(df_variacoes) == 1:
            st.info("Este produto é uma variação única.")
        else:
            st.info("Este produto não possui variações.")
            
    # =================================================================
    # --- COLUNA DIREITA: DETALHES, PREÇO E AÇÃO DE COMPRA ---
    # =================================================================
    with col_detalhes_compra:
        
        # --- Detalhes de Preço (DA VARIAÇÃO SELECIONADA) ---
        preco_original = produto_selecionado_row['PRECO']
        preco_final_variacao = produto_selecionado_row['PRECO_FINAL']
        is_promotion = pd.notna(produto_selecionado_row.get('PRECO_PROMOCIONAL'))
        condicao_pagamento = produto_selecionado_row.get('CONDICAOPAGAMENTO', 'Preço à vista')
        cashback_percent = pd.to_numeric(produto_selecionado_row.get('CASHBACKPERCENT'), errors='coerce')
        
        # Renderização do Preço
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

        st.markdown("---")
        
        # --- REMOVIDO: Opções do Vendedor (Circulado em Vermelho/Laranja) ---
        # Removido o bloco "with st.expander("Vendido e Entregue por:", expanded=True):"

        # --- Descrição em Expander (Dinâmico do CSV) ---
        # O st.expander é crucial para o estilo da "caixa preta" no Streamlit.
        with st.expander("Descrição Detalhada e Especificações", expanded=True):
            st.markdown(f"**Marca:** {row_principal.get('MARCA', 'N/A')}")
            st.markdown(f"**Descrição:** {row_principal.get('DESCRICAOLONGA', row_principal.get('DESCRICAOCURTA', 'Sem descrição detalhada'))}")

        st.markdown("---")
        
        # --- ÁREA DE COMPRA (Quantidae e Botão Adicionar - Dinâmico) ---
        
        estoque_atual_variacao = int(pd.to_numeric(produto_selecionado_row.get('QUANTIDADE', 999999), errors='coerce'))

        col_qtd, col_add = st.columns([1, 2])

        # === CORREÇÃO: Define valor inicial e mínimo com base no estoque (Para evitar StreamlitValueAboveMaxError) ===
        if estoque_atual_variacao > 0:
            initial_value = 1
            min_val = 1
        else:
            initial_value = 0
            min_val = 0
        # ===========================================================================================================

        qtd_a_adicionar = col_qtd.number_input(
            'Qtd',
            min_value=min_val,          # Usa 0 se esgotado, 1 se tem estoque
            max_value=estoque_atual_variacao,
            value=initial_value,        # Usa 0 se esgotado, 1 se tem estoque
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
        # FIM do with col_detalhes_compra:

    st.markdown("---")
    
    # =================================================================
    # --- 4. Seção "Produtos Relacionados" (VOLTA ÀS COLUNAS NATIVAS) ---
    # =================================================================
    st.header("PRODUTOS RELACIONADOS")
    st.markdown("<span style='font-weight: bold;'>Ver tudo ></span>", unsafe_allow_html=True) 

    # ESTE BLOCO ESTÁ CORRETAMENTE DENTRO DA FUNÇÃO AGORA
    df_amostra = df_catalogo_indexado[df_catalogo_indexado.index != id_principal_para_info].head(4).reset_index()
    
    if not df_amostra.empty:
        # Retorna para as colunas Streamlit nativas (melhor layout garantido)
        cols_cards = st.columns(len(df_amostra))

        for i, col in enumerate(cols_cards):
            if i < len(df_amostra):
                row_card = df_amostra.loc[i]
                prod_id_card = row_card['ID']
                
                with col:
                    # 1. O CARD É TOTALMENTE CLICÁVEL com esta função do ui_components.py
                    render_product_image_clickable(row_card['LINKIMAGEM'], prod_id_card) 
                    
                    # 2. Informações do Produto (sem subheader para manter o card limpo)
                    st.caption(f"**{row_card['NOME']}**")
                    st.markdown("⭐⭐⭐⭐ (342)", unsafe_allow_html=True) 
                    
                    st.write(f"<h5 style='color: #880E4F; margin:0;'>R$ {row_card['PRECO_FINAL']:.2f}</h5>", unsafe_allow_html=True)


    else:
        st.info("Simulação de produtos relacionados indisponível.")

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

























