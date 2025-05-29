import os
import json
import shutil
import subprocess
import streamlit as st
from datetime import datetime

class GitHubSync:
    def __init__(self):
        self.config_file = "config.json"
        self.repo_dir = "pedidos"  # Diretório fixo onde os arquivos serão mantidos
        self.load_config()

    def load_config(self):
        """Carrega ou cria configuração padrão"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'github_repo': 'https://github.com/Washington-Vieira/pedidos_bobina.git',
                'local_mapeamento': 'pedidos/Mapeamento de Racks - Cabos.xlsx',
                'local_pedidos': 'pedidos/pedidos.xlsx'
            }
            self.save_config()

    def save_config(self):
        """Salva configuração atual"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def _run_git_command(self, command, check_error=True):
        """Executa um comando git no diretório do repositório"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                shell=True
            )
            if check_error and result.returncode != 0:
                raise Exception(f"Erro no comando Git: {result.stderr}")
            return result.stdout.strip()
        except Exception as e:
            st.error(f"Erro ao executar comando Git: {str(e)}")
            raise

    def sync_files(self):
        """Sincroniza arquivos com GitHub"""
        try:
            # Configurar Git se estiver no Streamlit Cloud
            if os.getenv('IS_STREAMLIT_CLOUD', '0') == '1' and 'GITHUB_TOKEN' in st.secrets:
                token = st.secrets['GITHUB_TOKEN']
                repo_url = self.config['github_repo'].replace(
                    'https://',
                    f'https://{token}@'
                )
            else:
                repo_url = self.config['github_repo']

            # Inicializar ou atualizar o repositório Git
            if not os.path.exists(os.path.join(self.repo_dir, '.git')):
                # Se não existe, inicializa um novo repositório
                os.makedirs(self.repo_dir, exist_ok=True)
                self._run_git_command('git init')
                self._run_git_command(f'git remote add origin {repo_url}')
            else:
                # Se existe, configura a URL remota
                self._run_git_command(f'git remote set-url origin {repo_url}')

            # Configurar usuário do Git
            if os.getenv('IS_STREAMLIT_CLOUD', '0') == '1':
                self._run_git_command('git config user.name "Streamlit Cloud"')
                self._run_git_command('git config user.email "noreply@streamlit.io"')

            # Atualizar do remoto
            self._run_git_command('git fetch origin')
            self._run_git_command('git reset --hard origin/main', check_error=False)

            # Copiar arquivos atualizados
            if os.path.exists(self.config['local_mapeamento']):
                shutil.copy2(self.config['local_mapeamento'], 
                           os.path.join(self.repo_dir, 'Mapeamento de Racks - Cabos.xlsx'))
            if os.path.exists(self.config['local_pedidos']):
                shutil.copy2(self.config['local_pedidos'], 
                           os.path.join(self.repo_dir, 'pedidos.xlsx'))

            # Adicionar e commitar mudanças
            self._run_git_command('git add *.xlsx')
            self._run_git_command(
                f'git commit -m "Atualização automática de pedidos - {datetime.now().strftime("%d/%m/%Y %H:%M")}"',
                check_error=False
            )

            # Push das alterações
            self._run_git_command('git push -u origin main')

            return True, "Sincronização concluída com sucesso!"

        except Exception as e:
            error_msg = f"Erro na sincronização: {str(e)}"
            st.error(error_msg)
            return False, error_msg

    def render_config_page(self):
        """Renderiza página de configuração"""
        st.title("⚙️ Configuração de Sincronização")

        st.markdown("### Configurações do GitHub")
        repo_url = st.text_input(
            "URL do Repositório GitHub",
            value=self.config['github_repo']
        )

        st.markdown("### Configurações Locais")
        local_map = st.text_input(
            "Caminho do Arquivo de Mapeamento",
            value=self.config['local_mapeamento']
        )

        local_ped = st.text_input(
            "Diretório de Pedidos",
            value=self.config['local_pedidos']
        )

        if st.button("💾 Salvar Configurações"):
            self.config.update({
                'github_repo': repo_url,
                'local_mapeamento': local_map,
                'local_pedidos': local_ped
            })
            self.save_config()
            st.success("✅ Configurações salvas com sucesso!")

        if st.button("🔄 Sincronizar Agora"):
            success, message = self.sync_files()
            if success:
                st.success(message)
            else:
                st.error(message)

    def render_secrets_page(self):
        """Renderiza página de segredos"""
        st.title("🔑 Gerenciamento de Segredos")
        st.info("Os segredos agora são gerenciados diretamente pelo Streamlit Cloud ou variáveis de ambiente.")
        if st.checkbox("Mostrar segredos disponíveis (apenas para debug)"):
            st.json(st.secrets)