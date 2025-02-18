import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from st_aggrid import AgGrid, GridOptionsBuilder
from matplotlib.ticker import FuncFormatter
import datetime
from io import BytesIO
from xlsxwriter import Workbook
st.set_page_config(layout="wide")
excel_file_path = 'base_empilhada_total.csv'


st.markdown("""
    <style>
    div[data-baseweb="select"] > div {
        background-color: rgb(221, 235, 247);
        padding: 0.01px;
        border-radius: 5px;
        margin-top: -10px;  /* Ajustar a margem para mover tudo para cima */
        color: black !important; /* Texto preto */
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    div[data-testid="stSelectbox"] {
        background-color: rgb(221, 235, 247);
        padding: 5px;  /* Diminuir o padding para reduzir a altura */
        border-radius: 5px;
        margin-top: -30px;  /* Ajustar a margem para mover tudo para cima */
        color: black !important; /* Texto preto */
    }

    label[data-testid="stMarkdownContainer"] {
        margin-top: -30px;  /* Mover os títulos junto com as caixas */
    }
    </style>
    """, unsafe_allow_html=True)

# Inicializa uma variável de sessão para controlar o acesso
if 'acesso_permitido' not in st.session_state:
    st.session_state['acesso_permitido'] = False

# Se o acesso ainda não foi permitido, mostra a caixa de senha
if not st.session_state['acesso_permitido']:
    senha_usuario = st.text_input("Digite a senha para acessar o aplicativo:", type="password", key="senha")
    if senha_usuario:
        if senha_usuario == st.secrets["access_token"]:
            st.session_state['acesso_permitido'] = True
            st.success('Acesso permitido.')
            st.experimental_rerun()
        else:
            st.error("Senha incorreta. Você não tem permissão para acessar este aplicativo.")
            st.stop()  # Impede que o resto do aplicativo seja executado
    else:
        st.stop()  # Impede que o resto do aplicativo seja executado se nenhuma senha for inserida

