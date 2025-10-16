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
    .footer-container-full {
    position: relative;   /* <-- era fixed */
    bottom: auto;
    left: auto;
    width: 100%;
}

    .footer-grid {{ /* <-- Corrigido */
        display: grid;
        grid-template-columns: 1fr 1fr 1fr; /* 3 Colunas iguais */
        gap: 20px;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 40px;
    }} /* <-- Corrigido */
    .footer-column h4, .footer-column p {{ /* <-- Corrigido */
        font-weight: bold;
        margin-bottom: 15px;
        color: {COR_TEXTO};
    }} /* <-- Corrigido */
    .footer-column a {{ /* <-- Corrigido */
        color: {COR_LINK};
        text-decoration: none;
        display: block;
        margin-bottom: 8px;
        font-weight: normal;
    }} /* <-- Corrigido */
    .footer-column a:hover {{ /* <-- Corrigido */
        text-decoration: underline;
    }} /* <-- Corrigido */
    
    /* ---------------------------------------------------- */
/* CSS PARA POSICIONAMENTO E ESTILIZAÇÃO DO FORMULÁRIO */
/* ---------------------------------------------------- */

/* 1. POSICIONAMENTO ABSOLUTO DO CONTAINER DO FORMULÁRIO */
/* Seleciona o container geral do form */
div[data-testid="stForm"] {{ 
    position: absolute; 
    top: 600px; /* <--- Mantenha ou ajuste este valor conforme a necessidade visual */
    right: 40px; 
    width: 300px;
    z-index: 9999;
    padding: 0;
    margin: 0;
    /* CORREÇÃO 1: Garante que o fundo do container do formulário seja transparente */
    background: none !important; 
}}

/* 2. ESTILO DOS INPUTS E BOTÕES */

/* Seleciona o contêiner interno que envolve o input e o botão */
div[data-testid="stForm"] > div > div:not([role="button"]) {{
    /* CORREÇÃO 2: Força o layout horizontal (Input e Botão) */
    display: flex; 
    flex-direction: row !important;
    gap: 5px;
    align-items: center;
}}

/* Oculta o título e labels do formulário Streamlit */
div[data-testid="stForm"] h4, div[data-testid="stForm"] label {{
    display: none !important;
}}

/* Estiliza o campo E-mail */
div[data-testid="stForm"] input {{
    background-color: #F8B4C0 !important; /* Fundo rosa claro */
    color: #333 !important; /* Texto escuro legível */
    border: none;
    flex-grow: 1; 
    padding: 8px;
    min-width: 150px;
}}

/* Estilo específico para o botão ENVIAR */
div[data-testid="stForm"] button {{
    background-color: #E91E63 !important; /* Rosa Escuro/Vermelho */
    color: white !important;
    font-weight: bold;
    flex-grow: 0; 
    padding: 8px 15px;
    min-width: 80px;
    /* CORREÇÃO 3: Garante que o botão use a cor certa */
    border: none !important; 
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









