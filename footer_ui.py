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
COR_LINK = "white"

# --- URLs dos Ícones PNG ---
INSTAGRAM_ICON_URL = "https://static.vecteezy.com/system/resources/previews/018/930/415/non_2x/instagram-logo-instagram-icon-transparent-free-png.png"
WHATSAPP_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/2044px-WhatsApp.svg.png"

# --- FUNÇÃO: Salvar CSV no GitHub ---
def save_csv_github(nome, telefone):
    """
    Busca o CSV do GitHub, adiciona uma nova linha e faz o commit da nova versão.
    """
    try:
        # Carrega as credenciais do Streamlit Secrets
        token = st.secrets["github"]["token"]
        owner = st.secrets["github"]["owner"]
        repo = st.secrets["github"]["repo"]
        path = st.secrets["github"]["file_path"]
        
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}"}
        
        # 1. Tenta obter o arquivo existente para pegar o SHA
        response = requests.get(url, headers=headers)
        
        sha = None
        current_content = ""
        
        if response.status_code == 200:
            # Se o arquivo existe, decodifica o conteúdo
            data = response.json()
            sha = data['sha']
            content_encoded = data['content']
            current_content = base64.b64decode(content_encoded).decode('utf-8')
        elif response.status_code != 404:
            # Se ocorreu um erro que não seja "não encontrado", falha
            raise Exception(f"Erro ao buscar arquivo: {response.status_code} - {response.text}")

        # 2. Prepara o novo conteúdo
        new_line = f"{nome},{telefone}"
        if not current_content:
            # Se o arquivo é novo, cria o cabeçalho
            new_content = f"Nome,Telefone\n{new_line}"
        else:
            # Se o arquivo existe, apenas adiciona a nova linha
            new_content = f"{current_content}\n{new_line}"
            
        # 3. Codifica o novo conteúdo para a API do GitHub
        content_encoded = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
        
        # 4. Prepara os dados para o commit
        commit_message = f"Inscrição de novo lead: {nome}"
        payload = {
            "message": commit_message,
            "content": content_encoded,
        }
        # O SHA é obrigatório para ATUALIZAR um arquivo existente
        if sha:
            payload["sha"] = sha
            
        # 5. Envia o arquivo atualizado (ou novo) para o GitHub
        response_put = requests.put(url, headers=headers, json=payload)
        
        if response_put.status_code == 200 or response_put.status_code == 201:
            return True, None # Sucesso
        else:
            return False, f"Erro ao salvar: {response_put.status_code} - {response_put.text}"

    except Exception as e:
        return False, str(e)


def render_fixed_footer():
    """
    Renderiza o rodapé e gerencia o formulário de inscrição,
    agora salvando os dados no GitHub.
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
            .footer-wrapper-final h4, .footer-wrapper-final p, .footer-wrapper-final label {{
                color: {COR_TEXTO} !important;
                font-weight: bold;
            }}
            .footer-wrapper-final a {{
                color: {COR_LINK};
                text-decoration: none;
                display: block; /* Garante que cada link ocupe sua própria linha */
                margin-bottom: 8px;
                font-size: 1.1rem;
            }}
            .footer-wrapper-final a:hover {{ text-decoration: underline; }}
            .footer-wrapper-final .stForm {{
                border: none;
                padding: 0;
                background: transparent;
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
            /* --- Estilo para os contêineres dos ícones --- */
            .social-icons-container {{
                display: flex; /* Para alinhar os ícones lado a lado */
                align-items: center; /* Para centralizar verticalmente */
                gap: 20px; /* Espaçamento entre os ícones */
                margin-top: 10px; /* Margem acima dos ícones */
            }}
            .social-icon-link {{
                display: flex; /* Para alinhar a imagem dentro do link */
                align-items: center;
                text-decoration: none; /* Remover sublinhado padrão do link */
                color: {COR_LINK}; /* A cor padrão do link */
            }}
            .social-icon-link img {{
                width: 40px;  /* Tamanho fixo para ambos os ícones */
                height: 40px; /* Altura fixa para ambos os ícones */
                vertical-align: middle; /* Alinha a imagem com o texto, se houver */
                filter: brightness(0) invert(1); /* Deixa o ícone do WhatsApp branco */
            }}
            /* Se você quiser o ícone do Instagram original (branco) e do WhatsApp colorido, remova o filter: brightness(0) invert(1); */
            /* Se a imagem do Instagram já é branca, o filtro não a afetará se ela for monocromática */

            /* Ajuste para o texto ao lado do ícone, se houver */
            .social-icon-link span {{
                margin-left: 8px; /* Espaço entre o ícone e o texto */
                font-weight: bold; /* Deixa o texto do WhatsApp em negrito */
                font-size: 1.1em;
            }}

        </style>
    """), unsafe_allow_html=True)
    
    st.markdown('<div class="footer-wrapper-final">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
            <h4>ATENDIMENTO</h4>
            <div class="social-icons-container">
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank" class="social-icon-link">
                    <img src="{WHATSAPP_ICON_URL}" alt="WhatsApp">
                    <span>WhatsApp</span>
                </a>
                <a href="https://www.instagram.com/docebellacosmetico" target="_blank" class="social-icon-link">
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
                        # Para depuração, você pode querer ver o erro real:
                        # st.error(message)
                else:
                    st.warning("Por favor, preencha seu nome e telefone.")

    st.markdown("""
        <div class="footer-bottom-bar">
            <div>Meios de pagamento
                <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
            </div>
            <div>Copyright Doce&Bella - 2025.</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
