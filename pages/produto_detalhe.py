# pages/produto_detalhe.py
import streamlit as st
import pandas as pd
import ast # Para decodificar DetalhesGrade
from datetime import datetime
import time

# 🚨 IMPORTAÇÕES CRUCIAIS: GARANTA QUE ESSAS FUNÇÕES ESTÃO EXPOSTAS
# Apenas simula as importações necessárias
# from data_handler import carregar_catalogo, carregar_clientes_cashback
# from ui_components import (adicionar_qtd_ao_carrinho, calcular_cashback_total, 
#                            render_product_image_html, render_whatsapp_link) 
# from catalogo_utils import get_product_gallery_data, get_product_variations 


# --- SETUP INICIAL: Simula carregamento de dados e estado ---
# Em um ambiente real, você importaria e chamaria as funções de handler
if 'df_catalogo_base' not in st.session_state:
    st.error("Erro: Catálogo principal não carregado. Retorne à Página Principal.")
    st.stop()
    
# Usamos o DF base que contém o PaiID, DetalhesGrade, etc.
DF_CATALOGO_COMPLETO = st.session_state.df_catalogo_base 
DF_CLIENTES_CASH = st.session_state.get('DF_CLIENTES_CASH') # Assumindo que está no estado global

# === FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO DE CONTEÚDO ===

