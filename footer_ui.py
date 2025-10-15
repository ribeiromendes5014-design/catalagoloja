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
            padding-top: 30px; 
            padding-bottom: 50px;
            z-index: 9990; 
            font-size: 14px;
        }}
        
        /* ADICIONA ESPAÇAMENTO NA PARTE INFERIOR DO CORPO DO SITE */
        .stApp > header, .stApp > div:last-child {{
            margin-bottom: 250px !important; /* Ajuste este valor se o rodapé for muito alto */
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
        
        /* ---------------------------------------------------- */
        /* CSS PARA POSICIONAMENTO E ESTILIZAÇÃO DO FORMULÁRIO */
        /* ---------------------------------------------------- */

        /* 1. POSICIONAMENTO ABSOLUTO DO CONTAINER DO FORMULÁRIO */
        /* Seleciona o container geral do form */
        div[data-testid="stForm"] {
            /* Força a saída do fluxo normal e o alinhamento */
            position: absolute; 
            
            /* COORDENADAS AJUSTADAS para posicionar o form sobre a Coluna 3 */
            top: 60px;             /* Ajusta para ficar alinhado com o 'Newsletter' */
            right: 40px;           /* Alinha com a borda direita do rodapé */
            
            width: 300px;          /* Largura da Coluna 3 */
            z-index: 9999;
            padding: 0;
            margin: 0;
            background-color: transparent; 
       }}
        
        /* 2. ESTILO DOS INPUTS E BOTÕES */
        /* Torna os campos internos e o botão alinhados horizontalmente (Newsletter style) */
        div[data-testid="stForm"] > div > div:not([role="button"]) { 
            display: flex;
            gap: 5px;
            align-items: center;
        }}

        /* Oculta o título e labels (apenas queremos o input e o botão) */
        div[data-testid="stForm"] h4, div[data-testid="stForm"] label {
            display: none !important;
        }}
        
        /* Estiliza o campo E-mail */
        div[data-testid="stForm"] input {
            background-color: #F8B4C0 !important;
            color: #333 !important;
            border: none;
            flex-grow: 1; 
            padding: 8px;
            min-width: 150px;
       }}

        /* Estilo para o botão ENVIAR */
        div[data-testid="stForm"] button {
            background-color: #E91E63 !important;
            color: white !important;
            font-weight: bold;
            flex-grow: 0; 
            padding: 8px 15px;
            min-width: 80px;
        }}
        
        /* Rodapé Secundário (Bottom Bar) */
        .footer-bottom {{
            width: 100%;
            background-color: rgba(0, 0, 0, 0.1); 
            color: {COR_TEXTO};
            padding: 10px 40px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* Media Query para responsividade */
        @media (max-width: 768px) {{
            /* ... (Seções de media query) ... */

            /* Ajuste o formulário para o centro no mobile */
            div[data-testid="stForm"] {{
                position: relative; /* Volta para o fluxo normal no mobile */
                width: 90%;
                margin: 20px auto 0 auto;
                top: auto;
                right: auto;
            }}
        }}

        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # --- Estrutura do Rodapé (HTML e Injeção do Formulário) ---
    
    # 1. O Form Streamlit é renderizado AQUI e movido via CSS
    with st.form(key="footer_newsletter_form", clear_on_submit=True):
        
        # Campos de entrada
        # Usamos st.columns para alinhar Input e Botão horizontalmente, se o CSS falhar,
        # MAS neste caso, confiamos no CSS do stForm para o layout horizontal.
        # Mantemos o input e o botão simples:
        email_input = st.text_input("E-mail:", key="newsletter_email", label_visibility="collapsed", placeholder="E-mail")
        submit_newsletter = st.form_submit_button(label="Enviar", type="secondary")

        if submit_newsletter:
            if re.match(r"[^@]+@[^@]+\.[^@]+", email_input):
                st.success(f"Obrigado! E-mail '{email_input}' cadastrado (simulação).")
            else:
                st.error("Insira um e-mail válido.")

    
    # 2. Injeção do HTML principal (que é fixo)
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

