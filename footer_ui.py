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
    """Renderiza o rodapé simplificado com Atendimento e Newsletter."""

    # --- CSS ATUALIZADO ---
    # Alvo: um container que vamos criar para garantir o fundo rosa
    st.markdown(textwrap.dedent(f"""
        <style>
            .footer-container {{
                background-color: {COR_RODAPE};
                padding: 30px 40px;
                margin-top: 50px;
                border-radius: 8px;
            }}
            /* Estilos para textos e links dentro do container rosa */
            .footer-container h4, .footer-container p, .footer-container label {{
                color: {COR_TEXTO};
                font-weight: bold;
            }}
            .footer-container a {{
                color: {COR_LINK};
                text-decoration: none;
                display: block;
                margin-bottom: 8px;
                font-size: 1.1rem; /* Aumenta um pouco o tamanho dos links */
            }}
            .footer-container a:hover {{
                text-decoration: underline;
            }}
            /* Estilos para o formulário */
            .footer-container .stButton > button {{
                background-color: white;
                color: {COR_RODAPE};
                border: 2px solid white;
                font-weight: bold;
                width: 100%; /* Botão ocupa a largura toda */
            }}
            .footer-container .stButton > button:hover {{
                background-color: #f0f0f0;
                color: {COR_RODAPE};
            }}
            /* Barra cinza inferior */
            .footer-bottom {{
                background-color: #333333; /* Um cinza mais escuro */
                color: #dddddd;
                padding: 15px 40px;
                margin-top: 0; /* Remove espaço entre o rosa e o cinza */
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                font-size: 13px;
                border-radius: 0 0 8px 8px; /* Arredonda cantos inferiores */
            }}
        </style>
    """), unsafe_allow_html=True)

    # --- LAYOUT ATUALIZADO ---
    # Usamos um container do Streamlit para agrupar e aplicar o estilo
    with st.container():
        # Aplicamos a classe CSS ao container que conterá as colunas
        st.markdown('<div class="footer-container">', unsafe_allow_html=True)

        # Criamos 2 colunas: uma para Atendimento, outra para o Formulário
        col1, col2 = st.columns([1, 2])  # A coluna do form é 2x maior

        with col1:
            # Conteúdo da primeira coluna (APENAS o que você quer manter)
            st.markdown(textwrap.dedent(f"""
                <h4>ATENDIMENTO</h4>
                <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
                <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram</a>
            """), unsafe_allow_html=True)

        with col2:
            # Conteúdo da segunda coluna (O formulário)
            st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight: normal; margin-bottom: 1rem;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
            
            with st.form(key="footer_form", clear_on_submit=True):
                nome = st.text_input("Nome", key="footer_nome", label_visibility="collapsed", placeholder="Seu Nome")
                telefone = st.text_input("Telefone", key="footer_telefone", label_visibility="collapsed", placeholder="DDD + Número")
                
                submitted = st.form_submit_button("Enviar")
                if submitted and nome and telefone:
                    # Futuramente, adicione aqui a lógica para salvar os dados
                    st.success("Obrigado por se inscrever! 🎉")

        # Fecha a div do container rosa
        st.markdown('</div>', unsafe_allow_html=True)

    # A barra cinza inferior é renderizada fora do container principal
    st.markdown(textwrap.dedent("""
        <div class="footer-bottom">
            <div>
                Meios de pagamento
                <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
            </div>
            <div>
                Copyright Doce&Bella - 2025.
            </div>
        </div>
    """), unsafe_allow_html=True)
