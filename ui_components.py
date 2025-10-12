# ui_components.py

import streamlit as st
import pandas as pd
import time
import ast
import requests
import json
from data_handler import ESTOQUE_BAIXO_LIMITE # Importa a constante de limite

# --- Funções de Manipulação do Carrinho e Estado ---

def calcular_cashback_total(carrinho, df_catalogo_indexado):
    """Calcula o total de cashback a ser ganho pelos itens no carrinho."""
    cashback_total = 0.0
    for prod_id, item in carrinho.items():
        if prod_id in df_catalogo_indexado.index:
            row = df_catalogo_indexado.loc[prod_id]
            cashback_percent = pd.to_numeric(row.get('CASHBACKPERCENT'), errors='coerce') 
            preco_final = item['preco'] 
            
            if pd.notna(cashback_percent) and cashback_percent > 0:
                cashback_valor_unitario = (cashback_percent / 100) * preco_final
                cashback_total += cashback_valor_unitario * item['quantidade']
    return cashback_total


def adicionar_qtd_ao_carrinho(produto_id, produto_row, quantidade):
    produto_nome = produto_row['NOME']
    produto_preco = produto_row['PRECO_FINAL']
    produto_imagem = produto_row.get('LINKIMAGEM', '')
    
    df_catalogo = st.session_state.df_catalogo_indexado
    
    # Garante que a quantidade seja um número inteiro
    try:
        quantidade_max_raw = df_catalogo.loc[produto_id, 'QUANTIDADE']
        quantidade_max = int(pd.to_numeric(quantidade_max_raw, errors='coerce'))
    except (KeyError, ValueError):
        quantidade_max = 999999
    
    if quantidade_max <= 0:
         st.warning(f"⚠️ Produto '{produto_nome}' está esgotado.")
         return

    if produto_id in st.session_state.carrinho:
        nova_quantidade = st.session_state.carrinho[produto_id]['quantidade'] + quantidade
        
        if nova_quantidade > quantidade_max:
            disponivel = quantidade_max - st.session_state.carrinho[produto_id]['quantidade']
            st.warning(f"⚠️ Você só pode adicionar mais {disponivel} unidades. Total disponível: {quantidade_max}.")
            return
            
        st.session_state.carrinho[produto_id]['quantidade'] = nova_quantidade
    else:
        if quantidade > quantidade_max:
             st.warning(f"⚠️ Quantidade solicitada ({quantidade}) excede o estoque ({quantidade_max}) para '{produto_nome}'.")
             return
        st.session_state.carrinho[produto_id] = {
            'nome': produto_nome,
            'preco': produto_preco,
            'quantidade': quantidade,
            'imagem': produto_imagem
        }
    st.toast(f"✅ {quantidade}x {produto_nome} adicionado(s)!", icon="🛍️"); time.sleep(0.1)


def remover_do_carrinho(produto_id):
    if produto_id in st.session_state.carrinho:
        nome = st.session_state.carrinho[produto_id]['nome']
        del st.session_state.carrinho[produto_id]
        st.toast(f"❌ {nome} removido.", icon="🗑️")


def limpar_carrinho():
    st.session_state.carrinho = {}
    st.session_state.cupom_aplicado = None
    st.session_state.desconto_cupom = 0.0
    st.session_state.cupom_mensagem = ""
    st.toast("🗑️ Pedido limpo!", icon="🧹")
    st.rerun()

# --- Funções de Renderização de UI ---

def render_product_image(link_imagem):
    placeholder_html = """<div class="product-image-container" style="background-color: #f0f0f0; border-radius: 8px;"><span style="color: #a0a0a0; font-size: 1.1rem; font-weight: bold;">Sem Imagem</span></div>"""
    if link_imagem and str(link_imagem).strip().startswith('http'):
        st.markdown(f'<div class="product-image-container"><img src="{link_imagem}" alt="Imagem do produto"></div>', unsafe_allow_html=True)
    else:
        st.markdown(placeholder_html, unsafe_allow_html=True)


