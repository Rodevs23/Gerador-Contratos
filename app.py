import streamlit as st
import json
from pathlib import Path
from docx import Document
import io
import shutil
import os

def read_docx(file):
    """Lê o conteúdo do arquivo .docx"""
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def save_template(name, content, variables, original_file):
    """Salva o template com suas variáveis e o arquivo original"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    # Salvar informações do template
    data = {
        "content": content,
        "variables": variables
    }
    
    with open(template_path / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Salvar arquivo original
    original_file.seek(0)
    with open(template_path / f"{name}.docx", "wb") as f:
        f.write(original_file.read())

def load_templates():
    """Carrega os templates salvos"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    templates = {}
    for file in template_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            templates[file.stem] = json.load(f)
    return templates

def process_document(template_name, values):
    """Processa o documento substituindo as variáveis"""
    template_path = Path("templates")
    
    # Carregar o documento original
    doc = Document(template_path / f"{template_name}.docx")
    
    # Substituir variáveis em cada parágrafo
    for paragraph in doc.paragraphs:
        for var_name, value in values.items():
            if f"#{var_name}#" in paragraph.text:
                # Preservar a formatação original copiando os runs
                runs = []
                for run in paragraph.runs:
                    if f"#{var_name}#" in run.text:
                        # Substituir a variável mantendo a formatação do run
                        new_text = run.text.replace(f"#{var_name}#", value)
                        run.text = new_text
    
    # Substituir variáveis nas tabelas, se houver
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for var_name, value in values.items():
                        if f"#{var_name}#" in paragraph.text:
                            for run in paragraph.runs:
                                if f"#{var_name}#" in run.text:
                                    new_text = run.text.replace(f"#{var_name}#", value)
                                    run.text = new_text
    
    # Retornar o documento em bytes
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    return doc_bytes

def main():
    st.set_page_config(page_title="Gerador de Contratos", layout="wide")

    if "current_content" not in st.session_state:
        st.session_state.current_content = ""
    if "variables" not in st.session_state:
        st.session_state.variables = {}
    if "original_file" not in st.session_state:
        st.session_state.original_file = None

    st.title("Gerador de Contratos")

    with st.sidebar:
        option = st.radio(
            "Escolha a função:",
            ["Cadastrar Novo Modelo", "Preencher Contrato"]
        )

    if option == "Cadastrar Novo Modelo":
        st.header("Cadastrar Novo Modelo de Contrato")
        
        template_name = st.text_input("Nome do Modelo:", key="template_name")
        
        uploaded_file = st.file_uploader("Carregar arquivo do contrato (.docx)", type="docx")
        
        if uploaded_file:
            if "current_content" not in st.session_state or not st.session_state.current_content:
                st.session_state.original_file = uploaded_file
                st.session_state.current_content = read_docx(uploaded_file)

            st.subheader("Selecione o texto para criar variáveis:")
            
            # Mostrar texto atual
            current_text = st.text_area(
                "Texto do Contrato",
                st.session_state.current_content,
                height=400,
                key="contract_text"
            )

            col1, col2 = st.columns([2, 1])
            with col1:
                text_to_replace = st.text_input("Texto a ser marcado como variável:")
            with col2:
                if st.button("Marcar como Variável") and text_to_replace:
                    var_name = st.text_input("Nome da variável:").upper()
                    if var_name:
                        new_content = current_text.replace(
                            text_to_replace, 
                            f"#{var_name}#"
                        )
                        st.session_state.current_content = new_content
                        st.session_state.variables[var_name] = text_to_replace
                        st.rerun()

            if st.session_state.variables:
                st.subheader("Variáveis Marcadas:")
                for var_name, original_text in st.session_state.variables.items():
                    st.code(f"#{var_name}# = {original_text}")

            if st.button("Salvar Modelo", type="primary"):
                if not template_name:
                    st.error("Digite um nome para o modelo!")
                    return
                
                try:
                    save_template(
                        template_name,
                        st.session_state.current_content,
                        list(st.session_state.variables.keys()),
                        st.session_state.original_file
                    )
                    st.success("Modelo salvo com sucesso!")
                    st.session_state.current_content = ""
                    st.session_state.variables = {}
                    st.session_state.original_file = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {str(e)}")

    else:  # Preencher Contrato
        st.header("Preencher Contrato")
        
        templates = load_templates()
        if not templates:
            st.warning("Nenhum modelo cadastrado. Cadastre um modelo primeiro!")
            return

        template_name = st.selectbox(
            "Selecione o Modelo:",
            options=list(templates.keys())
        )

        if template_name:
            template = templates[template_name]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Preencher Dados")
                values = {}
                for var in template["variables"]:
                    values[var] = st.text_input(f"{var}:")

                if st.button("Gerar Contrato", type="primary"):
                    empty_fields = [var for var, val in values.items() if not val.strip()]
                    if empty_fields:
                        st.error("Preencha todos os campos!")
                        return

                    try:
                        # Processar documento
                        doc_bytes = process_document(template_name, values)

                        st.download_button(
                            "⬇️ Baixar Contrato",
                            doc_bytes,
                            file_name=f"contrato_preenchido.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                        st.success("Contrato gerado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar contrato: {str(e)}")
            
            with col2:
                st.subheader("Prévia do Contrato")
                preview = template["content"]
                for var, val in values.items():
                    preview = preview.replace(f"#{var}#", val if val else f"[{var}]")
                st.text_area("", value=preview, height=400, disabled=True)

if __name__ == "__main__":
    main()