def render_product_details_content(product_id: int, df_catalogo_base: pd.DataFrame, df_clientes_cash: pd.DataFrame):
    
    # 1. Busca a linha do produto (o Pai/Modelo)
    try:
        product_data = df_catalogo_base.loc[product_id]
    except KeyError:
        st.error(f"❌ Produto com ID {product_id} não encontrado no catálogo.")
        return

    # --- SIMULAÇÃO DE LÓGICA DE DETALHES NECESSÁRIA PARA ESTE ARQUIVO ---
    # *Você precisa garantir que estas funções sejam movidas para catalogo_utils.py ou data_handler.py*
    def get_product_gallery_data(product_data: pd.Series) -> list:
        all_photos = [product_data['LINKIMAGEM']] if product_data.get('LINKIMAGEM') else []
        # Adicione aqui a lógica de FOTOS_ADICIONAIS se ela existir no seu CSV
        return [url for url in all_photos if str(url).startswith('http')]

    def get_product_variations(product_id: int, df_catalogo_completo: pd.DataFrame) -> pd.DataFrame:
        df_filhos = df_catalogo_completo[
            df_catalogo_completo['PAIID'].astype(str) == str(product_id)
        ].copy()
        if 'DETALHESGRADE' in df_filhos.columns:
            def extract_label(details_json):
                if pd.isna(details_json) or not details_json: return ""
                try:
                    detalhes = ast.literal_eval(details_json)
                    # Exemplo de label: "Cor: Vermelho - Tam: 38"
                    return ' - '.join([f"{k.split('/')[0]}: {v}" for k, v in detalhes.items() if v])
                except: return ""

            df_filhos['Variação_Label'] = df_filhos.apply(
                lambda row: f"{extract_label(row.get('DETALHESGRADE'))} (Estoque: {int(row['QUANTIDADE'])})", 
                axis=1
            )
        return df_filhos


    # --- INÍCIO DA ESTRUTURA DA PÁGINA (Layout) ---

    st.title(f"✨ {product_data['NOME']}")
    
    # 1. CABEÇALHO E BOTÃO DE RETORNO
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ Voltar ao Catálogo"):
            st.experimental_set_query_params(view_product_id=None)
            st.rerun()

    st.markdown("---") 

    # --- SEÇÃO 2: CARROSSEL DE FOTOS E INFO RÁPIDA ---
    col_gallery, col_info = st.columns([2, 3]) 

    # Lógica do Carrossel de Fotos (Item 4)
    all_photos = get_product_gallery_data(product_data)
    selected_photo_key = f"selected_photo_index_{product_id}"
    if selected_photo_key not in st.session_state:
        st.session_state[selected_photo_key] = 0 
        
    current_photo_url = all_photos[st.session_state[selected_photo_key]] if all_photos else None


    with col_gallery:
        # Imagem Principal (Grande)
        if current_photo_url:
            st.image(current_photo_url, use_column_width=True)

        # Carrossel de Miniaturas (Renderização de botões para trocar a foto)
        if len(all_photos) > 1:
            st.markdown("<div style='margin-top: 10px; display: flex; gap: 5px; flex-wrap: wrap;'>", unsafe_allow_html=True)
            for i, photo_url in enumerate(all_photos):
                # Usamos um truque de CSS para aplicar borda à miniatura selecionada
                is_selected = st.session_state[selected_photo_key] == i
                style = "border: 2px solid #FF4B4B; border-radius: 5px;" if is_selected else "border: 1px solid #ccc; border-radius: 5px;"
                
                # O botão atualiza o estado e reruns
                if st.button(label=" ", key=f"thumb_{product_id}_{i}"):
                    st.session_state[selected_photo_key] = i
                    st.rerun() 
                    
                st.markdown(
                    f"""
                    <div style="width: 70px; height: 70px; overflow: hidden; {style}">
                       <img src="{photo_url}" style="width: 100%; height: 100%; object-fit: cover; margin-top: -38px;"/>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)


    # --- Informações e Ação de Compra ---
    with col_info:
        st.subheader("Especificações Rápidas")
        
        preco_final = product_data['PRECO_FINAL']
        preco_original = product_data['PRECO']
        is_promotion = pd.notna(product_data.get('PRECO_PROMOCIONAL'))
        condicao_pagamento = product_data.get('CONDICAOPAGAMENTO', 'Preço à vista')

        if is_promotion:
            st.markdown(f"""
            <div style="line-height: 1.2;">
                <span style='text-decoration: line-through; color: #757575; font-size: 1.1rem;'>R$ {preco_original:.2f}</span>
                <h2 style='color: #D32F2F; margin:0;'>R$ {preco_final:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final:.2f}</h2>", unsafe_allow_html=True)

        st.markdown(f"<span style='color: #757575; font-size: 1rem; font-weight: normal;'>({condicao_pagamento})</span>", unsafe_allow_html=True)
        st.markdown("---")
        
        # --- SELEÇÃO DE VARIAÇÃO (Item B5) ---
        df_filhos = get_product_variations(product_id, df_catalogo_base)
        produto_a_comprar = product_data # Default é o próprio pai/simples

        if not df_filhos.empty:
            st.markdown("##### 🎨 Escolha o Tom/Variação:")
            
            opcoes_labels = ['Selecione a Variação'] + df_filhos['Variação_Label'].tolist()
            
            variacao_selecionada_label = st.selectbox(
                "Variação:",
                options=opcoes_labels,
                key=f"select_variacao_{product_id}",
                label_visibility="collapsed"
            )

            if variacao_selecionada_label and variacao_selecionada_label != 'Selecione a Variação':
                # Encontra o produto filho (que tem estoque e ID real)
                produto_a_comprar = df_filhos[df_filhos['Variação_Label'] == variacao_selecionada_label].iloc[0]
                
                estoque_disponivel = int(produto_a_comprar['QUANTIDADE'])
                if estoque_disponivel <= 0:
                    st.error("🚫 Variação esgotada. Escolha outra opção.")
                    produto_a_comprar = None
                
            else:
                produto_a_comprar = None # Impede a compra se nada foi selecionado
        
        else:
            estoque_disponivel = int(product_data['QUANTIDADE'])


        # --- Bloco de Ação (Adicionar ao Carrinho) ---
        if produto_a_comprar is not None:
            id_final_compra = produto_a_comprar['ID']
            
            with st.container(border=True):
                # 🚨 IMPORTANTE: Se for um filho, use o estoque do filho
                max_qtd = int(produto_a_comprar['QUANTIDADE']) if not df_filhos.empty else int(product_data['QUANTIDADE'])

                qtd = st.number_input("Quantidade:", min_value=1, max_value=max_qtd, value=1, key=f"details_qtd_{product_id}")
                
                st.success(f"Cashback estimado: R$ X,XX") # Lógica A1/A2 viria aqui
                
                if st.button("🛒 Adicionar ao Pedido", key=f"details_add_cart_{product_id}", type="primary", use_container_width=True):
                    # adicionar_qtd_ao_carrinho(id_final_compra, produto_a_comprar, qtd) 
                    st.toast(f"{qtd}x {produto_a_comprar['NOME']} adicionado!", icon="🛒")
        else:
            st.error("Selecione uma variação válida ou aguarde a reposição de estoque.")


    # --- SEÇÃO 3: DETALHES COMPLETOS (Descrição, Especificações) ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---") 
    st.subheader("📚 Detalhes e Aplicação")
    descricao_longa = product_data.get('DESCRICAOLONGA')
    st.markdown(descricao_longa if descricao_longa else product_data['DESCRICAOCURTA'])
    
    # --- SEÇÃO 4: SUGESTÕES DE PRODUTOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("Você também pode gostar:")
    # Aqui viria a chamada para a função render_product_suggestions(product_id, df_catalogo_base)
    st.info("Sugestões de produtos relacionados virão aqui.")


# === FUNÇÃO PRINCIPAL QUE O STREAMLIT CHAMA ===
def main():
    
    # 1. Obter o ID do produto da URL (Crucial para o deep link)
    query_params = st.experimental_get_query_params()
    product_id_str = query_params.get("view_product_id", [None])[0]

    if not product_id_str:
        st.error("Erro: Nenhum ID de produto fornecido. Retorne ao catálogo.")
        return

    try:
        product_id = int(product_id_str)
        
        # 2. RENDERIZA A ESTRUTURA COMPLETA
        render_product_details_content(product_id, DF_CATALOGO_COMPLETO, DF_CLIENTES_CASH) 
        
    except ValueError:
        st.error("ID de produto inválido na URL.")

main()