def render_product_card(prod_id, row, key_prefix, df_catalogo_indexado):
    """Renderiza um card de produto com suporte para abas de foto e vídeo, seletor de quantidade e feedback de estoque."""
    with st.container(border=True):
        
        produto_nome = str(row['NOME'])
        descricao_curta = str(row.get('DESCRICAOCURTA', '')).strip()
        
        try:
            estoque_atual = int(pd.to_numeric(row.get('QUANTIDADE', 999999), errors='coerce'))
        except (ValueError, TypeError):
            estoque_atual = 999999
            
        esgotado = estoque_atual <= 0
        estoque_baixo = 0 < estoque_atual <= ESTOQUE_BAIXO_LIMITE
        
        if esgotado:
            st.markdown('<span class="esgotado-badge">🚫 ESGOTADO</span>', unsafe_allow_html=True)
        elif estoque_baixo:
            st.markdown(f'<span class="estoque-baixo-badge">⚠️ Últimas {estoque_atual} Unidades!</span>', unsafe_allow_html=True)

        youtube_url = row.get('YOUTUBE_URL')

        if youtube_url and isinstance(youtube_url, str) and youtube_url.strip().startswith('http'):
            tab_foto, tab_video = st.tabs(["📷 Foto", "▶️ Vídeo"])
            with tab_foto:
                render_product_image(row.get('LINKIMAGEM'))
            with tab_video:
                st.video(youtube_url)
        else:
            render_product_image(row.get('LINKIMAGEM'))

        preco_final = row['PRECO_FINAL']
        preco_original = row['PRECO']
        is_promotion = pd.notna(row.get('PRECO_PROMOCIONAL'))

        if is_promotion:
            st.markdown(f"""
            <div style="margin-bottom: 0.5rem;">
                <span style="background-color: #D32F2F; color: white; font-weight: bold; padding: 3px 8px; border-radius: 5px; font-size: 0.9rem;">
                    🔥 PROMOÇÃO
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**{produto_nome}**")
        if descricao_curta:
            st.caption(descricao_curta)

        with st.expander("Ver detalhes"):
            descricao_principal = row.get('DESCRICAOLONGA')
            detalhes_str = row.get('DETALHESGRADE')
            
            tem_descricao = descricao_principal and isinstance(descricao_principal, str) and descricao_principal.strip()
            tem_detalhes = detalhes_str and isinstance(detalhes_str, str) and detalhes_str.strip()
            
            if not tem_descricao and not tem_detalhes:
                st.info('Sem informações detalhadas disponíveis para este produto.')
            else:
                if tem_descricao and descricao_principal.strip() != descricao_curta:
                    st.subheader('Descrição')
                    st.markdown(descricao_principal)
                    if tem_detalhes:
                        st.markdown('---') 
                
                if tem_detalhes:
                    st.subheader('Especificações')
                    if detalhes_str.strip().startswith('{'):
                        try:
                            detalhes_dict = ast.literal_eval(detalhes_str)
                            texto_formatado = "\n".join([f"* **{chave.strip()}**: {str(valor).strip()}" for chave, valor in detalhes_dict.items()])
                            st.markdown(texto_formatado)
                        except (ValueError, SyntaxError):
                            st.markdown(detalhes_str)
                    else:
                        st.markdown(detalhes_str)
        
        # --- SEÇÃO CORRIGIDA: Preço e Ação agora estão juntos ---
        st.markdown('<div class="price-action-flex">', unsafe_allow_html=True)
        
        # Lado Esquerdo: Preços e Cashback
        with st.container():
            condicao_pagamento = row.get('CONDICAOPAGAMENTO', 'Preço à vista')
            cashback_percent = pd.to_numeric(row.get('CASHBACKPERCENT'), errors='coerce')
            
            # Formata o preço e as condições
            if is_promotion:
                st.markdown(f"""
                <div style="line-height: 1.2;">
                    <span style='text-decoration: line-through; color: #757575; font-size: 0.9rem;'>R$ {preco_original:.2f}</span>
                    <h4 style='color: #D32F2F; margin:0;'>R$ {preco_final:.2f}</h4>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<h4 style='color: #880E4F; margin:0; line-height:1;'>R$ {preco_final:.2f}</h4>", unsafe_allow_html=True)
            
            st.markdown(f"<span style='color: #757575; font-size: 0.85rem; font-weight: normal;'>({condicao_pagamento})</span>", unsafe_allow_html=True)

            if pd.notna(cashback_percent) and cashback_percent > 0:
                cashback_valor = (cashback_percent / 100) * preco_final
                st.markdown(f"<span style='color: #2E7D32; font-size: 0.8rem; font-weight: bold;'>Cashback: R$ {cashback_valor:.2f}</span>", unsafe_allow_html=True)

        # Lado Direito: Botões de Ação
        st.markdown('<div class="action-buttons-container">', unsafe_allow_html=True)
        with st.container():
            item_ja_no_carrinho = prod_id in st.session_state.carrinho

            if esgotado:
                st.empty() # Não mostra nada se estiver esgotado
            elif item_ja_no_carrinho:
                qtd_atual = st.session_state.carrinho[prod_id]['quantidade']
                st.button(f"✅ {qtd_atual}x NO PEDIDO", key=f'btn_in_cart_{key_prefix}', use_container_width=True, disabled=True)
            else:
                qtd_a_adicionar = st.number_input(
                    'Quantidade',
                    min_value=1,
                    max_value=estoque_atual,
                    value=1,
                    step=1,
                    key=f'qtd_input_{key_prefix}',
                    label_visibility="collapsed"
                )
                
                if st.button(f"🛒 Adicionar {qtd_a_adicionar} un.", key=f'btn_add_{key_prefix}', use_container_width=True):
                    if qtd_a_adicionar >= 1:
                        adicionar_qtd_ao_carrinho(prod_id, row, qtd_a_adicionar)
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True) # Fecha action-buttons-container
        st.markdown('</div>', unsafe_allow_html=True) # Fecha price-action-flex

