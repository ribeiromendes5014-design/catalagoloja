# components/global_cart.py
import streamlit as st
from ui_components import limpar_carrinho, remover_do_carrinho, calcular_cashback_total

def render_global_cart():
    if 'carrinho' not in st.session_state:
        st.session_state.carrinho = {}

    carrinho = st.session_state.carrinho
    num_itens = sum(item['quantidade'] for item in carrinho.values())
    total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    vazio = len(carrinho) == 0

    # CSS — ícone visível, botão do popover invisível e sem ocupar espaço
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
        text-align: center;
        font-size: 28px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        cursor: pointer;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
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

    /* Deixa o botão interno do popover invisível e sem layout (mantém no DOM) */
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

    # --- Popover (único lugar onde definimos o conteúdo do carrinho) ---
    # Atenção: se você deixou outro st.popover em outro arquivo, apague-o.
    with st.container():
        with st.popover("Carrinho"):
            st.header("🛒 Carrinho")
            if vazio:
                st.info("Seu carrinho está vazio.")
            else:
                desconto = st.session_state.get("desconto_cupom", 0.0)
                total_com_desconto = max(total - desconto, 0)
                cashback = calcular_cashback_total(carrinho, st.session_state.get('df_catalogo_indexado', {}))

                st.markdown(f"Subtotal: **R$ {total:.2f}**")
                if desconto > 0:
                    st.markdown(f"Desconto: -R$ {desconto:.2f}")
                st.markdown(f"💰 Cashback: R$ {cashback:.2f}")
                st.markdown(f"### Total: R$ {total_com_desconto:.2f}")
                st.markdown("---")

                for prod_id, item in list(carrinho.items()):
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"{item['quantidade']}x {item['nome']}")
                    c2.write(f"R$ {item['preco'] * item['quantidade']:.2f}")
                    if c3.button("❌", key=f"rem_{prod_id}_popover"):
                        remover_do_carrinho(prod_id)
                        st.rerun()

                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    limpar_carrinho()
                    st.rerun()

    # --- Ícone flutuante visível ---
    if num_itens > 0:
        st.markdown(f"""
        <div class="cart-float" id="floating_cart_btn" title="Abrir carrinho">
            🛒<span class="cart-float-count">{num_itens}</span>
        </div>

        <script>
        (function() {{
            const waitAndClick = () => {{
                // tenta encontrar todos os botões dentro do popover e clicar no primeiro existente
                const buttons = document.querySelectorAll('div[data-testid="stPopover"] button');
                if (buttons && buttons.length) {{
                    buttons[0].click();
                    return true;
                }}
                return false;
            }};

            const floatBtn = document.getElementById("floating_cart_btn");
            if (!floatBtn) return;

            floatBtn.addEventListener("click", function() {{
                // 1) tenta clicar imediatamente
                if (waitAndClick()) return;

                // 2) usa MutationObserver para esperar o popover/button aparecer
                const obs = new MutationObserver((mutations, observer) => {{
                    if (waitAndClick()) {{
                        observer.disconnect();
                    }}
                }});
                obs.observe(document.body, {{ childList: true, subtree: true }});

                // 3) fallback: tenta por até 3s a cada 200ms
                let attempts = 0;
                const interval = setInterval(() => {{
                    attempts++;
                    if (waitAndClick() || attempts > 15) {{
                        clearInterval(interval);
                        obs.disconnect();
                    }}
                }}, 200);
            }});
        }})();
        </script>
        """, unsafe_allow_html=True)
