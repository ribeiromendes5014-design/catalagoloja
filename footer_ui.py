# footer_ui.py

import streamlit as st
import requests
import re
import urllib.parse
# Importamos o NUMERO_WHATSAPP para o bloco de contato, caso ele seja usado.
from data_handler import NUMERO_WHATSAPP 

# Variáveis de Configuração do Novo Layout
COR_RODAPE = "#F28C9D"  # Rosa claro/salmão
COR_TEXTO = "white"
COR_LINK = "white"
NUMERO_EXIBIDO = "5511999999999"  # Exemplo


def render_fixed_footer():
    """Renderiza o rodapé fixo no estilo e-commerce (3 colunas, rosa)."""

    st.markdown(
        f"""
        <style>
        .footer-container-full {{
            position: relative; /* Fica no fim da página */
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
        """,
        unsafe_allow_html=True
    )

    # footer_ui.py (Dentro da variável html_footer)

# ⚠️ NÃO ALTERE A INDENTAÇÃO ABAIXO ⚠️
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
                </div>
        </div>

        <div class="footer-bottom">
            <div>
                Meios de pagamento 
                <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" 
                     style="height: 18px; vertical-align: middle; margin-left: 5px;">
            </div>
            <div>
                criado por 
                <span>
                    <img src="https://i.ibb.co/6R2b0S4/nuvemshop-logo.png" alt="Nuvemshop" 
                         style="height: 16px; vertical-align: middle;">
                </span> 
                | Copyright WE MAKE - 2025. Todos os direitos reservados.
            </div>
        </div>
    </div>
    """

    st.markdown(html_footer, unsafe_allow_html=True)














