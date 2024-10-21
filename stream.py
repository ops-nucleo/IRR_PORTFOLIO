import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from st_aggrid import AgGrid, GridOptionsBuilder
from matplotlib.ticker import FuncFormatter

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
                
                # Aplica o formatter para percentual com 2 casas decimais no eixo Y
                ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x * 100:.2f}%'))
                
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
                y_folga_pe = 0.4 * (max_pe - min_pe)
                ax2.set_ylim([min_pe - y_folga_pe, max_pe + y_folga_pe])
                
                # Formatar o P/E com uma casa decimal
                ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.2f}'))
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
                    ('Sem comparação', 'Variável vs CDI', 'Variável vs P/E'),
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
