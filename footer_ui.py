# footer_ui.py

import streamlit as st
import textwrap

try:
    from data_handler import NUMERO_WHATSAPP
except ImportError:
    NUMERO_WHATSAPP = "5511999999999"

COR_RODAPE = "#F28C9D"
COR_TEXTO = "white"
COR_LINK = "white"

def render_fixed_footer():
    """Renderiza o rodapé final 100% em HTML para evitar conflitos de CSS."""

    # --- CÓDIGO FINAL E ISOLADO ---
    # Usamos Flexbox no CSS para criar as colunas, em vez do st.columns.
    # Isso impede que o CSS do app principal interfira no rodapé.
    
    footer_html_block = f"""
    <style>
        .footer-wrapper {{
            background-color: {COR_RODAPE};
            padding: 40px;
            margin-top: 60px;
            border-radius: 12px;
            color: {COR_TEXTO};
        }}
        .footer-content {{
            display: flex;
            flex-wrap: wrap;
            gap: 30px; /* Espaço entre as colunas */
        }}
        .footer-col-atendimento {{
            flex: 1; /* Ocupa 1 parte do espaço */
            min-width: 200px;
        }}
        .footer-col-newsletter {{
            flex: 2; /* Ocupa 2 partes do espaço, sendo maior */
            min-width: 300px;
        }}
        .footer-wrapper h4 {{
            font-weight: bold;
            color: {COR_TEXTO};
        }}
        .footer-wrapper a {{
            color: {COR_LINK};
            text-decoration: none;
            display: block;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }}
        .footer-wrapper a:hover {{ text-decoration: underline; }}
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
        /* Estilos para o formulário Streamlit DENTRO do nosso HTML */
        .footer-wrapper .stForm {{
            border: none;
            padding: 0;
        }}
        .footer-wrapper .stButton > button {{
            background-color: white;
            color: {COR_RODAPE};
            border: 2px solid white;
            font-weight: bold;
            width: 100%;
        }}
    </style>

    <div class="footer-wrapper">
        <div class="footer-content">
            <div class="footer-col-atendimento">
                <h4>ATENDIMENTO</h4>
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
                <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram</a>
            </div>
            <div class="footer-col-newsletter">
    """
    st.markdown(footer_html_block, unsafe_allow_html=True)
    
    # O formulário Streamlit é injetado aqui, no meio do HTML
    st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight: normal; color: white; margin-bottom: 1rem;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
    with st.form(key="footer_form_final_isolado", clear_on_submit=True):
        nome = st.text_input("Nome", key="footer_nome", label_visibility="collapsed", placeholder="Seu Nome")
        telefone = st.text_input("Telefone", key="footer_telefone", label_visibility="collapsed", placeholder="DDD + Número")
        submitted = st.form_submit_button("Enviar")
        if submitted and nome and telefone:
            st.success("Obrigado por se inscrever! 🎉")

    # O resto do HTML para fechar as divs
    footer_html_block_fim = """
            </div>
        </div>
        <div class="footer-bottom-inner">
            <div>
                Meios de pagamento
                <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
            </div>
            <div>
                Copyright Doce&Bella - 2025.
            </div>
        </div>
    </div>
    """
    st.markdown(footer_html_block_fim, unsafe_allow_html=True)
