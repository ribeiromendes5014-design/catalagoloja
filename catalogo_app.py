# catalogo_app.py

import streamlit as st
import pandas as pd
import json
import time
from streamlit_autorefresh import st_autorefresh
import requests

# Importa as funções e constantes dos novos módulos
# CERTIFIQUE-SE DE QUE data_handler.py E ui_components.py EXISTEM NO MESMO DIRETÓRIO
from data_handler import (
    carregar_catalogo, carregar_cupons, carregar_clientes_cashback, buscar_cliente_cashback, 
    salvar_pedido, BACKGROUND_IMAGE_URL, LOGO_DOCEBELLA_URL, NUMERO_WHATSAPP
)
from ui_components import (
    adicionar_qtd_ao_carrinho, remover_do_carrinho, limpar_carrinho, 
    calcular_cashback_total, render_product_card
)

# --- Inicialização do Carrinho de Compras e Estado ---
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}
if 'pedido_confirmado' not in st.session_state:
    st.session_state.pedido_confirmado = None
if 'cupom_aplicado' not in st.session_state:
    st.session_state.cupom_aplicado = None
if 'desconto_cupom' not in st.session_state:
    st.session_state.desconto_cupom = 0.0
if 'cupom_mensagem' not in st.session_state:
    st.session_state.cupom_mensagem = ""
    
# OTIMIZAÇÃO: Cache do catálogo principal no estado da sessão para evitar re-leitura constante
if 'df_catalogo_indexado' not in st.session_state:
    st.session_state.df_catalogo_indexado = None


# --- Inicializa Dados (Uma vez) ---
if st.session_state.df_catalogo_indexado is None:
    st.session_state.df_catalogo_indexado = carregar_catalogo()

DF_CLIENTES_CASH = carregar_clientes_cashback()


