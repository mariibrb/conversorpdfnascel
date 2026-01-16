import streamlit as st
import pandas as pd
import pdfplumber
import io

def limpar_valor(valor_str):
    """Converte o valor do PDF (R$ 1.234,56) para número decimal (1234.56)."""
    if not valor_str:
        return 0.0
    # Remove R$, espaços e quebras de linha
    limpo = str(valor_str).replace('R$', '').replace('\n', '').replace(' ', '').strip()
    # Remove ponto de milhar e troca vírgula por ponto
    limpo = limpo.replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except:
        return 0.0

def processar_pdf_brunelis(pdf_file):
    """Extrai os dados especificamente do layout do seu relatório fiscal."""
    dados_extraidos = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            tabela = pagina.extract_table()
            if tabela:
                for linha in tabela:
                    # O seu arquivo tem "Emissão" no cabeçalho. Pulamos essa linha.
                    if linha[0] and "Emissão" not in str(linha[0]):
                        # Extraímos os campos: Número (índice 2), Chave (índice 4) e Valor (índice 6)
                        # Limpamos o \n que existe em todos os campos do seu PDF
                        try:
                            emissao = str(linha[0]).replace('\n', '').strip()
                            numero = str(linha[2]).replace('\n', '').strip()
                            situacao = str(linha[3]).replace('\n', '').strip()
                            chave = str(linha[4]).replace('\n', '').strip()
                            valor_original = linha[6]
                            valor_numerico = limpar_valor(valor_original)
                            
                            dados_extraidos.append({
                                "Emissão": emissao,
                                "Número": numero,
                                "Situação": situacao,
                                "Chave de acesso": chave,
                                "Valor (R$)": valor_numerico
                            })
                        except IndexError:
                            continue
                            
    return pd.DataFrame(dados_extraidos)

# Interface do Streamlit
st.set_page_config(page_title="Conversor Fiscal Bruneli's", layout="wide")
st.title("📊 Conversor de Relatório Fiscal para Excel")

uploaded_file = st.file_uploader("Suba o PDF 'Documentos de entradas e saídas' aqui", type="pdf")

if uploaded_file is not None:
    with st.spinner('Extraindo dados do PDF...'):
        df = processar_pdf_brunelis(uploaded_file)
        
    if not df.empty:
        st.success(f"Foram encontradas {len(df)} notas fiscais.")
        
        # Exibe o valor total para você conferir com o rodapé do PDF
        total_fiscal = df["Valor (R$)"].sum()
        st.metric("Valor Total das Notas", f"R$ {total_fiscal:,.2f}")
        
        # Preview da tabela
        st.dataframe(df, use_container_width=True)
        
        # Preparação do arquivo Excel para download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Garantimos que a Chave de Acesso não seja convertida para número científico
            df.to_excel(writer, index=False, sheet_name='Relatorio_Auditoria')
            
        buffer.seek(0)
        
        st.download_button(
            label="📥 Baixar Relatório em Excel",
            data=buffer,
            file_name="relatorio_fiscal_convertido.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Não foi possível ler as tabelas deste PDF. Verifique se ele é o relatório original.")
