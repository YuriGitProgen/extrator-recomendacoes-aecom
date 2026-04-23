import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# --- Configurações da Página ---
st.set_page_config(
    page_title="Extrator de Recomendações AECOM",
    page_icon="📄",
    layout="wide"
)

# --- Funções de Extração ---

def extract_text_from_pdf(pdf_file):
    """Extrai texto de todas as páginas de um PDF."""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_tables_from_pdf(pdf_file):
    """Extrai tabelas de todas as páginas de um PDF."""
    all_tables = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if table: # Garante que a tabela não está vazia
                    df = pd.DataFrame(table[1:], columns=table[0]) # Primeira linha como cabeçalho
                    df['Pagina'] = page_num + 1 # Adiciona a página da tabela
                    all_tables.append(df)
    return all_tables

def find_recommendations(text, keywords, stop_phrases):
    """
    Encontra recomendações no texto usando palavras-chave e frases de parada.
    Retorna uma lista de dicionários com 'Texto Original' e 'Página'.
    """
    recommendations = []

    # Padrões para identificar o início de uma recomendação
    # Ajuste estes padrões conforme os exemplos que você forneceu
    # Ex: "A auditoria recomenda", "A AECOM recomenda", "Recomenda-se que"
    # Adicionei alguns baseados nos seus exemplos
    patterns = [
        r"A auditoria recomenda[^.]*\.",
        r"A AECOM recomenda[^.]*\.",
        r"Recomenda-se que[^.]*\.",
        r"É fundamental que[^.]*\.",
        r"É essencial para[^.]*\.",
        r"É importante que[^.]*\.",
        r"Importante que sejam mantidos[^.]*\.",
        r"Manter o monitoramento contínuo[^.]*\.",
        r"Realizar o desassoreamento[^.]*\.",
        r"Elaborar um Manual de Operação específico[^.]*\.",
        r"Realizar manutenção preventiva[^.]*\.",
        r"Implementar proteção adequada[^.]*\.",
        r"Manter o monitoramento contínuo e realizar manutenções necessárias[^.]*\.",
        r"Adotar abordagem robusta e integrada[^.]*\.",
        r"Incorporar ao planejamento uma margem de segurança temporal[^.]*\.",
        r"Apresentar memoriais técnicos e estudos[^.]*\.",
        r"Realizar análise geotécnica[^.]*\.",
        r"Implementar medidas de proteção nas margens[^.]*\.",
        r"Manter o acompanhamento contínuo dos instrumentos[^.]*\.",
        r"Realizar inspeção local sempre que houver movimentação anormal[^.]*\.",
        r"Detalhar nos relatórios a localização dos eventos microssísmicos[^.]*\.",
        r"Concluir as etapas de revisão de critérios e interpretação dos ensaios[^.]*\.",
        r"Garantir a comunicação eficiente de alertas[^.]*\.",
        r"Esclarecer nos relatórios como os ensaios sem contrapressão contribuem[^.]*\.",
        r"Apresentar no relatório final do estudo tensão-deformação as condições de moldagem[^.]*\.",
        r"Remover os equipamentos remanescentes[^.]*\.",
        r"Realizar acompanhamento detalhado dos instrumentos[^.]*\.",
        r"Manter acompanhamento contínuo dos instrumentos[^.]*\.",
        r"Avaliar a representatividade dos dados das investigações geotécnicas[^.]*\.",
        r"Esclarecer os motivos do cancelamento das investigações[^.]*\.",
        r"Avaliar a perda quantitativa e qualitativa decorrente do cancelamento das investigações[^.]*\.",
        r"Apresentar os resultados do desassoreamento e levantamento batimétrico[^.]*\.",
        r"Esclarecer as medidas de mitigação para prevenir erosões[^.]*\.",
        r"Detalhar a solução proposta para o reaterro e conformação do canal Leste[^.]*\.",
        r"Definir o tipo de material, características geotécnicas e hidráulicas[^.]*\.",
        r"Apresentar informações sobre o tratamento do contato entre o reaterro[^.]*\.",
        r"Esclarecer a configuração da saída do fluxo a jusante[^.]*\.",
        r"Adequar o canal Leste da PDE Menezes III[^.]*\.",
        r"Regularizar áreas com inclinações negativas[^.]*\.",
        r"Ajustar o sequenciamento das frentes de escavação[^.]*\.",
        r"Restringir o tráfego e posicionamento de equipamentos[^.]*\.",
        r"Reforçar as medidas de segurança e o monitoramento[^.]*\.",
        r"Realizar monitoramento pós-obras com implantação de marcos de referência/topográficos[^.]*\.",
        r"Garantir que a movimentação de solo e intervenções[^.]*\.",
        r"Realizar atualização topográfica e fotográfica da área[^.]*\.",
        r"Substituir imediatamente o revestimento do Canal de desvio 2[^.]*\.",
        r"Concluir com brevidade as adequações no Canal de desvio 2[^.]*\.",
        r"Realizar inspeções frequentes nos Canais de desvio 1 e 2 e executar prontamente manutenções e reparos[^.]*\.",
        r"Manter acompanhamento contínuo dos instrumentos com comportamento atípico ou inconclusivo[^.]*\.",
        r"Verificar e validar em campo o correto funcionamento e as leituras dos instrumentos[^.]*\.",
        r"Conduzir a campanha adicional sem interferir nos cronogramas[^.]*\.",
        r"Disponibilizar a especificação técnica[^.]*\.",
        r"Apresentar plano objetivo para otimizar o caminho crítico[^.]*\.",
        r"Implementar controles de poropressão na fundação e no reservatório[^.]*\.",
        r"Priorizar soluções de drenagem para melhorar o desempenho hidráulico[^.]*\.",
        r"Gerir incrementos de carga durante as obras para mitigar deformações[^.]*\.",
        r"Monitorar a eficiência do sump a montante e a jusante[^.]*\.",
        r"Realizar desassoreamentos com frequência adequada[^.]*\.",
        r"Colocar em operação os instrumentos adicionais instalados[^.]*\.",
        r"Avaliar e reportar os ajustes necessários nos estudos hidrogeológicos[^.]*\.",
        r"Concluir com brevidade as obras das drenagens definitivas[^.]*\.",
        r"Apresentar o procedimento executivo de reaterro e conformação[^.]*\.",
        r"Apresentar cronograma detalhado das etapas de remoção[^.]*\.",
        r"Implantar o sump operacional provisório para contenção de sedimentos[^.]*\.",
        r"Apresentar o detalhamento e os dimensionamentos do sistema de drenagem superficial provisória[^.]*\.",
        r"Adotar medidas de segurança e planos de contingência específicos[^.]*\.",
        r"Remover prontamente o material desassoreado depositado[^.]*\.",
        r"Definir e implementar medidas de estabilização de margens[^.]*\.",
        r"Remover os sólidos sedimentados nos degraus da CEP‑1[^.]*\.",
        r"Executar proteção superficial nos canais provisórios e nas planícies adjacentes[^.]*\.",
        r"Realizar monitoramento contínuo dos canais provisórios e aplicar medidas corretivas imediatas[^.]*\.",
        r"Disponibilizar os volumes considerados no estudo de ruptura hipotética[^.]*\.",
        r"Manter o monitoramento sistemático do talude da MRS[^.]*\.",
        r"Manter monitoramento contínuo e controle de acesso na parede Oeste da cava[^.]*\.",
        r"Executar com brevidade as adequações na ruptura da parede Sudeste da Cava de Feijão[^.]*\.",
        r"Realizar monitoramento contínuo das condições e do desempenho da estrutura e executar prontamente as manutenções necessárias[^.]*\.",
        r"Realizar inspeções frequentes nos canais de desvio e executar rapidamente as manutenções ou reparos necessários[^.]*\.",
        r"Monitorar continuamente as condições e o desempenho da barragem B-VI e executar prontamente as manutenções necessárias[^.]*\.",
        r"Monitorar continuamente as condições e o desempenho da barragem Menezes I e executar prontamente as manutenções necessárias[^.]*\.",
        r"Monitorar continuamente as condições e o desempenho da barragem Menezes II e executar prontamente as manutenções necessárias[^.]*\.",
        r"Monitorar continuamente as condições e o desempenho da barragem Capim Branco e realizar as manutenções necessárias[^.]*\.",
        r"Monitorar continuamente as condições e o desempenho da barragem Lagoa Azul e executar prontamente as manutenções necessárias[^.]*\.",
        r"Concluir a recomposição vegetal e a desmobilização do Dique de Concreto conforme previsto[^.]*\.",
        r"Monitorar continuamente a PDE Menezes III, especialmente durante intervenções e no período chuvoso[^.]*\.",
        r"Realizar retaludamentos contínuos e implantar sistema de drenagem superficial eficaz e permanente[^.]*\.",
        r"Acompanhar a tendência negativa do sensor 15, avaliando precipitação e qualidade dos dados[^.]*\.",
        r"Avaliar e mitigar riscos de atrasos e descontinuidade operacional no cronograma de remoção integral dos rejeitos[^.]*\.",
        r"Incluir análises de estabilidade de todas as seções, identificação de mecanismos críticos, critérios de aceitação, memorial de cálculo e projeto geométrico consolidado[^.]*\.",
        r"Estabelecer critérios operacionais objetivos para remoção de rejeitos[^.]*\.",
        r"Incorporar dados dos testes de remoção de setembro de 2023 nos estudos Tensão-Deformação[^.]*\.",
        r"Realizar análises de sensibilidade para avaliar influência da variação dos parâmetros do modelo[^.]*\.",
        r"Apresentar os prazos previstos para execução das investigações e instalação dos novos instrumentos[^.]*\.",
        r"Realizar avaliação aprofundada das condições de instalação e operação dos instrumentos[^.]*\.",
        r"Realinhar ou substituir a régua linimétrica do reservatório[^.]*\.",
        r"Disponibilizar desenhos e relatórios técnicos atualizados do tratamento definitivo da erosão e trinca do Talude MRS[^.]*\.",
        r"Avaliar ajuste da estratégia executiva para que a obra avance de montante para jusante[^.]*\.",
        r"Restabelecer funcionalidade da drenagem, realizando inspeção e limpeza dos barbacãs[^.]*\.",
        r"Disponibilizar projeto definitivo completo de drenagem superficial da cava[^.]*\.",
        r"Reforçar e intensificar o monitoramento da erosão da face Oeste[^.]*\.",
        r"Disponibilizar projeto definitivo completo de drenagem superficial do Aterro Norte[^.]*\.",
        r"Apresentar comparação do volume disponível à montante da BH-2 e das malhas 2 e 3 com o volume necessário[^.]*\.",
        r"Apresentar protocolos de execução da escavação para remoção do material dragado dos sumps da dragagem[^.]*\.",
        r"Avaliar adoção de tempo de retorno mínimo de 2 anos para o canal provisório implantado após descomissionamento do Dique 2[^.]*\.",
        r"Manter o monitoramento contínuo das condições e do desempenho da B‑I e executar manutenções necessárias de forma imediata[^.]*\.",
        r"Manter a drenagem superficial da PDE Norte‑01 e da B‑VII em boas condições[^.]*\.",
        r"Disponibilizar o Projeto Básico e apresentar o Projeto Detalhado completo da drenagem definitiva da Cava[^.]*\.",
        r"Limpar a caixa de passagem na área da ponte P2 para prevenir comprometimento do desempenho hidráulico[^.]*\.",
        r"Adotar estratégias operacionais para evitar o lançamento de águas de baixa qualidade no rio Paraopeba[^.]*\.",
        r"Monitorar continuamente as condições e o desempenho do anfiteatro da barragem B‑I e executar prontamente as manutenções necessárias[^.]*\.",
        r"Realizar inspeções frequentes nos canais de desvio 1 e 2 do anfiteatro da barragem B‑I e executar prontamente manutenções ou reparos necessários[^.]*\.",
        r"Restabelecer ou substituir os instrumentos de monitoramento geotécnico do anfiteatro da barragem B‑I[^.]*\.",
        r"Manter o acompanhamento do comportamento dos sensores do radar interferométrico no anfiteatro da barragem B‑I[^.]*\.",
        r"Apresentar formalmente cronograma revisado do estudo tensão‑deformação do anfiteatro da barragem B‑I[^.]*\.",
        r"Apresentar a Lista de Documentos completa do Projeto Detalhado de remoção de rejeitos do anfiteatro da barragem B‑I[^.]*\.",
        r"Avaliar a implantação de revestimento mais robusto no canal CDI do anfiteatro da barragem B‑I[^.]*\.",
        r"Detalhar o diâmetro dos blocos da pedra argamassada do CDII e dos pontos de deságue dos canais[^.]*\.",
        r"Detalhar nos desenhos o sistema de contenção de rejeitos e sedimentos do trecho inferior do anfiteatro da barragem B‑I[^.]*\.",
        r"Disponibilizar os desenhos de acesso entre o bota‑espera 1 e a ombreira esquerda[^.]*\.",
        r"Ajustar o limite de intervenção de obra indicado no desenho 2021GG‑N‑00403[^.]*\.",
        r"Apresentar justificativa técnica para o aumento do prazo de elaboração do Projeto Básico no cronograma de descaracterização da barragem B‑VI[^.]*\.",
        r"Inserir o limite da estrutura da barragem Menezes I na seção da crista obtida pelo levantamento geofísico por eletrorresistividade[^.]*\.",
        r"Correlacionar as seções horizontais em cota com as seções horizontais em profundidade no levantamento geofísico por eletrorresistividade da barragem Menezes I[^.]*\.",
        r"Apresentar justificativa técnica para o aumento do prazo de elaboração do Projeto Básico no cronograma de descaracterização da barragem Menezes II[^.]*\.",
        r"Especificar no cronograma o prazo para instalação de novos instrumentos de monitoramento da barragem Menezes II[^.]*\.",
        r"Recuperar o acesso de veículos à barragem B‑VII, garantindo condições seguras para inspeções e intervenções na estrutura[^.]*\.",
        r"Compatibilizar o cronograma de fechamento da PDE Menezes III com o cronograma de descaracterização da barragem Menezes I[^.]*\.",
        r"Apresentar relatório técnico consolidado sobre a condição da erosão ou ruptura na parede Oeste da Cava de Feijão[^.]*\.",
        r"Realizar as ações necessárias para retomada do volume mínimo a montante do sistema de contenção de rejeitos[^.]*\.",
        r"Avaliar medidas de segurança adicionais na região a jusante da BH‑2[^.]*\.",
        r"Monitorar continuamente as condições e o desempenho do anfiteatro da barragem B‑I e executar as manutenções necessárias[^.]*\.",
        r"Realizar inspeções frequentes nos canais de desvio e executar prontamente manutenções ou reparos quando identificados[^.]*\.",
        r"Acompanhar continuamente a confiabilidade e a continuidade das leituras dos instrumentos de monitoramento geotécnico[^.]*\.",
        r"Compatibilizar a espessura de escavação do estudo Tensão–Deformação com as premissas do sequenciamento construtivo do projeto detalhado[^.]*\.",
        r"Implantar integralmente as estruturas de contenção de sedimentos antes do início das atividades de escavação[^.]*\.",
        r"Manter continuamente as estruturas hidráulicas da barragem B‑VI e executar prontamente as correções necessárias[^.]*\.",
        r"Manter monitoramento contínuo das condições e do desempenho da barragem Menezes I[^.]*\.",
        r"Manter monitoramento contínuo das condições e do desempenho da barragem Menezes II[^.]*\.",
        r"Realizar manutenções e correções no acesso à barragem B‑VII para restabelecer o tráfego operacional[^.]*\.",
        r"Definir indicadores, métricas e critérios técnicos para monitorar a efetividade da regeneração ambiental no Dique de Concreto[^.]*\.",
        r"Monitorar as leiras e acessos adjacentes ao Canal Leste da PDE Menezes III e reforçar a proteção superficial quando necessário[^.]*\.",
        r"Apresentar monitoramento sistemático dos deslocamentos da erosão da parede Oeste da Cava de Feijão[^.]*\.",
        r"Manter volume disponível no reservatório da BH‑2 compatível com os estudos de ruptura hipotética do remanescente da B‑I[^.]*\.",
        r"Implementar estratégias de controle para evitar o lançamento de águas com alta turbidez no rio Paraopeba[^.]*\.",
        r"Executar proteção superficial nos canais provisórios e áreas adjacentes para minimizar erosões e carreamento de sedimentos[^.]*\."
    ]

    # Compila todos os padrões em uma única regex para busca eficiente
    combined_pattern = "|".join(patterns)

    # Divide o texto em linhas para tentar identificar a página
    lines = text.split('\n')

    for i, line in enumerate(lines):
        # Tenta encontrar o padrão de recomendação na linha
        match = re.search(combined_pattern, line, re.IGNORECASE)
        if match:
            recommendation_text = match.group(0).strip()

            # Limpa espaços extras e quebras de linha dentro da recomendação
            recommendation_text = re.sub(r'\s+', ' ', recommendation_text).strip()

            # Tenta encontrar o número da página na linha ou nas próximas linhas
            page_num = "N/A"
            for j in range(max(0, i-5), min(len(lines), i+5)): # Busca em um raio de 5 linhas
                page_match = re.search(r'(?:p\.|pág\.|página)\s*(\d+)', lines[j], re.IGNORECASE)
                if page_match:
                    page_num = page_match.group(1)
                    break

            recommendations.append({
                "Texto Original (trecho)": recommendation_text,
                "Local (página/seção)": f"p.{page_num}" if page_num != "N/A" else "N/A",
                "Texto da recomendação (normalizada)": "", # Será preenchido manualmente ou com PLN
                "ÁREA RESPONSAVEL": "", # Será preenchido manualmente ou com PLN
                "COMENTÁRIO/ENCAMINHAMENTO": ""
            })
    return recommendations