# --- Funções Auxiliares de UI ---
def copy_to_clipboard_js(text_to_copy):
    js_code = f"""
    <script>
    function copyTextToClipboard(text) {{
      if (navigator.clipboard) {{
        navigator.clipboard.writeText(text).then(function() {{
          alert('Resumo do pedido copiado!');
        }}, function(err) {{
          console.error('Não foi possível copiar o texto: ', err);
          alert('Erro ao copiar o texto. Tente novamente.');
        }});
      }} else {{
        const textArea = document.createElement("textarea");
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {{
          document.execCommand('copy');
          alert('Resumo do pedido copiado!');
        }} catch (err) {{
          console.error('Fallback: Não foi possível copiar o texto: ', err);
          alert('Erro ao copiar o texto. Tente novamente.');
        }}
        document.body.removeChild(textArea);
      }}
    }}
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)


# --- Layout do Aplicativo (INÍCIO DO SCRIPT PRINCIPAL) ---
st.set_page_config(page_title="Catálogo Doce&Bella", layout="wide", initial_sidebar_state="collapsed")

# --- CSS (COM CORREÇÃO DE LAYOUT) ---
st.markdown(f"""
<style>
#MainMenu, footer, [data-testid="stSidebar"] {{visibility: hidden;}}
[data-testid="stSidebarHeader"], [data-testid="stToolbar"], a[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"], [data-testid="stDecoration"] {{ display: none !important; }}
div[data-testid="stPopover"] > div:first-child > button {{ display: none; }}
.stApp {{ background-image: url({BACKGROUND_IMAGE_URL}) !important; background-size: cover; background-attachment: fixed; }}

/* CORREÇÃO PARA MODO ESCURO: Força a cor do texto para ser escura dentro do container principal */
div.block-container {{ 
    background-color: rgba(255, 255, 255, 0.95); 
    border-radius: 10px; 
    padding: 2rem; 
    margin-top: 1rem; 
    color: #262626; /* Cor de texto padrão forçada para preto escuro */
}}
/* Garante que o texto em parágrafos e títulos também seja escuro, superando o modo escuro do celular */
div.block-container p, div.block-container h1, div.block-container h2, div.block-container h3, div.block-container h4, div.block-container h5, div.block-container h6, div.block-container span {{
    color: #262626 !important;
}}

.pink-bar-container {{ background-color: #E91E63; padding: 20px 0; width: 100vw; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
.pink-bar-content {{ width: 100%; max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; align-items: center; }}
.cart-badge-button {{ background-color: #C2185B; color: white; border-radius: 12px; padding: 8px 15px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; transition: background-color 0.3s; display: inline-flex; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 150px; justify-content: center; }}
.cart-badge-button:hover {{ background-color: #C2185B; }}
.cart-count {{ background-color: white; color: #E91E63; border-radius: 50%; padding: 2px 7px; margin-left: 8px; font-size: 14px; line-height: 1; }}
div[data-testid="stButton"] > button {{ background-color: #E91E63; color: white; border-radius: 10px; border: 1px solid #C2185B; font-weight: bold; }}
div[data-testid="stButton"] > button:hover {{ background-color: #C2185B; color: white; border: 1px solid #E91E63; }}
.product-image-container {{ height: 220px; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; overflow: hidden; }}
.product-image-container img {{ max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px; }}
.esgotado-badge {{ background-color: #757575; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem; margin-bottom: 0.5rem; display: block; }}
.estoque-baixo-badge {{ background-color: #FFC107; color: black; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem; margin-bottom: 0.5rem; display: block; }}

/* --- NOVO CSS PARA O CARD DO PRODUTO (CORREÇÃO DE LAYOUT) --- */
.price-action-flex {{
    display: flex;
    justify-content: space-between; 
    align-items: flex-end; 
    margin-top: 1rem;
    gap: 10px; 
}}

.action-buttons-container {{
    flex-shrink: 0;
    width: 45%; 
}}

/* Garante que o input de número se ajuste dentro da coluna de 45% */
.action-buttons-container div[data-testid="stNumberInput"] {{
    width: 100%;
}}

/* --- CSS para o Botão Flutuante --- */
.whatsapp-float {{
    position: fixed;
    bottom: 40px;
    right: 40px;
    background-color: #25D366;
    color: white;
    border-radius: 50px;
    width: 60px;
    height: 60px;
    text-align: center;
    font-size: 30px;
    box-shadow: 2px 2px 3px #999;
}}
.whatsapp-float span {{
    color: white !important;
    margin-top: 15px;
    display: block;
}}
</style>
""", unsafe_allow_html=True)


st_autorefresh(interval=6000000000, key="auto_refresh_catalogo")


# --- Tela de Pedido Confirmado ---
if st.session_state.pedido_confirmado:
    st.balloons()
    st.success("🎉 Pedido enviado com sucesso! Utilize o resumo abaixo para confirmar o pedido pelo WhatsApp.")
    
    pedido = st.session_state.pedido_confirmado
    itens_formatados = '\n'.join([
        f"- {item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f} un.)" 
        for item in pedido['itens']
    ])

    resumo_texto = (
        f"***📝 RESUMO DO PEDIDO - DOCE&BELLA ***\n\n"
        f"🛒 Cliente: {pedido['nome']}\n"
        f"📞 Contato: {pedido['contato']}\n"
        f"💎 Nível Atual: {pedido.get('cliente_nivel_atual', 'N/A')}\n"
        f"💰 Saldo Cashback: R$ {pedido.get('cliente_saldo_cashback', 0.00):.2f}\n\n"
        f"📦 Itens Pedidos:\n"
        f"{itens_formatados}\n\n"
        f"🎟️ Cupom Aplicado: {pedido.get('cupom_aplicado', 'Nenhum')}\n"
        f"📉 Desconto Total: R$ {pedido.get('desconto_cupom', 0.0):.2f}\n\n"
        f"✅ CASHBACK A SER GANHO: R$ {pedido.get('cashback_a_ganhar', 0.0):.2f}\n" 
        f"💰 VALOR TOTAL A PAGAR: R$ {pedido['total']:.2f}\n\n"
        f"Obrigado por seu pedido!"
    )

    st.text_area("Resumo do Pedido (Clique para copiar)", resumo_texto, height=300)
    
    copy_to_clipboard_js(resumo_texto)
    st.markdown(
        f'<button class="cart-badge-button" style="background-color: #25D366; width: 100%; margin-bottom: 15px;" onclick="copyTextToClipboard(\'{resumo_texto.replace("'", "\\'")}\')">✅ Copiar Resumo</button>',
        unsafe_allow_html=True
    )
    
    if st.button("Voltar ao Catálogo"):
        st.session_state.pedido_confirmado = None
        limpar_carrinho()
        st.rerun()
    st.stop()


# --- Banner Principal ---
st.markdown(f"""
<style>
.banner-colored {{
    background-color: #e91e63;
    padding: 10px 25px; 
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 25px;
    margin-bottom: 20px;
}}

.banner-colored img {{
    max-height: 80px;  /* Você pode ajustar a altura aqui */
    width: auto;
    object-fit: contain; /* <-- ESTA É A CORREÇÃO */
}}

.banner-colored h1 {{
    color: white;
    font-size: 2rem; 
    margin: 0;
}}
</style>

<div class="banner-colored">
    <img src="{LOGO_DOCEBELLA_URL}" alt="Doce&Bella Logo">
    <h1>Catálogo de Pedidos Doce&Bella</h1>
</div>
""", unsafe_allow_html=True)


# --- Barra de Busca e Carrinho (Pop-up) ---
total_acumulado = sum(item['preco'] * item['quantidade'] for item in st.session_state.carrinho.values())
num_itens = sum(item['quantidade'] for item in st.session_state.carrinho.values())
carrinho_vazio = not st.session_state.carrinho

df_catalogo_completo = st.session_state.df_catalogo_indexado 
cashback_a_ganhar = calcular_cashback_total(st.session_state.carrinho, df_catalogo_completo)

st.markdown("<div class='pink-bar-container'><div class='pink-bar-content'>", unsafe_allow_html=True)

col_pesquisa, col_carrinho = st.columns([5, 1])
with col_pesquisa:
    st.text_input("Buscar...", key='termo_pesquisa_barra', label_visibility="collapsed", placeholder="Buscar produtos...")

with col_carrinho:
    custom_cart_button = f"""
        <div class='cart-badge-button' onclick='document.querySelector("[data-testid=\\"stPopover\\"] > div:first-child > button").click();'>
            🛒 SEU PEDIDO
            <span class='cart-count'>{num_itens}</span>
        </div>
    """
    st.markdown(custom_cart_button, unsafe_allow_html=True)
    with st.popover(" ", use_container_width=False, help="Clique para ver os itens e finalizar o pedido"):
        st.header("🛒 Detalhes do Pedido")
        if carrinho_vazio:
            st.info("Seu carrinho está vazio.")
        else:
            desconto_cupom = st.session_state.get('desconto_cupom', 0.0)
            total_com_desconto = total_acumulado - desconto_cupom

            if total_com_desconto < 0:
                total_com_desconto = 0

            st.markdown(f"Subtotal: `R$ {total_acumulado:.2f}`")
            if desconto_cupom > 0:
                st.markdown(f"Desconto (`{st.session_state.cupom_aplicado}`): <span style='color: #D32F2F;'>- R$ {desconto_cupom:.2f}</span>", unsafe_allow_html=True)
            
            st.markdown(f"<span style='color: #2E7D32; font-weight: bold;'>Cashback a Ganhar: R$ {cashback_a_ganhar:.2f}</span>", unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='color: #E91E63; margin-top: 0;'>Total: R$ {total_com_desconto:.2f}</h3>", unsafe_allow_html=True)
            st.markdown("---")
            
            col_h1, col_h2, col_h3, col_h4 = st.columns([3, 1.5, 2.5, 1])
            col_h2.markdown("**Qtd**")
            col_h3.markdown("**Subtotal**")
            col_h4.markdown("")
            st.markdown('<div style="margin-top: -10px; border-top: 1px solid #ccc;"></div>', unsafe_allow_html=True)
            
            df_catalogo_completo = st.session_state.df_catalogo_indexado 
            
            for prod_id, item in list(st.session_state.carrinho.items()):
                c1, c2, c3, c4 = st.columns([3, 1.5, 2.5, 1])
                c1.write(f"*{item['nome']}*")
                
                if prod_id in df_catalogo_completo.index:
                    max_qtd = df_catalogo_completo.loc[prod_id, 'QUANTIDADE']
                    if isinstance(max_qtd, pd.Series):
                         max_qtd = max_qtd.iloc[0]
                else:
                    max_qtd = 999999
                max_qtd = int(max_qtd)
                
                if item['quantidade'] > max_qtd:
                    st.session_state.carrinho[prod_id]['quantidade'] = max_qtd
                    item['quantidade'] = max_qtd
                    st.toast(f"Ajustado: {item['nome']} ao estoque máximo de {max_qtd}.", icon="⚠️")
                    st.rerun()
                    
                nova_quantidade = c2.number_input(
                    label=f'Qtd_{prod_id}', min_value=1, max_value=max_qtd,
                    value=item['quantidade'], step=1, key=f'qtd_{prod_id}_popover',
                    label_visibility="collapsed"
                )
                
                if nova_quantidade != item['quantidade']:
                    st.session_state.carrinho[prod_id]['quantidade'] = nova_quantidade
                    st.rerun()

                subtotal_item = item['preco'] * item['quantidade']
                preco_unitario = item['preco']
                html_preco = f"""
                <div style="text-align: left; white-space: nowrap;">
                    <strong>R$ {subtotal_item:.2f}</strong>
                    <br>
                    <span style='font-size: 0.8rem; color: #757575;'>(R$ {preco_unitario:.2f} un.)</span>
                </div>
                """
                c3.markdown(html_preco, unsafe_allow_html=True)
                
                if c4.button("X", key=f'rem_{prod_id}_popover'):
                    remover_do_carrinho(prod_id)
                    st.rerun()
            st.markdown("---")
            
            # === LÓGICA DO CUPOM DE DESCONTO ===
            st.subheader("🎟️ Cupom de Desconto")
            
            cupom_col1, cupom_col2 = st.columns([3, 1])
            
            with cupom_col1:
                codigo_cupom_input = st.text_input("Código do Cupom", key="cupom_input", label_visibility="collapsed").upper()
            
            with cupom_col2:
                if st.button("Aplicar", key="aplicar_cupom_btn", use_container_width=True):
                    if codigo_cupom_input:
                        df_cupons_validos = carregar_cupons() 
                        cupom_encontrado = df_cupons_validos[df_cupons_validos['NOME_CUPOM'] == codigo_cupom_input]
                        
                        if not cupom_encontrado.empty:
                            cupom_info = cupom_encontrado.iloc[0]
                            valor_minimo = cupom_info['VALOR_MINIMO_PEDIDO']

                            if float(total_acumulado) >= float(valor_minimo):
                                tipo = cupom_info['TIPO_DESCONTO']
                                valor = cupom_info['VALOR_DESCONTO']
                                
                                desconto = 0.0
                                if tipo == 'PERCENTUAL':
                                    desconto = (valor / 100) * total_acumulado
                                elif tipo == 'FIXO':
                                    desconto = valor
                                
                                st.session_state.cupom_aplicado = codigo_cupom_input
                                st.session_state.desconto_cupom = desconto
                                st.session_state.cupom_mensagem = f"✅ Cupom '{codigo_cupom_input}' aplicado!"
                            else:
                                st.session_state.cupom_aplicado = None
                                st.session_state.desconto_cupom = 0.0
                                st.session_state.cupom_mensagem = f"❌ O valor mínimo para este cupom é de R$ {valor_minimo:.2f}."
                        else:
                            st.session_state.cupom_aplicado = None
                            st.session_state.desconto_cupom = 0.0
                            st.session_state.cupom_mensagem = "❌ Cupom inválido, expirado ou esgotado."
                    else:
                        st.session_state.cupom_mensagem = "⚠️ Digite um código de cupom."
                    st.rerun()

            if st.session_state.cupom_mensagem:
                if "✅" in st.session_state.cupom_mensagem:
                    st.success(st.session_state.cupom_mensagem)
                else:
                    st.error(st.session_state.cupom_mensagem)

            st.markdown("---")
            
            st.button("🗑️ Limpar Pedido", on_click=limpar_carrinho, use_container_width=True)
            st.markdown("---")
            
            # --- Finalizar Pedido ---
            st.subheader("Finalizar Pedido")

            nome_input = st.text_input("Seu Nome Completo:", key='checkout_nome_dynamic')
            contato_input = st.text_input("Seu Contato (WhatsApp - apenas números, com DDD):", key='checkout_contato_dynamic')
            
            nivel_cliente = 'N/A'
            saldo_cashback = 0.00
            
            if nome_input and contato_input and DF_CLIENTES_CASH is not None and not DF_CLIENTES_CASH.empty:
                existe, nome_encontrado, saldo_cashback, nivel_cliente = buscar_cliente_cashback(contato_input, DF_CLIENTES_CASH) 

                if existe:
                    st.success(
                        f"🎉 **Bem-vindo(a) de volta, {nome_encontrado}!** Seu Nível é: **{nivel_cliente.upper()}**."
                        f"\n\nSeu saldo atual de Cashback é de **R$ {saldo_cashback:.2f}**."
                    )
                elif contato_input.strip():
                    st.info("👋 **Novo Cliente!** Você começará a acumular cashback após a finalização do seu primeiro pedido no painel de administração.")

            with st.form("form_finalizar_pedido", clear_on_submit=True):
                st.text_input("Nome (Preenchido)", value=nome_input, disabled=True, label_visibility="collapsed")
                st.text_input("Contato (Preenchido)", value=contato_input, disabled=True, label_visibility="collapsed")

                if st.form_submit_button("✅ Enviar Pedido", type="primary", use_container_width=True):
                    if nome_input and contato_input:
                        
                        contato_limpo = contato_input.replace('(', '').replace(')', '').replace('-', '').replace(' ', '').strip()
                        
                        detalhes = {
                            "subtotal": total_acumulado,
                            "desconto_cupom": st.session_state.desconto_cupom,
                            "cupom_aplicado": st.session_state.cupom_aplicado,
                            "total": total_com_desconto,
                            "itens": [
                                {
                                    "id": int(k),
                                    "nome": v['nome'],
                                    "preco": v['preco'],
                                    "quantidade": v['quantidade'],
                                    "imagem": v.get('imagem', '')
                                } for k, v in st.session_state.carrinho.items()
                            ],
                            "nome": nome_input,
                            "contato": contato_limpo,
                            "cliente_nivel_atual": nivel_cliente, 
                            "cliente_saldo_cashback": saldo_cashback,
                            "cashback_a_ganhar": cashback_a_ganhar,
                        }
                        
                        if salvar_pedido(nome_input, contato_limpo, total_com_desconto, json.dumps(detalhes, ensure_ascii=False), detalhes): 
                            st.session_state.carrinho = {}
                            st.session_state.cupom_aplicado = None
                            st.session_state.desconto_cupom = 0.0
                            st.session_state.cupom_mensagem = ""
                            st.rerun()
                    else:
                        st.warning("Preencha seu nome e contato.")

st.markdown("</div></div>", unsafe_allow_html=True)


# --- Filtros e Ordenação ---
df_catalogo = st.session_state.df_catalogo_indexado.reset_index()

if 'CATEGORIA' in df_catalogo.columns:
    categorias = df_catalogo['CATEGORIA'].dropna().astype(str).unique().tolist()
    categorias.sort()
    categorias.insert(0, "TODAS AS CATEGORIAS")
else:
    categorias = ["TODAS AS CATEGORIAS"]
    if "Geral" not in df_catalogo.columns:
         st.warning("A coluna 'CATEGORIA' não foi encontrada no seu arquivo de catálogo. O filtro não será exibido.")

col_filtro_cat, col_select_ordem, _ = st.columns([1, 1, 3])

termo = st.session_state.get('termo_pesquisa_barra', '').lower()

with col_filtro_cat:
    categoria_selecionada = st.selectbox(
        "Filtrar por:",
        categorias,
        key='filtro_categoria_barra'
    )
    if termo:
        st.markdown(f'<div style="font-size: 0.8rem; color: #E91E63;">Busca ativa desabilita filtro.</div>', unsafe_allow_html=True)

df_filtrado = df_catalogo.copy()

if not termo and categoria_selecionada != "TODAS AS CATEGORIAS":
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA'].astype(str) == categoria_selecionada]
elif termo:
    df_filtrado = df_filtrado[df_filtrado.apply(
        lambda row: termo in str(row['NOME']).lower() or termo in str(row['DESCRICAOLONGA']).lower(), 
        axis=1
    )]

if df_filtrado.empty:
    if termo:
        st.info(f"Nenhum produto encontrado com o termo '{termo}' na categoria '{categoria_selecionada}'.")
    else:
        st.info(f"Nenhum produto encontrado na categoria '{categoria_selecionada}'.")
else:
    st.subheader("✨ Nossos Produtos")

    with col_select_ordem:
        opcoes_ordem = ['Lançamento', 'Promoção', 'Menor Preço', 'Maior Preço', 'Nome do Produto (A-Z)']
        ordem_selecionada = st.selectbox(
            "Ordenar por:",
            opcoes_ordem,
            key='ordem_produtos'
        )

    df_filtrado['EM_PROMOCAO'] = df_filtrado['PRECO_PROMOCIONAL'].notna()

    if ordem_selecionada == 'Lançamento':
        df_ordenado = df_filtrado.sort_values(by=['RECENCIA', 'EM_PROMOCAO'], ascending=[False, False])
    elif ordem_selecionada == 'Promoção':
        df_ordenado = df_filtrado.sort_values(by=['EM_PROMOCAO', 'RECENCIA'], ascending=[False, False])
    elif ordem_selecionada == 'Menor Preço':
        df_ordenado = df_filtrado.sort_values(by=['EM_PROMOCAO', 'PRECO_FINAL'], ascending=[False, True])
    elif ordem_selecionada == 'Maior Preço':
        df_ordenado = df_filtrado.sort_values(by=['EM_PROMOCAO', 'PRECO_FINAL'], ascending=[False, False])
    elif ordem_selecionada == 'Nome do Produto (A-Z)':
        df_ordenado = df_filtrado.sort_values(by=['EM_PROMOCAO', 'NOME'], ascending=[False, True])
    else:
        df_ordenado = df_filtrado

    df_filtrado = df_ordenado

    cols = st.columns(4)
    for i, row in df_filtrado.reset_index(drop=True).iterrows():
        product_id = row['ID']
        unique_key = f'prod_{product_id}_{i}'
        with cols[i % 4]:
            render_product_card(product_id, row, key_prefix=unique_key, df_catalogo_indexado=st.session_state.df_catalogo_indexado)


# --- Botão Flutuante do WhatsApp ---
MENSAGEM_PADRAO = "Olá, vi o catálogo de pedidos da Doce&Bella e gostaria de ajuda!"
LINK_WHATSAPP = f"https://wa.me/{NUMERO_WHATSAPP}?text={requests.utils.quote(MENSAGEM_PADRAO)}"

whatsapp_button_html = f"""
<a href="{LINK_WHATSAPP}" class="whatsapp-float" target="_blank" title="Fale Conosco pelo WhatsApp">
    <span>📞</span>
</a>
"""
st.markdown(whatsapp_button_html, unsafe_allow_html=True)

