# detalhes_produto_ui.py
# Arquivo separado para a UI da Tela de Detalhes do Produto
# VERSÃO CORRIGIDA 5: Usa colunas padronizadas (MAIÚSCULAS)
# e as colunas de preço corretas (PRECO, PRECO_FINAL, PRECO_PROMOCIONAL)

import streamlit as st
import pandas as pd
import time
import ast # Importa AST para processar a 'DetalhesGrade'

# Importações CRÍTICAS para a lógica de compra e estado (Do seu projeto)
from ui_components import adicionar_qtd_ao_carrinho, render_product_image_clickable
from data_handler import ESTOQUE_BAIXO_LIMITE 
from streamlit_carousel import carousel # Importação principal para a solução


def mostrar_detalhes_produto(df_catalogo_indexado):
    """
    Renderiza a tela de detalhes de um único produto, puxando dados do CSV (df_catalogo_indexado).
    Usa 'PAIID' (maiúsculo) para compatibilidade.
    Usa colunas de preço consistentes com catalogo_app.py (PRECO, PRECO_FINAL, etc.)
    """
    
    # 1. BUSCA E VALIDA O PRODUTO CLICADO
    produto_id_clicado = st.session_state.get('produto_detalhe_id')
    
    if not produto_id_clicado or produto_id_clicado not in df_catalogo_indexado.index:
        st.error("Produto não encontrado ou ID de detalhe ausente.")
        st.session_state.produto_detalhe_id = None
        # Adiciona um botão para voltar
        if st.button("Voltar ao catálogo"):
            st.session_state.produto_detalhe_id = None
            st.rerun()
        return 

    # --- LÓGICA DE VARIAÇÕES (PRODUTO PAI) ---
    row_clicada = df_catalogo_indexado.loc[produto_id_clicado].copy()
    
    # Usa 'PAIID' (maiúsculo) consistentemente
    id_pai_real = row_clicada.get('PAIID') 
    
    if pd.notna(id_pai_real):
        try:
            id_pai_real = int(id_pai_real)
            id_principal_para_info = id_pai_real
            row_para_info = df_catalogo_indexado.loc[id_pai_real].copy()
        except (KeyError, ValueError):
            st.warning("Produto órfão encontrado. Exibindo dados do item.")
            id_principal_para_info = produto_id_clicado
            row_para_info = row_clicada
    else:
        id_principal_para_info = produto_id_clicado
        row_para_info = row_clicada

    id_pai_para_buscar_filhos = id_principal_para_info 
    
    df_variacoes = df_catalogo_indexado[
        df_catalogo_indexado['PAIID'] == id_pai_para_buscar_filhos
    ].copy()
    
    try:
        # Usa 'DETALHESGRADE' (maiúsculo)
        detalhes_pai = ast.literal_eval(row_para_info.get('DETALHESGRADE', '{}'))
        if not isinstance(detalhes_pai, dict):
            detalhes_pai = {}
    except:
        detalhes_pai = {}

    if detalhes_pai and not df_variacoes.empty:
         df_variacoes = pd.concat([row_para_info.to_frame().T, df_variacoes])
         df_variacoes = df_variacoes[~df_variacoes.index.duplicated(keep='first')]

    # --- FIM LÓGICA VARIAÇÕES ---


    # --- 2. APLICAÇÃO DE ESTILO CSS ---
    st.markdown("""
    <style>
        .stButton>button { width: 100%; color: white; }
        .stButton>button[kind="primary"] { background-color: #880E4F; } /* Botão Voltar */
        .stButton>button[kind="secondary"] { background-color: #D32F2F; } /* Botão Add Carrinho */
        .stButton>button[kind="secondary"]:hover { background-color: #000000; }
        h1 { font-size: 1.8rem; }
        h3 { font-size: 1.3rem; }
        .stRadio [role="radiogroup"] { justify-content: flex-start; }
        .stRadio [role="radio"] { margin-right: 15px; }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("⬅️ Voltar ao Catálogo", type="primary"):
        st.session_state.produto_detalhe_id = None
        st.rerun()
    
    st.markdown("---") 


    # --- 3. LAYOUT DA TELA (COLUNAS) ---
    col_img, col_info = st.columns([2, 3]) # 40% img, 60% info

    with col_img:
        # --- LÓGICA DO CARROSSEL DE IMAGENS ---
        image_items = []
        urls_adicionadas = set() 
        
        # Usa 'FOTOURL' (maiúsculo)
        foto_principal_url = row_para_info.get('FOTOURL', row_para_info.get('LINKIMAGEM')) 
        
        if pd.notna(foto_principal_url) and foto_principal_url not in urls_adicionadas:
            image_items.append(
                {
                    "title": row_para_info['NOME'],
                    "text": row_para_info.get('CATEGORIA', row_para_info.get('MARCA', '')), 
                    "img": foto_principal_url,
                }
            )
            urls_adicionadas.add(foto_principal_url)
        
        if not df_variacoes.empty:
            for idx, row_var in df_variacoes.iterrows():
                foto_var_url = row_var.get('FOTOURL', row_var.get('LINKIMAGEM')) 
                
                if pd.notna(foto_var_url) and foto_var_url not in urls_adicionadas:
                    try:
                        # Usa 'DETALHESGRADE' (maiúsculo)
                        detalhes_var = ast.literal_eval(row_var.get('DETALHESGRADE', '{}'))
                        if isinstance(detalhes_var, dict) and detalhes_var:
                            desc_var = ", ".join([f"{k}: {v}" for k, v in detalhes_var.items()])
                        else:
                            desc_var = row_var['NOME'] 
                    except:
                        desc_var = row_var['NOME'] 
                        
                    image_items.append(
                        {
                            "title": row_para_info['NOME'], 
                            "text": desc_var,              
                            "img": foto_var_url,           
                        }
                    )
                    urls_adicionadas.add(foto_var_url)

        # Renderiza o Carrossel
        if len(image_items) > 1:
            carousel(items=image_items, controls=True, indicators=True, interval=None)
        elif image_items: 
            st.image(image_items[0]['img'], caption=image_items[0]['text'], use_column_width=True)
        else:
            st.image("https://via.placeholder.com/400x400.png?text=Sem+Imagem", caption="Imagem não disponível", use_column_width=True)
            
        # --- FIM DO CARROSSEL ---

    with col_info:
        # --- 4. INFORMAÇÕES DO PRODUTO (Nome, Preço, etc.) ---
        
        st.title(row_para_info['NOME'])
        st.caption(f"Marca: {row_para_info.get('MARCA', 'N/D')} | Categoria: {row_para_info.get('CATEGORIA', 'N/D')}")
        
        # --- SELEÇÃO DE VARIAÇÃO (GRADE) ---
        row_produto_selecionado = None
        id_produto_selecionado = None

        # Concatena o PAI e os FILHOS para criar os seletores
        all_products_for_grade = pd.concat([row_para_info.to_frame().T, df_variacoes])
        all_products_for_grade = all_products_for_grade[~all_products_for_grade.index.duplicated(keep='first')]
        
        products_with_grade = []
        for idx, row in all_products_for_grade.iterrows():
            try:
                # Usa 'DETALHESGRADE' (maiúsculo)
                detalhe_str = str(row.get('DETALHESGRADE', '')).strip() 
                
                if not detalhe_str or detalhe_str == 'nan' or detalhe_str == '{}':
                    continue 

                detalhes = ast.literal_eval(detalhe_str)
                
                if isinstance(detalhes, dict) and detalhes: 
                    products_with_grade.append(row)
            except (ValueError, SyntaxError, NameError):
                continue
        
        df_grade = pd.DataFrame(products_with_grade)

        if not df_grade.empty:
            st.markdown("---")
            st.subheader("Escolha sua variação:")
            
            # 1. Coleta todas as opções disponíveis
            opcoes_disponiveis = {} 
            
            for idx, row_g in df_grade.iterrows():
                # Usa 'DETALHESGRADE' (maiúsculo)
                detalhes_g = ast.literal_eval(str(row_g.get('DETALHESGRADE', '{}')).strip())
                for k, v in detalhes_g.items():
                    if k not in opcoes_disponiveis:
                        opcoes_disponiveis[k] = set()
                    
                    opcoes_disponiveis[k].add(str(v))
            
            for k in opcoes_disponiveis:
                opcoes_disponiveis[k] = sorted(list(opcoes_disponiveis[k]))

            # 2. Renderiza os st.radio/st.selectbox para cada tipo de grade
            selecao_usuario = {}
            
            try:
                # Usa 'DETALHESGRADE' (maiúsculo)
                detalhes_clicados_raw = ast.literal_eval(str(row_clicada.get('DETALHESGRADE', '{}')).strip())
                if not isinstance(detalhes_clicados_raw, dict):
                    detalhes_clicados_raw = {}
                
                detalhes_clicados = {k: str(v) for k, v in detalhes_clicados_raw.items()}
            except:
                detalhes_clicados = {}

            
            for tipo_grade, lista_opcoes in opcoes_disponiveis.items():
                default_value = detalhes_clicados.get(tipo_grade)
                try:
                    idx_default = lista_opcoes.index(default_value)
                except ValueError:
                    idx_default = 0 
                
                selecao_usuario[tipo_grade] = st.radio(
                    f"**{tipo_grade}**:",
                    options=lista_opcoes,
                    index=idx_default,
                    horizontal=True,
                    key=f"grade_{tipo_grade}_{id_principal_para_info}"
                )
            
            # 3. Filtra o produto final com base na seleção
            for idx, row_g in df_grade.iterrows():
                # Usa 'DETALHESGRADE' (maiúsculo)
                detalhes_g_raw = ast.literal_eval(str(row_g.get('DETALHESGRADE', '{}')).strip())
                detalhes_g_str = {k: str(v) for k, v in detalhes_g_raw.items()}
                
                if detalhes_g_str == selecao_usuario:
                    id_produto_selecionado = idx
                    row_produto_selecionado = row_g
                    break 
            
            if id_produto_selecionado is None:
                id_produto_selecionado = row_clicada.name
                row_produto_selecionado = row_clicada
        
        else:
            id_produto_selecionado = id_principal_para_info
            row_produto_selecionado = row_para_info
        
        # --- FIM DA SELEÇÃO DE VARIAÇÃO ---

        if row_produto_selecionado is None:
             st.error("Não foi possível selecionar o produto. Tente novamente.")
             return

        # --- PREÇO (CORRIGIDO) ---
        # Usa as colunas PRECO, PRECO_FINAL, e PRECO_PROMOCIONAL
        # (Consistente com catalogo_app.py)
        
        preco_original = row_produto_selecionado['PRECO'] 
        preco_final_selecionado = row_produto_selecionado['PRECO_FINAL']
        
        preco_promo_val = row_produto_selecionado.get('PRECO_PROMOCIONAL')
        is_promotion = pd.notna(preco_promo_val) and preco_promo_val > 0
        condicao_pagamento = row_produto_selecionado.get('CONDICAOPAGAMENTO', 'Preço à vista')

        st.markdown("---")
        
        if is_promotion and preco_original > preco_final_selecionado:
            st.markdown(f"""
            <div style="line-height: 1.2;">
                <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {preco_original:.2f}</span>
                <h2 style='color: #D32F2F; margin:0;'>R$ {preco_final_selecionado:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final_selecionado:.2f}</h2>", unsafe_allow_html=True)
        
        st.markdown(f"<span style='color: #757575; font-size: 0.85rem; font-weight: normal;'>({condicao_pagamento})</span>", unsafe_allow_html=True)

        # Usa 'CASHBACKPERCENT' (maiúsculo)
        cashback_percent = pd.to_numeric(row_produto_selecionado.get('CASHBACKPERCENT'), errors='coerce')
        if pd.notna(cashback_percent) and cashback_percent > 0:
            cashback_valor = (cashback_percent / 100) * preco_final_selecionado
            st.markdown(f"<span style='color: #2E7D32; font-size: 0.9rem; font-weight: bold;'>Cashback: R$ {cashback_valor:.2f}</span>", unsafe_allow_html=True)


        # --- 5. LÓGICA DE COMPRA (Quantidade e Estoque) ---
        
        # Usa 'QUANTIDADE' (maiúsculo)
        estoque_disponivel = int(pd.to_numeric(row_produto_selecionado.get('QUANTIDADE', 0), errors='coerce'))
        
        if estoque_disponivel > ESTOQUE_BAIXO_LIMITE:
            st.success(f"**Em estoque** ({estoque_disponivel} unidades)")
            max_qty = int(min(estoque_disponivel, 10)) 
        elif 0 < estoque_disponivel <= ESTOQUE_BAIXO_LIMITE:
            st.warning(f"**Últimas unidades!** ({estoque_disponivel} restantes)")
            max_qty = int(estoque_disponivel)
        else:
            st.error("**Produto indisponível**")
            max_qty = 0

        if max_qty > 0:
            key_qtd = f"qtd_{id_produto_selecionado}"
            
            col_qtd_1, col_qtd_2, col_qtd_3 = st.columns([1, 2, 1])
            with col_qtd_1:
                if st.button("➖", key=f"down_{key_qtd}", use_container_width=True):
                    if st.session_state.get(key_qtd, 1) > 1:
                        st.session_state[key_qtd] -= 1
            with col_qtd_2:
                if key_qtd not in st.session_state:
                    st.session_state[key_qtd] = 1
                
                if st.session_state[key_qtd] > max_qty:
                    st.session_state[key_qtd] = max_qty

                st.number_input(
                    "Quantidade", 
                    min_value=1, 
                    max_value=max_qty, 
                    step=1, 
                    key=key_qtd,
                    label_visibility="collapsed"
                )
            with col_qtd_3:
                if st.button("➕", key=f"up_{key_qtd}", use_container_width=True):
                    if st.session_state.get(key_qtd, 1) < max_qty:
                        st.session_state[key_qtd] += 1
            
            if st.button(f"Adicionar R$ {preco_final_selecionado * st.session_state.get(key_qtd, 1):.2f}", 
                         key=f"add_{id_produto_selecionado}", type="secondary", use_container_width=True):
                
                qtd = st.session_state.get(key_qtd, 1)
                
                adicionar_qtd_ao_carrinho(row_produto_selecionado, qtd, preco_final_selecionado)
                
                st.toast(f"{qtd}x {row_produto_selecionado['NOME']} adicionado(s)!")
                time.sleep(0.5)
        else:
            st.markdown("<br>", unsafe_allow_html=True)


    # --- 6. SEÇÃO DE DESCRIÇÃO E DETALHES TÉCNICOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab_desc, tab_details = st.tabs(["**Descrição do Produto**", "**Detalhes Técnicos**"])

    with tab_desc:
        st.subheader("Descrição")
        # Usa 'DESCRICAOLONGA' e 'DESCRICAOCURTA' (maiúsculo)
        descricao = row_para_info.get('DESCRICAOLONGA', row_para_info.get('DESCRICAOCURTA', 'Sem descrição detalhada'))
        st.write(descricao)

    with tab_details:
        st.subheader("Detalhes Técnicos")
        st.text(f"ID do Produto: {id_principal_para_info}")
        st.text(f"Marca: {row_para_info.get('MARCA', 'N/D')}") 
        st.text(f"Categoria: {row_para_info.get('CATEGORIA', 'N/D')}")
        st.text(f"Código de Barras: {row_para_info.get('CODIGOBARRAS', 'N/D')}")


    # --- 7. SEÇÃO DE PRODUTOS RELACIONADOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_rel_1, col_rel_2 = st.columns([3, 1])
    with col_rel_1:
        st.subheader("Quem viu, viu também")
    with col_rel_2:
        pass

    ids_para_excluir = [id_principal_para_info] + list(df_variacoes.index)
    
    categoria_pai = row_para_info.get('CATEGORIA') 
    df_relacionados = df_catalogo_indexado[
        (~df_catalogo_indexado.index.isin(ids_para_excluir)) &
        (df_catalogo_indexado['CATEGORIA'] == categoria_pai) &
        (df_catalogo_indexado['PAIID'].isna()) 
    ]

    if df_relacionados.empty:
         df_relacionados = df_catalogo_indexado[
            (~df_catalogo_indexado.index.isin(ids_para_excluir)) &
            (df_catalogo_indexado['PAIID'].isna())
        ]
        
    df_amostra = df_relacionados.head(4).reset_index() 
    
    if not df_amostra.empty:
        cols_cards = st.columns(len(df_amostra))

        for i, col in enumerate(cols_cards):
            if i < len(df_amostra):
                row_card = df_amostra.loc[i]
                prod_id_card = row_card['ID']
                
                with col:
                    render_product_image_clickable(row_card.get('FOTOURL', row_card.get('LINKIMAGEM')), prod_id_card) 
                    
                    st.caption(f"**{row_card['NOME']}**")
                    
                    # Usa 'PRECO' e 'PRECO_FINAL'
                    preco_card_orig = row_card['PRECO']
                    preco_card_final = row_card['PRECO_FINAL']
                    preco_promo_card = row_card.get('PRECO_PROMOCIONAL')
                    is_promo_card = pd.notna(preco_promo_card) and preco_promo_card > 0

                    if is_promo_card and preco_card_orig > preco_card_final:
                        st.write(f"<span style='text-decoration: line-through; color: #888; font-size: 0.9rem;'>R$ {preco_card_orig:,.2f}</span>", unsafe_allow_html=True)
                    else:
                        st.write("<br>", unsafe_allow_html=True) 

                    st.write(f"<h5 style='color: #880E4F; margin:0;'>R$ {preco_card_final:,.2f}</h5>", unsafe_allow_html=True)
