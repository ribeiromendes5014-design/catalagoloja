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
NUMERO_EXIBIDO = "55 11 99999-9999"

def render_fixed_footer():
    """Renderiza o rodapé fixo, incluindo o formulário de newsletter."""

    # --- ALTERAÇÃO 1: CSS para o container principal e colunas ---
    # Usamos um ID (#footer-container) para aplicar o fundo rosa
    st.markdown(textwrap.dedent(f"""
        <style>
            #footer-container {{
                background-color: {COR_RODAPE};
                padding: 30px 40px;
                margin-top: 50px;
                border-radius: 8px; /* Opcional: bordas arredondadas */
            }}
            #footer-container h4, #footer-container p, #footer-container label {{
                color: {COR_TEXTO};
                font-weight: bold;
            }}
            #footer-container a {{
                color: {COR_LINK};
                text-decoration: none;
                display: block;
                margin-bottom: 8px;
            }}
            #footer-container a:hover {{
                text-decoration: underline;
            }}
            #footer-container .stButton > button {{
                background-color: white;
                color: {COR_RODAPE};
                border: 2px solid white;
                font-weight: bold;
            }}
             #footer-container .stButton > button:hover {{
                background-color: #eee;
                color: {COR_RODAPE};
            }}
            .footer-bottom {{
                width: 100%;
                background-color: rgba(0,0,0,0.05);
                color: {COR_TEXTO};
                padding: 10px 40px;
                margin-top: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                font-size: 13px;
                border-radius: 0 0 8px 8px; /* Arredonda cantos inferiores */
            }}
        </style>
    """), unsafe_allow_html=True)

    # --- ALTERAÇÃO 2: Usar st.container e st.columns para o layout ---
    # Envolvemos tudo em um container para aplicar o estilo
    st.markdown('<div id="footer-container">', unsafe_allow_html=True)

    # Criamos 4 colunas para o conteúdo do rodapé
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5]) # A última coluna é um pouco maior

    with col1:
        st.markdown(textwrap.dedent(f"""
            <h4>ATENDIMENTO</h4>
            <p>{NUMERO_EXIBIDO}</p>
            <a href="https://wa.me/{NUMERO_WHATSAPP}" target="_blank">WhatsApp</a>
            <a href="https://www.instagram.com/doce_bella" target="_blank">Instagram</a>
        """), unsafe_allow_html=True)

    with col2:
        st.markdown(textwrap.dedent("""
            <h4>MARCAS</h4>
            <a href="#">MAQUIAGENS</a>
            <a href="#">ACESSÓRIOS</a>
            <a href="#">SKINCARE</a>
        """), unsafe_allow_html=True)

    with col3:
        st.markdown(textwrap.dedent("""
            <h4>INSTITUCIONAL</h4>
            <a href="#">Sobre Nós</a>
            <a href="#">Políticas de Privacidade</a>
        """), unsafe_allow_html=True)

    # --- ALTERAÇÃO 3: O formulário agora vive na última coluna ---
    with col4:
        st.markdown("<h4>Newsletter</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: normal;'>Receba novidades e promoções!</p>", unsafe_allow_html=True)
        
        # O formulário em si
        with st.form(key="footer_newsletter_form", clear_on_submit=True):
            nome = st.text_input("Nome", key="footer_nome", label_visibility="collapsed", placeholder="Seu Nome")
            telefone = st.text_input("Telefone", key="footer_telefone", label_visibility="collapsed", placeholder="DDD + Número")
            
            submitted = st.form_submit_button("Enviar")
            if submitted and nome and telefone:
                # Aqui você pode adicionar a lógica para salvar os dados
                st.success("Obrigado por se inscrever! 🎉")

    st.markdown('</div>', unsafe_allow_html=True) # Fecha o container principal
    
    # O "footer-bottom" continua sendo um HTML separado
    st.markdown(textwrap.dedent("""
        <div class="footer-bottom">
            <div>
                Meios de pagamento
                <img src="https://i.ibb.co/h7n1Xf7/pagamentos.png" alt="Pagamentos" style="height: 18px; vertical-align: middle; margin-left: 5px;">
            </div>
            <div>
                criado por
                <span>
                    <img src="https://i.ibb.co/6R2b0S4/nuvemshop-logo.png" alt="Nuvemshop" style="height: 16px; vertical-align: middle;">
                </span>
                | Copyright WE MAKE - 2025.
            </div>
        </div>
    """), unsafe_allow_html=True)
