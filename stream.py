import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from st_aggrid import AgGrid, GridOptionsBuilder
from matplotlib.ticker import FuncFormatter
import datetime
from datetime import date
from io import BytesIO
from xlsxwriter import Workbook
import base64
st.set_page_config(layout="wide")

excel_file_path = 'base_empilhada_total.csv'


if 'acesso_permitido' not in st.session_state:
    st.session_state['acesso_permitido'] = False

# Se o acesso ainda não foi permitido, mostra a caixa de senha
if not st.session_state['acesso_permitido']:
    senha_usuario = st.text_input("Digite a senha para acessar o aplicativo:", type="password", key="senha")
    if senha_usuario:
        if senha_usuario == st.secrets["access_token"]:
            st.session_state['acesso_permitido'] = True
            st.experimental_rerun()
        else:
            st.stop()  # Impede que o resto do aplicativo seja executado
    else:
        st.stop()  # Impede que o resto do aplicativo seja executado se nenhuma senha for inserida

if st.session_state['acesso_permitido']:
    with st.container():
        # Definir o CSS para usar uma imagem de fundo
        def set_background(logo_path):
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{logo_path}");
                    background-size: cover;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
        
        # Converter a imagem para Base64 para que possa ser incluída diretamente no CSS
    
        def get_image_as_base64(path):
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        
        # Caminho para o arquivo da logo
        logo_path = 'nucleo.png'
        set_background(get_image_as_base64(logo_path))
    
    
        st.markdown("""
                <style>
                    div[role="radiogroup"] {
                        display: flex;
                        justify-content: left;
                        gap: 10px;
                    }
        
                    /* Estilizando os botões de rádio quando NÃO estão selecionados */
                    div[role="radiogroup"] label {
                        background-color: rgb(0, 32, 96); /* Azul Nucleo Capital */
                        color: white !important; /* Texto branco */
                        padding: 10px 21px;
                        border-radius: 8px;
                        font-weight: normal;
                        cursor: pointer;
                        transition: 0.3s;
                        text-align: center;
                        display: block; /* Faz com que toda a área seja clicável */
                        border: 2px solid transparent;
                    }
            
                    /* Quando o botão NÃO está selecionado */
                    div[role="radiogroup"] div {
                        color: white;
                    }
                        /* Força a cor branca no texto dentro do botão não selecionado */
                    div[role="radiogroup"] label span {
                        color: white !important; 
                    }
        
                    /* Quando o botão está selecionado */
                    div[role="radiogroup"] input:checked + div {
                        background-color: rgb(0, 32, 96);
                        color: white;
                        border: 2px solid rgb(0, 32, 96);
                        text-align: left;
                        cursor: pointer;
                    }
                </style>
            """, unsafe_allow_html=True)
        
        st.markdown("""
            <style>
                /* Estilizando todas as selectbox */
                div[data-baseweb="select"] {
                    background-color: rgb(189, 215, 238) !important; /* Fundo azul claro */
                    border-radius: 5px; /* Bordas arredondadas */
                    padding: 5px; /* Espaçamento interno */
                    font-family: Calibri, sans-serif !important; /* Define a fonte como Calibri */
                }
        
                /* Estilizando o menu dropdown que aparece ao clicar */
                div[data-baseweb="popover"] {
                    background-color: rgb(189, 215, 238) !important;
                    font-family: Calibri, sans-serif !important;
                }
        
                /* Estilizando o texto dentro da selectbox */
                div[data-baseweb="select"] div {
                    color: black !important; /* Texto preto */
                    font-weight: bold;
                    font-family: Calibri, sans-serif !important;
                }
        
                /* Estilizando a borda da selectbox */
                div[data-baseweb="select"] > div {
                    border: 2px solid rgb(0, 32, 96) !important; /* Azul Nucleo Capital */
                    font-family: Calibri, sans-serif !important;
                }
            </style>
        """, unsafe_allow_html=True)
    
        class TabelaPortfolioLucro:
            def __init__(self, df_empresa):
                # Converte a coluna 'DATA ATUALIZACAO' para datetime
                self.df_empresa = df_empresa
                self.df_empresa['DATA ATUALIZACAO'] = pd.to_datetime(self.df_empresa['DATA ATUALIZACAO'], format='%m/%d/%Y')
            
            def filtrar_datas(self):
                # Obtém datas únicas e ordena do menor para o maior
                datas = np.sort(self.df_empresa['DATA ATUALIZACAO'].dropna().unique())[::-1]
                # Formata as datas para o formato brasileiro
                datas_formatadas = pd.to_datetime(datas).strftime('%d/%m/%Y')
                return datas_formatadas
        
            def filtrar_por_data(self, data_selecionada):
                # Converte a data do formato brasileiro para datetime antes de filtrar
                data_selecionada = pd.to_datetime(data_selecionada, format='%d/%m/%Y')
                df_filtrado = self.df_empresa[self.df_empresa['DATA ATUALIZACAO'] == data_selecionada]
                return df_filtrado
        
            def criar_tabela_portfolio(self, df_filtrado):
                # Primeira tabela: "Portfolio"
                df_portfolio = df_filtrado[['Ticker', '% Portfolio', 'Mkt Cap']].drop_duplicates().reset_index(drop=True)
                df_portfolio.columns = ['Empresa', '% Portfólio', 'Mkt cap']
        
                # Certificando-se de que os valores são numéricos e tratando NaN
                df_portfolio['% Portfólio'] = pd.to_numeric(df_portfolio['% Portfólio'], errors='coerce').fillna(0)
                df_portfolio = df_portfolio.sort_values(by='% Portfólio', ascending=False).reset_index(drop=True)
                # Formatando os números
                df_portfolio['% Portfólio'] = df_portfolio['% Portfólio'].apply(lambda x: f"{x * 100:.1f}%")
                df_portfolio['Mkt cap'] = pd.to_numeric(df_portfolio['Mkt cap'], errors='coerce').fillna(0).apply(lambda x: f"{x:,.0f}")
                df_portfolio = df_portfolio.rename(columns={"% Portfólio": "%"})
                return df_portfolio
        
            def criar_tabela_lucro(self, df_filtrado, data_selecionada,empresas_ordenadas):
                # Segunda tabela: "Lucro" (mostra os 4 anos a partir da data filtrada)
                ano_inicial = pd.to_datetime(data_selecionada, format='%d/%m/%Y').year
                ano_inicial -= 1
                anos = [ano_inicial + i for i in range(4)]
                    
                df_lucro = pd.DataFrame(columns=['Empresa'] + anos)
                df_lucro_ap = pd.DataFrame(columns=['Empresa'] + anos[1:])
                empresas = df_filtrado['Ticker'].unique()
        
                for empresa in empresas_ordenadas:
                    linha = {'Empresa': empresa}
                    for i, ano in enumerate(anos):
                        lucro_ano = df_filtrado[(df_filtrado['Ticker'] == empresa) & (df_filtrado['Ano Referência'] == ano)]['Lucro líquido ajustado']
                        linha[ano] = lucro_ano.values[0] if not lucro_ano.empty else np.nan
                    df_lucro = df_lucro.append(linha, ignore_index=True)
                
                    linha_ap = {'Empresa': empresa}
                    for ano in anos[1:]:
                        linha_ap[ano] = linha.get(ano, np.nan)
                    df_lucro_ap = df_lucro_ap.append(linha_ap, ignore_index=True)
                        
                for ano in anos:
                    df_lucro[ano] = pd.to_numeric(df_lucro[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.0f}" if not pd.isna(x) else 'nan')

                for ano in anos[1:]:   
                    df_lucro_ap[ano] = pd.to_numeric(df_lucro_ap[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.0f}" if not pd.isna(x) else 'nan')
                return df_lucro, df_lucro_ap
        
            def calcular_earnings_growth(self, df_lucro, anos):
                df_growth = pd.DataFrame(columns=['Empresa'] + anos[1:])
                for _, row in df_lucro.iterrows():
                    empresa = row['Empresa']
                    crescimento = {'Empresa': empresa}
                    for i in range(1, len(anos)):
                        if row[anos[i - 1]] != 'nan' and row[anos[i]] != 'nan':
                            try:
                                crescimento[anos[i]] = (float(row[anos[i]].replace(',', '')) / float(row[anos[i - 1]].replace(',', '')) - 1) * 100
                            except ValueError:
                                crescimento[anos[i]] = 'nan'
                        else:
                            crescimento[anos[i]] = 'nan'
                    df_growth = df_growth.append(crescimento, ignore_index=True)
                for ano in anos[1:]:
                    df_growth[ano] = df_growth[ano].apply(lambda x: f"{x:.1f}%" if x != 'nan' else 'nan')
                return df_growth
                
            def df_evebtda(self, df_filtrado, data_selecionada, empresas_ordenadas):
                ano_atual = pd.to_datetime(data_selecionada).year
                anos = [ano_atual + i for i in range(0, 2)]           
                df_ev = pd.DataFrame(columns=['Empresa'] + anos)         
                       
                for empresa in empresas_ordenadas:
                    ev_ebtda = {'Empresa': empresa}
            
                    for ano in anos:
                        try:
                            valor = df_filtrado.loc[
                                (df_filtrado['Ticker'] == empresa) & 
                                (df_filtrado['Ano Referência'] == ano), 
                                'EV/EBITDA'
                            ].values[0].round(1)
                            if valor > 0:
                                ev_ebtda[ano] = f"{round(valor, 1)}x"
                            else:
                                ev_ebtda[ano] = "&nbsp;"  # Mantém o espaço sem conteúdo visível
    
                        except IndexError:
                            ev_ebtda[ano] = ""  
            
                    df_ev = pd.concat([df_ev, pd.DataFrame([ev_ebtda])], ignore_index=True)
            
                return df_ev
            
            def apresentar_pe(self, df_filtrado, data_selecionada, empresas_ordenadas):
                ano_atual = pd.to_datetime(data_selecionada).year
                anos = [ano_atual + i for i in range(0, 2)]           
                df_pe_calc = pd.DataFrame(columns=['Empresa'] + anos)         
                       
                for empresa in empresas_ordenadas:
                    pe_cal = {'Empresa': empresa}
            
                    for ano in anos:
                        try:
                            valor = df_filtrado.loc[
                                (df_filtrado['Ticker'] == empresa) & 
                                (df_filtrado['Ano Referência'] == ano), 
                                'P/E Calculado'
                            ].values[0].round(1)
                            pe_cal[ano] = f"{valor}x"
                        except IndexError:
                            pe_cal[ano] = ""  
            
                    df_pe_calc = pd.concat([df_pe_calc, pd.DataFrame([pe_cal])], ignore_index=True)
            
                return df_pe_calc
    
            def apresentar_scorecard(self, df_filtrado, data_selecionada, empresas_ordenadas):
                colunas = ["Negocios", "Pessoas"]           
                df_score = pd.DataFrame(columns=['Empresa'] + colunas)         
                       
                for empresa in empresas_ordenadas:
                    score_cards = {'Empresa': empresa}
            
                    for coluna in colunas:
                        try:
                            score_cards[coluna] = df_filtrado.loc[
                                (df_filtrado['Ticker'] == empresa), 
                                coluna
                            ].values[0].round(1)
                        except IndexError:
                            score_cards[coluna] = ""  
            
                    df_score = pd.concat([df_score, pd.DataFrame([score_cards])], ignore_index=True)
                df_score = df_score.rename(columns={'Negocios': 'Business', 'People': 'Price'})

                return df_score
    
            def df_pe(self, df_filtrado, data_selecionada, empresas_ordenadas):
                colunas = {
                    'P/E': '&nbsp;',
                }
            
                df_pe = []
            
                for empresa in empresas_ordenadas:
                    dados = df_filtrado[df_filtrado['Ticker'] == empresa].fillna(" ")
            
                    linha = {'Empresa': empresa}
                    for coluna_original, coluna_nova in colunas.items():
                        valor = dados[coluna_original].values[0]
            
                        if isinstance(valor, (int, float)):  # Apenas formata se for número
                            linha[coluna_nova] = f"{round(valor, 1)}x"
                        else:
                            linha[coluna_nova] = "&nbsp;"  # Mantém o espaço sem conteúdo visível
            
                    df_pe.append(linha)
            
                return pd.DataFrame(df_pe)
            
            def calcular_tir(self, df_filtrado, data_selecionada, empresas_ordenadas):
                colunas = {
                    'TIR Fluxos Perp. (Real)': 'IRR perp',
                    'Ke Saída (Real)': 'IRR out',
                    'IRR': 'IRR'
                }
            
                df_tir = []
            
                for empresa in empresas_ordenadas:
                    dados = df_filtrado[df_filtrado['Ticker'] == empresa].fillna("")
            
                    linha = {'Empresa': empresa}
                    for coluna_original, coluna_nova in colunas.items():
                        valor = dados[coluna_original].values[0]
            
                        if isinstance(valor, (int, float)):  # Apenas formata se for número
                            linha[coluna_nova] = f"{valor:,.1%}" 
                        else:
                            linha[coluna_nova] = ""  # Mantém vazio se não for número válido
            
                    # Ajuste específico para a coluna 'IRR'
                    tir = dados['IRR'].astype(str).values[0]  # Converte para string antes de checar
                    linha['IRR'] = f"{float(tir):.1%}" if tir.lstrip("-").replace(".", "").isdigit() and float(tir) != 0 else 'faltando dados'
            
                    df_tir.append(linha)
            
                return pd.DataFrame(df_tir)
                
                
            def calcular_media_ponderada_tir(self, df_tir, df_portfolio):
                # Remover linhas onde TIR é 'faltando dados'
                df_validas = df_tir[df_tir['IRR'] != 'faltando dados'].copy()
        
                # Converter a coluna de TIR de string percentual para float
                df_validas['IRR'] = df_validas['IRR'].str.rstrip('%').astype(float) / 100
                
                # Atribuir % Portfólio da primeira tabela (df_portfolio) às empresas válidas de TIR
                df_validas = df_validas.merge(df_portfolio[['Empresa', '%']], on='Empresa', how='left')
        
                # Converter % Portfólio para float
                df_validas['%'] = df_validas['%'].str.rstrip('%').astype(float) / 100
        
                # Calcular a média ponderada
                weighted_avg_tir = (df_validas['IRR'] * df_validas['%']).sum() / df_validas['%'].sum()
                if pd.isna(weighted_avg_tir):
                    return 0
        
                return weighted_avg_tir
        
            def gerar_html_tabela(self, df, titulo):
                html = '<table style="width:100%; border-collapse: collapse; margin: auto;">'
                html += '<thead><tr style="background-color: rgb(0, 32, 96); color: white;">'
                colspan = df.shape[1]
                html += f'<th colspan="{colspan}" style="border: 1px solid #ddd; padding: 8px; text-align: center;">{titulo}</th>'
                html += '</tr><tr>'
                colunas_listadas = df.columns
                html += '<tr style="background-color: rgb(0, 32, 96); color: white;">'
                for col in colunas_listadas:
                    html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">{col}</th>'
                html += '</tr></thead><tbody>'
                for i, row in df.iterrows():
                    bg_color = 'rgb(191, 191, 191)' if i % 2 == 0 else 'white'
                    html += f'<tr style="background-color: {bg_color}; color: black;">'
                    for col in df.columns:
                        html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: black;">{row[col]}</td>'
                    html += '</tr>'
    
                html += '</tbody></table>'
                return html
        
            def download_excel(self, dfs_dict):
                # Função para baixar todas as DataFrames em uma única aba de um arquivo Excel
                output = BytesIO()
            
                # Converter todas as colunas possíveis para float
                for df_name, df in dfs_dict.items():
                    # Seleciona apenas as colunas que podem ser convertidas para float
                    dfs_dict[df_name] = df.apply(pd.to_numeric, errors='ignore')
            
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Definindo a aba onde as DataFrames serão adicionadas
                    sheet_name = "Dados Consolidado"
                    
                    # Posição inicial da primeira DataFrame
                    start_col = 0
                    
                    for df_name, df in dfs_dict.items():
                        # Salvando a DataFrame no arquivo, na aba 'Dados Consolidado' e nas colunas ao lado
                        df.to_excel(writer, sheet_name=sheet_name, startcol=start_col, index=False)
                        # Atualizando a posição inicial da próxima DataFrame
                        start_col += df.shape[1] + 1  # +1 para uma coluna de espaço entre elas
            
                    writer.save()
            
                # Download do arquivo
                st.download_button(
                    label="Download all tables in Excel",
                    data=output.getvalue(),
                    file_name="tabelas_IRR_portfolio_lucro.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            def mostrar_tabelas(self):
                # Filtra os dados pela data selecionada
                df_filtrado = self.filtrar_por_data(data_selecionada)
                df_portfolio = self.criar_tabela_portfolio(df_filtrado)
                empresas_ordenadas = df_portfolio['Empresa'].tolist()
                # Exibir tabelas lado a lado
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.15, 1.15, 1, 0.7, 0.7, 0.5, 1, 0.7])
        
                # Tabela de Portfolio
                with col1:
                    df_portfolio = self.criar_tabela_portfolio(df_filtrado)
                    df_portfolio4 = df_portfolio.copy()
                    df_portfolio4 = df_portfolio4.rename(columns={"Empresa": "Company"})
                    html_portfolio = self.gerar_html_tabela(df_portfolio4, "Portfolio")
                    st.markdown(html_portfolio, unsafe_allow_html=True)
        
                # Tabela de Lucro
                with col2:
                    df_lucro, df_lucro_ap  = self.criar_tabela_lucro(df_filtrado, data_selecionada,empresas_ordenadas)
                    df_lucro2 = df_lucro_ap.copy()
                    df_lucro2 = df_lucro2.drop(columns=['Empresa'])
                    html_lucro = self.gerar_html_tabela(df_lucro2, "Net Income Estimated")
                    st.markdown(html_lucro, unsafe_allow_html=True)
        
                # Tabela de earnings growth
                with col3:
                    anos = list(df_lucro.columns[1:])
                    df_growth = self.calcular_earnings_growth(df_lucro, anos)
                    df_growth = df_growth.drop(columns=['Empresa'])
                    st.markdown(self.gerar_html_tabela(df_growth, "Earnings growth"), unsafe_allow_html=True)
        
                # Tabela de P/E Calculado
                with col4:
                    df_pe = self.apresentar_pe(df_filtrado, data_selecionada, empresas_ordenadas)
                    df_pe2 = df_pe.copy()
                    df_pe2 = df_pe2.drop(columns=['Empresa'])
                    html_pe = self.gerar_html_tabela(df_pe2, "P/E")
                    st.markdown(html_pe, unsafe_allow_html=True)

                # Tabela EVEBITDA
                with col5:
                    df_ev = self.df_evebtda(df_filtrado, data_selecionada, empresas_ordenadas)
                    df_ev2 = df_ev.copy()
                    df_ev2 = df_ev2.drop(columns=['Empresa'])
                    html_pee = self.gerar_html_tabela(df_ev2, "EV/EBITDA")
                    st.markdown(html_pee, unsafe_allow_html=True)               

                
                # Tabela de Exit P/E
                with col6:
                    df_pee = self.df_pe(df_filtrado, data_selecionada, empresas_ordenadas)
                    df_pee2 = df_pee.copy()
                    df_pee2 = df_pee2.drop(columns=['Empresa'])
                    html_pee = self.gerar_html_tabela(df_pee2, "Exit P/E")
                    st.markdown(html_pee, unsafe_allow_html=True)
                    
    
                # Tabela de TIR
                with col7:
                    df_tir = self.calcular_tir(df_filtrado, data_selecionada, empresas_ordenadas)
                    df_tir2 = df_tir.copy()
                    df_tir2 = df_tir2.drop(columns=['Empresa'])
                    html_tir = self.gerar_html_tabela(df_tir2, "IRR")
                    st.markdown(html_tir, unsafe_allow_html=True)
                    
                # Tabela de Scorecards
                with col8:
                    df_score = self.apresentar_scorecard(df_filtrado, data_selecionada, empresas_ordenadas)
                    df_score2 = df_score.copy()
                    df_score2 = df_score2.drop(columns=['Empresa'])
                    html_score = self.gerar_html_tabela(df_score2, "Scorecard Quali")
                    st.markdown(html_score, unsafe_allow_html=True)
    
                
                st.markdown("<br>", unsafe_allow_html=True)  # Cria espaço extra entre os componentes
        
                # **Cálculo da média ponderada da TIR**
                media_ponderada_tir = self.calcular_media_ponderada_tir(df_tir, df_portfolio)
        
                # Exibir a média ponderada da TIR em formato de texto
                col11, col9, col10, col12 , col13, col14= st.columns([1, 1, 1, 1, 1, 1])
                with col9:
                    st.markdown("<h3 style='text-align: right; font-size:24px;'>Portfolio average IRR</h3>", unsafe_allow_html=True)  # Fonte menor ajustada
                with col10:
                    st.markdown(
                        f"""
                        <div style="background-color: rgb(0, 32, 96); color: white; padding: 10px; border-radius: 5px; text-align: center; font-size: 20px;">
                            {media_ponderada_tir:.1%}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                with col11:
                    # Exportar todas as tabelas em um arquivo Excel com abas separadas
                    dfs_dict = {
                        "Portfolio": df_portfolio,
                        "Lucro": df_lucro2,
                        "Earnings growth": df_growth,
                        "P/E e IRR": df_tir
                    }
                    self.download_excel(dfs_dict)
    
        df_empresa = pd.read_csv(excel_file_path)  # Substitua com o caminho correto no seu ambiente
        df_nubi = pd.read_excel('tabela_clust_irr.xlsx')
        tabela = TabelaPortfolioLucro(df_empresa)
        
        class TabelaRetornoNubi:
            def __init__(self, df_nubi):
                # Lê o arquivo
                self.df_empresa = df_nubi
                self.df_empresa['Prioridade'] = self.df_empresa['Prioridade'].fillna('Sem prioridade')
                self.df_empresa['date'] = pd.to_datetime(self.df_empresa['date']).dt.date  # Converte a coluna de data

            def filtrar_datas(self):
                datas = np.sort(self.df_empresa['date'].dropna().unique())[::-1]
                datas_formatadas = pd.to_datetime(datas).strftime('%d/%m/%Y')
                return datas_formatadas
        
            def filtrar_por_data(self, data_selecionada):
                data_selecionada = pd.to_datetime(data_selecionada, format='%d/%m/%Y')
                df_filtrado = self.df_empresa[self.df_empresa['date'] == data_selecionada]
                return df_filtrado

       
            def gerar_html_tabela(self, df, titulo):
                df = df.reset_index(drop=True)
                html = '<table style="width:100%; border-collapse: collapse; margin: auto;">'
                html += '<thead><tr style="background-color: rgb(0, 32, 96); color: white;">'
                colspan = df.shape[1]
                html += f'<th colspan="{colspan}" style="border: 1px solid #ddd; padding: 8px; text-align: center;">{titulo}</th>'
                html += '</tr><tr style="background-color: rgb(0, 32, 96); color: white;">'
                for col in df.columns:
                    html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">{col}</th>'
                html += '</tr></thead><tbody>'

                for i, row in df.iterrows():
                    bg_color = 'rgb(191, 191, 191)' if i % 2 == 0 else 'white'
                    html += f'<tr style="background-color: {bg_color}; color: black;">'
                    for col in df.columns:
                        html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{row[col]}</td>'
                    html += '</tr>'

                html += '</tbody></table>'
                return html

            def mostrar_tabela(self):
                # --- Filtro de Data ---
                df_filtrado = self.filtrar_por_data(data_selecionada)
                col20, co21, col22, col23 = st.columns([0.5, 3.5, 0.5, 0.5])
    
                with col20:
                    prioridades = df_filtrado['Prioridade'].unique()
                    prioridade_selecionada = st.selectbox('Select the status:', prioridades)                

                # --- Filtro de Prioridade ---
                df_filtrado = df_filtrado[df_filtrado['Prioridade'] == prioridade_selecionada]

                # --- Montar tabela final ---
                df_final = df_filtrado.rename(columns={
                    'TICKER': 'Company',
                    'price': 'Price',
                    'Year To Date': 'YTD',
                    'Retorno 3 meses': '3-month return',
                    'Retorno 6 meses': '6-month return'
                })

                colunas_exibir = ["Company", "Price", "YTD", "3-month return", "6-month return"]
                df_final = df_final[colunas_exibir]

                # --- Formatação numérica ---
                for col in ["Price", "YTD", "3-month return", "6-month return"]:
                    df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
                    if col == 'Price':
                        df_final[col] = df_final[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
                    else:
                        df_final[col] = df_final[col].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "")

                # --- Renderiza HTML ---
                html = self.gerar_html_tabela(df_final, "Nubi Companies")
                st.markdown(html, unsafe_allow_html=True)

        class lucroconsenso:
            def __init__(self, df_empresa):
                # Converte a coluna 'DATA ATUALIZACAO' para datetime
                self.df_empresa = df_empresa
                self.df_empresa['DATA ATUALIZACAO'] = pd.to_datetime(self.df_empresa['DATA ATUALIZACAO'], format='%m/%d/%Y')
                self.lista_empresas =  None
        
            def filtrar_datas(self):
                datas = np.sort(self.df_empresa['DATA ATUALIZACAO'].dropna().unique())[::-1]
                datas_formatadas = pd.to_datetime(datas).strftime('%d/%m/%Y')
                return datas_formatadas
        
            def filtrar_por_data(self, data_selecionada):
                data_selecionada = pd.to_datetime(data_selecionada, format='%d/%m/%Y')
                df_filtrado = self.df_empresa[self.df_empresa['DATA ATUALIZACAO'] == data_selecionada]
                return df_filtrado
        
            def criar_tabela_portfolio(self, df_filtrado, check):        
                df_portfolio = df_filtrado[['Ticker', '% Portfolio']].drop_duplicates().reset_index(drop=True)   
                df_portfolio['% Portfolio'] = pd.to_numeric(df_portfolio['% Portfolio'], errors='coerce').fillna(0)
                df_portfolio = df_portfolio.sort_values(by='% Portfolio', ascending=False).reset_index(drop=True)
                df_portfolio['%'] = df_portfolio['% Portfolio'].apply(lambda x: f"{x * 100:.1f}%")
                df_portfolio = df_portfolio.rename(columns={'Ticker': 'Company'})
    
                # Aplica o * em vermelho se for o caso
                if check == "x":
                    df_portfolio['Company'] = df_portfolio['Company'].apply(
                        lambda x: f"<span style='color:red'>{x}*</span>" if x in self.lista_empresas else x
                    )
                df_portfolio = df_portfolio[['Company', '%']]
                return df_portfolio
        
            def criar_lucro_nucleo(self, df_filtrado, data_selecionada,empresas_ordenadas):
                ano_inicial = pd.to_datetime(data_selecionada, format='%d/%m/%Y').year
                anos = [ano_inicial + i for i in range(2)]
                df_lucro = pd.DataFrame(columns=['Empresa'] + anos)
                for empresa in empresas_ordenadas:
                    linha = {'Empresa': empresa}
                    for i, ano in enumerate(anos):
                        coluna_lucro = 'EBITDA ajustado' if empresa in self.lista_empresas else 'Lucro líquido ajustado'
                        lucro_ano = df_filtrado[(df_filtrado['Ticker'] == empresa) & (df_filtrado['Ano Referência'] == ano)][coluna_lucro]
                        linha[ano] = lucro_ano.values[0] if not lucro_ano.empty else np.nan
                    df_lucro = pd.concat([df_lucro, pd.DataFrame([linha])], ignore_index=True)
        
        
                # Formatando os números no estilo americano
                for ano in anos:
                    df_lucro[ano] = pd.to_numeric(df_lucro[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.0f}" if not pd.isna(x) else 'nan')
                return df_lucro, anos
        
            def criar_lucro_consenso(self, df_filtrado, data_selecionada,empresas_ordenadas):
                ano_inicial = pd.to_datetime(data_selecionada, format='%d/%m/%Y').year
                anos = [ano_inicial + i for i in range(2)]
                df_lucro = pd.DataFrame(columns=['Empresa'] + anos)
                for empresa in empresas_ordenadas:
                    linha = {'Empresa': empresa}
                    for i, ano in enumerate(anos):
                        lucro_ano = df_filtrado[(df_filtrado['Ticker'] == empresa) & (df_filtrado['Ano Referência'] == ano)]['Lucro Consenso']
                        linha[ano] = lucro_ano.values[0] if not lucro_ano.empty else np.nan
                    df_lucro = pd.concat([df_lucro, pd.DataFrame([linha])], ignore_index=True)
        
                # Formatando os números no estilo americano
                for ano in anos:
                    df_lucro[ano] = pd.to_numeric(df_lucro[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.0f}" if x != 0 else "-")
    
                return df_lucro
        
            def nucleo_vs_consenso(self, df_lucro, df_lucro2, anos):
                df_lucro[anos] = df_lucro[anos].replace(',', '', regex=True).apply(pd.to_numeric, errors='coerce')
                df_lucro2[anos] = df_lucro2[anos].replace(',', '', regex=True).apply(pd.to_numeric, errors='coerce')
                # Criar a DataFrame final com a coluna 'Empresa'
                df_growth = pd.DataFrame({'Empresa': df_lucro['Empresa']})       
                # Loop pelos anos para calcular a diferença percentual
                for ano in anos:
                    df_growth[ano] = (df_lucro[ano] / df_lucro2[ano] - 1) * 100  # Cálculo da variação em %
                    # Tratar divisão por zero e valores NaN
                    df_growth[ano] = df_growth[ano].replace([float('inf'), -float('inf')], 0)  # Substituir infinitos por 0
                    df_growth[ano] = df_growth[ano].fillna(0)  # Substituir NaN por 0
                    # Converter para string formatada em %
                    df_growth[ano] = df_growth[ano].apply(lambda x: f"{x:.1f}%" if x != 0 else "-")
        
                return df_growth
        
            def gerar_html_tabela(self, df, titulo):
                html = '<table style="width:100%; border-collapse: collapse; margin: auto;">'
                html += '<thead><tr style="background-color: rgb(0, 32, 96); color: white;">'
                colspan = df.shape[1]
                html += f'<th colspan="{colspan}" style="border: 1px solid #ddd; padding: 8px; text-align: center;">{titulo}</th>'
                html += '</tr><tr style="background-color: rgb(0, 32, 96); color: white;">'
                for col in df.columns:
                    html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">{col}</th>'
                html += '</tr></thead><tbody>'
                for i, row in df.iterrows():
                    bg_color = 'rgb(191, 191, 191)' if i % 2 == 0 else 'white'
                    html += f'<tr style="background-color: {bg_color}; color: black;">'
                    for col in df.columns:
                        html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{row[col]}</td>'
                    html += '</tr>'
                html += '</tbody></table>'
                return html
    
        
            def mostrar_tabelas(self):
       
                # Mensagem de observação
                st.markdown("<p style='color:red; font-size:24px; text-align:left'>The companies marked with an asterisk (*) are using EBITDA in the table below.</p>", unsafe_allow_html=True)
                # Filtra os dados pela data selecionada
                df_filtrado = self.filtrar_por_data(data_selecionada)
                self.lista_empresas = (
                    df_filtrado[df_filtrado["P/E"].isna()]["Ticker"]
                    .drop_duplicates()
                    .tolist()
                )
                df_portfolio = self.criar_tabela_portfolio(df_filtrado, "y")
                empresas_ordenadas = df_portfolio['Company'].tolist()
                # Exibir tabelas lado a lado
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
                # Tabela de Portfolio
                with col1:
                    df_portfolio = self.criar_tabela_portfolio(df_filtrado, "x")                    
                    html_portfolio = self.gerar_html_tabela(df_portfolio, "Portfolio")
                    st.markdown(html_portfolio, unsafe_allow_html=True)
        
                # Tabela de Lucro
                with col2:
                    df_lucro, anos = self.criar_lucro_nucleo(df_filtrado, data_selecionada,empresas_ordenadas)
                    df_lucro2 = df_lucro.copy()
                    df_lucro2 = df_lucro2.drop(columns=['Empresa'])
                    html_lucro = self.gerar_html_tabela(df_lucro2, "Earnings (Nucleo Projection)")
                    st.markdown(html_lucro, unsafe_allow_html=True)
        
                # Tabela de earnings growth
                with col3:
                    df_lucro3 = self.criar_lucro_consenso(df_filtrado, data_selecionada,empresas_ordenadas)
                    df_lucro4 = df_lucro3.copy()
                    df_lucro4 = df_lucro4.drop(columns=['Empresa'])
                    html_lucro = self.gerar_html_tabela(df_lucro4, "Consensus Earnings")
                    st.markdown(html_lucro, unsafe_allow_html=True)
        
                # Tabela de P/E Calculado
                with col4:
                    df_growth = self.nucleo_vs_consenso(df_lucro, df_lucro4, anos)
                    df_growth = df_growth.drop(columns=['Empresa'])
                    st.markdown(self.gerar_html_tabela(df_growth, "Nucleo VS Consensus"), unsafe_allow_html=True)
                   # Uso da classe no Streamlit
    
        class TabelaAnaliticaProjecoes:
            def __init__(self, df_empresa):
                self.df_empresa = df_empresa
                self.df_empresa['DATA ATUALIZACAO'] = pd.to_datetime(self.df_empresa['DATA ATUALIZACAO'], format='%m/%d/%Y')
                self.variaveis = [
                    "Lucro líquido ajustado", "Receita líquida", "EBITDA ajustado", "Dividendos", "% Portfolio"
                ]  # Adicione mais variáveis se necessário
            
            def filtrar_datas_disponiveis(self):
                datas = np.sort(self.df_empresa['DATA ATUALIZACAO'].dropna().unique())[::-1]
                return pd.to_datetime(datas).strftime('%d/%m/%Y')
            
            def obter_tabela_projecoes(self, data_selecionada, variavel):
                data_selecionada = pd.to_datetime(data_selecionada, format='%d/%m/%Y')
                datas_disponiveis = np.sort(self.df_empresa['DATA ATUALIZACAO'].unique())[::-1]
                
                quintas = []
                i = 0
                while len(quintas) < 4 and i < 30:  # Limite para não fazer loop infinito
                    data_tentativa = (data_selecionada - pd.DateOffset(weeks=i)).normalize()
                    quinta_tentativa = data_tentativa - pd.DateOffset(days=(data_tentativa.weekday() - 3) % 7)  # 3 = quinta-feira
                    quinta_tentativa = quinta_tentativa.normalize()
                    
                    # Tenta usar a quinta-feira, senão usa o dia útil anterior disponível
                    if quinta_tentativa in datas_disponiveis and quinta_tentativa not in quintas:
                        quintas.append(quinta_tentativa)
                    else:
                        dias_uteis_anteriores = datas_disponiveis[datas_disponiveis < quinta_tentativa]
                        if len(dias_uteis_anteriores) > 0:
                            ultima_data_util = dias_uteis_anteriores[0]
                            if ultima_data_util not in quintas:
                                quintas.append(ultima_data_util)
                  
                    i += 1
            
                if len(quintas) < 4:
                    st.warning("Não há dados suficientes para exibir 4 quintas-feiras anteriores.")
                    return pd.DataFrame()
            
                datas_recentes = sorted(quintas)
                
                ano_inicial = data_selecionada.year
                anos = [ano_inicial + i for i in range(3)]
                colunas = ['Company']
                datas_formatadas = [pd.to_datetime(data).strftime('%d-%b-%y') for data in datas_recentes]
                
                for data in datas_formatadas:
                    if variavel == "% Portfolio":
                        colunas.append(f"{data}")
                    else:
                        for ano in anos:
                            colunas.append(f"{data} - {ano}")
                
                df_tabela = pd.DataFrame(columns=colunas)
                df_filtrado = df_empresa[df_empresa['DATA ATUALIZACAO'].isin(datas_recentes)]
                empresas = df_filtrado['Ticker'].unique()
                
                for empresa in empresas:
                    linha = {'Company': empresa}
                    for i, data in enumerate(datas_recentes):
                        if variavel == "% Portfolio":
                            valor = self.df_empresa[(self.df_empresa['Ticker'] == empresa) & (self.df_empresa['DATA ATUALIZACAO'] == data)][variavel]
                            linha[f"{datas_formatadas[i]}"] = valor.values[0] if not valor.empty else np.nan
                        else:
                            for ano in anos:
                                valor = self.df_empresa[(self.df_empresa['Ticker'] == empresa) & (self.df_empresa['DATA ATUALIZACAO'] == data) & (self.df_empresa['Ano Referência'] == ano)][variavel]
                                linha[f"{datas_formatadas[i]} - {ano}"] = valor.values[0] if not valor.empty else np.nan
                  
                    df_tabela = pd.concat([df_tabela, pd.DataFrame([linha])], ignore_index=True)

                for col in df_tabela.columns[1:]:
                    if variavel == "% Portfolio":
                        df_tabela[col] = pd.to_numeric(df_tabela[col], errors='coerce').fillna(0).apply(lambda x: f"{x:.1%}")
                    else:
                        df_tabela[col] = pd.to_numeric(df_tabela[col], errors='coerce').fillna(0).apply(lambda x: f"{x:,.0f}")
                if variavel == "% Portfolio":
                    return df_tabela, datas_formatadas
                else:
                    return df_tabela, datas_formatadas, anos
            
            def gerar_html_tabela(self, df, titulo, datas_formatadas, anos, variavel):
                html = f"<h3 style='color: black;'>{titulo}</h3>"
                html += '<table style="width:100%; border-collapse: collapse; margin: auto;">'
                
                # Criar cabeçalhos mesclados
                html += '<thead>'
                html += '<tr style="background-color: rgb(0, 32, 96); color: white;">'
                
                if variavel == "% Portfolio":
                    html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Company</th>'
                    for data in datas_formatadas:
                        html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">{data}</th>'
                    html += '</tr>'
                    html += '</thead><tbody>'
                    
                    for i, row in df.iterrows():
                        bg_color = 'rgb(191, 191, 191)' if i % 2 == 0 else 'white'
                        html += f'<tr style="background-color: {bg_color}; color: black;">'
                        for j, col in enumerate(df.columns):
                            cell_color = ""
                            if j > 1:  # Evita a primeira coluna (nomes das empresas)
                                prev_col = df.columns[j - 1] if j - 1 >= 1 else None  # Comparação com a mesma empresa na semana anterior
                                if prev_col:
                                    valor_atual = df.at[i, col]
                                    valor_anterior = df.at[i, prev_col]
                                    valor_atual = float(str(valor_atual).replace(",", "").replace("%", "").strip()) / 100  
                                    valor_anterior = float(str(valor_anterior).replace(",", "").replace("%", "").strip()) / 100
     
                                    # Verifica se os valores são numéricos e a diferença é maior que 0.3%
                                    if isinstance(valor_atual, (int, float)) and isinstance(valor_anterior, (int, float)):
                                        if abs(valor_atual - valor_anterior) > 0.003:
                                            cell_color = "background-color: yellow;"
                                        
                            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: black; {cell_color}">{row[col]}</td>'
                        html += '</tr>'        
                else:   
                    html += '<th rowspan="2" style="border: 1px solid #ddd; padding: 8px; text-align: center;">Company</th>'
                    for data in datas_formatadas:
                        html += f'<th colspan="3" style="border: 1px solid #ddd; padding: 8px; text-align: center;">{data}</th>'
                    html += '</tr>'
                    
                    html += '<tr style="background-color: rgb(0, 32, 96); color: white;">'
                    for _ in datas_formatadas:
                        for ano in anos:
                            html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">{ano}</th>'
                    html += '</tr>'
                    html += '</thead><tbody>'
                    
                    for i, row in df.iterrows():
                        bg_color = 'rgb(191, 191, 191)' if i % 2 == 0 else 'white'
                        html += f'<tr style="background-color: {bg_color}; color: black;">'
                        for j, col in enumerate(df.columns):
                            cell_color = ""
                            if j > 1:  # Evita a primeira coluna (nomes das empresas)
                                prev_col = df.columns[j - 3] if j - 3 >= 1 else None  # Comparação com a mesma empresa na semana anterior
                                if prev_col:
                                    valor_atual = df.at[i, col]
                                    valor_anterior = df.at[i, prev_col]
                                    valor_atual = float(str(valor_atual).replace(",", "."))
                                    valor_anterior = float(str(valor_anterior).replace(",", "."))
                                    if valor_anterior == 0 and valor_atual == 0:
                                        pass  # Ambos são zero, então não precisa pintar
                                    elif valor_anterior == 0 or valor_atual == 0:
                                        cell_color = "background-color: yellow;"  # Mudança brusca para ou de zero
                                    else:
                                        variacao = abs((valor_atual / valor_anterior) - 1)
                                        if variacao > 0.05:  # Mudança maior que 5%
                                            cell_color = "background-color: yellow;"
                                           
                            html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: black; {cell_color}">{row[col]}</td>'
                        html += '</tr>'
                
                html += '</tbody></table>'
                return html
            
            def mostrar_tabela_projecoes(self):
                st.markdown("<h1 style='text-align: center; margin-top: -50px;color: black;'></h1>", unsafe_allow_html=True)
                # Layout das seleções usando colunas para alinhamento
                col1, co21, col22, col23 = st.columns([0.7, 3.3, 0.5, 0.5])
    
                with col1:
                    variavel_selecionada = st.selectbox('Select the variable:', self.variaveis)
                
                if data_selecionada and variavel_selecionada:
                    if variavel_selecionada == "% Portfolio":
                        df_projecoes, datas_formatadas = self.obter_tabela_projecoes(data_selecionada, variavel_selecionada)
                        if not df_projecoes.empty:
                            anos = None
                            html_tabela = self.gerar_html_tabela(df_projecoes, "", datas_formatadas, anos, variavel_selecionada)
                            st.markdown(html_tabela, unsafe_allow_html=True)
                    else:
                        df_projecoes, datas_formatadas, anos = self.obter_tabela_projecoes(data_selecionada, variavel_selecionada)
                        if not df_projecoes.empty:
                            variavel_ = None
                            html_tabela = self.gerar_html_tabela(df_projecoes, "", datas_formatadas, anos, variavel_)
                            st.markdown(html_tabela, unsafe_allow_html=True)


        if 'graphs2' not in st.session_state:
            st.session_state.graphs2 = "IRR Portfolio Table"
        
        col20, co21, col22, col23 = st.columns([0.5, 3.5, 0.5, 0.5])
        
        with col20:
            datas_disponiveis = tabela.filtrar_datas()
            data_selecionada = st.selectbox('Select update date:', datas_disponiveis, key="selectbox_data")
        
        with co21:
            # ✅ NÃO atribui ao session_state de novo aqui
            graphs2 = st.radio( "", ["IRR Portfolio Table", "Nucleo VS Consensus", "Historical Projections","Nubi Companies Returns"], horizontal=True, key="graphs2" )
        
        # ✅ Usa a variável graphs2 para verificar a escolha
        if graphs2 == "IRR Portfolio Table":
            tabela.mostrar_tabelas()
        
        elif graphs2 == "Nucleo VS Consensus":
            consenso = lucroconsenso(df_empresa)
            consenso.mostrar_tabelas()
    
        if graphs2 == "Historical Projections":
            tabela_projecoes = TabelaAnaliticaProjecoes(df_empresa)
            tabela_projecoes.mostrar_tabela_projecoes()

        if graphs2 == "Nubi Companies Returns":
            tabela_nubi = TabelaRetornoNubi(df_nubi)
            tabela_nubi.mostrar_tabela()
        
        st.markdown("<br><br>", unsafe_allow_html=True)  # Cria espaço extra entre os componentes
        
        # Customizando o estilo dos botões
        st.markdown("""
            <style>
                div[role="radiogroup"] {
                    display: flex;
                    justify-content: left;
                    gap: 10px;
                }
    
                /* Estilizando os botões de rádio quando NÃO estão selecionados */
                div[role="radiogroup"] label {
                    background-color: rgb(0, 32, 96); /* Azul Nucleo Capital */
                    color: white !important; /* Texto branco */
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: normal;
                    cursor: pointer;
                    transition: 0.3s;
                    text-align: center;
                    border: 2px solid transparent;
                }
        
                /* Quando o botão NÃO está selecionado */
                div[role="radiogroup"] div {
                    color: white;
                }
                    /* Força a cor branca no texto dentro do botão não selecionado */
                div[role="radiogroup"] label span {
                    color: white !important; 
                }
    
                /* Quando o botão está selecionado */
                div[role="radiogroup"] input:checked + div {
                    background-color: rgb(0, 32, 96);
                    color: white;
                    border: 2px solid rgb(0, 32, 96);
                    text-align: left;
                }
            </style>
        """, unsafe_allow_html=True)
        # Criando um radio com opções lado a lado dentro de colunas
        col1, col2, col3  = st.columns([1, 1, 1])
        
        with col1:
            # Criando um radio estilizado
            graphs = st.radio(
                "",
                ["Model Projections Analysis", "Nucleo Capital Weighted Average IRR"],
                horizontal=True  # Exibe os botões lado a lado
            )
    
        
        # Exibir o gráfico correspondente
        if graphs == "Model Projections Analysis":
            class EmpresaAnalysis:
                def __init__(self):
                    self.df_mkt = pd.read_csv(excel_file_path, parse_dates=['DATA ATUALIZACAO'])  # Carregar com a data já formatada
                    self.colunas = ["Ativo permanente", "Capex", "Capital de giro", "Capital investido (medio)", 
                                    "Despesas operacionais", "Dívida Líquida", "Dividendos", "EBIT ajustado", 
                                    "EBITDA ajustado", "FCFE", "Lucro bruto", "Lucro líquido ajustado", 
                                    "Net debt/EBITDA", "Patrimônio líquido", "Receita líquida", "Resultado financeiro", "CDI", "P/E", "IRR"]
                    self.empresas = np.sort(self.df_mkt['Ticker'].dropna().unique())
        
                def filtrar_variaveis(self, empresa):
                    df_empresa = self.df_mkt[self.df_mkt['Ticker'] == empresa]
                    variaveis_disponiveis = [col for col in self.colunas if df_empresa[col].notna().any()]
                    return variaveis_disponiveis
                
                def filtrar_anos(self, empresa, variavel):
                    df_empresa = self.df_mkt[(self.df_mkt['Ticker'] == empresa) & (self.df_mkt[variavel].notna())]
                    return df_empresa['Ano Referência'].dropna().unique()
                
                def filtrar_datas(self, empresa, variavel, ano):
                    df_empresa = self.df_mkt[(self.df_mkt['Ticker'] == empresa) & (self.df_mkt['Ano Referência'] == ano) &(self.df_mkt[variavel].notna())]
                    datas = np.sort(df_empresa['DATA ATUALIZACAO'].dropna().unique())
                    return datas
        
                def gerar_grafico(self, empresa, variavel, ano_ref, data_de, data_ate):
                    df_filtrado = self.df_mkt[
                        (self.df_mkt['Ticker'] == empresa) & 
                        (self.df_mkt['Ano Referência'] == ano_ref) & 
                        (self.df_mkt['DATA ATUALIZACAO'] >= data_de) & 
                        (self.df_mkt['DATA ATUALIZACAO'] <= data_ate)
                    ]
                    
                    df_filtrado = df_filtrado.dropna(subset=[variavel])
                    if df_filtrado.empty:
                        st.warning(f"Não possuímos dados de {variavel} nessas datas.")
                        return None, None, None
                    # Ajuste de escala para evitar notação científica no eixo Y
                    df_filtrado[variavel] = df_filtrado[variavel].astype(str).str.replace(',', '')
                    df_filtrado[variavel] = pd.to_numeric(df_filtrado[variavel], errors='coerce')
                    
                    # Calculando os limites do eixo Y com base em 40% de folga
                    min_val = df_filtrado[variavel].min()
                    max_val = df_filtrado[variavel].max()
                    y_folga = 0.4 * (max_val - min_val)
                
                    # Calculando os limites do eixo X (datas) com folga
                    data_inicio = pd.to_datetime(df_filtrado['DATA ATUALIZACAO'].min())
                    data_fim = pd.to_datetime(df_filtrado['DATA ATUALIZACAO'].max())
                    x_folga = pd.Timedelta(days=2)  # Adicionando 2 dias de folga nas extremidades
                
                    # Cria o gráfico com o primeiro eixo Y (a variável principal)
                    fig, ax1 = plt.subplots(figsize=(10, 4.2))
                    ax1.plot(pd.to_datetime(df_filtrado['DATA ATUALIZACAO']), df_filtrado[variavel], marker='o', color='tab:blue', markersize=8)
                    ax1.set_title(f"{empresa} - {variavel} from {data_de.strftime('%d/%m/%Y')} to {data_ate.strftime('%d/%m/%Y')}", fontsize=7)
                    ax1.set_xlabel("Data", fontsize=5)
                    ax1.set_ylabel(variavel, fontsize=5)
                    ax1.tick_params(axis='x', labelsize=5)
                    ax1.tick_params(axis='y', labelsize=5)
                    ax1.set_xlim([data_inicio - x_folga, data_fim + x_folga])
                    ax1.set_ylim([min_val - y_folga, max_val + y_folga])
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
                    fig.autofmt_xdate()
                    ax1.grid(True)
                    
                    if variavel in {"CDI", "IRR"}:             
                        def formatar_percentual(x, pos):
                            return f'{x * 100:.1f}%'  # Multiplica por 100 para mostrar como percentual corretamente
                        ax1.yaxis.set_major_formatter(FuncFormatter(formatar_percentual))
                    
                    return fig, df_filtrado, self.df_mkt
            # Instancia a classe de análise
            analysis = EmpresaAnalysis()
            
            # Layout das seleções usando colunas para alinhamento
            col1, col3, col2, col4, col5 = st.columns([1, 1, 1, 1, 1])  # Adicionando col6 para os radio buttons
            
            # Dropdown para selecionar empresa (Ticker) no lado esquerdo
            with col1:
                empresa_selecionada = st.selectbox('Ticker', analysis.empresas)
            
            if empresa_selecionada:
                    
                # Inicializa o session_state se ainda não existir
                if "variavel_selecionada" not in st.session_state:
                    st.session_state.variavel_selecionada = None
                
                # Obtém as variáveis disponíveis para a empresa selecionada
                variaveis_disponiveis = analysis.filtrar_variaveis(empresa_selecionada)
                
                # Mantém a variável selecionada se ainda estiver na lista de disponíveis
                if st.session_state.variavel_selecionada in variaveis_disponiveis:
                    variavel_selecionada = st.session_state.variavel_selecionada
                else:
                    variavel_selecionada = variaveis_disponiveis[0] if variaveis_disponiveis else None
                
                # Renderiza o selectbox sem alterar a variável que já estava selecionada
                with col2:
                    variavel_selecionada = st.selectbox(
                        'Variable:', 
                        variaveis_disponiveis, 
                        index=variaveis_disponiveis.index(variavel_selecionada) if variavel_selecionada in variaveis_disponiveis else 0
                    )
                
                # Atualiza o session_state para manter a variável na próxima interação
                st.session_state.variavel_selecionada = variavel_selecionada
            
                if variavel_selecionada:
                    # Filtrar anos disponíveis para a variável selecionada
                    anos_disponiveis = analysis.filtrar_anos(empresa_selecionada, variavel_selecionada)
            
                    with col3:
                        ano_selecionado = st.selectbox('Reference Year:', anos_disponiveis)
            
                    # Filtrar datas disponíveis
                    datas_disponiveis = analysis.filtrar_datas(empresa_selecionada, variavel_selecionada, ano_selecionado)
                    # Ordenar as datas em ordem crescente
                    datas_disponiveis = np.sort(datas_disponiveis)
            
                    # Agora, colocar "De" e "Até" lado a lado ocupando a metade do espaço
                    with col4:
                        # Aqui convertemos as datas para exibição em formato correto
                        datas_formatadas = pd.to_datetime(datas_disponiveis).strftime('%d/%m/%Y')
            
                        # Caixa de seleção "De" (remover a última data)
                        data_de = st.selectbox('From:', datas_formatadas[:-1], key='data_de')  # Remover a última data da lista
            
                    with col5:
                        # Caixa de seleção "Até" (remover a primeira data)
                            data_ate = st.selectbox(
                            'To:',
                            datas_formatadas[1:],  # Remover a primeira data da lista
                            key='data_ate',
                            index=len(datas_formatadas[1:]) - 1  # Última data da lista como default
                        )
            
                    # Só atualiza o gráfico quando todas as seleções estão preenchidas
                    if ano_selecionado and data_de and data_ate:
                        # Converte as strings selecionadas de volta para datetime antes de usar no gráfico
                        data_de = pd.to_datetime(data_de, format='%d/%m/%Y')
                        data_ate = pd.to_datetime(data_ate, format='%d/%m/%Y')
            
                        # Gerar gráfico e obter DataFrame filtrado com a opção de comparação
                        fig, df_filtrado, df_completa = analysis.gerar_grafico(empresa_selecionada, variavel_selecionada, ano_selecionado, data_de, data_ate)
        
                        # Verifica se fig e df_filtrado não são None antes de exibir
                        if fig is not None and df_filtrado is not None:
                            # Exibir gráfico
                            st.pyplot(fig)
                            colunas_exibir = ['DATA ATUALIZACAO', 'Ticker' ,variavel_selecionada]  # Sempre a data e a variável principal
                        
                            # Filtra o DataFrame para exibir apenas as colunas selecionadas
                            df_filtrado_para_exibir = df_filtrado[colunas_exibir]
                        
                            # Ajustando a formatação da coluna DATA ATUALIZACAO para dd/mm/aaaa
                            df_filtrado_para_exibir['DATA ATUALIZACAO'] = pd.to_datetime(df_filtrado_para_exibir['DATA ATUALIZACAO']).dt.strftime('%d/%m/%Y')
        
        elif graphs == "Nucleo Capital Weighted Average IRR":
            class AvgIRRAnalysis:
                def __init__(self):
                    self.excel_file_path = 'base_empilhada_total.csv'
                    self.df_mkt = pd.read_csv(self.excel_file_path, parse_dates=['DATA ATUALIZACAO'])  # Carregar com a data já formatada
             
                def filtrar_datas(self,variavel):
                    df_empresa = self.df_mkt[(self.df_mkt[variavel].notna())]
                    datas = np.sort(df_empresa['DATA ATUALIZACAO'].dropna().unique())
                    return datas
        
                def gerar_grafico(self, variavel, data_de, data_ate):
                    df_filtrado = self.df_mkt[                           
                        (self.df_mkt['DATA ATUALIZACAO'] >= data_de) & 
                        (self.df_mkt['DATA ATUALIZACAO'] <= data_ate)
                    ]
                    df_filtrado = df_filtrado.dropna(subset=[variavel])
                    if df_filtrado.empty:
                        st.warning(f"Não possuímos dados de {variavel} nessas datas.")
                        return None, None, None
                    # Ajuste de escala para evitar notação científica no eixo Y
                    df_filtrado[variavel] = df_filtrado[variavel].astype(str).str.replace(',', '')
                    df_filtrado[variavel] = pd.to_numeric(df_filtrado[variavel], errors='coerce')
                    
                    # Calculando os limites do eixo Y com base em 40% de folga
                    min_val = df_filtrado[variavel].min()
                    max_val = df_filtrado[variavel].max()
                    y_folga = 0.4 * (max_val - min_val)
                
                    # Calculando os limites do eixo X (datas) com folga
                    data_inicio = pd.to_datetime(df_filtrado['DATA ATUALIZACAO'].min())
                    data_fim = pd.to_datetime(df_filtrado['DATA ATUALIZACAO'].max())
                    x_folga = pd.Timedelta(days=2)  # Adicionando 2 dias de folga nas extremidades
                
                    # Cria o gráfico com o primeiro eixo Y (a variável principal)
                    fig, ax1 = plt.subplots(figsize=(10, 4.2))
                    ax1.plot(pd.to_datetime(df_filtrado['DATA ATUALIZACAO']), df_filtrado[variavel], marker='o', color='tab:blue', markersize=8)
                    ax1.set_title(f"{variavel} from {data_de.strftime('%d/%m/%Y')} to {data_ate.strftime('%d/%m/%Y')}", fontsize=7)
                    ax1.set_xlabel("Data", fontsize=5)
                    ax1.set_ylabel(variavel, fontsize=5)
                    ax1.tick_params(axis='x', labelsize=5)
                    ax1.tick_params(axis='y', labelsize=5)
                    ax1.set_xlim([data_inicio - x_folga, data_fim + x_folga])
                    ax1.set_ylim([min_val - y_folga, max_val + y_folga])
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
                    fig.autofmt_xdate()
                    ax1.grid(True)
                    
                    def formatar_percentual(x, pos):
                        return f'{x * 100:.1f}%'  # Multiplica por 100 para mostrar como percentual corretamente
                    ax1.yaxis.set_major_formatter(FuncFormatter(formatar_percentual))
                
                    return fig, df_filtrado, self.df_mkt
            # Instancia a classe de análise
            analysis = AvgIRRAnalysis()
            
            # Layout das seleções usando colunas para alinhamento
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])  # Adicionando col6 para os radio buttons
            
            # Filtrar datas disponíveis
            datas_disponiveis = analysis.filtrar_datas("Portfolio average IRR")
            # Ordenar as datas em ordem crescente
            datas_disponiveis = np.sort(datas_disponiveis)
        
            # Agora, colocar "De" e "Até" lado a lado ocupando a metade do espaço
            with col1:
                # Aqui convertemos as datas para exibição em formato correto
                datas_formatadas = pd.to_datetime(datas_disponiveis).strftime('%d/%m/%Y')
        
                # Caixa de seleção "De" (remover a última data)
                data_de = st.selectbox('From:', datas_formatadas[:-1], key='data_de')  # Remover a última data da lista
        
            with col2:
                # Caixa de seleção "Até" (remover a primeira data)
                    data_ate = st.selectbox(
                    'To:',
                    datas_formatadas[1:],  # Remover a primeira data da lista
                    key='data_ate',
                    index=len(datas_formatadas[1:]) - 1  # Última data da lista como default
                )
        
            # Só atualiza o gráfico quando todas as seleções estão preenchidas
            if data_de and data_ate:
                # Converte as strings selecionadas de volta para datetime antes de usar no gráfico
                data_de = pd.to_datetime(data_de, format='%d/%m/%Y')
                data_ate = pd.to_datetime(data_ate, format='%d/%m/%Y')
        
                # Gerar gráfico e obter DataFrame filtrado com a opção de comparação
                fig, df_filtrado, df_completa = analysis.gerar_grafico("Portfolio average IRR", data_de, data_ate)
        
                # Verifica se fig e df_filtrado não são None antes de exibir
                if fig is not None and df_filtrado is not None:
                    # Exibir gráfico
                    st.pyplot(fig)
                    colunas_exibir = ['DATA ATUALIZACAO', "Portfolio average IRR"]  # Sempre a data e a variável principal
                
                    # Filtra o DataFrame para exibir apenas as colunas selecionadas
                    df_filtrado_para_exibir = df_filtrado[colunas_exibir]
                
                    # Ajustando a formatação da coluna DATA ATUALIZACAO para dd/mm/aaaa
                    df_filtrado_para_exibir['DATA ATUALIZACAO'] = pd.to_datetime(df_filtrado_para_exibir['DATA ATUALIZACAO']).dt.strftime('%d/%m/%Y')
    
    

        scroll_top_script = """
        <script>
        function scrollTopStreamlit() {
            // Pega a div do conteúdo principal do Streamlit.
            const main = window.parent.document.querySelector('section.main');
            if (main) {
                main.scrollTop = 0;
            }
            // Se não achar, tenta no window mesmo:
            else {
                window.scrollTo(0, 0);
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(scrollTopStreamlit, 800);
        });
        </script>
        """
        import streamlit.components.v1 as components
        components.html(scroll_top_script, height=0)
