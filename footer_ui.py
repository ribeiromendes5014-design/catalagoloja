# footer_ui.py

import streamlit as st
import textwrap
import requests
import base64
from datetime import datetime
import os

try:
    from data_handler import NUMERO_WHATSAPP
except ImportError:
    NUMERO_WHATSAPP = "5511999999999"

# --- Variáveis de Estilo ---
COR_RODAPE = "#F28C9D"
COR_TEXTO = "white"

# --- URLs dos Ícones PNG ---
INSTAGRAM_ICON_URL = "https://static.vecteezy.com/system/resources/previews/018/930/415/non_2x/instagram-logo-instagram-icon-transparent-free-png.png"
WHATSAPP_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/2044px-WhatsApp.svg.png"

# --- FUNÇÃO: Salvar CSV no GitHub ---
def save_csv_github(nome, telefone):
    # (Esta função permanece a mesma)
    try:
        token = st.secrets["github"]["token"]
        owner = st.secrets["github"]["owner"]
        repo = st.secrets["github"]["repo"]
        path = st.secrets["github"]["file_path"]
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}"}
        response = requests.get(url, headers=headers)
        sha = None
        current_content = ""
        if response.status_code == 200:
            data = response.json()
            sha = data['sha']
            content_encoded = data['content']
            current_content = base64.b64decode(content_encoded).decode('utf-8')
        elif response.status_code != 404:
            raise Exception(f"Erro ao buscar arquivo: {response.status_code} - {response.text}")
        new_line = f"{nome},{telefone}"
        if not current_content:
            new_content = f"Nome,Telefone\n{new_line}"
        else:
            new_content = f"{current_content}\n{new_line}"
        content_encoded = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
        commit_message = f"Inscrição de novo lead: {nome}"
        payload = {"message": commit_message, "content": content_encoded}
        if sha:
            payload["sha"] = sha
        response_put = requests.put(url, headers=headers, json=payload)
        if response_put.status_code in [200, 201]:
            return True, None
        else:
            return False, f"Erro ao salvar: {response_put.status_code} - {response_put.text}"
    except Exception as e:
        return False, str(e)


def render_fixed_footer():
    """
    Renderiza o rodapé com os ícones e a nova informação de pagamento.
    """

    st.markdown(textwrap.dedent(f"""
        <style>
            .footer-wrapper-final {{
                background-color: {COR_RODAPE};
                padding: 40px;
                margin-top: 60px;
                border-radius: 12px;
                color: {COR_TEXTO};
            }}
            .footer-wrapper-final h4, .footer-wrapper-final p {{
                color: {COR_TEXTO} !important;
                font-weight: bold;
            }}
            .footer-wrapper-final .stButton > button {{
                background-color: white;
                color: {COR_RODAPE};
                border: 2px solid white;
                font-weight: bold;
                width: 100%;
            }}
            .footer-bottom-bar {{
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
            .social-icons-container-corrigido {{
                display: flex;
                align-items: center;
                gap: 25px;
                margin-top: 15px;
            }}
            .social-icons-container-corrigido img {{
                width: 45px !important;
                height: 45px !important;
                transition: transform 0.2s;
            }}
            .social-icons-container-corrigido img:hover {{
                transform: scale(1.1);
            }}
            .payment-info {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .payment-info img {{
                height: 35px; /* <--- VALOR ALTERADO AQUI */
            }}
            .payment-info span {{
                color: #dddddd;
                font-size: 13px;
            }}
        </style>
    """), unsafe_allow_html=True)
    
    st.markdown('<div class="footer-wrapper-final">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
            <h4>ATENDIMENTO</h4>
            <div class="social-icons-container-corrigido">
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">
                    <img src="{WHATSAPP_ICON_URL}" alt="WhatsApp">
                </a>
                <a href="https://www.instagram.com/docebellacosmetico" target="_blank">
                    <img src="{INSTAGRAM_ICON_URL}" alt="Instagram">
                </a>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: normal; margin-bottom: 1rem;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
        
        with st.form(key="footer_form_github", clear_on_submit=True):
            nome = st.text_input("Nome", key="footer_nome_gh", label_visibility="collapsed", placeholder="Seu Nome")
            telefone = st.text_input("Telefone", key="footer_telefone_gh", label_visibility="collapsed", placeholder="DDD + Número")
            submitted = st.form_submit_button("Enviar")
            
            if submitted:
                if nome and telefone:
                    success, message = save_csv_github(nome, telefone)
                    if success:
                        st.success("Obrigado por se inscrever! 🎉")
                    else:
                        st.error("Ocorreu um erro ao salvar sua inscrição.")
                        # st.error(message)
                else:
                    st.warning("Por favor, preencha seu nome e telefone.")

    st.markdown("""
        <div class="footer-bottom-bar">
            <div class="payment-info">
                <img src="https://jequitai.khalsms.com.br/product_images/n/478/mercado-pago-logo__05862_zoom.png" alt="Logo Mercado Pago">
                <span>em até 3x no cartão</span>
            </div>
            <div>
                Copyright Doce&Bella - 2025.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
