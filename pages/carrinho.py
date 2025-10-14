import streamlit as st
import json
import requests
from ui_components import limpar_carrinho, remover_do_carrinho
from data_handler import carregar_cupons, salvar_pedido, buscar_cliente_cashback

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Carrinho", layout="wide", initial_sidebar_state="collapsed")

# --- SEGURANÇA: GARANTE QUE AS VARIÁVEIS EXISTAM ---
if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}
if "cupom_aplicado" not in st.session_state:
    st.session_state.cupom_aplicado = None
if "desconto_cupom" not in st.session_state:
    st.session_state.desconto_cupom = 0.0
if "cupom_mensagem" not in st.session_state:
    st.session_state.cupom_mensagem = ""

# --- VARIÁVEIS BASE ---
DF_CLIENTES_CASH = st.session_state.get("DF_CLIENTES_CASH", None)
df_catalogo_completo = st.session_state.get("df_catalogo_completo", None)
NUMERO_WHATSAPP = st.session_state.get("NUMERO_WHATSAPP", "5599999999999")

total_acumulado = sum(item["preco"] * item["quantidade"] for item in st.session_state.carrinho.values())
carrinho_vazio = len(st.session_state.carrinho) == 0
cashback_a_ganhar = round(total_acumulado * 0.05, 2)  # exemplo: 5% de cashback

# --- BLOCO DO CARRINHO (PÁGINA NORMAL, SEM POPOVER) ---
st.header("🛒 Detalhes do Pedido")

if carrinho_vazio:
    st.info("Seu carrinho está vazio. Volte ao catálogo para adicionar produtos.")
