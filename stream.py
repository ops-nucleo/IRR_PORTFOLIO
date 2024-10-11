import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
excel_file_path = 'base_empilhada_total.csv'

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
        
        def filtrar_datas(self, empresa, variavel):
            df_empresa = self.df_mkt[(self.df_mkt['Ticker'] == empresa) & (self.df_mkt[variavel].notna())]
            datas = np.sort(df_empresa['DATA ATUALIZACAO'].unique())
            return datas

        def gerar_grafico(self, empresa, variavel, ano_ref, data_de, data_ate):
            df_filtrado = self.df_mkt[
                (self.df_mkt['Ticker'] == empresa) & 
                (self.df_mkt['Ano Referência'] == ano_ref) & 
                (self.df_mkt['DATA ATUALIZACAO'] >= data_de) & 
                (self.df_mkt['DATA ATUALIZACAO'] <= data_ate)
            ]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(pd.to_datetime(df_filtrado['DATA ATUALIZACAO']), df_filtrado[variavel], marker='o')
            ax.set_title(f"Variável {variavel} para {empresa} de {data_de.strftime('%Y-%m-%d')} até {data_ate.strftime('%Y-%m-%d')}")
            ax.set_xlabel("Data")
            ax.set_ylabel(variavel)
            ax.set_ylim([df_filtrado[variavel].min(), df_filtrado[variavel].max()])  # Ajusta o range do eixo Y
            ax.grid(True)
            plt.xticks(rotation=45)  # Rotaciona os ticks de data
            return fig
    
    # Instancia a classe de análise
    analysis = EmpresaAnalysis()
    
    # Layout das seleções usando colunas para alinhamento
    col1, col2 = st.columns(2)
    
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
            col3, col4 = st.columns(2)

            with col3:
                ano_selecionado = st.selectbox('Ano Referência', anos_disponiveis)

            # Filtrar datas disponíveis
            datas_disponiveis = analysis.filtrar_datas(empresa_selecionada, variavel_selecionada)
            # Ordenar as datas em ordem crescente
            datas_disponiveis = np.sort(datas_disponiveis)

            with col4:
                # Aqui convertemos as datas para exibição em formato correto
                datas_formatadas = pd.to_datetime(datas_disponiveis).strftime('%Y-%m-%d')

                # Caixa de seleção "De" (remover a última data)
                data_de = st.selectbox('De', datas_formatadas[:-1])  # Remover a última data da lista

                # Caixa de seleção "Até" (remover a primeira data)
                data_ate = st.selectbox('Até', datas_formatadas[1:])  # Remover a primeira data da lista

            # Só atualiza o gráfico quando todas as seleções estão preenchidas
            if ano_selecionado and data_de and data_ate:
                # Converte as strings selecionadas de volta para datetime antes de usar no gráfico
                data_de = pd.to_datetime(data_de)
                data_ate = pd.to_datetime(data_ate)

                st.pyplot(analysis.gerar_grafico(empresa_selecionada, variavel_selecionada, ano_selecionado, data_de, data_ate))
