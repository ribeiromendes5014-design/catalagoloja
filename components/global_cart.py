# components/global_cart.py
import streamlit as st
from ui_components import calcular_cashback_total

def render_global_cart():
    if 'carrinho' not in st.session_state:
        st.session_state.carrinho = {}

    carrinho = st.session_state.carrinho
    num_itens = sum(item['quantidade'] for item in carrinho.values())

    # --- CSS para o botão flutuante ---
    st.markdown("""
    <style>
    .cart-float {
        position: fixed;
        bottom: 110px;
        right: 40px;
        background-color: #D32F2F;
        color: white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        cursor: pointer;
        z-index: 9999;
    }
    .cart-float-count {
        position: absolute;
        top: -6px;
        right: -6px;
        background: #FFD600;
        color: black;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        font-size: 12px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid white;
    }

    /* botão interno invisível (popover real) */
    div[data-testid="stPopover"] > div:first-child > button {
        position: fixed !important;
        bottom: 110px !important;
        right: 40px !important;
        width: 60px !important;
        height: 60px !important;
        opacity: 0 !important;
        pointer-events: auto !important;
        z-index: 1998 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Popover (vazio, apenas para click funcionar) ---
    with st.popover("Carrinho"):
        if num_itens == 0:
            st.info("Seu carrinho está vazio.")
        else:
            total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
            cashback = calcular_cashback_total(carrinho, st.session_state.get('df_catalogo_indexado', {}))
            st.markdown(f"🛍️ **{num_itens} item(ns)** no carrinho.")
            st.markdown(f"💰 **Total:** R$ {total:.2f}")
            st.markdown(f"🎁 **Cashback estimado:** R$ {cashback:.2f}")
            st.page_link("pages/carrinho.py", label="🧾 Ver detalhes do carrinho", icon="🛒")

    # --- Ícone flutuante visível ---
    if num_itens > 0:
        st.markdown(f"""
        <div class="cart-float" id="floating_cart_btn" title="Abrir carrinho">
            🛒<span class="cart-float-count">{num_itens}</span>
        </div>

        <script>
        (function() {{
            const floatBtn = document.getElementById("floating_cart_btn");
            if (!floatBtn) return;

            function clickPopover() {{
                const btns = document.querySelectorAll('div[data-testid="stPopover"] button');
                if (btns && btns.length) {{
                    btns[0].click();
                    return true;
                }}
                return false;
            }}

            floatBtn.addEventListener("click", function() {{
                if (clickPopover()) return;

                const obs = new MutationObserver(() => {{
                    if (clickPopover()) obs.disconnect();
                }});
                obs.observe(document.body, {{ childList: true, subtree: true }});
            }});
        }})();
        </script>
        """, unsafe_allow_html=True)