else:
    desconto_cupom = st.session_state.get('desconto_cupom', 0.0)
    total_com_desconto = total_acumulado - desconto_cupom
    if total_com_desconto < 0:
        total_com_desconto = 0

    st.markdown(f"Subtotal: `R$ {total_acumulado:.2f}`")
    if desconto_cupom > 0:
        st.markdown(
            f"Desconto (`{st.session_state.cupom_aplicado}`): <span style='color: #D32F2F;'>- R$ {desconto_cupom:.2f}</span>",
            unsafe_allow_html=True
        )

    st.markdown(f"<span style='color: #2E7D32; font-weight: bold;'>Cashback a Ganhar: R$ {cashback_a_ganhar:.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #E91E63; margin-top: 0;'>Total: R$ {total_com_desconto:.2f}</h3>", unsafe_allow_html=True)
    st.markdown("---")

    col_h1, col_h2, col_h3, col_h4 = st.columns([3, 1.5, 2.5, 1])
    col_h2.markdown("**Qtd**")
    col_h3.markdown("**Subtotal**")
    col_h4.markdown("")
    st.markdown('<div style="margin-top: -10px; border-top: 1px solid #ccc;"></div>', unsafe_allow_html=True)

    for prod_id, item in list(st.session_state.carrinho.items()):
        c1, c2, c3, c4 = st.columns([3, 1.5, 2.5, 1])
        c1.write(f"*{item['nome']}*")

        max_qtd = int(df_catalogo_completo.loc[prod_id, 'QUANTIDADE']) if (df_catalogo_completo is not None and prod_id in df_catalogo_completo.index) else 999999

        if item['quantidade'] > max_qtd:
            st.session_state.carrinho[prod_id]['quantidade'] = max_qtd
            item['quantidade'] = max_qtd
            st.toast(f"Ajustado: {item['nome']} ao estoque máximo de {max_qtd}.", icon="⚠️")
            st.rerun()

        nova_quantidade = c2.number_input(label=f'Qtd_{prod_id}', min_value=1, max_value=max_qtd, value=item['quantidade'], step=1, key=f'qtd_{prod_id}_popover', label_visibility="collapsed")

        if nova_quantidade != item['quantidade']:
            st.session_state.carrinho[prod_id]['quantidade'] = nova_quantidade
            st.rerun()

        subtotal_item = item['preco'] * item['quantidade']
        preco_unitario = item['preco']
        c3.markdown(f"<div style='text-align: left; white-space: nowrap;'><strong>R$ {subtotal_item:.2f}</strong><br><span style='font-size: 0.8rem; color: #757575;'>(R$ {preco_unitario:.2f} un.)</span></div>", unsafe_allow_html=True)

        if c4.button("X", key=f'rem_{prod_id}_popover'):
            remover_do_carrinho(prod_id)
            st.rerun()

    st.markdown("---")
            st.subheader("🎟️ Cupom de Desconto")

            cupom_col1, cupom_col2 = st.columns([3, 1])
            codigo_cupom_input = cupom_col1.text_input("Código do Cupom", key="cupom_input", label_visibility="collapsed").upper()

            if cupom_col2.button("Aplicar", key="aplicar_cupom_btn", use_container_width=True):
                if codigo_cupom_input:
                    df_cupons_validos = carregar_cupons()
                    cupom_encontrado = df_cupons_validos[df_cupons_validos['NOME_CUPOM'] == codigo_cupom_input]
                    if not cupom_encontrado.empty:
                        cupom_info = cupom_encontrado.iloc[0]
                        valor_minimo = cupom_info['VALOR_MINIMO_PEDIDO']
                        if float(total_acumulado) >= float(valor_minimo):
                            tipo = cupom_info['TIPO_DESCONTO']
                            valor = cupom_info['VALOR_DESCONTO']
                            desconto = (valor / 100) * total_acumulado if tipo == 'PERCENTUAL' else valor
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

            st.subheader("Finalizar Pedido")
            nome_input = st.text_input("Seu Nome Completo:", key='checkout_nome_dynamic')
            contato_input = st.text_input("Seu Contato (WhatsApp - apenas números, com DDD):", key='checkout_contato_dynamic')

            nivel_cliente, saldo_cashback = 'N/A', 0.00

            if nome_input and contato_input and DF_CLIENTES_CASH is not None and not DF_CLIENTES_CASH.empty:
                existe, nome_encontrado, saldo_cashback, nivel_cliente = buscar_cliente_cashback(contato_input, DF_CLIENTES_CASH)

                if existe:
                    st.success(f"🎉 **Bem-vindo(a) de volta, {nome_encontrado}!** Nível: **{nivel_cliente.upper()}**. Saldo de Cashback: **R$ {saldo_cashback:.2f}**.")
                elif contato_input.strip():
                    st.info("👋 **Novo Cliente!** Você começará a acumular cashback após este pedido.")
            elif nome_input and contato_input:
                st.info("👋 **Novo Cliente!** Você começará a acumular cashback após este pedido.")

            with st.form("form_finalizar_pedido", clear_on_submit=True):
                st.text_input("Nome (Preenchido)", value=nome_input, disabled=True, label_visibility="collapsed")
                st.text_input("Contato (Preenchido)", value=contato_input, disabled=True, label_visibility="collapsed")
                if st.form_submit_button("✅ Enviar Pedido", type="primary", use_container_width=True):
                    if nome_input and contato_input:
                        contato_limpo = ''.join(filter(str.isdigit, contato_input))
                        detalhes = {
                            "subtotal": total_acumulado,
                            "desconto_cupom": st.session_state.desconto_cupom,
                            "cupom_aplicado": st.session_state.cupom_aplicado,
                            "total": total_com_desconto,
                            "itens": [
                                {"id": int(k), "nome": v['nome'], "preco": v['preco'], "quantidade": v['quantidade'], "imagem": v.get('imagem', '')}
                                for k, v in st.session_state.carrinho.items()
                            ],
                            "nome": nome_input,
                            "contato": contato_limpo,
                            "cliente_nivel_atual": nivel_cliente,
                            "cliente_saldo_cashback": saldo_cashback,
                            "cashback_a_ganhar": cashback_a_ganhar
                        }

                        sucesso, id_pedido = salvar_pedido(nome_input, contato_limpo, total_com_desconto, json.dumps(detalhes, ensure_ascii=False), detalhes)

                        if sucesso:
                            mensagem_optin = (
                                f"Olá! Acabei de fazer um pedido (ID: {id_pedido}) pelo catálogo da Doce&Bella. "
                                f"Confirmo meu Opt-in e desejo prosseguir com a compra. Meu nome é {nome_input}."
                            )
                            link_whats = f"https://wa.me/{NUMERO_WHATSAPP}?text={requests.utils.quote(mensagem_optin)}"

                            js_redirect = f"""
                            <script>
                            window.location.href = '{link_whats}';
                            </script>
                            """
                            st.markdown(js_redirect, unsafe_allow_html=True)

                            st.session_state.carrinho = {}
                            st.session_state.cupom_aplicado = None
                            st.session_state.desconto_cupom = 0.0
                            st.session_state.cupom_mensagem = ""
                        else:
                            st.error("❌ Erro ao salvar o pedido. Tente novamente.")
                    else:
                        st.warning("Preencha seu nome e contato.")
