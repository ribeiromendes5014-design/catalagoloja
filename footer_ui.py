# footer_ui.py

import streamlit as st
import textwrap

# Tenta importar a variável do arquivo de dados.
# Se falhar, usa um valor padrão para não quebrar o app.
try:
    from data_handler import NUMERO_WHATSAPP
except ImportError:
    NUMERO_WHATSAPP = "5511999999999" # Defina um número padrão aqui

# Variáveis de Configuração
COR_RODAPE = "#F28C9D" # Rosa
COR_TEXTO = "white"
COR_LINK = "white"

def render_fixed_footer():
    """Renderiza o rodapé final, integrado em um único bloco."""

    # --- CÓDIGO CORRIGIDO E MAIS ROBUSTO ---
    # Esta função interna vai limpar os espaços invisíveis (U+00A0)
    # e depois remover a indentação do bloco de texto.
    def clean_and_dedent(text_block):
        cleaned_text = text_block.replace('\u00A0', ' ')
        return textwrap.dedent(cleaned_text)

    # Bloco de texto do CSS
    css_style_block = f"""
        <style>
            /* O container principal que cria o fundo rosa grande */
            .footer-wrapper {{
                background-color: {COR_RODAPE};
                padding: 40px;
                margin-top: 60px;
                border-radius: 12px;
            }}
            /* Estilos gerais para os textos dentro do bloco rosa */
            .footer-wrapper h4, .footer-wrapper p, .footer-wrapper label {{
                color: {COR_TEXTO};
                font-weight: bold;
            }}
            .footer-wrapper a {{
                color: {COR_LINK};
                text-decoration: none;
                display: block;
                margin-bottom: 8px;
                font-size: 1.1rem;
            }}
            .footer-wrapper a:hover {{ text-decoration: underline; }}
            /* Estilo específico para o botão do formulário */
            .footer-wrapper .stButton > button {{
                background-color: white;
                color: {COR_RODAPE};
                border: 2px solid white;
                font-weight: bold;
                width: 100%;
            }}
            .footer-wrapper .stButton > button:hover {{
                background-color: #f0f0f0;
                color: {COR_RODAPE};
            }}
            /* A barra cinza de copyright, que fica DENTRO do bloco rosa */
            .footer-bottom-inner {{
                background-color: #333333;
                color: #dddddd;
                padding: 15px 20px;
                margin-top: 40px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                font-size: 13px;
                gap: 15px;
            }}
        </style>
    """
    st.markdown(clean_and_dedent(css_style_block), unsafe_allow_html=True)

    # --- INÍCIO DO LAYOUT ---
    with st.container():
        st.markdown('<div class="footer-wrapper">', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])
        
        with col1:
            atendimento_html = f"""
                <h4>ATENDIMENTO</h4>
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
                <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram</a>
            """
            st.markdown(clean_and_dedent(atendimento_html), unsafe_allow_html=True)

        with col2:
            st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight: normal; margin-bottom: 1rem;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
            
            with st.form(key="footer_form_final", clear_on_submit=True):
                nome = st.text_input("Nome", key="footer_nome", label_visibility="collapsed", placeholder="Seu Nome")
                telefone = st.text_input("Telefone", key="footer_telefone", label_visibility="collapsed", placeholder="DDD + Número")
                submitted = st.form_submit_button("Enviar")
                if submitted and nome and telefone:
                    st.success("Obrigado por se inscrever! 🎉")

        bottom_bar_html = """
            <div class="footer-bottom-inner">
                <div>
                    Meios de pagamento
                    <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
                </div>
                <div>
                    Copyright Doce&Bella - 2025.
                </div>
            </div>
        """
        st.markdown(clean_and_dedent(bottom_bar_html), unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
