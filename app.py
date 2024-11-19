import streamlit as st
from docx import Document
import pandas as pd
import os
from datetime import datetime
import io

# Configuração da página
st.set_page_config(
    page_title="Sistema de Contratos - Consult Contabilidade",
    page_icon="📄",
    layout="wide"
)

# Função para carregar ou criar banco de dados de modelos
def load_templates():
    if 'templates.csv' not in os.listdir():
        df = pd.DataFrame(columns=['nome', 'arquivo', 'variaveis'])
        df.to_csv('templates.csv', index=False)
    return pd.read_csv('templates.csv')

# Função para salvar modelo
def save_template(nome, arquivo, variaveis):
    df = load_templates()
    new_row = pd.DataFrame({
        'nome': [nome],
        'arquivo': [arquivo],
        'variaveis': [variaveis]
    })
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv('templates.csv', index=False)

# Função para processar documento
def process_document(doc_bytes, replacements):
    doc = Document(io.BytesIO(doc_bytes))
    
    # Substituir todas as variáveis no documento
    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if f'#{key}#' in paragraph.text:
                paragraph.text = paragraph.text.replace(f'#{key}#', value)
    
    # Também substituir em tabelas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in replacements.items():
                    if f'#{key}#' in cell.text:
                        cell.text = cell.text.replace(f'#{key}#', value)
    
    # Salvar documento modificado
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

# Interface principal
def main():
    # Cabeçalho
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("logo.png", use_column_width=True)
    st.title("Sistema de Contratos - Consult Contabilidade")
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu",
        ["Gerar Contrato", "Gerenciar Modelos"]
    )
    
    if menu == "Gerar Contrato":
        show_contract_generation()
    else:
        show_template_management()

def show_contract_generation():
    st.header("Gerar Contrato")
    
    # Carregar modelos disponíveis
    df_templates = load_templates()
    if len(df_templates) == 0:
        st.warning("Nenhum modelo cadastrado. Por favor, adicione um modelo primeiro.")
        return
    
    # Selecionar modelo
    template_name = st.selectbox(
        "Selecione o modelo",
        df_templates['nome'].tolist()
    )
    
    # Carregar template selecionado
    template = df_templates[df_templates['nome'] == template_name].iloc[0]
    variables = eval(template['variaveis'])  # Lista de variáveis do template
    
    # Criar formulário para preenchimento
    with st.form("contract_form"):
        st.subheader("Preencha as informações")
        
        # Criar campos dinâmicos baseados nas variáveis do template
        values = {}
        col1, col2 = st.columns(2)
        
        for i, var in enumerate(variables):
            with col1 if i % 2 == 0 else col2:
                values[var] = st.text_input(var.replace('_', ' ').title())
        
        submitted = st.form_submit_button("Gerar Contrato")
        
        if submitted:
            try:
                # Carregar documento base
                doc_bytes = template['arquivo'].encode()
                
                # Processar documento
                output = process_document(doc_bytes, values)
                
                # Oferecer download
                st.download_button(
                    label="📥 Download do Contrato",
                    data=output,
                    file_name=f"contrato_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                st.success("Contrato gerado com sucesso!")
                
            except Exception as e:
                st.error(f"Erro ao gerar contrato: {str(e)}")

def show_template_management():
    st.header("Gerenciar Modelos")
    
    # Mostrar modelos existentes
    df_templates = load_templates()
    if len(df_templates) > 0:
        st.subheader("Modelos Cadastrados")
        st.dataframe(df_templates[['nome', 'variaveis']])
    
    # Adicionar novo modelo
    st.subheader("Adicionar Novo Modelo")
    
    with st.form("template_form"):
        nome = st.text_input("Nome do Modelo")
        arquivo = st.file_uploader("Arquivo do Modelo (.docx)", type=['docx'])
        variaveis = st.text_area(
            "Variáveis (uma por linha)",
            help="Digite as variáveis do modelo, uma em cada linha"
        )
        
        submitted = st.form_submit_button("Salvar Modelo")
        
        if submitted:
            if nome and arquivo and variaveis:
                try:
                    # Processar variáveis
                    vars_list = [v.strip() for v in variaveis.split('\n') if v.strip()]
                    
                    # Salvar modelo
                    save_template(
                        nome,
                        arquivo.read(),
                        str(vars_list)
                    )
                    
                    st.success("Modelo salvo com sucesso!")
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao salvar modelo: {str(e)}")
            else:
                st.error("Por favor, preencha todos os campos")

if __name__ == "__main__":
    main()