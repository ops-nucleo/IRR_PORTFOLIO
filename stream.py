import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.colors as mcolors
import plotly.express as px
import numpy as np
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

st.set_page_config(layout="wide")
excel_file_path = 'base_ret_acum.xlsx'
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

# O resto do seu código de aplicativo
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
        def __init__(self, excel_file_path):
            self.excel_file_path = 'base_ret_acum.xlsx'
            self.df_mkt = pd.read_excel(self.excel_file_path, sheet_name='Mkt cap - Volume')
            self.empresas = np.sort(self.df_mkt['Ticker'].unique())

        def to_percent(self, y, position):
            """Converte o valor de eixo para porcentagem."""
            s = f"{100 * y:.0f}%"
            _ = position
            return s
    
        def formatar_numero(self, valor):
            if valor >= 1_000_000_000:  # para valores iguais ou superiores a 1 bilhão
                return f'{valor/1_000_000_000:.0f} bi'
            elif valor >= 1_000_000:  # para valores iguais ou superiores a 1 milhão
                return f'{valor/1_000_000:.0f} mm'
            elif valor >= 1_000:  # para valores iguais ou superiores a 1 mil
                return f'{valor/1_000:.0f} k'
            else:
                return str(valor)  # para valores abaixo de 1 mil
    
        def gerar_grafico(self, empresa):
            df = pd.read_excel(self.excel_file_path, sheet_name=empresa).set_index("date")
            df_preco = pd.read_excel(self.excel_file_path, sheet_name='PRECO').set_index("date")
            mkt = self.df_mkt.loc[self.df_mkt['Ticker'] == empresa, 'MKT Cap'].iloc[0]
            vlm = self.df_mkt.loc[self.df_mkt['Ticker'] == empresa, 'Volume médio'].iloc[0]
            mkt_rounded = self.formatar_numero(mkt)
            vlm_rounded = self.formatar_numero(vlm)
            cores_linhas = {
                'Master FIA': ('blue', 2.5),
                'IBOV': ('black', 1.5),
                'CDI': ('darkgreen', 1.5),
                empresa: ('orange', 1.5)  # Supondo que 'empresa' seja uma das colunas
            }
            fig, ax = plt.subplots(figsize=(12, 5))

            for col in df.columns:
                cor, espessura = cores_linhas.get(col, ('gray', 2))  # Cor padrão cinza se não especificado
                ax.plot(df.index.values, df[col].values, label=col, color=cor, linewidth=espessura)  # Modificação aqui
           
            data_inicial = df.index.min()
            data_final = df.index.max()
            

            coluna = f'{empresa}'
            preco_inicial = round(df_preco.loc[data_inicial, coluna], 2)
            preco_final = round(df_preco.loc[data_final, coluna], 2)
    
            desc = f'Preço inicial:\nR$ {preco_inicial:.2f}'
            desc2 = (f'Preço Final: R$ {preco_final:.2f}\n'
                     f'Dados de {data_final.strftime("%d/%m/%Y")}: \n'
                     f'Volume médio: {vlm_rounded}\n'
                     f'Market cap: {mkt_rounded}')
    
            posicao_inicial = df.loc[data_inicial, df.columns[0]]
            posicao_final = df.loc[data_final, df.columns[-1]]
            data_inicial = data_inicial - pd.Timedelta(days=55)
            data_final = data_final + pd.Timedelta(days=20)
            
            ax.annotate(desc, xy=(data_inicial, posicao_inicial),
                        xytext=(data_inicial, posicao_inicial + 0.2),
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', alpha=1),
                        fontsize=7)
    
            ax.annotate(desc2, xy=(data_final, posicao_final),
                        xytext=(data_final, posicao_final),
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', alpha=1),
                        fontsize=8)
            
    
            formatter = mticker.FuncFormatter(self.to_percent)
            ax.yaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            ax.set_ylabel('Rentabilidade (%)')
            ax.legend(loc='upper left', ncol=4)
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)
            return fig
    
    # Supondo que excel_file_path seja uma variável definida anteriormente com o caminho para o arquivo Excel
    analysis = EmpresaAnalysis(excel_file_path)
    # CSS global para ajustes visuais do título e dropdown
    analysis = EmpresaAnalysis(excel_file_path)
    # CSS global para ajustes visuais do título e dropdown
    st.markdown("""
    <style>
    .custom-font {
        font-family: "Calibri", sans-serif;
        color: black;
        font-size: 20px;
        text-align: Left;  /* Alinhamento centralizado do título */
    }
    div.stSelectbox > div {
        width: 50%;  /* Ajusta a largura do dropdown para ocupar metade da coluna */
        margin-top: -40px;  /* Ajusta a posição vertical para cima */
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Criação de colunas para dropdown e título
    col1, col2 = st.columns([3, 7])
    
    with col1:
        # Dropdown para seleção da empresa
        empresa_selecionada = st.selectbox('', analysis.empresas)
    
    with col2:
        st.markdown("""
            <style>
            .custom-font {
                font-family: "Calibri", sans-serif;
                color: black;
                font-size: 24px;
                margin-top: -30px;
                padding-left: -50px;  /* Adiciona um espaço à esquerda dentro da div, movendo o texto para a direita */
                text-align: Left;  /* Alinha o texto à esquerda */
            }
            .centered {
                text-align: Left;
            }
            .stSelectbox {
                margin-top: -24px;  # Ajuste o valor conforme necessário para subir o dropdown
            }
            </style>
            <div class="custom-font centered">Rentabilidade Empresas, CDI e IBOV | Últimos 3 anos</div>
            """, unsafe_allow_html=True)
    
    # Continuação do seu código para mostrar o gráfico, etc.
    if empresa_selecionada:
        st.pyplot(analysis.gerar_grafico(empresa_selecionada))
                                
    

    class RollingGraphs:
        def __init__(self, file_path, empresa_analysis):
            self.empresa_analysis = empresa_analysis
            self.file_path = file_path
            self.df_avg = pd.read_excel('bbg_precos_rolling_returns_avg.xlsx')
            self.df_avg['ticker'] = self.df_avg['ticker'].str.upper()
            self.df_avg['ticker'] = self.df_avg['ticker'].str.replace(' BZ EQUITY', '', regex=True)
        def to_percent(self, y, position):
            """Converte o valor de eixo para porcentagem."""
            s = f"{100 * y:.0f}%"
            _ = position
            return s
        
        def gerar_grafico(self, empresa_selecionada):
            df_empresa  = pd.read_excel(self.file_path, sheet_name=empresa_selecionada)
            df_empresa['date'] = pd.to_datetime(df_empresa['date'])
            df_empresa = df_empresa.set_index("date")
            
            if df_empresa[[f'{empresa_selecionada} rolling_3_y', f'{empresa_selecionada} rolling_5_y']].isna().all().all():
                # Se todas as entradas nas colunas são NaN, exiba uma mensagem e não crie um gráfico
                st.warning(f'A empresa {empresa_selecionada} não possui dados suficientes para análise de retorno anualizado de rolagem.')
                return None  # Retorna None para evitar a criação de um gráfico vazio
            else:
                # Configurar o gráfico
                fig, ax = plt.subplots(figsize=(12, 5))
    
                # Plotar as colunas de interesse, ignorando as demais colunas
                colunas_interesse = [
                    f'{empresa_selecionada} rolling_3_y', 
                    f'{empresa_selecionada} rolling_5_y', 
                    'Master FIA rolling_3_y', 
                    'Master FIA rolling_5_y'
                    ]  # exemplo
                estilos_linha = {
                        f'{empresa_selecionada} rolling_3_y': {'linestyle': '-', 'linewidth': 0.5, 'color': '#355E3B'},
                        f'{empresa_selecionada} rolling_5_y': {'linestyle': '-', 'linewidth': 0.5, 'color': '#191970'},
                        'Master FIA rolling_3_y': {'linestyle': '--', 'linewidth': 2, 'color': '#90EE90'},
                        'Master FIA rolling_5_y': {'linestyle': '--', 'linewidth': 2, 'color': '#ADD8E6'}
                    }

                for col in colunas_interesse:
                    estilo = estilos_linha.get(col, {'linestyle': '-', 'linewidth': 1, 'color': 'black'}) 
                    ax.plot(df_empresa.index.values, df_empresa[col].values, label=col, **estilo)
                    
                # for col in colunas_interesse:
                #     ax.plot(df_empresa.index.values, df_empresa[col].values, label=col)
    
                # Formatar o eixo x para mostrar as datas no formato 'Mês/Ano'
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))  # Intervalo de 6 meses
                ax.xaxis.set_minor_locator(mdates.MonthLocator())
                ax.tick_params(axis='x', which='major', labelsize=7)
                formatter = mticker.FuncFormatter(self.to_percent)
                ax.yaxis.set_major_formatter(formatter)
    
                # Rodar os rótulos do eixo x para melhor visualização
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
                # Títulos e legendas
                plt.title(f'Rolling returns - {empresa_selecionada} VS Master FIA')
                plt.ylabel('Retorno Anualizado (%)')
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.subplots_adjust(bottom=0.2) 
                ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
                ax.yaxis.grid(False)
                    # Retorna o objeto figura para ser usado pelo Streamlit
                st.pyplot(fig) 
                
        def gerar_tabela(self, empresa_selecionada):
            df_empresa  = pd.read_excel(self.file_path, sheet_name=empresa_selecionada)
            df_empresa['date'] = pd.to_datetime(df_empresa['date'])
            df_empresa = df_empresa.set_index("date")
            
            if df_empresa[[f'{empresa_selecionada} rolling_3_y', f'{empresa_selecionada} rolling_5_y']].isna().all().all():
                # Se todas as entradas nas colunas são NaN, exiba uma mensagem e não crie um gráfico
                st.warning(f'A empresa {empresa_selecionada} não possui dados suficientes para análise de retorno anualizado de rolagem.')
                return None  # Retorna None para evitar a criação de um gráfico vazio
            else:
                       
                media_rolling_3_y_master = df_empresa['Master FIA rolling_3_y'].mean(skipna=True)
                media_rolling_5_y_master = df_empresa['Master FIA rolling_5_y'].mean(skipna=True)
        
                # Prepara os dados da tabela da empresa selecionada
                df_mediaS = self.df_avg.copy()
                df_mediaS = df_mediaS[df_mediaS["ticker"] == empresa_selecionada]
                empresa_cagr_3y = df_mediaS['avg_annualized_rolling_ret_3_y'].mean(skipna=True)
                empresa_cagr_5y = df_mediaS['avg_annualized_rolling_ret_5_y'].mean(skipna=True)
        
                # Combina os dados em uma única lista para a tabela
                combined_table_data = [
                    [f"{round(empresa_cagr_3y*100, 2)}%" if pd.notna(empresa_cagr_3y) else "-", 
                     f"{round(empresa_cagr_5y*100, 2)}%" if pd.notna(empresa_cagr_5y) else "-"],
                    [f"{round(media_rolling_3_y_master*100, 2)}%" if pd.notna(media_rolling_3_y_master) else "-", 
                     f"{round(media_rolling_5_y_master*100, 2)}%" if pd.notna(media_rolling_5_y_master) else "-"]
                ]
        
                # Cria uma nova figura para a tabela combinada
                fig_combined, ax_combined = plt.subplots(figsize=(8, 2))
                ax_combined.axis('off')  # Desliga os eixos
        
                # Plota a tabela combinada
                column_labels = ['Média CAGR móvel 3Y', 'Média CAGR móvel 5Y']
                row_labels = [empresa_selecionada, 'Master FIA']
                table_combined = ax_combined.table(
                    cellText=combined_table_data,
                    colLabels=column_labels,
                    rowLabels=row_labels,
                    cellLoc='center',
                    loc='top',
                    rowLoc='center',
                    colColours=['#F1F1F2']*4,  # A cor branca para fundo de cabeçalho de coluna
                    rowColours=['#F1F1F2', '#F1F1F2']*2  # Alternar cores para as linhas se desejar
                )
                table_combined.auto_set_font_size(False)
                table_combined.set_fontsize(7)
                table_combined.scale(1, 0.8)  # Ajuste o escalonamento conforme necessário
        
                plt.show()
                st.pyplot(fig_combined)  # Se estiver usando Streamlit
                
    # Criação da instância da classe RollingGraphs
    rolling_graphs = RollingGraphs('base_roll.xlsx', analysis)
    
    # Quando uma empresa é selecionada, gera o gráfico correspondente
    if empresa_selecionada:
        rolling_graphs.gerar_grafico(empresa_selecionada)
        rolling_graphs.gerar_tabela(empresa_selecionada)

