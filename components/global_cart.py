# components/global_cart.py
import streamlit as st
from ui_components import limpar_carrinho, remover_do_carrinho, calcular_cashback_total

def render_global_cart():
    """
    Renderiza:
      1) um st.popover 'invisível' contendo TODO o conteúdo do carrinho (único lugar do app)
      2) um ícone flutuante visível (HTML/CSS) que aciona clique no botão invisível via JS
    Observação importante: NÃO execute esta função no próprio módulo (não chamar aqui).
    Apenas importe e chame render_global_cart() a partir do seu script principal (ex: catalogo_app.py).
    """

    # garante estados mínimos
    if 'carrinho' not in st.session_state:
        st.session_state.carrinho = {}
    carrinho = st.session_state.carrinho
    num_itens = sum(int(item.get('quantidade', 0)) for item in carrinho.values())
    total = sum(float(item.get('preco', 0.0)) * int(item.get('quantidade', 0)) for item in carrinho.values())
    vazio = len(carrinho) == 0

    # CSS: ícone visível + torna o botão interno do popover invisível MAS clicável
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
        z-index: 99999 !important;
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

    # --- Popover: único local onde definimos TODO o conteúdo do carrinho ---
    # Atenção: não tenha outro st.popover em outros arquivos (procure e remova).
    with st.container():
        with st.popover("Conteúdo do Carrinho"):
            st.header("🛒 Detalhes do Pedido")
            if vazio:
                st.info("Seu carrinho está vazio.")
            else:
                desconto = float(st.session_state.get("desconto_cupom", 0.0) or 0.0)
                total_com_desconto = max(total - desconto, 0.0)
                # usa o df indexado se existir (safe-get)
                df_index = st.session_state.get('df_catalogo_indexado', {})
                cashback = calcular_cashback_total(carrinho, df_index)

                st.markdown(f"Subtotal: **R$ {total:.2f}**")
                if desconto > 0:
                    st.markdown(f"Desconto: -R$ {desconto:.2f}")
                st.markdown(f"💰 Cashback: R$ {cashback:.2f}")
                st.markdown(f"### Total: R$ {total_com_desconto:.2f}")
                st.markdown("---")

                # lista itens (simples)
                for prod_id, item in list(carrinho.items()):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"{item.get('quantidade', 0)}x {item.get('nome', 'Produto')}")
                    c2.write(f"R$ {float(item.get('preco', 0.0)) * int(item.get('quantidade', 0)):.2f}")
                    if c3.button("❌", key=f"rem_{prod_id}_popover"):
                        remover_do_carrinho(prod_id)
                        st.rerun()

                st.markdown("---")
                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    limpar_carrinho()
                    st.rerun()

    # --- Ícone flutuante visível (somente se tiver itens) ---
    if num_itens > 0:
        st.markdown(f"""
        <div class="cart-float" id="floating_cart_btn" title="Abrir carrinho">
            🛒<span class="cart-float-count">{num_itens}</span>
        </div>

        <script>
        (function() {{
            const waitAndClick = () => {{
                // tenta encontrar os botões do popover (tempo de render varia)
                const buttons = document.querySelectorAll('div[data-testid="stPopover"] button');
                if (buttons && buttons.length) {{
                    buttons[0].click(); // clica no primeiro (único) botão do popover
                    return true;
                }}
                return false;
            }};

            const floatBtn = document.getElementById("floating_cart_btn");
            if (!floatBtn) return;

            floatBtn.addEventListener("click", function() {{
                // tentativa imediata
                if (waitAndClick()) return;

                // observar mudanças no DOM
                const obs = new MutationObserver((mutations, observer) => {{
                    if (waitAndClick()) {{
                        observer.disconnect();
                    }}
                }});
                obs.observe(document.body, {{ childList: true, subtree: true }});

                // fallback: tentativas periódicas por 3s
                let attempts = 0;
                const interval = setInterval(() => {{
                    attempts++;
                    if (waitAndClick() || attempts > 15) {{
                        clearInterval(interval);
                        try {{ obs.disconnect(); }} catch(e){{}}
                    }}
                }}, 200);
            }});
        }})();
        </script>
        """, unsafe_allow_html=True)
