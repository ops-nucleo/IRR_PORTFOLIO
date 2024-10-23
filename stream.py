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
                    dividendo_ano = df_filtrado[(df_filtrado['Ticker'] == empresa) & (df_filtrado['Ano Referência'] == ano)]['Dividendo']
                    linha[ano] = dividendo_ano.values[0] if not dividendo_ano.empty else np.nan
                df_dividendos = df_dividendos.append(linha, ignore_index=True)
    
            # Formatando os números no estilo americano
            for ano in anos:
                df_dividendos[ano] = pd.to_numeric(df_dividendos[ano], errors='coerce').fillna(0).apply(lambda x: f"{x:,.2f}" if not pd.isna(x) else 'nan')
            return df_dividendos
    
        def gerar_html_tabela(self, df, titulo):
            # Gera o código HTML da tabela com formatação e ajuste de largura
            html = f"<h3>{titulo}</h3>"
            html += '<table style="width:100%; border-collapse: collapse; margin: auto;">'  # Ajustando largura para 100% da coluna
            html += '<thead><tr style="background-color: #f2f2f2;">'
    
            # Cabeçalhos da tabela
            for col in df.columns:
                html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{col}</th>'
            html += '</tr></thead><tbody>'
    
            # Linhas da tabela
            for i, row in df.iterrows():
                html += '<tr>'
                for col in df.columns:
                    html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: left;">{row[col]}</td>'
                html += '</tr>'
    
            html += '</tbody></table>'
            return html
    
        def mostrar_tabelas(self):
            # Título ajustado
            st.markdown("<h1 style='text-align: center; margin-top: -50px;'>IRR Portfólio e Lucro</h1>", unsafe_allow_html=True)
    
            # Espaçamento negativo para mover o select box mais para cima
            st.markdown("<div style='margin-top: -60px;'></div>", unsafe_allow_html=True)
    
            # Filtro para selecionar a data no formato brasileiro (ajustando tamanho do botão)
            st.markdown("""
                <style>
                div[data-baseweb="select"] {
                    width: 50%;  /* Reduz o tamanho do selectbox para 50% */
                    margin: auto;  /* Centraliza o selectbox */
                    display: block;
                }
                </style>
            """, unsafe_allow_html=True)
    
            # Selectbox sozinho no topo
            datas_disponiveis = self.filtrar_datas()
            data_selecionada = st.selectbox('Selecione a data de atualização:', datas_disponiveis)
    
            # Exibir tabelas lado a lado, à esquerda
            col1, col2 = st.columns([1, 1])  # Usei 1:1 para manter as duas tabelas na metade da tela
    
            with col1:
                # Criando a tabela Portfolio
                df_portfolio = self.criar_tabela_portfolio(self.filtrar_por_data(data_selecionada))
                html_portfolio = self.gerar_html_tabela(df_portfolio, "Portfolio")
                st.markdown(html_portfolio, unsafe_allow_html=True)
    
            with col2:
                # Criando a tabela Lucro
                df_lucro = self.criar_tabela_lucro(self.filtrar_por_data(data_selecionada), data_selecionada)
                html_lucro = self.gerar_html_tabela(df_lucro, "Lucro")
                st.markdown(html_lucro, unsafe_allow_html=True)
    
            # Reservar espaço para mais duas tabelas na segunda metade
            col3, col4 = st.columns([1, 1])
            with col3:
                # Criando a tabela de Dividendos
                df_dividendos = self.criar_tabela_dividendos(self.filtrar_por_data(data_selecionada), data_selecionada)
                html_dividendos = self.gerar_html_tabela(df_dividendos, "Dividendos")
                st.markdown(html_dividendos, unsafe_allow_html=True)
    
            with col4:
                st.write("Aqui entra a tabela de P/E e TIR")  # Placeholder para a tabela de P/E e TIR
