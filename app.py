import streamlit as st
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# Template fixo do contrato
TEMPLATE = """CONTRATO DE PRESTAÇÃO DE SERVIÇOS CONTÁBEIS

Por este instrumento particular de Contrato de Prestação de Serviços Contábeis que fazem entre si, de um lado, #RAZAO_SOCIAL#, com sede na cidade de #CIDADE#, Estado do #ESTADO#, na #ENDERECO#, #NUMERO#, inscrita no CNPJ sob nº #CNPJ#, neste ato representada por seu sócio administrador #NOME_RESPONSAVEL#, doravante denominada CONTRATANTE, e de outro lado CONSULT ASSESSORIA CONTÁBIL LTDA, pessoa jurídica de direito privado, inscrita no CNPJ sob nº 11.111.111/0001-11, com sede na Avenida Principal, 123, Centro, Maringá/PR, neste ato representada por seu sócio administrador João da Silva, brasileiro, casado, contador, inscrito no CRC sob nº PR-123456/O-1, doravante denominada CONTRATADA, têm entre si justo e contratado o seguinte:

CLÁUSULA PRIMEIRA - DO OBJETO

1.1. O presente contrato tem por objeto a prestação de serviços de contabilidade, compreendendo os seguintes serviços:
a) Escrituração contábil;
b) Escrituração fiscal;
c) Folha de pagamento;
d) Declarações fiscais;
e) Demonstrações contábeis.

CLÁUSULA SEGUNDA - DO PREÇO E FORMA DE PAGAMENTO

2.1. Pelos serviços prestados, a CONTRATANTE pagará à CONTRATADA o valor mensal de R$ #VALOR_CONTRATO# (#VALOR_EXTENSO#), com vencimento todo dia #DIA_VENCIMENTO# de cada mês.

CLÁUSULA TERCEIRA - DA VIGÊNCIA

3.1. O presente contrato tem vigência de 12 (doze) meses, iniciando-se em #DATA_INICIO#, podendo ser renovado por iguais períodos.

CLÁUSULA QUARTA - DAS OBRIGAÇÕES

4.1. São obrigações da CONTRATADA:
a) Executar os serviços com zelo e dedicação;
b) Manter sigilo sobre as informações da CONTRATANTE;
c) Cumprir todos os prazos legais.

4.2. São obrigações da CONTRATANTE:
a) Fornecer toda documentação necessária;
b) Efetuar os pagamentos nos prazos acordados;
c) Comunicar à CONTRATADA qualquer alteração.

E por estarem assim justos e contratados, firmam o presente em duas vias de igual teor.

#CIDADE#, #DATA_ASSINATURA#


_______________________________
#RAZAO_SOCIAL#
CNPJ: #CNPJ#
#NOME_RESPONSAVEL#


_______________________________
CONSULT ASSESSORIA CONTÁBIL LTDA
CNPJ: 11.111.111/0001-11
João da Silva
CRC PR-123456/O-1"""

def init_session_state():
    if 'template_content' not in st.session_state:
        st.session_state.template_content = TEMPLATE
    if 'variables' not in st.session_state:
        # Extrair variáveis do template
        variables = re.findall(r'#(\w+)#', TEMPLATE)
        st.session_state.variables = sorted(set(variables))

def format_cnpj(cnpj):
    """Formata o CNPJ"""
    cnpj = re.sub(r'\D', '', cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def generate_docx(values):
    """Gera documento Word formatado"""
    doc = Document()
    
    # Configurar margens
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(3)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(3)
    
    # Configurar estilo padrão
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)
    
    # Substituir variáveis
    content = TEMPLATE
    for var, value in values.items():
        content = content.replace(f"#{var}#", value)
    
    # Processar parágrafos
    for paragraph in content.split('\n'):
        if not paragraph.strip():
            continue
            
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(0)
        
        # Título centralizado
        if "CONTRATO DE PRESTAÇÃO" in paragraph:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(paragraph)
            run.bold = True
        # Cabeçalhos de cláusulas
        elif paragraph.startswith("CLÁUSULA"):
            run = p.add_run(paragraph)
            run.bold = True
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.add_run(paragraph)
    
    # Converter para bytes
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    
    return doc_bytes

def main():
    st.set_page_config(
        page_title="Gerador de Contratos",
        page_icon="📄",
        layout="wide"
    )

    init_session_state()

    st.title("Gerador de Contratos")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Preencher Dados")
        values = {}
        
        # Campos especiais com formatação
        for var in st.session_state.variables:
            if var == "CNPJ":
                value = st.text_input(
                    "CNPJ",
                    help="Formato: XX.XXX.XXX/XXXX-XX",
                    key=var
                )
                values[var] = format_cnpj(value)
            elif var == "VALOR_CONTRATO":
                values[var] = st.text_input(
                    "Valor do Contrato (R$)",
                    help="Exemplo: 1.000,00",
                    key=var
                )
            elif var == "VALOR_EXTENSO":
                values[var] = st.text_input(
                    "Valor por Extenso",
                    help="Exemplo: um mil reais",
                    key=var
                )
            elif var == "DIA_VENCIMENTO":
                values[var] = st.text_input(
                    "Dia do Vencimento",
                    help="Exemplo: 05",
                    key=var
                )
            elif var == "DATA_INICIO" or var == "DATA_ASSINATURA":
                values[var] = st.text_input(
                    var.replace("_", " ").title(),
                    help="Exemplo: 01/01/2024",
                    key=var
                )
            else:
                values[var] = st.text_input(
                    var.replace("_", " ").title(),
                    key=var
                )

        if st.button("Gerar Contrato", type="primary"):
            empty_fields = [var for var, val in values.items() if not val.strip()]
            if empty_fields:
                st.error("Preencha todos os campos!")
                for field in empty_fields:
                    st.warning(field.replace("_", " ").title())
                return

            try:
                doc_bytes = generate_docx(values)
                
                st.download_button(
                    "⬇️ Baixar Contrato (DOCX)",
                    doc_bytes,
                    file_name=f"contrato_{values['RAZAO_SOCIAL']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                st.success("Contrato gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao gerar contrato: {str(e)}")

    with col2:
        st.subheader("Prévia do Contrato")
        preview = TEMPLATE
        for var, val in values.items():
            preview = preview.replace(f"#{var}#", val if val else f"[{var}]")
        st.text_area("", value=preview, height=600, disabled=True)

if __name__ == "__main__":
    main()
