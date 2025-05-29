import os
import json
import shutil
from git import Repo
import streamlit as st

class GitHubSync:
    def __init__(self):
        self.config_file = "config.json"
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
      def sync_files(self):
        """Sincroniza arquivos com GitHub"""
        try:
            if not os.path.exists('repo_temp'):
                Repo.clone_from(self.config['github_repo'], 'repo_temp')
            
            repo = Repo('repo_temp')
            repo.remotes.origin.pull()
            
            # Sincroniza arquivos de mapeamento e pedidos
            shutil.copy2(self.config['local_mapeamento'], 
                        os.path.join('repo_temp', 'pedidos', 'Mapeamento de Racks - Cabos.xlsx'))
            shutil.copy2(self.config['local_pedidos'], 
                        os.path.join('repo_temp', 'pedidos', 'pedidos.xlsx'))
            
            # Push changes
            repo.index.add(['pedidos/*.xlsx'])
            repo.index.commit('Atualização automática de pedidos')
            repo.remotes.origin.push()
            
            return True, "Sincronização concluída com sucesso!"
        except Exception as e:
            return False, f"Erro na sincronização: {str(e)}"
    
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