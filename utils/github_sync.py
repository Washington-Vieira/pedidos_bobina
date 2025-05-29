import os
import json
import shutil
from git import Repo
import streamlit as st
from datetime import datetime

class GitHubSync:
    def __init__(self):
        self.config_file = "config.json"
        self.repo_path = "repo_temp"
        self.load_config()
        self._setup_git()
        
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
    
    def _setup_git(self):
        """Configura o Git com as credenciais"""
        try:
            if os.getenv('IS_STREAMLIT_CLOUD', '0') == '1':
                if 'GITHUB_TOKEN' in st.secrets:
                    repo_url = self.config['github_repo'].replace(
                        'https://', 
                        f'https://{st.secrets["GITHUB_TOKEN"]}@'
                    )
                    self.config['github_repo'] = repo_url
      def save_config(self):
        """Salva configuração atual"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
      def sync_files(self):
        """Sincroniza arquivos com GitHub"""
        try:
            # Limpar diretório temporário se existir
            if os.path.exists(self.repo_path):
                shutil.rmtree(self.repo_path)
            
            # Clonar repositório
            repo = Repo.clone_from(self.config['github_repo'], self.repo_path)
            
            # Garantir que a pasta pedidos existe
            pedidos_path = os.path.join(self.repo_path, 'pedidos')
            os.makedirs(pedidos_path, exist_ok=True)
            
            # Sincronizar arquivos
            dest_mapeamento = os.path.join(pedidos_path, 'Mapeamento de Racks - Cabos.xlsx')
            dest_pedidos = os.path.join(pedidos_path, 'pedidos.xlsx')
            
            # Copiar arquivos locais para o repo
            if os.path.exists(self.config['local_mapeamento']):
                shutil.copy2(self.config['local_mapeamento'], dest_mapeamento)
            if os.path.exists(self.config['local_pedidos']):
                shutil.copy2(self.config['local_pedidos'], dest_pedidos)
            
            # Commit e push das alterações
            repo.index.add(['pedidos/*.xlsx'])
            repo.index.commit('Atualização automática de pedidos')
            repo.remotes.origin.push()
            
            # Copiar arquivos do repo de volta para local
            if os.path.exists(dest_pedidos):
                os.makedirs(os.path.dirname(self.config['local_pedidos']), exist_ok=True)
                shutil.copy2(dest_pedidos, self.config['local_pedidos'])
            
            return True, "Sincronização concluída com sucesso!"        except Exception as e:
            error_msg = f"Erro na sincronização: {str(e)}"
            st.error(error_msg)
            return False, error_msg
        finally:
            # Limpar diretório temporário
            if os.path.exists(self.repo_path):
                try:
                    shutil.rmtree(self.repo_path)
                except:
                    pass
    
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