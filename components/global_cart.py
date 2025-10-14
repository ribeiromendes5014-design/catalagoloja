import streamlit as st
from ui_components import limpar_carrinho, remover_do_carrinho, calcular_cashback_total
from data_handler import NUMERO_WHATSAPP

def render_global_cart():
    """Renderiza o ícone flutuante do carrinho e o popover invisível (global)."""

    num_itens = sum(item['quantidade'] for item in st.session_state.carrinho.values())
    total = sum(item['preco'] * item['quantidade'] for item in st.session_state.carrinho.values())
    carrinho_vazio = not st.session_state.carrinho

    # ==========================================================
    # 1️⃣ POPUP INVISÍVEL — precisa existir mas sem aparecer
    # ==========================================================
    with st.container():
        st.markdown(
            """
            <style>
            div[data-testid="stPopover"] > div:first-child > button {
                position: fixed !important;
                bottom: 110px !important;
                right: 40px !important;
                width: 60px !important;
                height: 60px !important;
                opacity: 0 !important; /* invisível */
                pointer-events: auto !important;
                z-index: 1001 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        with st.popover("Conteúdo do Carrinho"):
            st.header("🛒 Detalhes do Pedido")

            if carrinho_vazio:
                st.info("Seu carrinho está vazio.")
                return

            desconto = st.session_state.get('desconto_cupom', 0.0)
            total_com_desconto = total - desconto
            cashback = calcular_cashback_total(st.session_state.carrinho, st.session_state.df_catalogo_indexado)

            st.markdown(f"Subtotal: **R$ {total:.2f}**")
            if desconto > 0:
                st.markdown(f"Desconto: -R$ {desconto:.2f}")
            st.markdown(f"💰 Cashback: R$ {cashback:.2f}")
            st.markdown(f"### Total: R$ {total_com_desconto:.2f}")
            st.markdown("---")

            for prod_id, item in list(st.session_state.carrinho.items()):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"{item['quantidade']}x {item['nome']}")
                c2.write(f"R$ {item['preco'] * item['quantidade']:.2f}")
                if c3.button("❌", key=f"rem_{prod_id}_popover"):
                    remover_do_carrinho(prod_id)
                    st.rerun()

            st.markdown("---")
            if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                limpar_carrinho()
                st.rerun()

    # ==========================================================
    # 2️⃣ BOTÃO FLUTUANTE VISÍVEL
    # ==========================================================
    if num_itens > 0:
        st.markdown(f"""
        <div class="cart-float" id="floating_cart_btn" title="Ver Carrinho">
            🛒<span class="cart-float-count">{num_itens}</span>
        </div>

        <script>
        (function() {{
            const waitForPopoverButton = () => {{
                return document.querySelector('div[data-testid="stPopover"] button');
            }};
            const floatBtn = document.getElementById("floating_cart_btn");
            if (floatBtn) {{
                floatBtn.addEventListener("click", function() {{
                    const popBtn = waitForPopoverButton();
                    if (popBtn) popBtn.click();
                }});
            }}
        }})();
        </script>
        """, unsafe_allow_html=True)
