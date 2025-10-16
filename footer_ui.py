# footer_ui.py

import streamlit as st
import requests
import re
import urllib.parse
# Importamos o NUMERO_WHATSAPP para o bloco de contato, caso ele seja usado.
from data_handler import NUMERO_WHATSAPP 

# cores / constantes
COR_RODAPE = "#F28C9D"
COR_TEXTO = "white"
COR_LINK = "white"
NUMERO_EXIBIDO = "5511999999999"

def render_fixed_footer():
    """Renderiza o rodapé. Versão corrigida: chama CSS em f-string com chaves dobradas."""
    st.markdown(
    f"""
    <style>
    /* Estilos do Rodapé Principal */
    .footer-container-full {{ /* <- chaves dobradas para f-string */
        position: relative;
        bottom: auto;
        left: auto;
        width: 100%;
        background-color: {COR_RODAPE};
        color: {COR_TEXTO};
        padding-top: 30px;
        padding-bottom: 30px;
        z-index: 9990;
        font-size: 14px;
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
        font-weight: normal;
    }}

    .footer-column a:hover {{
        text-decoration: underline;
    }}

    /* Formulário posicionado (mantive como relativo/absoluto opcional) */
    div[data-testid="stForm"] {{
        position: relative;
        /* Se preferir usar position:absolute, troque relative por absolute e ajuste top/right */
        width: 100%;
        max-width: 320px;
        z-index: 9999;
        padding: 0;
        margin: 0;
        background: none !important;
    }}

    div[data-testid="stForm"] > div > div:not([role="button"]) {{
        display: flex;
        flex-direction: row !important;
        gap: 5px;
        align-items: center;
    }}

    div[data-testid="stForm"] h4, div[data-testid="stForm"] label {{
        display: none !important;
    }}

    div[data-testid="stForm"] input {{
        background-color: #F8B4C0 !important;
        color: #333 !important;
        border: none;
        flex-grow: 1;
        padding: 8px;
        min-width: 150px;
    }}

    div[data-testid="stForm"] button {{
        background-color: #E91E63 !important;
        color: white !important;
        font-weight: bold;
        flex-grow: 0;
        padding: 8px 15px;
        min-width: 80px;
        border: none !important;
    }}

    .footer-bottom {{
        width: 100%;
        background-color: rgba(0, 0, 0, 0.05);
        color: {COR_TEXTO};
        padding: 10px 40px;
        margin-top: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    @media (max-width: 768px) {{
        div[data-testid="stForm"] {{
            position: relative;
            width: 90%;
            margin: 20px auto 0 auto;
        }}
        .footer-grid {{
            grid-template-columns: 1fr;
            padding: 0 20px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

    html_footer = f"""
    <div class="footer-container-full">
        <div class="footer-grid">
            <div class="footer-column">
                <p style="margin-top: 0;"><i class="fa fa-instagram"></i></p>
                <p>{NUMERO_EXIBIDO}</p>
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
                <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram</a>
            </div>

            <div class="footer-column">
                <h4>MARCAS</h4>
                <a href="#maquiagens">MAQUIAGENS</a>
                <a href="#acessorios">ACESSÓRIOS</a>
                <a href="#skincare">SKINCARE</a>
            </div>

            <div class="footer-column">
                <h4>Newsletter</h4>
                <p style="margin: 0;">Receba novidades e promoções!</p>
            </div>
        </div>

        <div class="footer-bottom">
            <div>Meios de pagamento <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;"></div>
            <div>
                criado por <span><img src="https://i.ibb.co/6R2b0S4/nuvemshop-logo.png" alt="Nuvemshop" style="height: 16px; vertical-align: middle;"></span> | Copyright WE MAKE - 2025. Todos os direitos reservados.
            </div>
        </div>
    </div>
    """
    st.markdown(html_footer, unsafe_allow_html=True)










