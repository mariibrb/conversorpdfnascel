import streamlit as st
import pandas as pd
import pdfplumber
import io

def limpar_e_converter(valor_str):
    """Limpa caracteres especiais e converte para float para cálculos fiscais."""
    if not valor_str:
        return 0.0
    # Remove quebras de linha, R$, pontos de milhar e ajusta a vírgula decimal
    limpo = str(valor_str).replace('\n', '').replace('R$', '').replace(' ', '')
    limpo = limpo.replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except:
        return 0.0

def extrair_dados_pdf(pdf_file):
    dados_finais = []
    # Colunas baseadas exatamente no cabeçalho do seu documento
    colunas = ["Emissão", "Série", "Número", "Situação", "Chave de acesso", "CFOP", "Valor (R$)"]
    
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            tabela = pagina.extract_table()
            if tabela:
                for linha in tabela:
                    # Ignora linhas vazias ou o próprio cabeçalho que se repete nas páginas
                    if linha[0] and "Emissão" not in linha[0]:
                        # Limpa quebras de linha de todas as colunas
                        linha_tratada = [str(c).replace('\n', ' ').strip() for c in linha]
                        
                        # Converte a coluna de valor (índice 6) para número real
                        if len(linha_tratada) >= 7:
                            linha_tratada[6] = limpar_e_converter(linha[6])
                        
                        dados_finais.append(linha_tratada)
    
    return pd.DataFrame(dados_finais, columns=colunas)

# Interface Streamlit
st.set_page_config(page_title="Conversor Fiscal Bruneli's", layout="wide")
st.title("📑 Auditoria Fiscal: PDF para Excel")

upload = st.file_uploader("Arraste o relatório de Entradas e Saídas (PDF) aqui", type="pdf")

if upload:
    with st.spinner("Extraindo dados e convertendo valores..."):
        df = extrair_dados_pdf(upload)
        
        if not df.empty:
            st.success(f"Sucesso! {len(df)} notas fiscais encontradas.")
            
            # Cálculo de conferência
            valor_total_pdf = df["Valor (R$)"].sum()
            st.metric("Soma Total das Notas (Conferência)", f"R$ {valor_total_pdf:,.2f}")
            
            # Exibição da tabela
            st.dataframe(df, use_container_width=True)
            
            # Geração do Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Relatorio_Fiscal')
            
            st.download_button(
                label="📥 Baixar Excel para Auditoria",
                data=buffer.getvalue(),
                file_name="relatorio_fiscal_convertido.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Não foi possível extrair dados deste PDF. Verifique o formato.")
