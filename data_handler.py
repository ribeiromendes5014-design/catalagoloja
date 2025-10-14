# data_handler.py

import os
import requests
import base64
from io import StringIO
import pandas as pd
from datetime import datetime
import json
import pytz
import streamlit as st 


# --- Variáveis de Configuração ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
DATA_REPO_NAME = os.environ.get("DATA_REPO_NAME", os.environ.get("REPO_NAME"))
BRANCH = os.environ.get("BRANCH")
ESTOQUE_BAIXO_LIMITE = 2 

# URLs da API
GITHUB_BASE_API = f"https://api.github.com/repos/{DATA_REPO_NAME}/contents/"

# Fontes de Dados (CSV no GitHub)
SHEET_NAME_CATALOGO_CSV = "produtos_estoque.csv"
SHEET_NAME_PROMOCOES_CSV = "promocoes.csv"
SHEET_NAME_PEDIDOS_CSV = "pedidos.csv"
SHEET_NAME_VIDEOS_CSV = "video.csv"
SHEET_NAME_CLIENTES_CASHBACK_CSV = "clientes_cash.csv"
SHEET_NAME_CUPONS_CSV = "cupons.csv"
BACKGROUND_IMAGE_URL = 'https://i.ibb.co/x8HNtgxP/Без-na-zvania-3.jpg'
LOGO_DOCEBELLA_URL = "https://i.ibb.co/sdMgFXmT/logo_docebella.png"

# NÚMERO DE TELEFONE PARA O BOTÃO FLUTUANTE DO WHATSAPP
NUMERO_WHATSAPP = "5541987876191" 


# --- Funções de Conexão GITHUB ---
def get_data_from_github(file_name):
    """
    Lê o conteúdo de um CSV do GitHub diretamente via API (sem cache da CDN).
    Garante que sempre trará a versão mais recente do arquivo.
    """
    api_url = f"{GITHUB_BASE_API}{file_name}?ref={BRANCH}"

    try:
        headers_content = {
            "Authorization": f"token {GITHUB_TOKEN}",
        }
        response = requests.get(api_url, headers=headers_content)

        if response.status_code == 404:
            if file_name != SHEET_NAME_CUPONS_CSV:
                st.error(f"Erro 404: Arquivo '{file_name}' não encontrado no repositório '{DATA_REPO_NAME}' na branch '{BRANCH}'. Verifique o nome do arquivo/branch/repo.")
            return None

        response.raise_for_status()

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            st.error(f"Erro de JSON ao decodificar a resposta da API do GitHub para '{file_name}'.")
            st.code(response.text[:500])
            return None

        if "content" not in data:
            st.error(f"O campo 'content' não foi encontrado na resposta da API. Verifique se o arquivo {file_name} existe na branch '{BRANCH}'.")
            st.json(data)
            return None

        content = base64.b64decode(data["content"]).decode("utf-8")
        csv_data = StringIO(content)
        df = pd.read_csv(csv_data, sep=",", encoding="utf-8", engine="python", on_bad_lines="warn")
        df.columns = [col.strip().upper().replace(' ', '_') for col in df.columns]
        return df

    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            st.error(f"Erro HTTP ao acessar '{file_name}' via API ({e.response.status_code}). URL: {api_url}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar '{file_name}' via API do GitHub: {e}")
        return None


