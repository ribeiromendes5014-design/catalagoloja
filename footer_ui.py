# footer_ui.py

import streamlit as st
import textwrap
import urllib.parse

# Se o arquivo data_handler.py existir, este import funciona.
# Caso contrário, defina as variáveis manualmente.
try:
    from data_handler import NUMERO_WHATSAPP
except ImportError:
    NUMERO_WHATSAPP = "5511999999999" # Coloque seu número aqui

# Variáveis de Configuração do Layout
COR_RODAPE = "#F28C9D"  # Rosa claro/salmão
COR_TEXTO = "white"
COR_LINK = "white"
NUMERO_EXIBIDO = "55 11 99999-9999"  # Exemplo formatado

def render_fixed_footer():
    """Renderiza o rodapé fixo no estilo e-commerce (3 colunas, rosa)."""

    css_style = textwrap.dedent(f"""
        <style>
        .footer-container-full {{
            position: relative;
            width: 100%;
            background-color: {COR_RODAPE};
            color: {COR_TEXTO};
            padding-top: 30px;
            padding-bottom: 30px;
            font-size: 14px;
            margin-top: 50px;
        }}
        .footer-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 40px;
        }}
        .footer-column h4, .footer-column p {{
            font-weight: bold;
            margin-bottom: 15px;
            color: {COR_TEXTO};
        }}
        .footer-column a {{
            color: {COR_LINK};
            text-decoration: none;
            display: block;
            margin-bottom: 8px;
        }}
        .footer-column a:hover {{
            text-decoration: underline;
        }}
        .footer-bottom {{
            width: 100%;
            background-color: rgba(0,0,0,0.05);
            color: {COR_TEXTO};
            padding: 10px 40px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            font-size: 13px;
        }}
        @media (max-width: 768px) {{
            .footer-grid {{
                grid-template-columns: 1fr;
                padding: 0 20px;
            }}
            .footer-bottom {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
        }}
        </style>
    """)
    st.markdown(css_style, unsafe_allow_html=True)

    html_footer = f"""
    <div class="footer-container-full">
        <div class="footer-grid">
            <div class="footer-column">
                <h4>ATENDIMENTO</h4>
                <p>{NUMERO_EXIBIDO}</p>
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
                <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram</a>
            </div>
            <div class="footer-column">
                <h4>MARCAS</h4>
                <a href="#">MAQUIAGENS</a>
                <a href="#">ACESSÓRIOS</a>
                <a href="#">SKINCARE</a>
            </div>
            <div class="footer-column">
                <h4>INSTITUCIONAL</h4>
                <a href="#">Sobre Nós</a>
                <a href="#">Políticas de Privacidade</a>
            </div>
        </div>
        <div class="footer-bottom">
            <div>
                Meios de pagamento
                <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
            </div>
            <div>
                criado por
                <span>
                    <img src="https://i.ibb.co/6R2b0S4/nuvemshop-logo.png" alt="Nuvemshop" style="height: 16px; vertical-align: middle;">
                </span>
                | Copyright WE MAKE - 2025.
            </div>
        </div>
    </div>
    """

    # A correção principal: remover a indentação do bloco de texto
    st.markdown(textwrap.dedent(html_footer), unsafe_allow_html=True)
