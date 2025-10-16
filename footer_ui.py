# footer_ui.py

import streamlit as st
import textwrap

# Se o arquivo data_handler.py existir, este import funciona.
try:
    from data_handler import NUMERO_WHATSAPP
except ImportError:
    NUMERO_WHATSAPP = "5511999999999" # Coloque seu número aqui

# Variáveis de Configuração do Layout
COR_RODAPE = "#F28C9D"
COR_TEXTO = "white"
COR_LINK = "white"

def render_fixed_footer():
    """Renderiza um rodapé único e integrado, conforme o desenho."""

    # --- CSS ATUALIZADO ---
    # Agora temos um único container principal: .footer-wrapper
    st.markdown(textwrap.dedent(f"""
        <style>
            /* O "MEGA-RODAPÉ" ROSA QUE ENVOLVE TUDO */
            .footer-wrapper {{
                background-color: {COR_RODAPE};
                padding: 40px; /* Aumenta o espaçamento interno */
                margin-top: 60px; /* Mais espaço acima do rodapé */
                border-radius: 12px; /* Bordas mais arredondadas */
            }}
            /* Estilos para textos e links dentro do container rosa */
            .footer-wrapper h4, .footer-wrapper p, .footer-wrapper label {{
                color: {COR_TEXTO};
                font-weight: bold;
            }}
            .footer-wrapper a {{
                color: {COR_LINK};
                text-decoration: none;
                display: block;
                margin-bottom: 8px;
                font-size: 1.1rem;
            }}
            .footer-wrapper a:hover {{
                text-decoration: underline;
            }}
            /* Estilos para o formulário */
            .footer-wrapper .stButton > button {{
                background-color: white;
                color: {COR_RODAPE};
                border: 2px solid white;
                font-weight: bold;
                width: 100%;
            }}
            .footer-wrapper .stButton > button:hover {{
                background-color: #f0f0f0;
                color: {COR_RODAPE};
            }}
            /* A BARRA CINZA INFERIOR, AGORA DENTRO DA ROSA */
            .footer-bottom-inner {{
                background-color: #333333;
                color: #dddddd;
                padding: 15px 20px;
                margin-top: 40px; /* Espaço entre o form e a barra cinza */
                border-radius: 8px; /* Bordas arredondadas para a barra interna */
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                font-size: 13px;
                gap: 15px; /* Espaçamento para quando o texto quebrar a linha */
            }}
        </style>
    """), unsafe_allow_html=True)

    # --- LAYOUT ATUALIZADO ---
    # Usamos um container do Streamlit para agrupar tudo
    with st.container():
        # 1. Abrimos a div do "mega-rodapé" rosa
        st.markdown('<div class="footer-wrapper">', unsafe_allow_html=True)

        # 2. Criamos as colunas para Atendimento e Newsletter
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(textwrap.dedent(f"""
                <h4>ATENDIMENTO</h4>
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
                <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram</a>
            """), unsafe_allow_html=True)

        with col2:
            st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight: normal; margin-bottom: 1rem;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
            
            with st.form(key="footer_form_final", clear_on_submit=True):
                nome = st.text_input("Nome", key="footer_nome", label_visibility="collapsed", placeholder="Seu Nome")
                telefone = st.text_input("Telefone", key="footer_telefone", label_visibility="collapsed", placeholder="DDD + Número")
                
                submitted = st.form_submit_button("Enviar")
                if submitted and nome and telefone:
                    st.success("Obrigado por se inscrever! 🎉")

        # 3. Renderizamos a barra cinza DENTRO da div rosa
        st.markdown(textwrap.dedent("""
            <div class="footer-bottom-inner">
                <div>
                    Meios de pagamento
                    <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
                </div>
                <div>
                    Copyright Doce&Bella - 2025.
                </div>
            </div>
        """), unsafe_allow_html=True)

        # 4. Fechamos a div do "mega-rodapé" rosa
        st.markdown('</div>', unsafe_allow_html=True)
