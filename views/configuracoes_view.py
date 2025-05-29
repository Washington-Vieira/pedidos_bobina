import streamlit as st
import os
from datetime import datetime
import win32print

class ConfiguracoesView:
    def __init__(self):
        self.base_dir = os.path.join(
            os.path.expanduser("~"),
            "OneDrive - Yazaki",
            "Solicitação",
            "Pedidos"
        )
        self.arquivo_pedidos = os.path.join(self.base_dir, "pedidos.xlsx")
        self.arquivo_backup = os.path.join(self.base_dir, "backup")

    def _get_impressoras_disponiveis(self):
        """Retorna lista de impressoras disponíveis no sistema"""
        try:
            impressoras = []
            for p in win32print.EnumPrinters(2):  # 2 = PRINTER_ENUM_LOCAL
                impressoras.append(p[2])
            return sorted(impressoras)
        except Exception:
            return []

    def mostrar_interface(self):
        st.markdown("### ⚙️ Configurações do Sistema", unsafe_allow_html=True)
        
        # Seção de Impressora
        st.markdown("#### 🖨️ Configuração da Impressora")
        
        # Obter impressora atual
        impressora_atual = win32print.GetDefaultPrinter()
        
        # Listar impressoras disponíveis
        impressoras = self._get_impressoras_disponiveis()
        
        if impressoras:
            impressora_selecionada = st.selectbox(
                "Selecione a Impressora Fiscal",
                options=impressoras,
                index=impressoras.index(impressora_atual) if impressora_atual in impressoras else 0
            )
            
            if st.button("💾 Definir como Padrão"):
                try:
                    win32print.SetDefaultPrinter(impressora_selecionada)
                    st.success(f"✅ Impressora {impressora_selecionada} definida como padrão!")
                except Exception as e:
                    st.error(f"❌ Erro ao definir impressora padrão: {str(e)}")
        else:
            st.error("❌ Nenhuma impressora encontrada no sistema")
        
        st.markdown("---")
        
        # Mostrar localização dos arquivos
        st.markdown("#### 📁 Localização dos Arquivos")
        st.markdown(f"""
        **Pasta Principal:** {self.base_dir}  
        **Arquivo de Pedidos:** {self.arquivo_pedidos}  
        **Pasta de Backup:** {self.arquivo_backup}
        """)
        
        # Mostrar backups disponíveis
        st.markdown("#### 💾 Backups Disponíveis")
        
        if not os.path.exists(self.arquivo_backup):
            os.makedirs(self.arquivo_backup, exist_ok=True)
            
        backups = sorted([
            f for f in os.listdir(self.arquivo_backup)
            if f.endswith('.xlsx')
        ], reverse=True)
        
        if not backups:
            st.info("Nenhum backup encontrado")
        else:
            for backup in backups:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(backup)
                with col2:
                    if st.button("📥 Restaurar", key=f"restore_{backup}"):
                        try:
                            # Restaurar backup
                            backup_path = os.path.join(self.arquivo_backup, backup)
                            os.replace(backup_path, self.arquivo_pedidos)
                            st.success("Backup restaurado com sucesso!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao restaurar backup: {str(e)}")
        
        # Informações adicionais
        st.markdown("#### ℹ️ Informações")
        st.markdown("""
        - O sistema mantém automaticamente os últimos 10 backups
        - Um novo backup é criado sempre que há alterações nos pedidos
        - Os backups são nomeados com data e hora para fácil identificação
        - Use o botão "Restaurar" para voltar a uma versão anterior dos dados
        """)
        
        # Aviso importante
        st.warning("""
        **⚠️ Atenção!**  
        Ao restaurar um backup, a versão atual dos dados será substituída.
        Certifique-se de que deseja realmente fazer isso antes de prosseguir.
        """) 