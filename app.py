import streamlit as st
import pandas as pd
import pdfplumber
import io

def limpar_string(txt):
    """Remove aspas, quebras de linha e espaços extras comuns no seu relatório."""
    if txt:
        return str(txt).replace('"', '').replace('\n', '').strip()
    return ""

def limpar_valor_monetario(valor_str):
    """Converte o valor do relatório (ex: 11,99) para formato numérico (11.99)."""
    if not valor_str:
        return 0.0
    limpo = limpar_string(valor_str).replace('R$', '').replace(' ', '')
    # Remove ponto de milhar e troca vírgula por ponto decimal
    limpo = limpo.replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except:
        return 0.0

def extrair_dados_pdf_brunelis(pdf_file):
    dados_finais = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            # Extraímos o texto bruto para garantir que não perderemos linhas que não pareçam tabelas
            linhas = pagina.extract_text().split('\n')
            
            # Tentativa de extração por tabela estruturada primeiro
            tabela = pagina.extract_table()
            
            if tabela:
                for linha in tabela:
                    # Verifica se a linha tem as colunas esperadas e não é o cabeçalho
                    if linha and len(linha) >= 7 and "Emissão" not in str(linha[0]):
                        dados_finais.append({
                            "Emissão": limpar_string(linha[0]),
                            "Série": limpar_string(linha[1]),
                            "Número": limpar_string(linha[2]),
                            "Situação": limpar_string(linha[3]),
                            "Chave de acesso": limpar_string(linha[4]),
                            "CFOP": limpar_string(linha[5]),
                            "Valor (R$)": limpar_valor_monetario(linha[6])
                        })
            
    return pd.DataFrame(dados_finais)

# Interface Streamlit
st.set_page_config(page_title="Auditoria Fiscal Bruneli's", layout="wide")
st.title("📑 Conversor de Notas Fiscais (PDF para Excel)")

uploaded_file = st.file_uploader("Suba o arquivo 'Documentos de entradas e saídas'", type="pdf")

if uploaded_file:
    with st.spinner("Lendo dados do relatório..."):
        df = extrair_dados_pdf_brunelis(uploaded_file)
        
    if not df.empty:
        st.success(f"Foram processadas {len(df)} notas fiscais com sucesso.")
        
        # Resumo Financeiro
        total_acumulado = df["Valor (R$)"].sum()
        st.metric("Soma Total das Notas no PDF", f"R$ {total_acumulado:,.2f}")
        
        # Tabela na tela
        st.dataframe(df, use_container_width=True)
        
        # Gerar o arquivo Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # A Chave de Acesso é salva como texto para não perder números
            df.to_excel(writer, index=False, sheet_name='Relatorio_Fiscal')
        
        output.seek(0)
        
        # Botão de Download
        st.download_button(
            label="📥 Baixar Planilha para Comparar Valores",
            data=output,
            file_name="conferência_fiscal_brunelis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("O sistema não conseguiu identificar a tabela. O PDF pode estar protegido ou em um formato de imagem.")
