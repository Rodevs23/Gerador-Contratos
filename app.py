import streamlit as st
from docx import Document
from pathlib import Path
import json
import io
import os
import logging
from datetime import datetime

# Configuração do logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GeradorContratosStreamlit:
    def __init__(self):
        st.set_page_config(
            page_title="Gerador de Contratos",
            layout="wide",
            page_icon="📄"
        )
        self.initialize_session_state()
        self.setup_folders()

    @staticmethod
    @st.cache_data
    def load_document(file):
        """Carrega o documento com cache do Streamlit"""
        return Document(file)
    def setup_folders(self):
        """Cria as pastas necessárias para o funcionamento do sistema"""
        for folder in ['templates', 'backups', 'temp']:
            Path(folder).mkdir(exist_ok=True)

    def initialize_session_state(self):
        """Inicializa as variáveis de estado do Streamlit"""
        if 'current_content' not in st.session_state:
            st.session_state.current_content = ""
        if 'variables' not in st.session_state:
            st.session_state.variables = {}
        if 'original_file' not in st.session_state:
            st.session_state.original_file = None

    @st.cache_data
    def load_document(self, file):
        """Carrega o documento com cache do Streamlit"""
        return Document(file)

    def validate_template(self, doc):
        """Valida o template do documento"""
        problems = []
        try:
            for paragraph in doc.paragraphs:
                # Verifica formatação complexa
                if len(paragraph.runs) > 50:
                    problems.append("Parágrafo com formatação muito complexa")
                
                # Verifica marcadores inválidos
                text = paragraph.text
                if text.count('#') % 2 != 0:
                    problems.append("Marcadores # não estão fechados corretamente")
                
                # Verifica tabelas complexas
                if len(doc.tables) > 10:
                    problems.append("Documento possui muitas tabelas")

        except Exception as e:
            problems.append(f"Erro na validação: {str(e)}")
        return problems

    def replace_text_keeping_format(self, doc, old_text, new_text):
        """Substitui texto mantendo a formatação original"""
        for paragraph in doc.paragraphs:
            if old_text in paragraph.text:
                for run in paragraph.runs:
                    if old_text in run.text:
                        run.text = run.text.replace(old_text, new_text)

    def auto_backup(self, doc, filename):
        """Cria backup automático do documento"""
        backup_path = Path("backups")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc.save(backup_path / f"{filename}_{timestamp}.docx")
        logging.info(f"Backup criado: {filename}_{timestamp}.docx")

    def main(self):
        st.title("🔖 Gerador de Contratos")
        
        tabs = st.tabs(["📝 Cadastrar Novo Modelo", "✨ Preencher Contrato"])
        
        with tabs[0]:
            self.template_tab()
        
        with tabs[1]:
            self.fill_tab()

    def template_tab(self):
        st.subheader("📝 Cadastrar Novo Modelo")
        
        # Nome do modelo
        template_name = st.text_input("Nome do Modelo")
        
        # Upload do arquivo
        uploaded_file = st.file_uploader(
            "Selecione o arquivo .docx",
            type=['docx'],
            help="Apenas arquivos .docx são aceitos"
        )
        
        if uploaded_file:
            try:
                doc = self.load_document(uploaded_file)
                st.session_state.current_content = '\n'.join(para.text for para in doc.paragraphs)
                st.session_state.original_file = uploaded_file
                
                # Área de texto
                text_area = st.text_area(
                    "Texto do Contrato",
                    value=st.session_state.current_content,
                    height=300
                )
                
                # Adicionar variável
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_text = st.text_input("Texto selecionado")
                with col2:
                    var_name = st.text_input("Nome da variável").upper()
                
                if st.button("➕ Adicionar Variável"):
                    if selected_text and var_name:
                        self.add_variable(selected_text, var_name)
                
                # Lista de variáveis
                st.subheader("📋 Variáveis Adicionadas")
                for var, text in st.session_state.variables.items():
                    st.text(f"#{var}#: {text}")
                
                # Salvar modelo
                if st.button("💾 Salvar Modelo"):
                    self.save_template(template_name)
                
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo: {str(e)}")
                logging.error(f"Erro ao carregar arquivo: {str(e)}")

    def fill_tab(self):
        st.subheader("✨ Preencher Contrato")
        
        # Carregar templates disponíveis
        template_path = Path("templates")
        templates = [f.stem for f in template_path.glob("*.json")]
        
        if not templates:
            st.warning("⚠️ Nenhum modelo cadastrado ainda!")
            return
        
        # Seleção do modelo
        selected_template = st.selectbox(
            "Selecione o Modelo",
            options=templates,
            help="Escolha o modelo de contrato"
        )
        
        if selected_template:
            try:
                with open(template_path / f"{selected_template}.json", "r", encoding="utf-8") as f:
                    template = json.load(f)
                
                # Criar campos para cada variável
                values = {}
                for var in template["variables"]:
                    values[var] = st.text_input(f"📝 {var}")
                
                if st.button("🔄 Gerar Contrato"):
                    try:
                        doc = self.load_document(template_path / f"{selected_template}.docx")
                        
                        # Substituir variáveis preservando formatação
                        for var_name, value in values.items():
                            if not value:  # Validação de campos vazios
                                st.warning(f"⚠️ Campo {var_name} está vazio!")
                                return
                            placeholder = f"#{var_name}#"
                            self.replace_text_keeping_format(doc, placeholder, value)
                        
                        # Criar backup antes de gerar
                        self.auto_backup(doc, f"{selected_template}_preenchido")
                        
                        # Salvar em memória
                        doc_io = io.BytesIO()
                        doc.save(doc_io)
                        doc_io.seek(0)
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Contrato",
                            data=doc_io,
                            file_name=f"{selected_template}_preenchido_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            help="Clique para baixar o contrato gerado"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar contrato: {str(e)}")
                        logging.error(f"Erro ao gerar contrato {selected_template}: {str(e)}")
            
            except Exception as e:
                st.error(f"❌ Erro ao carregar template: {str(e)}")
                logging.error(f"Erro ao carregar template {selected_template}: {str(e)}")

    def add_variable(self, selected_text, var_name):
        """Adiciona uma nova variável"""
        if not var_name:
            st.warning("⚠️ Nome da variável não pode ser vazio!")
            return
            
        if var_name in st.session_state.variables:
            st.warning("⚠️ Variável já existe!")
            return
        
        st.session_state.variables[var_name] = selected_text
        st.success(f"✅ Variável {var_name} adicionada com sucesso!")
        logging.info(f"Variável adicionada: {var_name}")

    def save_template(self, name):
        """Salva o template com todas as validações"""
        if not name:
            st.warning("⚠️ Digite um nome para o modelo!")
            return
        
        if not st.session_state.original_file:
            st.warning("⚠️ Carregue um arquivo primeiro!")
            return
        
        try:
            # Carrega e valida o documento
            doc = self.load_document(st.session_state.original_file)
            
            # Valida o template
            if problems := self.validate_template(doc):
                st.warning("⚠️ Problemas encontrados no template:")
                for p in problems:
                    st.write(f"- {p}")
                if not st.button("Continuar mesmo assim"):
                    return
            
            template_path = Path("templates")
            
            # Cria backup antes de salvar
            self.auto_backup(doc, name)
            
            data = {
                "variables": list(st.session_state.variables.keys()),
                "last_modified": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Salva metadata
            with open(template_path / f"{name}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Salva documento
            doc.save(template_path / f"{name}.docx")
            
            st.success("✅ Modelo salvo com sucesso!")
            st.session_state.variables = {}
            st.session_state.current_content = ""
            st.session_state.original_file = None
            
            logging.info(f"Template salvo com sucesso: {name}")
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {str(e)}")
            logging.error(f"Erro ao salvar template {name}: {str(e)}")

if __name__ == "__main__":
    app = GeradorContratosStreamlit()
    app.main()
