import streamlit as st
import json
from pathlib import Path

def init_session_state():
    """Inicializa variáveis da sessão se não existirem"""
    if 'current_template' not in st.session_state:
        st.session_state.current_template = None
    if 'template_name' not in st.session_state:
        st.session_state.template_name = ""
    if 'template_content' not in st.session_state:
        st.session_state.template_content = ""
    if 'variables' not in st.session_state:
        st.session_state.variables = []

def main():
    st.set_page_config(
        page_title="Gerador de Contratos",
        page_icon="📄",
        layout="wide"
    )

    # Inicializar variáveis da sessão
    init_session_state()

    # Cabeçalho
    st.title("Gerador de Contratos")
    st.markdown("---")

    # Menu lateral
    with st.sidebar:
        st.header("Menu")
        page = st.radio(
            "Selecione uma opção:",
            ["Editor de Template", "Preencher Contrato"]
        )

    if page == "Editor de Template":
        show_template_editor()
    else:
        show_contract_fill()

def show_template_editor():
    """Página do editor de template"""
    st.header("Editor de Template")

    # Layout em duas colunas
    col1, col2 = st.columns(2)

    with col1:
        # Campo para nome do template
        template_name = st.text_input(
            "Nome do Template",
            value=st.session_state.template_name
        )

        # Área de texto para o conteúdo
        template_content = st.text_area(
            "Conteúdo do Template",
            value=st.session_state.template_content,
            height=400
        )

        if st.button("Marcar Variável"):
            text_selected = st.text_input(
                "Digite o texto que deseja marcar como variável:"
            )
            if text_selected:
                variable_name = st.text_input(
                    "Nome da Variável (apenas letras, números e underscore):"
                ).upper()
                
                if variable_name and variable_name not in st.session_state.variables:
                    st.session_state.variables.append(variable_name)
                    st.session_state.template_content = template_content.replace(
                        text_selected,
                        f"#{variable_name}#"
                    )
                    st.success(f"Variável {variable_name} marcada com sucesso!")
                    st.rerun()

    with col2:
        st.subheader("Variáveis Marcadas")
        for var in st.session_state.variables:
            st.code(f"#{var}#")

        if st.button("Salvar Template", type="primary"):
            if not template_name or not template_content:
                st.error("Preencha todos os campos!")
                return

            try:
                save_template(template_name, template_content, st.session_state.variables)
                st.success("Template salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar: {str(e)}")

def show_contract_fill():
    """Página de preenchimento do contrato"""
    st.header("Preencher Contrato")

    # Carregar templates disponíveis
    templates = load_templates()
    if not templates:
        st.warning("Nenhum template disponível. Crie um template primeiro!")
        return

    # Seleção do template
    template_name = st.selectbox(
        "Selecione o Template",
        options=list(templates.keys())
    )

    template = templates[template_name]

    # Layout em duas colunas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Preencher Dados")
        values = {}
        
        # Criar campos para cada variável
        for var in template["variables"]:
            values[var] = st.text_input(var.replace("_", " "))

        if st.button("Gerar Contrato", type="primary"):
            # Verificar campos vazios
            empty_fields = [var for var, val in values.items() if not val.strip()]
            if empty_fields:
                st.error("Preencha todos os campos!")
                return

            # Gerar contrato
            content = template["content"]
            for var, val in values.items():
                content = content.replace(f"#{var}#", val)

            # Oferecer download
            st.download_button(
                "⬇️ Baixar Contrato",
                content,
                file_name=f"contrato_{template_name}.txt",
                mime="text/plain"
            )

    with col2:
        st.subheader("Prévia")
        preview = template["content"]
        for var, val in values.items():
            preview = preview.replace(f"#{var}#", val if val else f"[{var}]")
        st.text_area("", value=preview, height=400, disabled=True)

def save_template(name, content, variables):
    """Salva um template"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    data = {
        "content": content,
        "variables": variables
    }
    
    with open(template_path / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_templates():
    """Carrega os templates salvos"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    templates = {}
    for file in template_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            templates[file.stem] = json.load(f)
    return templates

if __name__ == "__main__":
    main()
