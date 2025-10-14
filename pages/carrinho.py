import streamlit as st
import requests
import json
from components.global_cart import render_global_cart
from ui_components import remover_do_carrinho, limpar_carrinho, calcular_cashback_total
from data_handler import carregar_cupons, buscar_cliente_cashback, carregar_clientes_cashback, salvar_pedido, NUMERO_WHATSAPP

# --- Configuração da Página ---
st.set_page_config(page_title="Meu Carrinho - Doce&Bella", layout="wide", initial_sidebar_state="collapsed")

# --- Ícone flutuante e popover do carrinho (global) ---
render_global_cart()

# --- Garante estados principais ---
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}
if 'df_catalogo_indexado' not in st.session_state:
    st.warning("Catálogo ainda não carregado. Volte para o catálogo principal.")
    st.stop()

# --- Dados principais ---
carrinho = st.session_state.carrinho
carrinho_vazio = not carrinho
df_catalogo = st.session_state.df_catalogo_indexado
clientes_cash = carregar_clientes_cashback()

st.title("🛒 Revisar Pedido")

if carrinho_vazio:
    st.info("Seu carrinho está vazio. Volte ao catálogo para adicionar produtos.")
    st.stop()

# --- Tabela de Itens ---
total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
cashback = calcular_cashback_total(carrinho, df_catalogo)

st.subheader("Itens no Carrinho")
for prod_id, item in list(carrinho.items()):
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    col1.markdown(f"**{item['nome']}**")
    col2.write(f"R$ {item['preco']:.2f}")
    qtd = col3.number_input(
        "Qtd",
        min_value=1,
        max_value=int(df_catalogo.loc[prod_id, 'QUANTIDADE']),
        value=item['quantidade'],
        step=1,
        key=f"qtd_carrinho_{prod_id}",
        label_visibility="collapsed"
    )
    if qtd != item['quantidade']:
        st.session_state.carrinho[prod_id]['quantidade'] = qtd
        st.rerun()
    if col4.button("❌", key=f"remover_{prod_id}"):
        remover_do_carrinho(prod_id)
        st.rerun()

st.markdown("---")
st.markdown(f"**Subtotal:** R$ {total:.2f}")
st.markdown(f"**Cashback a ganhar:** R$ {cashback:.2f}")

# --- Cupom de desconto ---
st.subheader("🎟️ Cupom de Desconto")
col_cupom, col_btn = st.columns([3, 1])
codigo_cupom = col_cupom.text_input("Código do Cupom", placeholder="Digite seu cupom...").upper()

if col_btn.button("Aplicar"):
    df_cupons = carregar_cupons()
    cupom = df_cupons[df_cupons['NOME_CUPOM'] == codigo_cupom]
    if not cupom.empty:
        info = cupom.iloc[0]
        if total >= info['VALOR_MINIMO_PEDIDO']:
            valor = info['VALOR_DESCONTO']
            tipo = info['TIPO_DESCONTO']
            desconto = (valor / 100) * total if tipo == "PERCENTUAL" else valor
            st.session_state.desconto_cupom = desconto
            st.session_state.cupom_aplicado = codigo_cupom
            st.success(f"Cupom **{codigo_cupom}** aplicado com sucesso!")
        else:
            st.error(f"Valor mínimo para este cupom: R$ {info['VALOR_MINIMO_PEDIDO']:.2f}")
    else:
        st.error("Cupom inválido ou expirado.")
    st.rerun()

# --- Total Final ---
desconto = st.session_state.get("desconto_cupom", 0.0)
total_final = max(total - desconto, 0)
st.markdown("---")
st.markdown(f"### 💰 Total Final: R$ {total_final:.2f}")

# --- Dados do Cliente ---
st.subheader("👤 Identificação")
nome = st.text_input("Seu Nome Completo:")
telefone = st.text_input("WhatsApp (somente números, com DDD):")

nivel_cliente, saldo_cashback = "Novo Cliente", 0.0
if nome and telefone:
    existe, nome_real, saldo, nivel = buscar_cliente_cashback(telefone, clientes_cash)
    if existe:
        nivel_cliente, saldo_cashback = nivel, saldo
        st.success(f"Cliente encontrado: {nome_real} | Nível {nivel_cliente.upper()} | Saldo: R$ {saldo_cashback:.2f}")
    else:
        st.info("Novo cliente! Você começará a acumular cashback após este pedido.")

# --- Enviar Pedido ---
st.markdown("---")
if st.button("✅ Enviar Pedido pelo WhatsApp", use_container_width=True):
    if not nome or not telefone:
        st.warning("Preencha nome e WhatsApp antes de continuar.")
        st.stop()

    detalhes = {
        "itens": [
            {"id": k, "nome": v['nome'], "quantidade": v['quantidade'], "preco": v['preco']}
            for k, v in carrinho.items()
        ],
        "subtotal": total,
        "total_final": total_final,
        "cashback_a_ganhar": cashback,
        "nome": nome,
        "telefone": telefone,
        "cupom": st.session_state.get("cupom_aplicado"),
    }

    sucesso, id_pedido = salvar_pedido(nome, telefone, total_final, json.dumps(detalhes, ensure_ascii=False), detalhes)
    if sucesso:
        msg = f"Olá! Fiz um pedido (ID: {id_pedido}) no catálogo da Doce&Bella. Meu nome é {nome}."
        link = f"https://wa.me/{NUMERO_WHATSAPP}?text={requests.utils.quote(msg)}"
        st.markdown(f"[👉 Enviar Pedido no WhatsApp]({link})", unsafe_allow_html=True)
        limpar_carrinho()
    else:
        st.error("Erro ao salvar o pedido. Tente novamente.")
