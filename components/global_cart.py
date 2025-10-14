import streamlit as st
from ui_components import limpar_carrinho, remover_do_carrinho, calcular_cashback_total

def render_global_cart():
    """Carrinho global com ícone flutuante (sem criar colunas extras)."""

    # --- Segurança: evita erros se não houver carrinho ---
    if 'carrinho' not in st.session_state:
        st.session_state.carrinho = {}

    carrinho = st.session_state.carrinho
    num_itens = sum(item['quantidade'] for item in carrinho.values())
    total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    vazio = len(carrinho) == 0

    # --- CSS global ---
    st.markdown("""
    <style>
    /* Ícone flutuante */
    .cart-float {
        position: fixed;
        bottom: 110px;
        right: 40px;
        background-color: #D32F2F;
        color: white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        text-align: center;
        font-size: 28px;
        box-shadow: 2px 2px 5px #999;
        cursor: pointer;
        z-index: 2000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .cart-float-count {
        position: absolute;
        top: -5px;
        right: -5px;
        background-color: #FFD600;
        color: black;
        border-radius: 50%;
        width: 22px;
        height: 22px;
        font-size: 13px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid white;
    }

    /* Deixa o popover invisível */
    div[data-testid="stPopover"] > div:first-child > button {
        position: fixed !important;
        bottom: 110px !important;
        right: 40px !important;
        width: 60px !important;
        height: 60px !important;
        opacity: 0 !important;
        z-index: 1999 !important;
        pointer-events: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Popover invisível ---
    with st.container():
        with st.popover("Carrinho"):
            st.header("🛒 Carrinho de Compras")

            if vazio:
                st.info("Seu carrinho está vazio.")
                return

            desconto = st.session_state.get("desconto_cupom", 0.0)
            total_com_desconto = max(total - desconto, 0)
            cashback = calcular_cashback_total(carrinho, st.session_state.df_catalogo_indexado)

            st.markdown(f"Subtotal: **R$ {total:.2f}**")
            if desconto > 0:
                st.markdown(f"Desconto: -R$ {desconto:.2f}")
            st.markdown(f"💰 Cashback: R$ {cashback:.2f}")
            st.markdown(f"### Total: R$ {total_com_desconto:.2f}")
            st.markdown("---")

            for prod_id, item in list(carrinho.items()):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"{item['quantidade']}x {item['nome']}")
                c2.write(f"R$ {item['preco'] * item['quantidade']:.2f}")
                if c3.button("❌", key=f"rem_{prod_id}_global"):
                    remover_do_carrinho(prod_id)
                    st.rerun()

            if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                limpar_carrinho()
                st.rerun()

    # --- Ícone flutuante ---
    if num_itens > 0:
        st.markdown(f"""
        <div class="cart-float" id="floating_cart_btn" title="Abrir carrinho">
            🛒<span class="cart-float-count">{num_itens}</span>
        </div>

        <script>
        (function() {{
            const floatBtn = document.getElementById("floating_cart_btn");
            const findPopover = () => document.querySelector('div[data-testid="stPopover"] button');
            if (floatBtn) {{
                floatBtn.addEventListener("click", () => {{
                    const btn = findPopover();
                    if (btn) btn.click();
                }});
            }}
        }})();
        </script>
        """, unsafe_allow_html=True)
