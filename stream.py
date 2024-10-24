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
            datas = np.sort(self.df_empresa['DATA ATUALIZACAO'].unique())
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
            
            # Formatando os números
            df_portfolio['% Portfólio'] = df_portfolio['% Portfólio'].apply(lambda x: f"{x * 100:.2f}%")
            df_portfolio['Mkt cap'] = pd.to_numeric(df_portfolio['Mkt cap'], errors='coerce').fillna(0).apply(lambda x: f"{x:,.2f}")
            return df_portfolio
    
        def criar_tabela_lucro(self, df_filtrado, data_selecionada):
            # Segunda tabela: "Lucro" (mostra os 4 anos a partir da data filtrada)
            ano_inicial = pd.to_datetime(data_selecionada, format='%d/%m/%Y').year
            anos = [ano_inicial + i for i in range(4)]
            
            df_lucro = pd.DataFrame(columns=['Empresa'] + anos)
            empresas = df_filtrado['Ticker'].unique()
    
            for empresa in empresas:
                linha = {'Empresa': empresa}
                for i, ano in enumerate(anos):
                    lucro_ano = df_filtrado[(df_filtrado['Ticker'] == empresa) & (df_filtrado['Ano Referência'] == ano)]['Lucro líquido ajustado']
                    linha[ano] = lucro_ano.values[0] if not lucro_ano.empty else np.nan
                df_lucro = df_lucro.append(linha, ignore_index=True)
    
            # Formatando os números no estilo americano
            for ano in anos:
                df_lucro[ano] = pd.to_numeric(df_lucro[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.2f}" if not pd.isna(x) else 'nan')
            return df_lucro
    
        def criar_tabela_dividendos(self, df_filtrado, data_selecionada):
            # Tabela de Dividendos (mesma lógica da tabela de Lucro)
            ano_inicial = pd.to_datetime(data_selecionada, format='%d/%m/%Y').year
            anos = [ano_inicial + i for i in range(4)]
            
            df_dividendos = pd.DataFrame(columns=['Empresa'] + anos)
            empresas = df_filtrado['Ticker'].unique()
    
            for empresa in empresas:
                linha = {'Empresa': empresa}
                for i, ano in enumerate(anos):
                    dividendo_ano = df_filtrado[(df_filtrado['Ticker'] == empresa) & (df_filtrado['Ano Referência'] == ano)]['Dividendos']
                    linha[ano] = dividendo_ano.values[0] if not dividendo_ano.empty else np.nan
                df_dividendos = df_dividendos.append(linha, ignore_index=True)
    
            # Formatando os números no estilo americano
            for ano in anos:
                df_dividendos[ano] = pd.to_numeric(df_dividendos[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.2f}" if not pd.isna(x) else 'nan')
            return df_dividendos
    

        def calcular_tir(self, df_filtrado, data_selecionada):
            empresas = df_filtrado['Ticker'].unique()
            pe_coluna = 'P/E'
            tir_coluna = 'TIR'  # Coluna de onde vamos buscar os valores de TIR
            df_tir = pd.DataFrame(columns=['Empresa', 'P/E', 'TIR'])
        
            for empresa in empresas:
                linha = {'Empresa': empresa}
        
                # Obtendo o P/E e tratando valores NaN
                pe = df_filtrado[df_filtrado['Ticker'] == empresa][pe_coluna].fillna(0).values[0]
                linha['P/E'] = f"{pe:,.2f}"  # Formatando P/E para duas casas decimais
        
                # Obtendo a TIR da coluna 'TIR' e convertendo para float
                tir = df_filtrado[df_filtrado['Ticker'] == empresa][tir_coluna].astype(float).values[0]
        
                # Verificar se a TIR é numérica, diferente de zero e não NaN
                if not pd.isna(tir) and tir != 0:
                    linha['TIR'] = f"{tir:.2%}"  # Formatando TIR como percentual xx.xx%
                else:
                    linha['TIR'] = 'faltando dados'  # Se for 0 ou NaN, exibe "faltando dados"
        
                # Adicionando a linha no DataFrame
                df_tir = df_tir.append(linha, ignore_index=True)
        
            return df_tir
    
        def gerar_html_tabela(self, df, titulo):
            # Gera o código HTML da tabela com formatação e ajuste de largura
            html = f"<h3>{titulo}</h3>"
            html += '<table style="width:100%; border-collapse: collapse; margin: auto;">'
            
            # Adicionando os cabeçalhos da tabela com cor personalizada (R: 0, G: 32, B: 96)
            html += '<thead><tr style="background-color: rgb(0, 32, 96); color: white;">'
            for col in df.columns:
                html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{col}</th>'
            html += '</tr></thead><tbody>'
            
            # Linhas alternadas (cinza e branco)
            for i, row in df.iterrows():
                # Alterna as cores de fundo entre cinza e branco
                if i % 2 == 0:
                    bg_color = 'rgb(242, 242, 242)'  # Cinza
                else:
                    bg_color = 'white'  # Branco
        
                html += f'<tr style="background-color: {bg_color};">'
                for col in df.columns:
                    html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: left;">{row[col]}</td>'
                html += '</tr>'
        
            html += '</tbody></table>'
            return html
    
        def download_excel(self, dfs_dict):
            # Função para baixar todas as DataFrames em um único arquivo Excel com abas separadas
            output = BytesIO()
            
            # Substituir caracteres inválidos no nome da aba
            safe_sheet_names = {
                sheet_name: sheet_name.replace('/', '').replace('\\', '').replace('*', '').replace('[', '').replace(']', '').replace(':', '').replace('?', '') 
                for sheet_name in dfs_dict.keys()
            }
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for sheet_name, df in dfs_dict.items():
                    # Usa o nome corrigido para evitar erros
                    safe_name = safe_sheet_names[sheet_name]
                    df.to_excel(writer, sheet_name=safe_name, index=False)
                writer.save()
        
            # Download do arquivo
            st.download_button(
                label="Baixar todas as tabelas em Excel",
                data=output.getvalue(),
                file_name="tabelas_IRR_portfolio_lucro.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
        def mostrar_tabelas(self):
            # Título ajustado
            st.markdown("<h1 style='text-align: center; margin-top: -50px;'>IRR Portfólio</h1>", unsafe_allow_html=True)
    
            # Seção do Selectbox para a data (com a formatação que você mencionou)
            col5, col6, col7, col8 = st.columns([0.5, 1.5, 1, 1]) 
            with col5:
                datas_disponiveis = self.filtrar_datas()
                data_selecionada = st.selectbox('Selecione a data de atualização:', datas_disponiveis)
            # Filtra os dados pela data selecionada
            df_filtrado = self.filtrar_por_data(data_selecionada)
    
            # Exibir tabelas lado a lado
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
            # Tabela de Portfolio
            with col1:
                df_portfolio = self.criar_tabela_portfolio(df_filtrado)
                html_portfolio = self.gerar_html_tabela(df_portfolio, "Portfolio")
                st.markdown(html_portfolio, unsafe_allow_html=True)
    
            # Tabela de Lucro
            with col2:
                df_lucro = self.criar_tabela_lucro(df_filtrado, data_selecionada)
                html_lucro = self.gerar_html_tabela(df_lucro, "Lucro")
                st.markdown(html_lucro, unsafe_allow_html=True)
    
            # Tabela de Dividendos
            with col3:
                df_dividendos = self.criar_tabela_dividendos(df_filtrado, data_selecionada)
                html_dividendos = self.gerar_html_tabela(df_dividendos, "Dividendos")
                st.markdown(html_dividendos, unsafe_allow_html=True)
    
            # Tabela de P/E e TIR
            with col4:
                df_tir = self.calcular_tir(df_filtrado, data_selecionada)
                html_tir = self.gerar_html_tabela(df_tir, "P/E e TIR")
                st.markdown(html_tir, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)  # Cria espaço extra entre os componentes

    
            # Exportar todas as tabelas em um arquivo Excel com abas separadas
            dfs_dict = {
                "Portfolio": df_portfolio,
                "Lucro": df_lucro,
                "Dividendos": df_dividendos,
                "P/E e TIR": df_tir
            }
            self.download_excel(dfs_dict)
                

    # Uso da classe no Streamlit
    df_empresa = pd.read_csv(excel_file_path)  # Substitua com o caminho correto no seu ambiente
    tabela = TabelaPortfolioLucro(df_empresa)
    tabela.mostrar_tabelas()
    
    st.markdown("<br><br>", unsafe_allow_html=True)  # Cria espaço extra entre os componentes

    
    class EmpresaAnalysis:
        def __init__(self):
            self.df_mkt = pd.read_csv(excel_file_path, parse_dates=['DATA ATUALIZACAO'])  # Carregar com a data já formatada
            self.colunas = ["Ativo permanente", "Capex", "Capital de giro", "Capital investido (medio)", 
                            "Despesas operacionais", "Dívida Líquida", "Dividendos", "EBIT ajustado", 
                            "EBITDA ajustado", "FCFE", "Lucro bruto", "Lucro líquido ajustado", 
                            "Net debt/EBITDA", "Patrimônio líquido", "Receita líquida", "Resultado financeiro"]
            self.empresas = np.sort(self.df_mkt['Ticker'].unique())

        def filtrar_variaveis(self, empresa):
            df_empresa = self.df_mkt[self.df_mkt['Ticker'] == empresa]
            variaveis_disponiveis = [col for col in self.colunas if df_empresa[col].notna().any()]
            return variaveis_disponiveis
        
        def filtrar_anos(self, empresa, variavel):
            df_empresa = self.df_mkt[(self.df_mkt['Ticker'] == empresa) & (self.df_mkt[variavel].notna())]
            return df_empresa['Ano Referência'].unique()
        
        def filtrar_datas(self, empresa, variavel, ano):
            df_empresa = self.df_mkt[(self.df_mkt['Ticker'] == empresa) & (self.df_mkt['Ano Referência'] == ano) &(self.df_mkt[variavel].notna())]
            datas = np.sort(df_empresa['DATA ATUALIZACAO'].unique())
            return datas

        def gerar_grafico(self, empresa, variavel, ano_ref, data_de, data_ate, comparacao):
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
            ax1.set_title(f"{empresa} - {variavel} de {data_de.strftime('%d/%m/%Y')} até {data_ate.strftime('%d/%m/%Y')}", fontsize=7)
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
                return f'{x * 100:.2f}%'  # Multiplica por 100 para mostrar como percentual corretamente
            
            # Se for selecionado "Variável vs CDI"
            if comparacao == "Variável vs CDI":
                ax2 = ax1.twinx()  # Cria um segundo eixo Y
                df_comp = df_filtrado.copy()  # Copia o DataFrame original para evitar alterações no original
                df_comp['CDI'] = df_comp['CDI'].astype(float)  # Garante que a coluna CDI é do tipo float
                df_comp = df_comp.dropna(subset=['CDI'])  # Remove linhas onde CDI é NaN
                
                # Checa se todas as linhas do CDI estão vazias
                if df_comp['CDI'].isna().all():
                    st.warning(f"Não possuímos dados de CDI para as datas selecionadas.")
                    return None, None, None
                
                # Plota o CDI no segundo eixo Y com marcadores
                ax2.plot(pd.to_datetime(df_comp['DATA ATUALIZACAO']), df_comp['CDI'], marker='o', color='tab:red', markersize=3)
            
                # Define o label para o segundo eixo Y
                ax2.set_ylabel('CDI (%)', fontsize=6)
            
                # Aplica o formatter que multiplica por 100 e mostra o CDI como percentual
                ax2.yaxis.set_major_formatter(FuncFormatter(formatar_percentual))
                
                # Ajusta os limites do eixo Y do CDI com folga de 40%
                min_cdi = df_comp['CDI'].min()
                max_cdi = df_comp['CDI'].max()
                y_folga_cdi = 0.4 * (max_cdi - min_cdi)
                ax2.set_ylim([min_cdi - y_folga_cdi, max_cdi + y_folga_cdi])
                
                # Ajusta o tamanho das labels do eixo Y
                ax2.tick_params(axis='y', labelsize=5)
        
            # Se for selecionado "Variável vs P/E"
            elif comparacao == "Variável vs P/E":
                ax2 = ax1.twinx()  # Cria um segundo eixo Y
                df_comp2 = df_filtrado.copy()
                df_comp2['P/E'] = df_comp2['P/E'].astype(float)
                df_comp2 = df_comp2.dropna(subset=['P/E'])
                if df_comp2['P/E'].isna().all():
                    st.warning(f"Não possuímos dados de P/E para as datas selecionadas.")
                    return None, None, None
                # Adicionar o P/E no segundo eixo Y e formatar como número inteiro
                ax2.plot(pd.to_datetime(df_comp2['DATA ATUALIZACAO']), df_comp2['P/E'], marker='o', color='tab:green', markersize=3)
                ax2.set_ylabel('P/E', fontsize=6)
                
                # Ajusta o limite do segundo eixo Y (P/E) com folga de 40%
                min_pe = df_comp2['P/E'].min()
                max_pe = df_comp2['P/E'].max()
                y_folga_pe = 0.4 * (min_pe - max_pe)
                ax2.set_ylim([min_pe - y_folga_pe, max_pe + y_folga_pe])
                
                ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.2f}'))
                ax2.tick_params(axis='y', labelsize=5)
        
            # Se for selecionado "Variável vs TIR"
            elif comparacao == "Variável vs TIR":
                ax2 = ax1.twinx()  # Cria um segundo eixo Y
                df_comp3 = df_filtrado.copy()
                df_comp3['TIR'] = df_comp3['TIR'].astype(float)
                df_comp3 = df_comp3.dropna(subset=['TIR'])
                if df_comp3['TIR'].isna().all():
                    st.warning(f"Não possuímos dados de TIR para as datas selecionadas.")
                    return None, None, None
                # Adicionar o TIR no segundo eixo Y e formatar como percentual
                ax2.plot(pd.to_datetime(df_comp3['DATA ATUALIZACAO']), df_comp3['TIR'], marker='o', color='tab:orange', markersize=3)
                ax2.set_ylabel('TIR (%)', fontsize=6)
                
                # Ajusta o limite do segundo eixo Y (TIR) com folga de 40%
                min_tir = df_comp3['TIR'].min()
                max_tir = df_comp3['TIR'].max()
                y_folga_tir = 0.4 * (min_tir - max_tir)
                ax2.set_ylim([min_tir - y_folga_tir, max_tir + y_folga_tir])
                
                ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x * 100:.2f}%'))
                ax2.tick_params(axis='y', labelsize=5)
        
            return fig, df_filtrado, self.df_mkt
    # Instancia a classe de análise
    analysis = EmpresaAnalysis()
    
    # Layout das seleções usando colunas para alinhamento
    col1, col3, col2, col6, col4, col5 = st.columns([1, 1, 1, 1, 1, 1])  # Adicionando col6 para os radio buttons
    
    # Dropdown para selecionar empresa (Ticker) no lado esquerdo
    with col1:
        empresa_selecionada = st.selectbox('Ticker', analysis.empresas)
    
    if empresa_selecionada:
        # Filtrar variáveis disponíveis para a empresa selecionada
        variaveis_disponiveis = analysis.filtrar_variaveis(empresa_selecionada)
    
        # Caixa de seleção para variável analisada no lado direito
        with col2:
            variavel_selecionada = st.selectbox('Variável analisada', variaveis_disponiveis)
    
        if variavel_selecionada:
            # Filtrar anos disponíveis para a variável selecionada
            anos_disponiveis = analysis.filtrar_anos(empresa_selecionada, variavel_selecionada)
    
            with col3:
                ano_selecionado = st.selectbox('Ano Referência', anos_disponiveis)
    
            # Filtrar datas disponíveis
            datas_disponiveis = analysis.filtrar_datas(empresa_selecionada, variavel_selecionada, ano_selecionado)
            # Ordenar as datas em ordem crescente
            datas_disponiveis = np.sort(datas_disponiveis)
    
            # Agora, colocar "De" e "Até" lado a lado ocupando a metade do espaço
            with col4:
                # Aqui convertemos as datas para exibição em formato correto
                datas_formatadas = pd.to_datetime(datas_disponiveis).strftime('%d/%m/%Y')
    
                # Caixa de seleção "De" (remover a última data)
                data_de = st.selectbox('De', datas_formatadas[:-1], key='data_de')  # Remover a última data da lista
    
            with col5:
                # Caixa de seleção "Até" (remover a primeira data)
                data_ate = st.selectbox('Até', datas_formatadas[1:], key='data_ate')  # Remover a primeira data da lista
    
            # Adicionando Radio Buttons na coluna col6 para seleção de comparação
            with col6:
                comparacao = st.radio(
                    "Comparação",
                    ('Sem comparação', 'Variável vs CDI', 'Variável vs P/E', 'Variável vs TIR'),
                    index=0  # "Sem comparação" como padrão
                )
    
            # Só atualiza o gráfico quando todas as seleções estão preenchidas
            if ano_selecionado and data_de and data_ate:
                # Converte as strings selecionadas de volta para datetime antes de usar no gráfico
                data_de = pd.to_datetime(data_de, format='%d/%m/%Y')
                data_ate = pd.to_datetime(data_ate, format='%d/%m/%Y')
    
                # Gerar gráfico e obter DataFrame filtrado com a opção de comparação
                fig, df_filtrado, df_completa = analysis.gerar_grafico(empresa_selecionada, variavel_selecionada, ano_selecionado, data_de, data_ate, comparacao)

                # Verifica se fig e df_filtrado não são None antes de exibir
                if fig is not None and df_filtrado is not None:
                    # Exibir gráfico
                    st.pyplot(fig)
                    colunas_exibir = ['DATA ATUALIZACAO', 'Ticker' ,variavel_selecionada]  # Sempre a data e a variável principal
                
                    # Adiciona CDI ou P/E dependendo da comparação
                    if comparacao == 'Variável vs CDI':
                        colunas_exibir.append('CDI')
                    elif comparacao == 'Variável vs P/E':
                        colunas_exibir.append('P/E')
                
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
                            label="Baixar dados filtrados em CSV",
                            data=csv,
                            file_name='dados_filtrados.csv',
                            mime='text/csv'
                        )
                    with col10:
                                                # Converter o DataFrame para CSV
                        csv2 = df_completa.to_csv(index=False)
                    
                        # Botão de download
                        st.download_button(
                            label="Baixar base completa em CSV",
                            data=csv2,
                            file_name='df_completa.csv',
                            mime='text/csv'
                        )
                        
                                    
                else:
                    pass