def render_countdown_timer(data_fim_str):
    """
    Renderiza um contador regressivo HTML/CSS para a data/hora final.
    O JavaScript é usado para atualizar o contador a cada segundo no frontend.
    """
    try:
        # 1. Definir o fuso horário (ex: 'America/Sao_Paulo' ou 'UTC' se for a preferência)
        # É CRUCIAL que o fuso horário aqui e o usado ao salvar a promoção sejam os mesmos!
        # Vamos assumir UTC se você estiver lidando com strings simples de data.
        # Se você estiver no Brasil (SP), use 'America/Sao_Paulo'
        fuso_horario = pytz.timezone('America/Sao_Paulo') 
        
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').replace(
            hour=23, minute=59, second=59
        )
        
        # Converte para o fuso horário definido
        data_fim_tz = fuso_horario.localize(data_fim)
        
        agora_tz = datetime.now(fuso_horario)
        
        # Calcula a diferença em segundos
        tempo_restante_segundos = (data_fim_tz - agora_tz).total_seconds()
        
        if tempo_restante_segundos <= 0:
            return '<div style="color: red; font-weight: bold; text-align: center;">⏳ PROMOÇÃO ENCERRADA</div>'

        # Calcula dias, horas, minutos e segundos restantes (para a primeira exibição)
        dias = math.floor(tempo_restante_segundos / (60 * 60 * 24))
        horas = math.floor((tempo_restante_segundos % (60 * 60 * 24)) / (60 * 60))
        minutos = math.floor((tempo_restante_segundos % (60 * 60)) / 60)
        segundos = math.floor(tempo_restante_segundos % 60)
        
        # Geração do HTML e JavaScript do contador
        timer_html = f"""
        <style>
            .countdown-timer-container {{
                background-color: #f7e2e5; /* Cor de fundo suave (rosa claro) */
                border: 2px solid #e91e63; /* Borda rosa vibrante */
                border-radius: 8px;
                padding: 5px 10px;
                margin-bottom: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .countdown-title {{
                font-weight: bold;
                color: #e91e63; /* Rosa vibrante */
                margin-bottom: 5px;
                font-size: 0.9em;
            }}
            .countdown-time-unit {{
                display: inline-block;
                margin: 0 5px;
            }}
            .countdown-time-value {{
                font-size: 1.2em;
                font-weight: 900;
                color: #333;
                display: block;
            }}
            .countdown-time-label {{
                font-size: 0.7em;
                color: #555;
                display: block;
            }}
        </style>
        
        <div class="countdown-timer-container">
            <div class="countdown-title">⏰ FIM DA PROMOÇÃO EM:</div>
            <div id="countdown-timer-{data_fim_str.replace('-', '_')}" style="font-size: 1.1em; color: #333;">
                <span class="countdown-time-unit"><span class="countdown-time-value">{dias:02}</span><span class="countdown-time-label">Dias</span></span>
                <span style="font-size: 1.2em; font-weight: bold;">:</span>
                <span class="countdown-time-unit"><span class="countdown-time-value">{horas:02}</span><span class="countdown-time-label">Horas</span></span>
                <span style="font-size: 1.2em; font-weight: bold;">:</span>
                <span class="countdown-time-unit"><span class="countdown-time-value">{minutos:02}</span><span class="countdown-time-label">Mins</span></span>
                <span style="font-size: 1.2em; font-weight: bold;">:</span>
                <span class="countdown-time-unit"><span class="countdown-time-value">{segundos:02}</span><span class="countdown-time-label">Segs</span></span>
            </div>
        </div>
        
        <script>
        function startCountdown(elementId, endTimeStr, timeZone) {{
            const countdownEl = document.getElementById(elementId);
            if (!countdownEl) return;
            
            const [year, month, day] = endTimeStr.split('-').map(Number);
            // Cria a data de término (23:59:59) no fuso horário local do navegador para evitar desync.
            const endTime = new Date(year, month - 1, day, 23, 59, 59);

            function updateCountdown() {{
                const now = new Date();
                const timeRemaining = endTime.getTime() - now.getTime();
                
                if (timeRemaining <= 0) {{
                    countdownEl.innerHTML = '<span style="color: red; font-weight: bold;">PROMOÇÃO ENCERRADA!</span>';
                    clearInterval(interval);
                    return;
                }}

                let seconds = Math.floor(timeRemaining / 1000);
                const days = Math.floor(seconds / (60 * 60 * 24));
                seconds -= days * (60 * 60 * 24);
                const hours = Math.floor(seconds / (60 * 60));
                seconds -= hours * (60 * 60);
                const minutes = Math.floor(seconds / 60);
                seconds -= minutes * 60;
                
                const format = (value) => String(value).padStart(2, '0');
                
                countdownEl.innerHTML = `
                    <span class="countdown-time-unit"><span class="countdown-time-value">${format(days)}</span><span class="countdown-time-label">Dias</span></span>
                    <span style="font-size: 1.2em; font-weight: bold;">:</span>
                    <span class="countdown-time-unit"><span class="countdown-time-value">${format(hours)}</span><span class="countdown-time-label">Horas</span></span>
                    <span style="font-size: 1.2em; font-weight: bold;">:</span>
                    <span class="countdown-time-unit"><span class="countdown-time-value">${format(minutes)}</span><span class="countdown-time-label">Mins</span></span>
                    <span style="font-size: 1.2em; font-weight: bold;">:</span>
                    <span class="countdown-time-unit"><span class="countdown-time-value">${format(seconds)}</span><span class="countdown-time-label">Segs</span></span>
                `;
            }}

            const interval = setInterval(updateCountdown, 1000);
            updateCountdown(); // Chama imediatamente para evitar atraso
        }}
        
        // Inicializa o contador
        startCountdown('countdown-timer-{data_fim_str.replace('-', '_')}', '{data_fim_str}', 'America/Sao_Paulo');
        </script>
        """
        
        return timer_html
        
    except Exception as e:
        # st.error(f"Erro ao calcular contador: {e}") # Descomente para debug
        return "" # Não mostra nada em caso de erro



