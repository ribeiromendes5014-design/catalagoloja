# footer_ui.py

import streamlit as st
import textwrap

try:
    from data_handler import NUMERO_WHATSAPP
except ImportError:
    NUMERO_WHATSAPP = "5511999999999"

# --- Variáveis de Estilo ---
COR_RODAPE = "#F28C9D"
COR_TEXTO = "white"
COR_LINK = "white"

def render_fixed_footer():
    """
    Renderiza o rodapé final usando um container Streamlit com uma classe CSS
    para garantir que todos os elementos fiquem dentro do bloco rosa.
    """

    # --- CSS Definitivo e Específico ---
    # Usamos uma classe de container (.footer-wrapper-final) para aplicar todos os estilos.
    st.markdown(textwrap.dedent(f"""
        <style>
            /* O container principal que cria o fundo rosa */
            .footer-wrapper-final {{
                background-color: {COR_RODAPE};
                padding: 40px;
                margin-top: 60px;
                border-radius: 12px;
                color: {COR_TEXTO};
            }}

            /* Estilos para todos os elementos de texto dentro do container */
            .footer-wrapper-final h4, .footer-wrapper-final p, .footer-wrapper-final label {{
                color: {COR_TEXTO} !important; /* !important força a cor */
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
            
            /* Remove bordas e fundos indesejados do formulário Streamlit */
            .footer-wrapper-final .stForm {{
                border: none;
                padding: 0;
                background: transparent;
            }}

            /* Estiliza o botão "Enviar" */
            .footer-wrapper-final .stButton > button {{
                background-color: white;
                color: {COR_RODAPE};
                border: 2px solid white;
                font-weight: bold;
                width: 100%;
            }}

            /* A barra cinza inferior */
            .footer-bottom-bar {{
                background-color: #333333;
                color: #dddddd;
                padding: 15px 20px;
                margin-top: 40px; /* Espaço entre o form e a barra */
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

    # --- Layout com st.container e st.columns ---
    
    # 1. Abre uma div com a nossa classe CSS personalizada.
    # Todos os comandos Streamlit seguintes serão renderizados dentro dela.
    st.markdown('<div class="footer-wrapper-final">', unsafe_allow_html=True)

    # 2. Cria as colunas para o conteúdo principal
    col1, col2 = st.columns([1, 2])

    with col1:
        # Conteúdo de Atendimento
        st.markdown(f"""
            <h4>ATENDIMENTO</h4>
            <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
            <a href="https://www.instagram.com/docebellacosmetico" target="_blank">Instagram</a>
        """, unsafe_allow_html=True)

    with col2:
        # Títulos do formulário
        st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: normal; margin-bottom: 1rem;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
        
        # O formulário Streamlit, agora garantido de estar dentro da div rosa
        with st.form(key="footer_form_final_correto", clear_on_submit=True):
            nome = st.text_input("Nome", key="footer_nome", label_visibility="collapsed", placeholder="Seu Nome")
            telefone = st.text_input("Telefone", key="footer_telefone", label_visibility="collapsed", placeholder="DDD + Número")
            submitted = st.form_submit_button("Enviar")
            if submitted and nome and telefone:
                st.success("Obrigado por se inscrever! 🎉")

    # 3. Adiciona a barra cinza inferior, ainda dentro da nossa div principal
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

    # 4. Fecha a div principal. Este é o passo crucial.
    st.markdown('</div>', unsafe_allow_html=True)

