# Em detalhes_produto_ui.py
# (Mantenha todos os seus imports no topo do arquivo como estão)
import streamlit as st
import pandas as pd
import time
import ast 
from ui_components import adicionar_qtd_ao_carrinho, render_product_image_clickable
from data_handler import ESTOQUE_BAIXO_LIMITE 
from streamlit_carousel import carousel 
# from carrinho_ui import render_carrinho_popover # Este import não é necessário aqui


def mostrar_detalhes_produto(df_catalogo_indexado):
    """
    Renderiza a tela de detalhes de um único produto, puxando dados do CSV (df_catalogo_indexado).
    Usa colunas em MAIÚSCULAS e as colunas de preço corretas (PRECO, PRECO_FINAL)
    """
# --- INÍCIO DA CORREÇÃO ---
    # Força a página a rolar para o topo (posição 0, 0)
    st.markdown(
        """
        <script>
            // Encontra o frame principal do Streamlit e rola para o topo
            const main = window.parent.document.querySelector('[data-testid="stAppViewBlockContainer"]');
            if (main) {
                main.scrollTo(0, 0);
            } else {
                // Fallback para rolar a janela inteira
                window.parent.scrollTo(0, 0);
            }
        </script>
        """,
        unsafe_allow_html=True
    )
    
    # 1. BUSCA E VALIDA O PRODUTO CLICADO (Sem mudanças)
    produto_id_clicado = st.session_state.get('produto_detalhe_id')
    
    if not produto_id_clicado or produto_id_clicado not in df_catalogo_indexado.index:
        st.error("Produto não encontrado ou ID de detalhe ausente.")
        st.session_state.produto_detalhe_id = None
        if st.button("Voltar ao catálogo"):
            st.session_state.produto_detalhe_id = None
            st.rerun()
        return 

    # --- LÓGICA DE VARIAÇÕES (PRODUTO PAI) --- (Sem mudanças)
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
        detalhes_pai = ast.literal_eval(row_para_info.get('DETALHESGRADE', '{}'))
        if not isinstance(detalhes_pai, dict):
            detalhes_pai = {}
    except:
        detalhes_pai = {}

    if detalhes_pai and not df_variacoes.empty:
         df_variacoes = pd.concat([row_para_info.to_frame().T, df_variacoes])
         df_variacoes = df_variacoes[~df_variacoes.index.duplicated(keep='first')]
    # --- FIM LÓGICA VARIAÇÕES ---

    # --- 2. APLICAÇÃO DE ESTILO CSS --- (Sem mudanças)
    st.markdown("""
    <style>
        /* ... (Seu CSS existente vai aqui) ... */
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("⬅️ Voltar ao Catálogo", type="primary"):
        st.session_state.produto_detalhe_id = None
        st.rerun()
    
    st.markdown("---") 

    # --- 3. REESTRUTURAÇÃO DO LAYOUT ---
    
    # --- 3.1. Crie as colunas ---
    col_img, col_info = st.columns([2, 3]) # 40% img, 60% info

    # --- 3.2. CRIE OS PLACEHOLDERS ---
    image_placeholder = col_img.empty()
    price_placeholder = col_info.empty() 

    # --- 3.3. PREENCHA A COLUNA DE INFORMAÇÕES (col_info) PRIMEIRO ---
    with col_info:
        # --- 4. INFORMAÇÕES DO PRODUTO (Nome, Preço, etc.) ---
        
        st.title(row_para_info['NOME'])
        st.caption(f"Marca: {row_para_info.get('MARCA', 'N/D')} | Categoria: {row_para_info.get('CATEGORIA', 'N/D')}")
        
        # --- Lógica de Preço (Função de renderização) ---
        def render_price(row_selecionada):
            po = row_selecionada['PRECO']
            pf = row_selecionada['PRECO_FINAL']
            pp = row_selecionada.get('PRECO_PROMOCIONAL')
            is_promo = pd.notna(pp) and pp > 0
            cp = row_selecionada.get('CONDICAOPAGAMENTO', 'Preço à vista')
            
            with price_placeholder.container(): 
                if is_promo and po > pf:
                    st.markdown(f"""
                    <div style="line-height: 1.2;">
                        <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {po:.2f}</span>
                        <h2 style='color: #D32F2F; margin:0;'>R$ {pf:.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h2 style='color: #880E4F; margin:0; line-height:1;'>R$ {pf:.2f}</h2>", unsafe_allow_html=True)
                
                st.markdown(f"<span style='color: #757575; font-size: 0.85rem; font-weight: normal;'>({cp})</span>", unsafe_allow_html=True)

                cashback_percent = pd.to_numeric(row_selecionada.get('CASHBACKPERCENT'), errors='coerce')
                if pd.notna(cashback_percent) and cashback_percent > 0:
                    cashback_valor = (cashback_percent / 100) * pf
                    st.markdown(f"<span style='color: #2E7D32; font-size: 0.9rem; font-weight: bold;'>Cashback: R$ {cashback_valor:.2f}</span>", unsafe_allow_html=True)
        
        
        # --- 5. SELEÇÃO DE VARIAÇÃO (GRADE) ---
        
        row_produto_selecionado = None
        id_produto_selecionado = None

        all_products_for_grade = pd.concat([row_para_info.to_frame().T, df_variacoes])
        all_products_for_grade = all_products_for_grade[~all_products_for_grade.index.duplicated(keep='first')]
        
        products_with_grade = []
        for idx, row in all_products_for_grade.iterrows():
            try:
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
            
            # --- ################################################## ---
            # --- INÍCIO DO BLOCO DE LÓGICA CORRIGIDO ---
            # --- Esta é a nova lógica de "Seletores em Cascata" ---
            # --- ################################################## ---
            
            # 1. Pega os detalhes do produto que foi clicado (ex: Branco, 37)
            try:
                detalhes_clicados_raw = ast.literal_eval(str(row_clicada.get('DETALHESGRADE', '{}')).strip())
                if not isinstance(detalhes_clicados_raw, dict):
                    detalhes_clicados_raw = {}
                detalhes_clicados = {k: str(v) for k, v in detalhes_clicados_raw.items()}
            except:
                detalhes_clicados = {}

            # 2. Descobre quais são os tipos de grade (ex: ['Cor', 'Numeração'])
            opcoes_disponiveis = {} 
            for idx, row_g in df_grade.iterrows():
                detalhes_g = ast.literal_eval(str(row_g.get('DETALHESGRADE', '{}')).strip())
                for k, v in detalhes_g.items():
                    if k not in opcoes_disponiveis:
                        opcoes_disponiveis[k] = set()
                    opcoes_disponiveis[k].add(str(v))
            
            grade_attributes = sorted(list(opcoes_disponiveis.keys()))
            selecao_usuario = {}
            df_grade_filtrada = df_grade.copy() # Começa com todos os produtos
            
            # 3. Faz um loop por tipo de grade (ex: primeiro 'Cor', depois 'Numeração')
            for i, tipo_grade in enumerate(grade_attributes):
                
                # 4. Encontra as opções válidas para *este* seletor
                #    baseado no que já foi selecionado *antes*.
                opcoes_validas = set()
                for idx, row_g in df_grade_filtrada.iterrows():
                    detalhes_g = ast.literal_eval(str(row_g.get('DETALHESGRADE', '{}')).strip())
                    if tipo_grade in detalhes_g:
                        opcoes_validas.add(str(detalhes_g[tipo_grade]))
                
                lista_opcoes = sorted(list(opcoes_validas))
                
                if not lista_opcoes:
                    # Se não houver opções, pula este seletor
                    continue

                # 5. Determina o 'index' (opção selecionada)
                widget_key = f"grade_{tipo_grade}_{id_principal_para_info}"
                selected_index = 0
                
                if widget_key in st.session_state:
                    # O usuário já selecionou algo. Verifica se ainda é uma opção válida.
                    current_val = st.session_state[widget_key]
                    if current_val in lista_opcoes:
                        selected_index = lista_opcoes.index(current_val)
                    # Se não for válida (ex: '37' não existe para 'Rosa'), 
                    # o selected_index fica 0, selecionando a primeira opção válida ('35').
                
                elif i == 0: # É o primeiro seletor (ex: 'Cor')
                    # Usa o valor do produto que foi clicado no catálogo
                    default_value = detalhes_clicados.get(tipo_grade)
                    try:
                        selected_index = lista_opcoes.index(default_value)
                    except ValueError:
                        selected_index = 0
                
                # 6. Renderiza o st.radio
                valor_selecionado = st.radio(
                    f"**{tipo_grade}**:",
                    options=lista_opcoes,
                    index=selected_index, 
                    horizontal=True,
                    key=widget_key
                )
                
                # 7. Salva a seleção e filtra o df para o *próximo* loop
                selecao_usuario[tipo_grade] = valor_selecionado
                
                indices_para_manter = []
                for idx, row_g in df_grade_filtrada.iterrows():
                    detalhes_g = ast.literal_eval(str(row_g.get('DETALHESGRADE', '{}')).strip())
                    if str(detalhes_g.get(tipo_grade)) == valor_selecionado:
                        indices_para_manter.append(idx)
                
                df_grade_filtrada = df_grade.loc[indices_para_manter]

            # 8. Ao final do loop, df_grade_filtrada conterá o produto exato
            if not df_grade_filtrada.empty:
                row_produto_selecionado = df_grade_filtrada.iloc[0]
                id_produto_selecionado = row_produto_selecionado.name
            else:
                # Fallback final (não deve ser atingido)
                row_produto_selecionado = row_clicada
                id_produto_selecionado = row_clicada.name
            
            # --- ################################################## ---
            # --- FIM DO BLOCO DE LÓGICA CORRIGIDO ---
            # --- ################################################## ---
        
        else:
            # Caso 3: O produto NÃO TEM grade
            id_produto_selecionado = id_principal_para_info
            row_produto_selecionado = row_para_info
        
        # --- FIM DA SELEÇÃO DE VARIAÇÃO ---

        # --- Garantia de que row_produto_selecionado é uma Series ---
        if isinstance(row_produto_selecionado, (int, float)):
            try:
                row_produto_selecionado = df_catalogo_indexado.loc[int(row_produto_selecionado)]
            except Exception as e:
                st.error(f"Erro ao recuperar dados do produto selecionado: {e}")
                return
        elif isinstance(row_produto_selecionado, dict):
            row_produto_selecionado = pd.Series(row_produto_selecionado)

        if row_produto_selecionado is None:
             st.error("Não foi possível selecionar o produto. Tente novamente.")
             return

        # --- 6. RENDERIZA O PREÇO (AGORA QUE TEMOS A ROW) ---
        render_price(row_produto_selecionado)
        
        preco_final_selecionado = row_produto_selecionado['PRECO_FINAL']


        # --- 7. LÓGICA DE COMPRA (Quantidade e Estoque) ---
        estoque_disponivel = int(pd.to_numeric(row_produto_selecionado.get('QUANTIDADE', 0), errors='coerce'))
        
        st.markdown("---") 
        
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
            
            # --- INÍCIO DA CORREÇÃO ---
            
            # 1. Garante que o estado existe
            if key_qtd not in st.session_state:
                st.session_state[key_qtd] = 1

            # 2. Define as funções de callback (elas rodam ANTES de desenhar os widgets)
            def incrementar_qtd():
                if st.session_state[key_qtd] < max_qty:
                    st.session_state[key_qtd] += 1

            def decrementar_qtd():
                if st.session_state[key_qtd] > 1:
                    st.session_state[key_qtd] -= 1

            # 3. Cria o layout
            col_qtd_1, col_qtd_2, col_qtd_3 = st.columns([1, 2, 1])
            
            with col_qtd_1:
                # 4. Chama o callback no 'on_click'
                st.button("➖", key=f"down_{key_qtd}", use_container_width=True,
                          on_click=decrementar_qtd)
            
            with col_qtd_2:
                # 5. Apenas exibe o number_input. Ele vai ler o valor 
                #    que os callbacks modificaram no session_state.
                
                # Garante que o valor não ultrapasse o max_qty se ele mudar
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
                # 6. Chama o callback no 'on_click'
                st.button("➕", key=f"up_{key_qtd}", use_container_width=True,
                          on_click=incrementar_qtd)
            
            # --- FIM DA CORREÇÃO ---

            # O seu botão de adicionar ao carrinho continua igual,
            # ele apenas LÊ o valor do session_state, o que está correto.
            if st.button(f"Adicionar R$ {preco_final_selecionado * st.session_state.get(key_qtd, 1):.2f}", 
                         key=f"add_{id_produto_selecionado}", type="secondary", use_container_width=True):
                
                qtd = st.session_state.get(key_qtd, 1)
                
                adicionar_qtd_ao_carrinho(row_produto_selecionado, qtd, preco_final_selecionado)
                time.sleep(0.5) 
                st.rerun()

        else:
            st.markdown("<br>", unsafe_allow_html=True)


    # --- 8. PREENCHA O PLACEHOLDER DA IMAGEM ---
    # (Sem mudanças nesta seção)
    with image_placeholder.container():
        image_items = []
        urls_adicionadas = set() 
        
        # --- PRIORIDADE 1: Imagem da variação selecionada ---
        if row_produto_selecionado is not None and not isinstance(row_produto_selecionado, (int, float)):
            foto_selecionada_url = row_produto_selecionado.get('FOTOURL', row_produto_selecionado.get('LINKIMAGEM'))
            
            if pd.notna(foto_selecionada_url) and foto_selecionada_url not in urls_adicionadas:
                try:
                    detalhes_var = ast.literal_eval(row_produto_selecionado.get('DETALHESGRADE', '{}'))
                    if isinstance(detalhes_var, dict) and detalhes_var:
                        desc_var = ", ".join([f"{k}: {v}" for k, v in detalhes_var.items()])
                    else:
                        desc_var = row_produto_selecionado['NOME'] 
                except:
                    desc_var = row_produto_selecionado['NOME'] 

                image_items.append(
                    {
                        "title": row_para_info['NOME'], 
                        "text": desc_var,              
                        "img": foto_selecionada_url,           
                    }
                )
                urls_adicionadas.add(foto_selecionada_url)

        # --- PRIORIDADE 2: Imagem principal (do Pai) ---
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
        
        # --- PRIORIDADE 3: Outras imagens de variação ---
        if not df_variacoes.empty:
            for idx, row_var in df_variacoes.iterrows():
                foto_var_url = row_var.get('FOTOURL', row_var.get('LINKIMAGEM')) 
                
                if pd.notna(foto_var_url) and foto_var_url not in urls_adicionadas:
                    try:
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
            st.image(image_items[0]['img'], caption=image_items[0]['text'], use_container_width=True)
        else:
            st.image("https://via.placeholder.com/400x400.png?text=Sem+Imagem", caption="Imagem não disponível", use_container_width=True)
            
        # --- FIM DO CARROSSEL ---


    # --- 9. SEÇÃO DE DESCRIÇÃO E DETALHES TÉCNICOS --- (Sem mudanças)
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
        st.text(f"Marca: {row_para_info.get('MARCA', 'N/D')}") 
        st.text(f"Categoria: {row_para_info.get('CATEGORIA', 'N/D')}")
        st.text(f"Código de Barras: {row_para_info.get('CODIGOBARRAS', 'N/D')}")


    # --- 10. SEÇÃO DE PRODUTOS RELACIONADOS --- (Sem mudanças)
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
                    
                    preco_card_orig = row_card['PRECO']
                    preco_card_final = row_card['PRECO_FINAL']
                    preco_promo_card = row_card.get('PRECO_PROMOCIONAL')
                    is_promo_card = pd.notna(preco_promo_card) and preco_promo_card > 0

                    if is_promo_card and preco_card_orig > preco_card_final:
                        st.write(f"<span style='text-decoration: line-through; color: #888; font-size: 0.9rem;'>R$ {preco_card_orig:,.2f}</span>", unsafe_allow_html=True)
                    else:
                        st.write("<br>", unsafe_allow_html=True) 

                    st.write(f"<h5 style='color: #880E4F; margin:0;'>R$ {preco_card_final:,.2f}</h5>", unsafe_allow_html=True)