def process_pdf(uploaded_file):
    """Processa o PDF para extrair texto e tabelas, e encontrar recomendações."""

    # Extrair texto
    text_content = extract_text_from_pdf(uploaded_file)

    # Encontrar recomendações no texto
    # As palavras-chave e frases de parada podem ser ajustadas conforme necessário
    keywords = ["recomenda", "auditoria ressalta", "importante que", "necessário que", "fundamental que", "essencial para"]
    stop_phrases = ["anexo", "apêndice", "tabela", "figura"] # Frases para parar a busca antes dos anexos

    # Implementar a lógica para parar a busca antes dos anexos
    # Por simplicidade, vamos buscar em todo o texto por enquanto,
    # mas em uma versão mais avançada, você dividiria o texto antes dos anexos.
    # Para o seu caso, a regex já busca frases completas, o que é um bom começo.

    recommendations_from_text = find_recommendations(text_content, keywords, stop_phrases)

    # Extrair tabelas
    tables_from_pdf = extract_tables_from_pdf(uploaded_file)

    # Processar tabelas para recomendações implícitas
    recommendations_from_tables = []
    for df_table in tables_from_pdf:
        # Assumindo que a coluna 'Texto original (trecho)' ou similar contém as recomendações
        # E que a coluna 'Local (página/seção)' ou similar contém a página
        if 'Texto original (trecho)' in df_table.columns and 'Local (página/seção)' in df_table.columns:
            for index, row in df_table.iterrows():
                recommendations_from_tables.append({
                    "Texto Original (trecho)": row['Texto original (trecho)'],
                    "Local (página/seção)": row['Local (página/seção)'],
                    "Texto da recomendação (normalizada)": row.get('Texto da recomendação (normalizada)', ''),
                    "ÁREA RESPONSAVEL": row.get('ÁREA RESPONSAVEL', ''),
                    "COMENTÁRIO/ENCAMINHAMENTO": row.get('COMENTÁRIO/ENCAMINHAMENTO', '')
                })
        # Se a tabela não tiver essas colunas, podemos tentar extrair do texto da tabela
        else:
            for col in df_table.columns:
                for item in df_table[col].dropna():
                    # Tenta encontrar recomendações em cada célula da tabela
                    found_in_cell = find_recommendations(str(item), keywords, stop_phrases)
                    if found_in_cell:
                        # Adiciona a informação da página da tabela
                        for rec in found_in_cell:
                            rec['Local (página/seção)'] = f"Tabela na p.{df_table['Pagina'].iloc[0]}" if 'Pagina' in df_table.columns else "Tabela (página N/A)"
                            recommendations_from_tables.append(rec)

    # Combinar todas as recomendações
    all_recommendations = recommendations_from_text + recommendations_from_tables

    # Remover duplicatas (se houver)
    unique_recommendations = []
    seen_texts = set()
    for rec in all_recommendations:
        if rec["Texto Original (trecho)"] not in seen_texts:
            unique_recommendations.append(rec)
            seen_texts.add(rec["Texto Original (trecho)"])

    return pd.DataFrame(unique_recommendations)

