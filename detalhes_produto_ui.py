# detalhes_produto_ui.py
# Arquivo separado para a UI da Tela de Detalhes do Produto
# VERSÃO CORRIGIDA 4: Converte TODOS os valores da grade para STRING

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
    Usa 'PRECO' e 'PRECO_FINAL' para preços.
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
    # Copia a linha para evitar 'SettingWithCopyWarning'
    row_clicada = df_catalogo_indexado.loc[produto_id_clicado].copy()
    
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
        detalhes_pai = ast.literal_eval(row_para_info.get('DetalhesGrade', '{}'))
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
        
        foto_principal_url = row_para_info.get('FotoURL', row_para_info.get('LINKIMAGEM')) 
        
        if pd.notna(foto_principal_url) and foto_principal_url not in urls_adicionadas:
            image_items.append(
                {
                    "title": row_para_info['NOME'],
                    "text": row_para_info.get('CATEGORIA', row_para_info.get('Marca', '')), 
                    "img": foto_principal_url,
                }
            )
            urls_adicionadas.add(foto_principal_url)
        
        if not df_variacoes.empty:
            for idx, row_var in df_variacoes.iterrows():
                foto_var_url = row_var.get('FotoURL', row_var.get('LINKIMAGEM')) 
                
                if pd.notna(foto_var_url) and foto_var_url not in urls_adicionadas:
                    try:
                        detalhes_var = ast.literal_eval(row_var.get('DetalhesGrade', '{}'))
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
        st.caption(f"Marca: {row_para_info.get('Marca', 'N/D')} | Categoria: {row_para_info.get('CATEGORIA', 'N/D')}")
        
        # --- SELEÇÃO DE VARIAÇÃO (GRADE) ---
        row_produto_selecionado = None
        id_produto_selecionado = None

        # Concatena o PAI e os FILHOS para criar os seletores
        all_products_for_grade = pd.concat([row_para_info.to_frame().T, df_variacoes])
        all_products_for_grade = all_products_for_grade[~all_products_for_grade.index.duplicated(keep='first')]
        
        products_with_grade = []
        for idx, row in all_products_for_grade.iterrows():
            try:
                detalhe_str = str(row.get('DetalhesGrade', '')).strip() 
                
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
            opcoes_disponiveis = {} # Ex: {'Cor': ['Café', 'Vermelho'], 'Tamanho': ['37/38', '35/36']}
            
            for idx, row_g in df_grade.iterrows():
                detalhes_g = ast.literal_eval(str(row_g.get('DetalhesGrade', '{}')).strip())
                for k, v in detalhes_g.items():
                    if k not in opcoes_disponiveis:
                        opcoes_disponiveis[k] = set()
                    
                    # --- CORREÇÃO AQUI ---
                    # Converte TODOS os valores para string (ex: 38 vira '38')
                    opcoes_disponiveis[k].add(str(v))
            
            # Converte sets para listas ordenadas (agora seguro, pois são todas strings)
            for k in opcoes_disponiveis:
                opcoes_disponiveis[k] = sorted(list(opcoes_disponiveis[k]))

            # 2. Renderiza os st.radio/st.selectbox para cada tipo de grade
            selecao_usuario = {}
            
            # Tenta pré-selecionar com base no 'row_clicada'
            try:
                detalhes_clicados_raw = ast.literal_eval(str(row_clicada.get('DetalhesGrade', '{}')).strip())
                if not isinstance(detalhes_clicados_raw, dict):
                    detalhes_clicados_raw = {}
                
                # --- CORREÇÃO AQUI ---
                # Converte os valores para string para bater com as 'opcoes_disponiveis'
                detalhes_clicados = {k: str(v) for k, v in detalhes_clicados_raw.items()}
            except:
                detalhes_clicados = {}

            
            for tipo_grade, lista_opcoes in opcoes_disponiveis.items():
                default_value = detalhes_clicados.get(tipo_grade)
                try:
                    # Tenta achar o índice do valor clicado
                    idx_default = lista_opcoes.index(default_value)
                except ValueError:
                    idx_default = 0 # Padrão é o primeiro item
                
                selecao_usuario[tipo_grade] = st.radio(
                    f"**{tipo_grade}**:",
                    options=lista_opcoes,
                    index=idx_default,
                    horizontal=True,
                    key=f"grade_{tipo_grade}_{id_principal_para_info}"
                )
            
            # 3. Filtra o produto final com base na seleção
            for idx, row_g in df_grade.iterrows():
                # --- CORREÇÃO AQUI ---
                # Pega o dicionário original do CSV (com int, str, etc.)
                detalhes_g_raw = ast.literal_eval(str(row_g.get('DetalhesGrade', '{}')).strip())
                # Converte seus valores para string ANTES de comparar
                detalhes_g_str = {k: str(v) for k, v in detalhes_g_raw.items()}
                
                # Compara o dicionário (str:str) com o dicionário (str:str) do st.radio
                if detalhes_g_str == selecao_usuario:
                    id_produto_selecionado = idx
                    row_produto_selecionado = row_g
                    break # Encontrou
            
            # Fallback: Se não encontrar (ex: combinação inválida), usa o clicado
            if id_produto_selecionado is None:
                id_produto_selecionado = row_clicada.name
                row_produto_selecionado = row_clicada
        
        else:
            # Produto Simples (sem variações de grade)
            id_produto_selecionado = id_principal_para_info
            row_produto_selecionado = row_para_info
        
        # --- FIM DA SELEÇÃO DE VARIAÇÃO ---

        if row_produto_selecionado is None:
             st.error("Não foi possível selecionar o produto. Tente novamente.")
             return

        # --- PREÇO (CORRIGIDO) ---
        preco_original = row_produto_selecionado['PRECO_CARTAO'] # Usei PrecoCartao como base do seu CSV
        preco_final_selecionado = row_produto_selecionado['PRECO_VISTA'] # Usei PrecoVista como base
        
        # Lógica de Promoção (se PrecoCartao for maior que PrecoVista)
        is_promotion = preco_original > preco_final_selecionado
        condicao_pagamento = "Preço à vista" # Definido manualmente com base no PrecoVista

        st.markdown("---")
        
        if is_promotion:
            st.markdown(f"""
            <div style="line-height: 1.2;">
                <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {preco_original:.2f}</span>
                <h2 style='color: #D32F2F; margin:0;'>R$ {preco_final_selecionado:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final_selecionado:.2f}</h2>", unsafe_allow_html=True)
        
        st.markdown(f"<span style='color: #757575; font-size: 0.85rem; font-weight: normal;'>({condicao_pagamento})</span>", unsafe_allow_html=True)

        cashback_percent = pd.to_numeric(row_produto_selecionado.get('CASHBACKPERCENT'), errors='coerce')
        if pd.notna(cashback_percent) and cashback_percent > 0:
            cashback_valor = (cashback_percent / 100) * preco_final_selecionado
            st.markdown(f"<span style='color: #2E7D32; font-size: 0.9rem; font-weight: bold;'>Cashback: R$ {cashback_valor:.2f}</span>", unsafe_allow_html=True)


        # --- 5. LÓGICA DE COMPRA (Quantidade e Estoque) ---
        
        estoque_disponivel = int(pd.to_numeric(row_produto_selecionado.get('Quantidade', 0), errors='coerce'))
        
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
                
                # Usa 'PrecoVista' (preco_final_selecionado) como preço de adição
                adicionar_qtd_ao_carrinho(row_produto_selecionado, qtd, preco_final_selecionado)
                
                st.toast(f"{qtd}x {row_produto_selecionado['Nome']} adicionado(s)!")
                time.sleep(0.5)
        else:
            st.markdown("<br>", unsafe_allow_html=True)


    # --- 6. SEÇÃO DE DESCRIÇÃO E DETALHES TÉCNICOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab_desc, tab_details = st.tabs(["**Descrição do Produto**", "**Detalhes Técnicos**"])

    with tab_desc:
        st.subheader("Descrição")
        descricao = row_para_info.get('DESCRICAOLONGA', row_para_info.get('DESCRICAOCURTA', 'Sem descrição detalhada'))
        st.write(descricao)

    with tab_details:
        st.subheader("Detalhes Técnicos")
        st.text(f"ID do Produto: {id_principal_para_info}")
        st.text(f"Marca: {row_para_info.get('Marca', 'N/D')}") 
        st.text(f"Categoria: {row_para_info.get('Categoria', 'N/D')}")
        st.text(f"Código de Barras: {row_para_info.get('CodigoBarras', 'N/D')}")


    # --- 7. SEÇÃO DE PRODUTOS RELACIONADOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_rel_1, col_rel_2 = st.columns([3, 1])
    with col_rel_1:
        st.subheader("Quem viu, viu também")
    with col_rel_2:
        pass

    ids_para_excluir = [id_principal_para_info] + list(df_variacoes.index)
    
    categoria_pai = row_para_info.get('Categoria') # Corrigido para 'Categoria' (minúsculo)
    df_relacionados = df_catalogo_indexado[
        (~df_catalogo_indexado.index.isin(ids_para_excluir)) &
        (df_catalogo_indexado['Categoria'] == categoria_pai) &
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
                    render_product_image_clickable(row_card.get('LINKIMAGEM', row_card.get('FotoURL')), prod_id_card) 
                    
                    st.caption(f"**{row_card['Nome']}**")
                    
                    preco_card_orig = row_card['PrecoCartao']
                    preco_card_final = row_card['PrecoVista']
                    is_promo_card = preco_card_orig > preco_card_final

                    if is_promo_card:
                        st.write(f"<span style='text-decoration: line-through; color: #888; font-size: 0.9rem;'>R$ {preco_card_orig:,.2f}</span>", unsafe_allow_html=True)
                    else:
                        st.write("<br>", unsafe_allow_html=True) 

                    st.write(f"<h5 style='color: #880E4F; margin:0;'>R$ {preco_card_final:,.2f}</h5>", unsafe_allow_html=True)