@st.cache_data(ttl=None)
def carregar_cupons():
    """Carrega os cupons do 'cupons.csv' do GitHub, validando com fuso horário do Brasil."""
    df = get_data_from_github(SHEET_NAME_CUPONS_CSV)
    
    colunas_essenciais = ['CODIGO', 'TIPO_DESCONTO', 'VALOR', 'DATA_VALIDADE', 
                           'VALOR_MINIMO_PEDIDO', 'LIMITE_USOS', 'USOS_ATUAIS', 'STATUS']
                           
    if df is None or df.empty:
        return pd.DataFrame(columns=colunas_essenciais)

    df.rename(columns={'CODIGO': 'NOME_CUPOM', 'VALOR': 'VALOR_DESCONTO'}, inplace=True)
    colunas_essenciais_renomeadas = ['NOME_CUPOM', 'TIPO_DESCONTO', 'VALOR_DESCONTO', 'DATA_VALIDADE', 
                                    'VALOR_MINIMO_PEDIDO', 'LIMITE_USOS', 'USOS_ATUAIS', 'STATUS']

    for col in colunas_essenciais_renomeadas:
        if col not in df.columns:
            st.warning(f"A planilha de cupons existe, mas a coluna essencial '{col}' não foi encontrada.")
            return pd.DataFrame(columns=colunas_essenciais_renomeadas)

    df_ativo = df[df['STATUS'].astype(str).str.strip().str.upper() == 'ATIVO'].copy()
    if df_ativo.empty:
        return pd.DataFrame(columns=colunas_essenciais_renomeadas)

    df_ativo['NOME_CUPOM'] = df_ativo['NOME_CUPOM'].astype(str).str.strip().str.upper()
    df_ativo['TIPO_DESCONTO'] = df_ativo['TIPO_DESCONTO'].astype(str).str.strip().str.upper()
    df_ativo['VALOR_DESCONTO'] = pd.to_numeric(df_ativo['VALOR_DESCONTO'].astype(str).str.replace(',', '.'), errors='coerce')
    df_ativo['VALOR_MINIMO_PEDIDO'] = pd.to_numeric(df_ativo['VALOR_MINIMO_PEDIDO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    df_ativo['LIMITE_USOS'] = pd.to_numeric(df_ativo['LIMITE_USOS'], errors='coerce').fillna(999999)
    df_ativo['USOS_ATUAIS'] = pd.to_numeric(df_ativo['USOS_ATUAIS'], errors='coerce').fillna(0)
    
    # --- INÍCIO DA CORREÇÃO: Validação Segura da DATA_VALIDADE ---
    
    # Tenta converter a data para o formato datetime. Falhas viram NaT (Not a Time).
    df_ativo['DATA_VALIDADE'] = pd.to_datetime(df_ativo['DATA_VALIDADE'], format='%d/%m/%Y', errors='coerce')

    # Define o fuso horário e a data atual
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    hoje_brasil = pd.Timestamp.now(tz=tz_brasil).normalize()

    # 1. Cria uma máscara para identificar quais linhas TÊM uma data válida (não são NaT).
    datas_validas_mask = df_ativo['DATA_VALIDADE'].notna()

    # 2. Somente para as linhas com datas válidas, aplica o fuso horário.
    if datas_validas_mask.any():
        df_ativo.loc[datas_validas_mask, 'DATA_VALIDADE'] = df_ativo.loc[datas_validas_mask, 'DATA_VALIDADE'].dt.tz_localize(tz_brasil)

        # 3. Cria uma máscara para identificar os cupons que estão expirados.
        # Um cupom é expirado SE ele tem uma data VÁLIDA E essa data é ANTERIOR a hoje.
        cupons_expirados_mask = datas_validas_mask & (df_ativo['DATA_VALIDADE'].dt.normalize() < hoje_brasil)

        # 4. Mantém todos os cupons que NÃO estão na lista de expirados.
        # A negação (~) garante que cupons sem data (onde a máscara era False)
        # e cupons com data futura sejam mantidos.
        df_ativo = df_ativo[~cupons_expirados_mask]

    # --- FIM DA CORREÇÃO ---

    df_ativo = df_ativo[df_ativo['USOS_ATUAIS'] < df_ativo['LIMITE_USOS']]

    return df_ativo.dropna(subset=['NOME_CUPOM', 'VALOR_DESCONTO']).reset_index(drop=True)


@st.cache_data(ttl=None)
def carregar_promocoes():
    """Carrega as promoções do 'promocoes.csv' do GitHub."""
    df = get_data_from_github(SHEET_NAME_PROMOCOES_CSV)

    colunas_essenciais = ['ID_PRODUTO', 'PRECO_PROMOCIONAL', 'STATUS']
    if df is None or df.empty:
        return pd.DataFrame(columns=colunas_essenciais)

    for col in colunas_essenciais:
        if col not in df.columns:
            st.error(f"Coluna essencial '{col}' não encontrada no 'promocoes.csv'. Verifique o cabeçalho.")
            return pd.DataFrame(columns=colunas_essenciais)

    df = df[df['STATUS'].astype(str).str.strip().str.upper() == 'ATIVO'].copy()
    df_essencial = df[colunas_essenciais].copy()

    df_essencial['PRECO_PROMOCIONAL'] = pd.to_numeric(df_essencial['PRECO_PROMOCIONAL'].astype(str).str.replace(',', '.'), errors='coerce')
    df_essencial['ID_PRODUTO'] = pd.to_numeric(df_essencial['ID_PRODUTO'], errors='coerce').astype('Int64')

    return df_essencial.dropna(subset=['ID_PRODUTO', 'PRECO_PROMOCIONAL']).reset_index(drop=True)


@st.cache_data(ttl=None)
def carregar_catalogo():
    """
    Carrega o catálogo, aplica promoções e vídeos, e prepara o DataFrame.
    IMPORTANTE: Retorna o DataFrame com 'ID' como índice para buscas rápidas (indexação).
    """
    df_produtos = get_data_from_github(SHEET_NAME_CATALOGO_CSV)

    if df_produtos is None or df_produtos.empty:
        st.warning(f"Catálogo indisponível. Verifique o arquivo '{SHEET_NAME_CATALOGO_CSV}' no GitHub.")
        return pd.DataFrame()

    if 'ID' in df_produtos.columns:
        df_produtos['RECENCIA'] = pd.to_numeric(df_produtos['ID'], errors='coerce')
        df_produtos['ID'] = pd.to_numeric(df_produtos['ID'], errors='coerce').astype('Int64')
        df_produtos.dropna(subset=['ID'], inplace=True)
    else:
        df_produtos['RECENCIA'] = range(len(df_produtos), 0, -1)
        
    # --- NOVO: Lidar com PRECOVISTA e PRECOCARTAO ---
    colunas_minimas = ['PRECOVISTA', 'ID', 'NOME']
    for col in colunas_minimas:
        if col not in df_produtos.columns:
            st.error(f"Coluna essencial '{col}' não encontrada no '{SHEET_NAME_CATALOGO_CSV}'. O aplicativo não pode continuar.")
            return pd.DataFrame()
    
    mapa_renomeacao = {'PRECOVISTA': 'PRECO', 'MARCA': 'DESCRICAOCURTA'}
    df_produtos.rename(columns=mapa_renomeacao, inplace=True)
    
    if 'PRECOCARTAO' not in df_produtos.columns:
        df_produtos['PRECOCARTAO'] = df_produtos['PRECO']
    
    df_produtos['PRECO'] = pd.to_numeric(df_produtos['PRECO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
    df_produtos['PRECOCARTAO'] = pd.to_numeric(df_produtos['PRECOCARTAO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(df_produtos['PRECO'])
    
    if 'CONDICAOPAGAMENTO' not in df_produtos.columns:
        def gerar_condicao_pagamento(row):
            preco_cartao = row['PRECOCARTAO']
            if preco_cartao > 0:
                parcela = preco_cartao / 3
                return f"3x de R$ {parcela:.2f} no cartão"
            return 'Preço à vista'
            
        df_produtos['CONDICAOPAGAMENTO'] = df_produtos.apply(gerar_condicao_pagamento, axis=1)
    # --- Fim: Lidar com PRECOVISTA e PRECOCARTAO ---

    coluna_foto_encontrada = None
    nomes_possiveis_foto = ['FOTOURL', 'LINKIMAGEM', 'FOTO_URL', 'IMAGEM', 'URL_FOTO', 'LINK']
    for nome in nomes_possiveis_foto:
        if nome in df_produtos.columns:
            coluna_foto_encontrada = nome
            break
            
    if coluna_foto_encontrada:
        df_produtos.rename(columns={coluna_foto_encontrada: 'LINKIMAGEM'}, inplace=True, errors='ignore')
    else:
        st.warning("Nenhuma coluna de imagem encontrada (Ex: FOTOURL, IMAGEM). Os produtos serão exibidos sem fotos.")
        df_produtos['LINKIMAGEM'] = ""

    df_produtos.rename(columns={'MARCA': 'DESCRICAOCURTA'}, inplace=True, errors='ignore')

    if 'DISPONIVEL' not in df_produtos.columns:
        df_produtos['DISPONIVEL'] = 'SIM'
    if 'DESCRICAOLONGA' not in df_produtos.columns:
        df_produtos['DESCRICAOLONGA'] = df_produtos.get('CATEGORIA', '')

    df_produtos = df_produtos[df_produtos['DISPONIVEL'].astype(str).str.strip().str.lower() == 'sim'].copy()
    
    if 'CASHBACKPERCENT' not in df_produtos.columns:
        df_produtos['CASHBACKPERCENT'] = 0.0
    df_produtos['CASHBACKPERCENT'] = pd.to_numeric(df_produtos['CASHBACKPERCENT'], errors='coerce').fillna(0.0)
    
    if 'QUANTIDADE' in df_produtos.columns:
        df_produtos['QUANTIDADE'] = pd.to_numeric(df_produtos['QUANTIDADE'], errors='coerce').fillna(0)
    else:
        df_produtos['QUANTIDADE'] = 999999
    

    df_promocoes = carregar_promocoes()

    if not df_promocoes.empty:
        df_final = pd.merge(df_produtos.reset_index(), df_promocoes[['ID_PRODUTO', 'PRECO_PROMOCIONAL']], left_on='ID', right_on='ID_PRODUTO', how='left')
        df_final['PRECO_FINAL'] = df_final['PRECO_PROMOCIONAL'].fillna(df_final['PRECO']) 
        df_final.drop(columns=['ID_PRODUTO'], inplace=True, errors='ignore')
    else:
        df_final = df_produtos.reset_index()
        df_final['PRECO_FINAL'] = df_final['PRECO']
        df_final['PRECO_PROMOCIONAL'] = None

    df_videos = get_data_from_github(SHEET_NAME_VIDEOS_CSV)

    if df_videos is not None and not df_videos.empty:
        if 'ID_PRODUTO' in df_videos.columns and 'YOUTUBE_URL' in df_videos.columns:
            df_videos['ID_PRODUTO'] = pd.to_numeric(df_videos['ID_PRODUTO'], errors='coerce').astype('Int64')
            df_final = pd.merge(df_final, df_videos[['ID_PRODUTO', 'YOUTUBE_URL']], left_on='ID', right_on='ID_PRODUTO', how='left')
            df_final.drop(columns=['ID_PRODUTO_y'], inplace=True, errors='ignore')
            df_final.rename(columns={'ID_PRODUTO_x': 'ID_PRODUTO'}, inplace=True, errors='ignore')
        else:
            st.warning("Arquivo 'video.csv' encontrado, mas as colunas 'ID_PRODUTO' ou 'YOUTUBE_URL' estão faltando.")

    if 'CATEGORIA' not in df_final.columns:
         df_final['CATEGORIA'] = 'Geral'
         
    return df_final.set_index('ID')


@st.cache_data(ttl=None) 
def carregar_clientes_cashback():
    """Carrega os clientes do cashback, limpa o contato e renomeia as colunas para facilitar."""
    df = get_data_from_github(SHEET_NAME_CLIENTES_CASHBACK_CSV)
    
    if df is None or df.empty:
        return pd.DataFrame(columns=['NOME', 'CONTATO', 'CASHBACK_DISPONIVEL', 'NIVEL_ATUAL'])
        
    # --- NOVO BLOCO DE RENOMEAÇÃO SIMPLIFICADO ---
    # O código já transforma todas as colunas para MAIÚSCULAS e substitui ' ' por '_'
    # A coluna 'CONTATO' e 'NOME' JÁ EXISTEM com esses nomes.
    
    # Mapeamento para tratar CASHBACK_DISPONÍVEL (com acento) e APELIDO/DESCRIÇÃO
    df.rename(columns={
        'CASHBACK_DISPONÍVEL': 'CASHBACK_DISPONIVEL',
        'APELIDO/DESCRIÇÃO': 'APELIDO_DESCRICAO' # Renomeia a coluna que contém a barra
    }, inplace=True, errors='ignore')
    
    # ----------------------------------------------

    # Garante que as colunas essenciais estejam presentes (o cabeçalho do seu CSV garante isso)
    if 'CONTATO' in df.columns:
        # A limpeza de contato é essencial para a busca
        df['CONTATO'] = df['CONTATO'].astype(str).str.replace(r'\D', '', regex=True).str.strip() 
        df['CASHBACK_DISPONIVEL'] = pd.to_numeric(df['CASHBACK_DISPONIVEL'], errors='coerce').fillna(0.0)
        df['NIVEL_ATUAL'] = df['NIVEL_ATUAL'].fillna('Prata')
    
        # Garante que o DataFrame retornado tenha as colunas que o 'buscar_cliente_cashback' usa
        colunas_retorno = ['NOME', 'CONTATO', 'CASHBACK_DISPONIVEL', 'NIVEL_ATUAL']
        df = df.reindex(columns=colunas_retorno, fill_value='')
        
        return df.dropna(subset=['CONTATO'])
        
    else:
        # Este bloco só será atingido se a coluna 'CONTATO' sumir
        st.error("Erro: A coluna 'CONTATO' não foi encontrada após o processamento. Verifique o cabeçalho.")
        return pd.DataFrame(columns=['NOME', 'CONTATO', 'CASHBACK_DISPONIVEL', 'NIVEL_ATUAL'])


def buscar_cliente_cashback(numero_contato, df_clientes_cash):
    """Busca um cliente pelo número de contato (limpo) e retorna saldo e nível."""
    
    # Garante a mesma limpeza robusta de caracteres não numéricos.
    # Usando a mesma lógica da limpeza 'str.replace(r'\D', '', regex=True)'
    # Para um único string, podemos fazer manualmente:
    
    import re # É necessário importar 're'
    
    contato_limpo = str(numero_contato).strip()
    if contato_limpo:
        contato_limpo = re.sub(r'\D', '', contato_limpo)
        
    if df_clientes_cash.empty:
        return False, None, 0.00, 'NENHUM'
        
    # A comparação só funcionará se as limpezas forem idênticas!
    cliente = df_clientes_cash[df_clientes_cash['CONTATO'] == contato_limpo] 



def salvar_pedido(nome_cliente, contato_cliente, valor_total, itens_json, pedido_data):
    """Salva o novo pedido no 'pedidos.csv' do GitHub usando a Content API."""
    file_path = SHEET_NAME_PEDIDOS_CSV
    api_url = f"{GITHUB_BASE_API}{file_path}"

    novo_cabecalho = 'ID_PEDIDO,DATA_HORA,NOME_CLIENTE,CONTATO_CLIENTE,ITENS_PEDIDO,VALOR_TOTAL,LINKIMAGEM,STATUS,itens_json'

    headers_get = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.com.v3+json"
    }

    try:
        response_get = requests.get(f"{api_url}?ref={BRANCH}", headers=headers_get)
        response_get.raise_for_status()

        file_data = response_get.json()
        current_sha = file_data['sha']
        content_base64 = file_data.get('content', '')

        if not content_base64:
            current_content = novo_cabecalho
        else:
            current_content = base64.b64decode(content_base64).decode('utf-8')

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.info(f"Arquivo '{file_path}' não encontrado. Criando um novo.")
            current_sha = None
            current_content = novo_cabecalho
        else:
            st.error(f"Erro HTTP ao obter o SHA do arquivo no GitHub: {e}")
            return False, None # <--- PONTO DE ERRO CRÍTICO CORRIGIDO (non-404)
    except Exception as e:
        st.error(f"Erro na decodificação ou leitura do arquivo 'pedidos.csv'. Detalhe: {e}")
        return False, None # <--- PONTO DE ERRO CRÍTICO CORRIGIDO (decoding/other)

    # O pedido ID só é gerado se as requisições GET acima não retornarem False.
    timestamp = int(datetime.now().timestamp())
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    id_pedido = timestamp
    status = "PENDENTE"
    link_imagem = ""

    try:
        itens_data = json.loads(itens_json)
        resumo_itens = "; ".join([f"{i['quantidade']}x {i['nome']}" for i in itens_data.get('itens', [])])
    except Exception:
        resumo_itens = "Erro ao gerar resumo"

    escaped_itens_json = itens_json.replace('"', '""')

    novo_registro = (
        f'\n"{id_pedido}","{data_hora}","{nome_cliente}","{contato_cliente}",'
        f'"{resumo_itens}","{valor_total:.2f}","{link_imagem}","{status}","{escaped_itens_json}"'
    )

    if current_content.strip() and current_content.strip() != novo_cabecalho:
        new_content = current_content.strip() + novo_registro
    else:
        new_content = novo_cabecalho + novo_registro

    encoded_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')

    commit_data = {
        "message": f"PEDIDO: Novo pedido de {nome_cliente} - PENDENTE",
        "content": encoded_content,
        "branch": BRANCH
    }
    if current_sha:
        commit_data["sha"] = current_sha

    headers_put = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.com.v3+json"
    }

    try:
        response_put = requests.put(api_url, headers=headers_put, data=json.dumps(commit_data))
        response_put.raise_for_status()
        
        # PONTO DE SUCESSO
        pedido_data['id_pedido'] = id_pedido
        st.session_state.pedido_confirmado = pedido_data
        
        return True, id_pedido # <--- RETORNO DE SUCESSO CORRIGIDO
    
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro ao salvar o pedido (Commit no GitHub). Status {e.response.status_code}. "
                 f"Verifique as permissões 'repo' do seu PAT. Detalhe: {e.response.text}")
        return False, None # <--- RETORNO DE ERRO CORRIGIDO
    except Exception as e:
        st.error(f"Erro desconhecido ao enviar o pedido: {e}")
        return False, None # <--- RETORNO DE ERRO CORRIGIDO









