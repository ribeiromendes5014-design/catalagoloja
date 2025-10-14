# components/global_cart.py
import streamlit as st
from ui_components import limpar_carrinho, remover_do_carrinho, calcular_cashback_total
from data_handler import carregar_cupons, NUMERO_WHATSAPP

def render_global_cart():
    """Desenha o ícone flutuante do carrinho e o popover de conteúdo — disponível em qualquer página."""
    num_itens = sum(item['quantidade'] for item in st.session_state.carrinho.values())
    total = sum(item['preco'] * item['quantidade'] for item in st.session_state.carrinho.values())
    carrinho_vazio = not st.session_state.carrinho

    # --- Botão Flutuante ---
    if num_itens > 0:
        st.markdown(f"""
        <div class="cart-float" id="floating_cart_btn" title="Ver seu pedido" role="button" aria-label="Abrir carrinho">
            🛒
            <span class="cart-float-count">{num_itens}</span>
        </div>
        <script>
        (function() {{
            const waitForPopoverButton = () => {{
                return document.querySelector('div[data-testid="stPopover"] button');
            }};
            const btn = document.getElementById("floating_cart_btn");
            if (btn) {{
                btn.addEventListener("click", () => {{
                    const popBtn = waitForPopoverButton();
                    if (popBtn) popBtn.click();
                }});
            }}
        }})();
        </script>
        """, unsafe_allow_html=True)

    # --- Conteúdo do Carrinho ---
    with st.popover("Conteúdo do Carrinho"):
        st.header("🛒 Seu Pedido")
        if carrinho_vazio:
            st.info("Carrinho vazio.")
            return

        desconto_cupom = st.session_state.get('desconto_cupom', 0.0)
        total_com_desconto = total - desconto_cupom
        cashback = calcular_cashback_total(st.session_state.carrinho, st.session_state.df_catalogo_indexado)

        st.markdown(f"Subtotal: R$ {total:.2f}")
        if desconto_cupom > 0:
            st.markdown(f"Desconto: -R$ {desconto_cupom:.2f}")
        st.markdown(f"**Total: R$ {total_com_desconto:.2f}**")
        st.markdown(f"💰 Cashback: R$ {cashback:.2f}")
        st.markdown("---")

        for prod_id, item in list(st.session_state.carrinho.items()):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"{item['quantidade']}x {item['nome']}")
            c2.write(f"R$ {item['preco'] * item['quantidade']:.2f}")
            if c3.button("❌", key=f"rem_{prod_id}_global"):
                remover_do_carrinho(prod_id)
                st.rerun()

        st.markdown("---")
        if st.button("🗑️ Limpar Carrinho", use_container_width=True):
            limpar_carrinho()
            st.rerun()