# --- Interface Streamlit ---

st.title("📄 Extrator de Recomendações AECOM")
st.markdown("""
    Esta ferramenta permite extrair recomendações de relatórios em PDF,
    incluindo aquelas presentes em tabelas e no corpo do texto.
    O resultado é um arquivo Excel com as recomendações encontradas.
""")

uploaded_file = st.file_uploader("Faça o upload do arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.success("Arquivo PDF carregado com sucesso!")

    with st.spinner("Processando o PDF e extraindo recomendações..."):
        df_recommendations = process_pdf(uploaded_file)

    if not df_recommendations.empty:
        st.subheader("Recomendações Encontradas")
        st.dataframe(df_recommendations)

        # Botão para download do Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_recommendations.to_excel(writer, index=False, sheet_name='Recomendações')
        excel_buffer.seek(0)

        st.download_button(
            label="Baixar Recomendações em Excel",
            data=excel_buffer,
            file_name="recomendacoes_extraidas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.info(f"Total de recomendações encontradas: {len(df_recommendations)}")
        st.markdown("---")
        st.markdown("### Observações:")
        st.markdown("- A coluna 'Texto da recomendação (normalizada)' e 'ÁREA RESPONSAVEL' podem precisar de revisão manual para maior precisão, pois a extração automática é complexa.")
        st.markdown("- A detecção de 'Local (página/seção)' para recomendações em texto é uma estimativa baseada na proximidade de números de página.")
        st.markdown("- A extração de tabelas tenta identificar as colunas relevantes, mas pode ser necessário ajustar a lógica para formatos de tabela muito específicos.")

    else:
        st.warning("Nenhuma recomendação encontrada no PDF com os padrões atuais.")
        st.info("Você pode ajustar os padrões de busca no código-fonte (`app.py`) para tentar encontrar mais recomendações.")
