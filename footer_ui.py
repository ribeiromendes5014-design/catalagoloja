# footer_ui.py

import streamlit as st
import requests
import re
import urllib.parse
# Importamos o NUMERO_WHATSAPP para o bloco de contato, caso ele seja usado.
from data_handler import NUMERO_WHATSAPP 

# Variáveis de Configuração do Novo Layout
COR_RODAPE = "#F28C9D" # Rosa claro/salmão (Ajustado com base na imagem)
COR_TEXTO = "white"
COR_LINK = "white" # Links brancos para contraste
NUMERO_EXIBIDO = "5511999999999" # Número fictício para exibição

def render_fixed_footer():
    """Renderiza o rodapé fixo no estilo e-commerce (3 colunas, rosa) com formulário de e-mail."""

    # --- HTML e CSS para o Rodapé Fixo ---
    
    st.markdown(
        f"""
        <style>
        /* Estilos do Rodapé Principal */
        .footer-container-full {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: {COR_RODAPE};
            color: {COR_TEXTO};
            padding-top: 30px; /* Mais espaço no topo */
            padding-bottom: 50px;
            z-index: 9990; 
            font-size: 14px;
        }}
        .footer-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr; /* 3 Colunas iguais */
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
        
        /* Estilos do Formulário */
        .email-input-container {{
            display: flex;
            gap: 5px;
            margin-top: 15px;
        }}
        /* Estilo para simular o input com fundo claro/rosa */
        .email-input-container input {{
            background-color: #F8B4C0 !important; /* Cor mais clara que o fundo */
            color: #333 !important;
            border: none;
            border-radius: 4px;
            padding: 8px;
            flex-grow: 1;
        }}
        /* Estilo para o botão "Enviar" */
        .email-input-container button {{
            background-color: #E91E63 !important; /* Rosa Escuro/Vermelho para o botão */
            color: white !important;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }}
        
        /* Rodapé Secundário (Bottom Bar) */
        .footer-bottom {{
            width: 100%;
            background-color: rgba(0, 0, 0, 0.1); /* Faixa mais escura no fundo */
            color: {COR_TEXTO};
            padding: 10px 40px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* Media Query para responsividade */
        @media (max-width: 768px) {{
            .footer-grid {{
                grid-template-columns: 1fr; /* 1 coluna em mobile */
                padding: 0 20px;
            }}
            .footer-container-full {{
                padding-bottom: 10px;
            }}
            .footer-bottom {{
                flex-direction: column;
                text-align: center;
            }}
        }}

        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # --- Estrutura do Rodapé (HTML e Injeção do Formulário) ---
    
    # Criamos um form Streamlit simples que irá forçar um rerun (newsletter simulada)
    with st.form(key="footer_newsletter_form", clear_on_submit=True):
        
        # O formulário Streamlit deve ser renderizado aqui, mas seu HTML
        # real com as colunas será injetado abaixo.
        
        # Campos visíveis no layout Streamlit (mas serão escondidos/re-estilizados pelo CSS)
        email_input = st.text_input("E-mail:", key="newsletter_email", label_visibility="collapsed", placeholder="E-mail")
        submit_newsletter = st.form_submit_button(label="Enviar", type="secondary")

        if submit_newsletter:
            if re.match(r"[^@]+@[^@]+\.[^@]+", email_input):
                st.success(f"Obrigado! E-mail '{email_input}' cadastrado (simulação).")
                # Aqui você faria a integração real da newsletter
            else:
                st.error("Insira um e-mail válido.")

    
    # Injeção do HTML principal do rodapé
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
                
                <div style="margin-top: 10px; width: 100%;">
                    </div>
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

# A função render_fixed_footer será chamada no catalogo_app.py
