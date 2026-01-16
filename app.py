import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def limpar_texto(texto):
    if texto:
        return str(texto).replace('\n', ' ').strip()
    return ""

def converter_valor(valor_str):
    if not valor_str:
        return 0.0
    # Remove \n, R$, espaços e ajusta vírgula para ponto
    limpo = str(valor_str).replace('\n', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(limpo)
    except:
        return 0.0

def extrair_dados_fiscal(pdf_file):
    dados_completos = []
    colunas = ["Emissão", "Série", "Número", "Situação", "Chave de acesso", "CFOP", "Valor (R$)"]
    
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            tabela = pagina.extract_table()
            if tabela:
                for linha in tabela:
                    # Filtra para pegar apenas linhas que parecem conter dados (ex: série ou número preenchido)
                    if linha[0] and "Emissão" not in linha[0]:
                        linha_limpa = [limpar_texto(celula) for celula in linha]
                        # Tratamento específico para a coluna de Valor (índice 6)
                        if len(linha_limpa) >= 7:
                            linha_limpa[6] = converter_valor(linha[6])
                        dados_completos.append(linha_limpa)
    
    return pd.DataFrame(dados_completos, columns=colunas)

def main():
    st.set_page_config(page_title="Auditoria Fiscal - PDF para Excel", layout="wide")
    st.title("📑 Conversor de Notas Fiscais para Auditoria")
    
    arquivo = st.file_uploader("Suba seu PDF de Entradas e Saídas", type="pdf")
    
    if arquivo:
        df = extrair_dados_fiscal(arquivo)
        
        if not df.empty:
            st.subheader("Visualização dos Dados Extraídos")
            st.dataframe(df, use_container_width=True)
            
            # Resumo para conferência rápida
            total_pdf = df["Valor (R$)"].sum()
            qtd_notas = len(df)
            
            col1, col2 = st.columns(2)
            col1.metric("Quantidade de Notas", qtd_notas)
            col2.metric("Valor Total Acumulado", f"R$ {total_pdf:,.2f}")

            # Botão de Exportação
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Auditoria')
            
            st.download_button(
                label="📥 Baixar Excel para Comparar com Sistema",
                data=output.getvalue(),
                file_name="auditoria_fiscal.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.warning("💡 Dica: Verifique se o valor total acima bate com o rodapé do seu PDF. Se houver diferença, cheque as notas com situação 'Cancelada' ou 'Inutilizada'.")

if __name__ == "__main__":
    main()
