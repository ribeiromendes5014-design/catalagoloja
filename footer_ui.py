# footer_ui.py

import streamlit as st
import requests
import pandas as pd
import time
import re
import urllib.parse
from data_handler import NUMERO_WHATSAPP, carregar_clientes_cashback # Assumindo que essas variáveis são úteis

# Variáveis de Configuração do Footer (Ajuste conforme suas necessidades)
COR_RODAPE = "#E91E63" # Rosa vibrante
COR_TEXTO = "white"
COR_LINK = "#FFD600" # Amarelo para destaque


def render_fixed_footer():
    """Renderiza um rodapé fixo com links, redes sociais e formulário de cadastro no WhatsApp."""

    # --- LÓGICA DE CADASTRO DO FORMULÁRIO ---
    
    # Este formulário é processado ao clicar, o que força um rerun para salvar.
    
    # É necessário um truque: Streamlit não tem submissão de formulário puro que NÃO chame rerun.
    # Vamos usar st.session_state para um formulário simples.
    
    with st.container():
        # Este container simula o layout do rodapé antes da injeção do CSS
        
        # Formulário de Cadastro (Simples, para evitar a complexidade do JS)
        with st.form(key="footer_cadastro_form", clear_on_submit=False):
            st.markdown(f'<h4 style="color:{COR_LINK};">Receba nossas promoções!</h4>', unsafe_allow_html=True)
            
            nome_cadastro = st.text_input("Seu Nome:", key="nome_cadastro_footer", label_visibility="collapsed", placeholder="Seu Nome Completo")
            contato_cadastro = st.text_input("WhatsApp (DDD+números):", key="contato_cadastro_footer", label_visibility="collapsed", placeholder="Ex: 5541987876191")
            
            submit_button = st.form_submit_button(label="Quero Receber Promoções", type="primary", use_container_width=True)

            if submit_button:
                if nome_cadastro and contato_cadastro:
                    contato_limpo = re.sub(r'\D', '', contato_cadastro)
                    
                    if len(contato_limpo) < 11:
                        st.error("Por favor, insira um número de WhatsApp válido (com DDD).")
                    else:
                        # 1. Logica de Processamento (Salvar o Opt-in)
                        # NOTA: O Streamlit não tem um backend direto. Aqui, você faria a integração
                        # com um Google Sheet, Planilha ou endpoint API para salvar o contato.
                        # Para esta simulação, vamos apenas construir a mensagem.
                        
                        mensagem_optin = (
                            f"Olá, Doce&Bella! Meu nome é {nome_cadastro} e confirmo meu Opt-in. "
                            "Quero receber as promoções exclusivas e novidades!"
                        )
                        
                        # 2. Redirecionar para o WhatsApp
                        link_whats_final = f"https://wa.me/{contato_limpo}?text={urllib.parse.quote(mensagem_optin)}"
                        
                        # Truque Streamlit para abrir link: usa markdown + HTML
                        st.markdown(
                            f'<a href="{link_whats_final}" target="_blank">'
                            f'<button style="background-color: #25D366; color: white; border-radius: 5px; padding: 10px 20px; font-weight: bold; cursor: pointer;">'
                            f'✅ CLIQUE PARA ABRIR O WHATSAPP E CONFIRMAR'
                            f'</button></a>',
                            unsafe_allow_html=True
                        )
                        st.success("Clique no botão verde acima para confirmar seu Opt-in no WhatsApp!")
                else:
                    st.warning("Preencha seu nome e contato para se cadastrar.")

        
    # --- HTML e CSS para o Rodapé Fixo (Design) ---
    
    # CSS que torna o rodapé fixo e responsivo
    st.markdown(
        f"""
        <style>
        .footer-container {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: {COR_RODAPE};
            color: {COR_TEXTO};
            padding: 20px 40px;
            box-shadow: 0 -4px 10px rgba(0, 0, 0, 0.3);
            z-index: 9990; /* Abaixo dos botões flutuantes, mas acima do conteúdo */
        }}
        .footer-content {{
            display: flex;
            justify-content: space-between;
            max-width: 1200px;
            margin: 0 auto;
            flex-wrap: wrap; /* Permite quebras em telas pequenas */
        }}
        .footer-column {{
            flex: 1;
            min-width: 200px; /* Garante que a coluna não fique muito estreita */
            padding: 10px;
        }}
        .footer-column a {{
            color: {COR_LINK};
            text-decoration: none;
            display: block;
            margin-bottom: 5px;
        }}
        .footer-column a:hover {{
            text-decoration: underline;
        }}
        .footer-column h4 {{
            border-bottom: 2px solid {COR_LINK};
            padding-bottom: 5px;
            margin-bottom: 10px;
            color: {COR_TEXTO};
        }}
        
        /* Oculta os widgets Streamlit nativos e usa nosso HTML/Markdown */
        div[data-testid="stForm"] {{
             background: none;
             padding: 0;
             margin: 0;
        }}
        
        /* Media Query para responsividade em telas muito pequenas */
        @media (max-width: 768px) {{
            .footer-content {{
                flex-direction: column;
            }}
            .footer-container {{
                padding: 10px 20px;
            }}
        }}

        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # Estrutura do Rodapé (HTML)
    html_footer = f"""
    <div class="footer-container">
        <div class="footer-content">
            
            <div class="footer-column">
                <h4>CATEGORIAS</h4>
                <a href="#catalogo">Maquiagem</a>
                <a href="#catalogo">Cabelo</a>
                <a href="#catalogo">Skincare</a>
                <a href="#catalogo">Lançamentos</a>
            </div>

            <div class="footer-column">
                <h4>PAGAMENTO E ENTREGA</h4>
                <a href="#contato">Formas de Pagamento</a>
                <a href="#contato">Política de Frete</a>
                <a href="#contato">Política de Troca</a>
            </div>

            <div class="footer-column">
                <h4>REDES E CONTATO</h4>
                <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram (@doce_bella)</a>
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">Fale Conosco (WhatsApp)</a>
                <a href="#sobre">Sobre a Loja</a>
            </div>

            <div class="footer-column">
                <h4>Fique por dentro!</h4>
                <p style="font-size: 0.9rem; margin-top: 5px; color: {COR_TEXTO};">Cadastre seu nome e WhatsApp para receber as melhores promoções!</p>
                </div>

        </div>
    </div>
    """
    
    # st.markdown(html_footer, unsafe_allow_html=True) # Descomente se for testar o HTML Puro.

# A função render_fixed_footer será chamada no catalogo_app.py