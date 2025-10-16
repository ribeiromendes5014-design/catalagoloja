# footer_ui.py

import streamlit as st
import textwrap
import pandas as pd  # <-- 1. Importe o pandas
import os          # <-- 1. Importe o os

try:
    from data_handler import NUMERO_WHATSAPP
except ImportError:
    NUMERO_WHATSAPP = "5511999999999"

# --- Variáveis de Estilo ---
COR_RODAPE = "#F28C9D"
COR_TEXTO = "white"
COR_LINK = "white"

# --- Nome do arquivo CSV para salvar os dados ---
NEWSLETTER_CSV_PATH = 'newsletter_subscribers.csv'

# --- 2. Função para salvar os dados no CSV ---
def append_to_csv(nome, telefone):
    """
    Adiciona uma nova linha com nome e telefone a um arquivo CSV.
    Cria o arquivo e o cabeçalho se não existirem.
    """
    # Verifica se o arquivo existe para decidir se o cabeçalho deve ser escrito
    file_exists = os.path.exists(NEWSLETTER_CSV_PATH)
    
    # Cria um DataFrame com os novos dados
    new_data = pd.DataFrame({'Nome': [nome], 'Telefone': [telefone]})
    
    # Salva no CSV
    # mode='a' significa 'append' (adicionar ao final do arquivo)
    # header=not file_exists significa que o cabeçalho só será escrito se o arquivo não existir
    new_data.to_csv(NEWSLETTER_CSV_PATH, mode='a', header=not file_exists, index=False)


def render_fixed_footer():
    """
    Renderiza o rodapé final usando um container Streamlit com uma classe CSS
    para garantir que todos os elementos fiquem dentro do bloco rosa.
    """

    # ... (O seu CSS continua o mesmo aqui) ...
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
                display: block;
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
        </style>
    """), unsafe_allow_html=True)
    
    st.markdown('<div class="footer-wrapper-final">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
            <h4>ATENDIMENTO</h4>
            <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
            <a href="https://www.instagram.com/docebellacosmetico" target="_blank">Instagram</a>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: normal; margin-bottom: 1rem;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
        
        with st.form(key="footer_form_final_correto", clear_on_submit=True):
            nome = st.text_input("Nome", key="footer_nome", label_visibility="collapsed", placeholder="Seu Nome")
            telefone = st.text_input("Telefone", key="footer_telefone", label_visibility="collapsed", placeholder="DDD + Número")
            submitted = st.form_submit_button("Enviar")
            
            # --- 3. Lógica de salvamento quando o botão é pressionado ---
            if submitted and nome and telefone:
                try:
                    append_to_csv(nome, telefone)
                    st.success("Obrigado por se inscrever! 🎉")
                except Exception as e:
                    st.error(f"Ocorreu um erro ao salvar: {e}")

    st.markdown("""
        <div class="footer-bottom-bar">
            <div>
                Meios de pagamento
                <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
            </div>
            <div>
                Copyright Doce&Bella - 2025.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