if st.session_state['acesso_permitido']:
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
    import base64
    def get_image_as_base64(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    
    # Caminho para o arquivo da logo
    logo_path = 'nucleo.png'
    set_background(get_image_as_base64(logo_path))


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
            if ano_inicial == 2025:
                ano_inicial = 2024
                anos = [ano_inicial + i for i in range(4)]
            else:
                anos = [ano_inicial + i for i in range(4)]
                
            df_lucro = pd.DataFrame(columns=['Empresa'] + anos)
            empresas = df_filtrado['Ticker'].unique()
    
            for empresa in empresas_ordenadas:
                linha = {'Empresa': empresa}
                for i, ano in enumerate(anos):
                    lucro_ano = df_filtrado[(df_filtrado['Ticker'] == empresa) & (df_filtrado['Ano Referência'] == ano)]['Lucro líquido ajustado']
                    linha[ano] = lucro_ano.values[0] if not lucro_ano.empty else np.nan
                df_lucro = df_lucro.append(linha, ignore_index=True)
    
            # Formatando os números no estilo americano
            for ano in anos:
                df_lucro[ano] = pd.to_numeric(df_lucro[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.0f}" if not pd.isna(x) else 'nan')
            return df_lucro
    
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

        def apresentar_pe(self, df_filtrado, data_selecionada, empresas_ordenadas):
            ano_atual = pd.to_datetime(data_selecionada).year
            anos = [ano_atual + i for i in range(0, 2)]           
            df_pe_calc = pd.DataFrame(columns=['Empresa'] + anos)         
                   
            for empresa in empresas_ordenadas:
                pe_cal = {'Empresa': empresa}
        
                for ano in anos:
                    try:
                        pe_cal[ano] = df_filtrado.loc[
                            (df_filtrado['Ticker'] == empresa) & 
                            (df_filtrado['Ano Referência'] == ano), 
                            'P/E Calculado'
                        ].values[0].round(1)
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
                        linha[coluna_nova] = f"{valor:,.1f}"
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
                linha['IRR'] = f"{float(tir):.1%}" if tir.replace(".", "").isdigit() and float(tir) != 0 else 'faltando dados'
        
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
            # Título ajustado
            st.markdown("<h1 style='text-align: center; margin-top: -50px;color: black;'>IRR Portfólio</h1>", unsafe_allow_html=True)
            
            # Seção do Selectbox para a data (com a formatação que você mencionou)
            col10, co11, col2, col3 = st.columns([0.5, 1.5, 1, 1]) 
            with col10:
                datas_disponiveis = self.filtrar_datas()
                data_selecionada = st.selectbox('Select update date:', datas_disponiveis)
            # Filtra os dados pela data selecionada
            df_filtrado = self.filtrar_por_data(data_selecionada)
            df_portfolio = self.criar_tabela_portfolio(df_filtrado)
            empresas_ordenadas = df_portfolio['Empresa'].tolist()
            # Exibir tabelas lado a lado
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.15, 1.15, 1, 0.7, 0.5, 1.25, 1.25])
    
            # Tabela de Portfolio
            with col1:
                df_portfolio = self.criar_tabela_portfolio(df_filtrado)
                html_portfolio = self.gerar_html_tabela(df_portfolio, "Portfolio")
                st.markdown(html_portfolio, unsafe_allow_html=True)
    
            # Tabela de Lucro
            with col2:
                df_lucro = self.criar_tabela_lucro(df_filtrado, data_selecionada,empresas_ordenadas)
                df_lucro2 = df_lucro.copy()
                df_lucro2 = df_lucro2.drop(columns=['Empresa'])
                html_lucro = self.gerar_html_tabela(df_lucro2, "Lucro")
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
            # Tabela de P/E
            with col5:
                df_pee = self.df_pe(df_filtrado, data_selecionada, empresas_ordenadas)
                df_pee2 = df_pee.copy()
                df_pee2 = df_pee2.drop(columns=['Empresa'])
                html_pee = self.gerar_html_tabela(df_pee2, "P/E saída")
                st.markdown(html_pee, unsafe_allow_html=True)
                

            # Tabela de TIR
            with col6:
                df_tir = self.calcular_tir(df_filtrado, data_selecionada, empresas_ordenadas)
                df_tir2 = df_tir.copy()
                df_tir2 = df_tir2.drop(columns=['Empresa'])
                html_tir = self.gerar_html_tabela(df_tir2, "IRR")
                st.markdown(html_tir, unsafe_allow_html=True)
                
            # Tabela de Scorecards
            with col7:
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
    
    # Uso da classe no Streamlit
    df_empresa = pd.read_csv(excel_file_path)  # Substitua com o caminho correto no seu ambiente
    tabela = TabelaPortfolioLucro(df_empresa)
    tabela.mostrar_tabelas()
    
    st.markdown("<br><br>", unsafe_allow_html=True)  # Cria espaço extra entre os componentes
    
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
            
            idx = np.where(datas_disponiveis == data_selecionada)[0][0] if data_selecionada in datas_disponiveis else None
            
            if idx is not None and idx + 3 < len(datas_disponiveis):
                datas_recentes = datas_disponiveis[idx:idx+4][::-1]  # Mantendo a data selecionada e pegando as 3 seguintes da esquerda para a direita
            else:
                st.warning("Não há dados suficientes para exibir 4 semanas.")
                return pd.DataFrame()
            
            anos = [2024, 2025, 2026, 2027]
            colunas = ['Empresa']
            datas_formatadas = [pd.to_datetime(data).strftime('%d-%b-%y') for data in datas_recentes]
            
            for data in datas_formatadas:
                if variavel == "% Portfolio":
                    colunas.append(f"{data}")
                else:
                    for ano in anos:
                        colunas.append(f"{data} - {ano}")
            
            df_tabela = pd.DataFrame(columns=colunas)
            empresas = self.df_empresa['Ticker'].unique()
            
            for empresa in empresas:
                linha = {'Empresa': empresa}
                for i, data in enumerate(datas_recentes):
                    if variavel == "% Portfolio":
                        valor = self.df_empresa[(self.df_empresa['Ticker'] == empresa) & (self.df_empresa['DATA ATUALIZACAO'] == data)][variavel]
                        linha[f"{datas_formatadas[i]}"] = valor.values[0] if not valor.empty else np.nan
                    else:
                        for ano in anos:
                            valor = self.df_empresa[(self.df_empresa['Ticker'] == empresa) & (self.df_empresa['DATA ATUALIZACAO'] == data) & (self.df_empresa['Ano Referência'] == ano)][variavel]
                            linha[f"{datas_formatadas[i]} - {ano}"] = valor.values[0] if not valor.empty else np.nan
                df_tabela = df_tabela.append(linha, ignore_index=True)
            
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
                html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Empresa</th>'
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
                html += '<th rowspan="2" style="border: 1px solid #ddd; padding: 8px; text-align: center;">Empresa</th>'
                for data in datas_formatadas:
                    html += f'<th colspan="4" style="border: 1px solid #ddd; padding: 8px; text-align: center;">{data}</th>'
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
                            prev_col = df.columns[j - 4] if j - 4 >= 1 else None  # Comparação com a mesma empresa na semana anterior
                            if prev_col and df.at[i, col] != df.at[i, prev_col]:
                                cell_color = "background-color: yellow;"
                        html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: black; {cell_color}">{row[col]}</td>'
                    html += '</tr>'
            
            html += '</tbody></table>'
            return html
        
        def mostrar_tabela_projecoes(self):
            st.markdown("<h1 style='text-align: center; margin-top: -50px;color: black;'></h1>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                datas_disponiveis = self.filtrar_datas_disponiveis()
                data_selecionada = st.selectbox('Selecione a data:', datas_disponiveis)
            with col2:
                variavel_selecionada = st.selectbox('Selecione a variável:', self.variaveis)
            
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
    
    # Instanciando e exibindo a nova classe no Streamlit
    df_empresa = pd.read_csv('base_empilhada_total.csv')
    tabela_projecoes = TabelaAnaliticaProjecoes(df_empresa)
    tabela_projecoes.mostrar_tabela_projecoes()

           
    st.markdown("<br><br>", unsafe_allow_html=True)  # Cria espaço extra entre os componentes
    
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

                    col8, col9, col10 = st.columns([2, 1, 1])  # 2/3 da tela para o AgGrid, 1/3 para o botão
                    
                    with col8:
                        # Configurar AgGrid
                        gb = GridOptionsBuilder.from_dataframe(df_filtrado_para_exibir)
                        gb.configure_pagination(paginationAutoPageSize=True)  # Habilitar paginação
                        gb.configure_side_bar()  # Adicionar barra lateral para filtros
                        gb.configure_selection('multiple', use_checkbox=True)  # Habilitar múltiplas seleções
                        grid_options = gb.build()
                        
                        # Exibir a tabela
                        AgGrid(df_filtrado_para_exibir, gridOptions=grid_options, enable_enterprise_modules=True)
                    
                    with col9:
                        # Converter o DataFrame para CSV
                        csv = df_filtrado_para_exibir.to_csv(index=False)
                    
                        # Botão de download
                        st.download_button(
                            label="Download filtered data in CSV",
                            data=csv,
                            file_name='dados_filtrados.csv',
                            mime='text/csv'
                        )
                    with col10:
                                                # Converter o DataFrame para CSV
                        csv2 = df_completa.to_csv(index=False)
                    
                        # Botão de download
                        st.download_button(
                            label="Download complete database in CSV",
                            data=csv2,
                            file_name='df_completa.csv',
                            mime='text/csv'
                        )
                        
                                    
                else:
                    pass
