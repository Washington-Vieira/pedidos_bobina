 import streamlit as st
from utils.github_sync import GitHubSync

class ConfigView:
    def __init__(self):
        self.sync_manager = GitHubSync()
    
    def mostrar_interface(self):
        """Mostra a interface de configuração"""
        self.sync_manager.render_config_page()