# detalhes_produto_ui.py

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
    Remove o bloco "Vendido e Entregue por" e mantém a estrutura de descrição.
    
    NOVA FUNCIONALIDADE: Usa um carrossel para exibir a foto do produto PAI
    e de todas as suas VARIAÇÕES (filhos).
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
    id_pai_real = row_clicada.get('PaiID')
    
    # VERIFICA SE O ITEM CLICADO É UM FILHO (tem um PaiID)
    if pd.notna(id_pai_real):
        try:
            # Se for filho, busca o PAI VERDADEIRO para exibir as infos
            id_pai_real = int(id_pai_real) # Converte para int caso seja float
            id_principal_para_info = id_pai_real
            row_para_info = df_catalogo_indexado.loc[id_pai_real].copy()
        except (KeyError, ValueError):
            # Fallback: Se o PaiID não for encontrado (dado órfão), usa o próprio produto
            st.warning("Produto órfão encontrado. Exibindo dados do item.")
            id_principal_para_info = produto_id_clicado
            row_para_info = row_clicada
    else:
        # Se for pai (ou item simples), usa ele mesmo
        id_principal_para_info = produto_id_clicado
        row_para_info = row_clicada

    # AGORA, BUSCA AS VARIAÇÕES (FILHOS)
    # Se o item clicado for PAI, busca os filhos dele
    # Se o item clicado for FILHO, busca os filhos do PAI dele (irmãos)
    id_pai_para_buscar_filhos = id_principal_para_info 
    
    df_variacoes = df_catalogo_indexado[
        df_catalogo_indexado['PaiID'] == id_pai_para_buscar_filhos
    ].copy()
    
    # Tenta avaliar a grade do PAI
    try:
        detalhes_pai = ast.literal_eval(row_para_info.get('DetalhesGrade', '{}'))
        if not isinstance(detalhes_pai, dict):
            detalhes_pai = {}
    except:
        detalhes_pai = {}

    # Se o PAI também tiver 'DetalhesGrade' (for uma variação vendável)
    # E houver outras variações, nós o adicionamos à lista para seleção
    if detalhes_pai and not df_variacoes.empty:
         # Adiciona o PAI ao DF de variações
         df_variacoes = pd.concat([row_para_info.to_frame().T, df_variacoes])
         # Remove duplicatas
         df_variacoes = df_variacoes[~df_variacoes.index.duplicated(keep='first')]

    # --- FIM LÓGICA VARIAÇÕES ---


    # --- 2. APLICAÇÃO DE ESTILO CSS (Opcional, mas melhora a aparência) ---
    st.markdown("""
    <style>
        /* Ajusta o padding/margin da imagem e info */
        .stButton>button { width: 100%; background-color: #880E4F; color: white; }
        .stButton>button:hover { background-color: #6a0b3d; color: white; }
        h1 { font-size: 1.8rem; }
        h3 { font-size: 1.3rem; }
        .stRadio [role="radiogroup"] { justify-content: flex-start; }
        .stRadio [role="radio"] { margin-right: 15px; }
    </style>
    """, unsafe_allow_html=True)


    # --- 3. LAYOUT DA TELA (COLUNAS) ---
    col_img, col_info = st.columns([2, 3]) # 40% img, 60% info

    with col_img:
        # --- INÍCIO DA ALTERAÇÃO: LÓGICA DO CARROSSEL DE IMAGENS ---
        
        # 1. Prepara a lista de imagens para o carrossel
        image_items = []
        urls_adicionadas = set() # Para evitar fotos duplicadas
        
        # Adiciona a imagem principal (do PAI ou produto principal)
        foto_principal_url = row_para_info['FotoURL']
        if pd.notna(foto_principal_url) and foto_principal_url not in urls_adicionadas:
            image_items.append(
                {
                    "title": row_para_info['NOME'],
                    "text": row_para_info.get('CATEGORIA', row_para_info.get('Marca', '')), 
                    "img": foto_principal_url,
                }
            )
            urls_adicionadas.add(foto_principal_url)
        
        # Adiciona as imagens das VARIAÇÕES (FILHOS), se houver
        if not df_variacoes.empty:
            for idx, row_var in df_variacoes.iterrows():
                foto_var_url = row_var['FotoURL']
                # Adiciona apenas se a URL for válida e ainda não estiver no carrossel
                if pd.notna(foto_var_url) and foto_var_url not in urls_adicionadas:
                    
                    # Tenta extrair a descrição da variação (Ex: "Cor: Café")
                    try:
                        detalhes_var = ast.literal_eval(row_var.get('DetalhesGrade', '{}'))
                        if isinstance(detalhes_var, dict) and detalhes_var:
                            # Formata os detalhes: "Cor: Café, Tamanho: 37/38"
                            desc_var = ", ".join([f"{k}: {v}" for k, v in detalhes_var.items()])
                        else:
                            desc_var = row_var['NOME'] # Fallback
                    except:
                        desc_var = row_var['NOME'] # Fallback
                        
                    image_items.append(
                        {
                            "title": row_para_info['NOME'], # Título é o mesmo
                            "text": desc_var,              # Texto é a variação
                            "img": foto_var_url,           # Imagem da variação
                        }
                    )
                    urls_adicionadas.add(foto_var_url)

        # 2. Renderiza o Carrossel (se houver mais de 1 img) ou Imagem Única
        if len(image_items) > 1:
            # Usa o streamlit_carousel (já importado no topo do arquivo)
            carousel(items=image_items, controls=True, indicators=True, interval=None, use_container_width=True)
        elif image_items: # Garante que a lista não está vazia
            # Renderiza a imagem única (comportamento antigo)
            st.image(image_items[0]['img'], caption=image_items[0]['text'], use_column_width=True)
        else:
            # Fallback se nenhuma imagem for encontrada
            st.image("https://via.placeholder.com/400x400.png?text=Sem+Imagem", caption="Imagem não disponível", use_column_width=True)
            
        # --- FIM DA ALTERAÇÃO ---

    with col_info:
        # --- 4. INFORMAÇÕES DO PRODUTO (Nome, Preço, etc.) ---
        
        # Usa 'row_para_info' para o título e infos principais
        st.title(row_para_info['NOME'])
        st.caption(f"Marca: {row_para_info.get('Marca', 'N/D')} | Categoria: {row_para_info.get('CATEGORIA', 'N/D')}")
        
        # --- SELEÇÃO DE VARIAÇÃO (GRADE) ---
        row_produto_selecionado = None
        id_produto_selecionado = None

        # Concatena o PAI e os FILHOS para criar os seletores
        all_products_for_grade = pd.concat([row_para_info.to_frame().T, df_variacoes])
        all_products_for_grade = all_products_for_grade[~all_products_for_grade.index.duplicated(keep='first')]
        # Filtra apenas os que têm 'DetalhesGrade' válidos
        products_with_grade = []
        for idx, row in all_products_for_grade.iterrows():
            try:
                detalhes = ast.literal_eval(row.get('DetalhesGrade', '{}'))
                if isinstance(detalhes, dict) and detalhes:
                    products_with_grade.append(row)
            except:
                continue
        
        df_grade = pd.DataFrame(products_with_grade)

        if not df_grade.empty:
            st.markdown("---")
            st.subheader("Escolha sua variação:")
            
            # 1. Coleta todas as opções disponíveis
            opcoes_disponiveis = {} # Ex: {'Cor': ['Café', 'Vermelho'], 'Tamanho': ['37/38', '35/36']}
            
            for idx, row_g in df_grade.iterrows():
                detalhes_g = ast.literal_eval(row_g.get('DetalhesGrade', '{}'))
                for k, v in detalhes_g.items():
                    if k not in opcoes_disponiveis:
                        opcoes_disponiveis[k] = set()
                    opcoes_disponiveis[k].add(v)
            
            # Converte sets para listas ordenadas
            for k in opcoes_disponiveis:
                opcoes_disponiveis[k] = sorted(list(opcoes_disponiveis[k]))

            # 2. Renderiza os st.radio/st.selectbox para cada tipo de grade
            selecao_usuario = {}
            
            # Tenta pré-selecionar com base no 'row_clicada'
            try:
                detalhes_clicados = ast.literal_eval(row_clicada.get('DetalhesGrade', '{}'))
                if not isinstance(detalhes_clicados, dict):
                    detalhes_clicados = {}
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
            # Itera novamente para encontrar o ID que bate com a 'selecao_usuario'
            for idx, row_g in df_grade.iterrows():
                detalhes_g = ast.literal_eval(row_g.get('DetalhesGrade', '{}'))
                if detalhes_g == selecao_usuario:
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

        # Agora, 'id_produto_selecionado' e 'row_produto_selecionado' 
        # contêm o item exato (seja pai ou filho) a ser exibido o preço e adicionado ao carrinho

        if row_produto_selecionado is None:
             st.error("Não foi possível selecionar o produto. Tente novamente.")
             return

        # --- PREÇO ---
        # Usa o preço do 'row_produto_selecionado'
        preco_original = row_produto_selecionado['PRECO_CARTAO']
        preco_promocional = row_produto_selecionado.get('PRECO_PROMOCIONAL') # Usa .get() por segurança

        st.markdown("---")
        if pd.notna(preco_promocional) and preco_promocional > 0:
            st.write(f"De: <span style='text-decoration: line-through; color: #888;'>R$ {preco_original:,.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: #880E4F; margin:0;'>Por: R$ {preco_promocional:,.2f}</h3>", unsafe_allow_html=True)
            st.caption(f"no PIX ou à vista")
            preco_final_selecionado = preco_promocional
        else:
            st.markdown(f"<h3 style='color: #880E4F; margin:0;'>R$ {row_produto_selecionado['PRECO_VISTA']:,.2f}</h3>", unsafe_allow_html=True)
            st.caption(f"no PIX ou à vista")
            preco_final_selecionado = row_produto_selecionado['PRECO_VISTA']


        # --- 5. LÓGICA DE COMPRA (Quantidade e Estoque) ---
        
        # Usa o estoque do 'row_produto_selecionado'
        estoque_disponivel = row_produto_selecionado['QUANTIDADE']
        
        if estoque_disponivel > ESTOQUE_BAIXO_LIMITE:
            st.success(f"**Em estoque** ({estoque_disponivel} unidades)")
            max_qty = int(min(estoque_disponivel, 10)) # Limita a 10 ou ao estoque
        elif 0 < estoque_disponivel <= ESTOQUE_BAIXO_LIMITE:
            st.warning(f"**Últimas unidades!** ({estoque_disponivel} restantes)")
            max_qty = int(estoque_disponivel)
        else:
            st.error("**Produto indisponível**")
            max_qty = 0

        if max_qty > 0:
            key_qtd = f"qtd_{id_produto_selecionado}"
            
            # Botões +/- para quantidade
            col_qtd_1, col_qtd_2, col_qtd_3 = st.columns([1, 2, 1])
            with col_qtd_1:
                if st.button("➖", key=f"down_{key_qtd}", use_container_width=True):
                    if st.session_state.get(key_qtd, 1) > 1:
                        st.session_state[key_qtd] -= 1
            with col_qtd_2:
                # Inicializa a quantidade
                if key_qtd not in st.session_state:
                    st.session_state[key_qtd] = 1
                
                # Garante que a quantidade não exceda o estoque
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
            
            # Botão Adicionar ao Carrinho
            if st.button("Adicionar ao carrinho", key=f"add_{id_produto_selecionado}", type="primary"):
                qtd = st.session_state.get(key_qtd, 1)
                
                # Passa o 'row_produto_selecionado' completo
                adicionar_qtd_ao_carrinho(row_produto_selecionado, qtd, preco_final_selecionado)
                
                st.toast(f"{qtd}x {row_produto_selecionado['NOME']} adicionado(s)!")
                time.sleep(0.5)
                # Não precisa de rerun, o popover do carrinho atualiza
        else:
            st.markdown("<br>", unsafe_allow_html=True)


    # --- 6. SEÇÃO DE DESCRIÇÃO E DETALHES TÉCNICOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab_desc, tab_details = st.tabs(["**Descrição do Produto**", "**Detalhes Técnicos**"])

    with tab_desc:
        # Usa a descrição do PAI
        st.subheader("Descrição")
        # Substitua pela coluna de descrição do seu CSV (se houver)
        descricao = row_para_info.get('DESCRICAO', "Descrição detalhada do produto... Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam scelerisque id nunc nec volutpat. Vivamus nec quamS.")
        st.write(descricao)

    with tab_details:
        st.subheader("Detalhes Técnicos")
        st.text(f"ID do Produto: {id_principal_para_info}")
        st.text(f"Marca: {row_para_info.get('Marca', 'N/D')}")
        st.text(f"Categoria: {row_para_info.get('CATEGORIA', 'N/D')}")
        st.text(f"Código de Barras: {row_para_info.get('CodigoBarras', 'N/D')}")
        # Adicione mais detalhes técnicos se necessário


    # --- 7. SEÇÃO DE PRODUTOS RELACIONADOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Layout do título "Relacionados"
    col_rel_1, col_rel_2 = st.columns([3, 1])
    with col_rel_1:
        st.subheader("Quem viu, viu também")
    with col_rel_2:
        # Este link pode voltar para a home/categoria
        # st.markdown("<span style='font-weight: bold;'>Ver tudo ></span>", unsafe_allow_html=True) 
        pass

    # Filtra o próprio produto e seus filhos da lista de relacionados
    ids_para_excluir = [id_principal_para_info] + list(df_variacoes.index)
    
    df_amostra = df_catalogo_indexado[
        ~df_catalogo_indexado.index.isin(ids_para_excluir)
    ].head(4).reset_index() # Pega 4 aleatórios (ou da mesma categoria)
    
    if not df_amostra.empty:
        cols_cards = st.columns(len(df_amostra))

        for i, col in enumerate(cols_cards):
            if i < len(df_amostra):
                row_card = df_amostra.loc[i]
                prod_id_card = row_card['ID']
                
                with col:
                    # 1. A imagem é clicável
                    render_product_image_clickable(row_card['LINKIMAGEM'], prod_id_card) 
                    
                    # 2. Informações
                    st.caption(f"**{row_card['NOME']}**")
                    # st.markdown("⭐⭐⭐⭐ (342)", unsafe_allow_html=True) 
                    
                    # Lógica de preço para os cards relacionados
                    preco_card_orig = row_card['PRECO_CARTAO']
                    preco_card_promo = row_card.get('PRECO_PROMOCIONAL')

                    if pd.notna(preco_card_promo) and preco_card_promo > 0:
                        preco_final_card = preco_card_promo
                        st.write(f"<span style='text-decoration: line-through; color: #888; font-size: 0.9rem;'>R$ {preco_card_orig:,.2f}</span>", unsafe_allow_html=True)
                    else:
                        preco_final_card = row_card['PRECO_VISTA']
                        st.write("<br>", unsafe_allow_html=True) # Espaçador

                    st.write(f"<h5 style='color: #880E4F; margin:0;'>R$ {preco_final_card:,.2f}</h5>", unsafe_allow_html=True)
