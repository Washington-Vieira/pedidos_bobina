import pandas as pd
from datetime import datetime
from models.pedido import Pedido
from typing import List, Optional
import streamlit as st
import os
import shutil

class PedidoController:
    def __init__(self, caminho_planilha: str):
        """
        Inicializa o controlador com o caminho da planilha de localizações
        Args:
            caminho_planilha: Caminho da planilha que contém as localizações (definido no .env)
        """
        self.caminho_planilha = caminho_planilha
        self.pedidos = []
        self.arquivo_pedidos = os.path.join('pedidos', 'pedidos.xlsx')
        self.diretorio_backup = os.path.join('pedidos', 'backup')
        
        # Criar diretório de backup se não existir
        os.makedirs(self.diretorio_backup, exist_ok=True)

    @staticmethod
    @st.cache_data
    def _carregar_planilha(caminho: str) -> List[Pedido]:
        """
        Carrega os dados da planilha com cache do Streamlit para melhor performance
        """
        try:
            # Lê a aba específica 'Projeto' da planilha
            df = pd.read_excel(
                caminho, 
                sheet_name='Projeto',
                dtype={
                    'RACK': str,
                    'CÓD Yazaki': str,
                    'Codigo Cabo': str,
                    'Secção': str,
                    'Cor': str,
                    'Cliente': str,
                    'Locação': str,
                    'Projeto': str,
                    'Cod OES': str
                }
            )
            
            # Mapeia os nomes das colunas da planilha
            colunas_mapeadas = {
                'RACK': 'rack',
                'CÓD Yazaki': 'cod_yazaki',
                'Codigo Cabo': 'codigo_cabo',
                'Secção': 'seccao',
                'Cor': 'cor',
                'Cliente': 'cliente',
                'Locação': 'locacao',
                'Projeto': 'projeto',
                'Cod OES': 'cod_oes'
            }
            
            # Renomeia as colunas para corresponder aos nomes dos atributos da classe
            df = df.rename(columns=colunas_mapeadas)
            
            # Limpa os dados
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('').astype(str).str.strip()
            
            # Converte o DataFrame para lista de objetos Pedido
            pedidos = [
                Pedido(
                    id=idx + 1,
                    rack=row['rack'],
                    cod_yazaki=row['cod_yazaki'],
                    codigo_cabo=row['codigo_cabo'],
                    seccao=row['seccao'],
                    cor=row['cor'],
                    cliente=row['cliente'],
                    locacao=row['locacao'],
                    projeto=row['projeto'],
                    cod_oes=row['cod_oes']
                )
                for idx, row in df.iterrows()
            ]
            
            return pedidos
            
        except Exception as e:
            raise Exception(f"Erro ao carregar dados da planilha: {str(e)}")

    def carregar_dados(self):
        """Carrega os dados usando a função cacheada"""
        self.pedidos = self._carregar_planilha(self.caminho_planilha)
        return self.pedidos

    def _fazer_backup(self):
        """Faz backup do arquivo antes de modificá-lo"""
        if os.path.exists(self.arquivo_pedidos):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(
                self.diretorio_backup, 
                f"pedidos_backup_{timestamp}.xlsx"
            )
            
            # Copiar arquivo atual para backup
            pd.read_excel(self.arquivo_pedidos).to_excel(backup_path, index=False)
            
            # Manter apenas os últimos 10 backups
            backups = sorted([
                os.path.join(self.diretorio_backup, f) 
                for f in os.listdir(self.diretorio_backup)
                if f.endswith('.xlsx')
            ])
            while len(backups) > 10:
                os.remove(backups.pop(0))

    def _ler_pedidos(self) -> pd.DataFrame:
        """Lê a planilha de pedidos"""
        try:
            if not os.path.exists(self.arquivo_pedidos):
                return pd.DataFrame(columns=[
                    "Numero_Pedido", "Data", "Cliente", "RACK", "Localizacao",
                    "Solicitante", "Observacoes", "Status", "Ultima_Atualizacao",
                    "Responsavel_Atualizacao"
                ])
            df = pd.read_excel(self.arquivo_pedidos, sheet_name='Pedidos')

            # Garantir que as colunas 'Ultima_Atualizacao' e 'Responsavel_Atualizacao' existam
            if 'Ultima_Atualizacao' not in df.columns:
                df['Ultima_Atualizacao'] = ""
            if 'Responsavel_Atualizacao' not in df.columns:
                df['Responsavel_Atualizacao'] = ""

            return df
        except Exception as e:
            raise Exception(f"Erro ao ler pedidos: {str(e)}")

    def _ler_itens(self) -> pd.DataFrame:
        """Lê a planilha de itens"""
        try:
            if not os.path.exists(self.arquivo_pedidos):
                return pd.DataFrame(columns=[
                    "Numero_Pedido", "cod_yazaki", "codigo_cabo", "seccao",
                    "cor", "quantidade"
                ])
            return pd.read_excel(self.arquivo_pedidos, sheet_name='Itens')
        except Exception as e:
            raise Exception(f"Erro ao ler itens: {str(e)}")

    def _gerar_numero_pedido(self) -> str:
        """Gera um número único para o pedido"""
        try:
            df = self._ler_pedidos()
            if df.empty:
                return "REQ-001"
            ultimo_numero = df["Numero_Pedido"].iloc[-1]
            numero = int(ultimo_numero.split("-")[1]) + 1
            return f"REQ-{numero:03d}"
        except:
            return "REQ-001"

    def salvar_pedido(self, pedido_info: dict) -> str:
        """Salva o pedido e sincroniza com GitHub"""
        from utils.github_sync import GitHubSync
        
        numero_pedido = self._gerar_numero_pedido()
        
        try:
            # Carregar dados existentes
            df_pedidos = self._ler_pedidos()
            df_itens = self._ler_itens()
            
            # Criar novo registro de pedido
            novo_pedido = pd.DataFrame([{
                "Numero_Pedido": numero_pedido,
                "Data": pedido_info["data"].strftime('%d/%m/%Y %H:%M'),
                "Cliente": pedido_info["cliente"],
                "RACK": pedido_info["rack"],
                "Localizacao": pedido_info["locacao"],
                "Solicitante": pedido_info["solicitante"],
                "Observacoes": pedido_info["observacoes"] if pedido_info["observacoes"] else "",
                "Status": "Pendente"
            }])
            
            # Criar registros de itens
            novos_itens = []
            for item in pedido_info["itens"]:
                novos_itens.append({
                    "Numero_Pedido": numero_pedido,
                    "cod_yazaki": item["cod_yazaki"],
                    "codigo_cabo": item["codigo_cabo"],
                    "seccao": item["seccao"],
                    "cor": item["cor"],
                    "quantidade": item["quantidade"]
                })
            
            df_novos_itens = pd.DataFrame(novos_itens)
            
            # Concatenar com os dados existentes
            df_pedidos = pd.concat([df_pedidos, novo_pedido], ignore_index=True)
            df_itens = pd.concat([df_itens, df_novos_itens], ignore_index=True)
            
            # Preencher valores NaN com string vazia
            df_pedidos = df_pedidos.fillna("")
            df_itens = df_itens.fillna("")
            
            # Fazer backup antes de salvar
            self._fazer_backup()
            
            # Salvar na planilha
            with pd.ExcelWriter(self.arquivo_pedidos, engine='openpyxl') as writer:
                df_pedidos.to_excel(writer, sheet_name='Pedidos', index=False)
                df_itens.to_excel(writer, sheet_name='Itens', index=False)
            
            # Sincronizar com GitHub
            sync = GitHubSync()
            success, message = sync.sync_files()
            if not success:
                st.warning(f"⚠️ Aviso: {message}")
            
            return numero_pedido
            
        except Exception as e:
            raise Exception(f"Erro ao salvar pedido: {str(e)}")

    def buscar_pedidos(self, 
                      numero_pedido: Optional[str] = None,
                      cliente: Optional[str] = None,
                      status: Optional[str] = None) -> pd.DataFrame:
        """Busca pedidos com filtros opcionais"""
        try:
            df = self._ler_pedidos()
            
            # Preencher valores NaN com string vazia
            df = df.fillna("")
            
            if numero_pedido:
                df = df[df["Numero_Pedido"].str.contains(numero_pedido, case=False)]
            if cliente:
                df = df[df["Cliente"].str.contains(cliente, case=False)]
            if status:
                df = df[df["Status"] == status]
            
            return df
        except Exception as e:
            raise Exception(f"Erro ao buscar pedidos: {str(e)}")

    def get_pedido_detalhes(self, numero_pedido: str) -> dict:
        """Retorna os detalhes completos de um pedido"""
        try:
            # Carregar dados
            df_pedidos = pd.read_excel(self.arquivo_pedidos, sheet_name='Pedidos')
            df_itens = pd.read_excel(self.arquivo_pedidos, sheet_name='Itens')
            
            # Buscar informações do pedido
            pedido = df_pedidos[df_pedidos["Numero_Pedido"] == numero_pedido].iloc[0]
            itens = df_itens[df_itens["Numero_Pedido"] == numero_pedido].to_dict('records')
            
            # Converter o pedido para dicionário
            info_dict = {
                "Numero_Pedido": pedido["Numero_Pedido"],
                "Data": pedido["Data"],
                "Cliente": pedido["Cliente"],
                "RACK": pedido["RACK"],
                "Localizacao": pedido["Localizacao"],
                "Solicitante": pedido["Solicitante"],
                "Observacoes": pedido["Observacoes"],
                "Ultima_Atualizacao": pedido["Ultima_Atualizacao"] if pd.notna(pedido["Ultima_Atualizacao"]) else "",
                "Responsavel_Atualizacao": pedido["Responsavel_Atualizacao"] if pd.notna(pedido["Responsavel_Atualizacao"]) else ""
            }
            
            return {
                "info": info_dict,
                "itens": itens,
                "status": pedido["Status"]
            }
            
        except Exception as e:
            raise Exception(f"Erro ao buscar detalhes do pedido: {str(e)}")

    def atualizar_status_pedido(self, numero_pedido: str, novo_status: str, responsavel: str):
        """Atualiza o status de um pedido"""
        try:
            # Carregar dados atuais
            df_pedidos = pd.read_excel(self.arquivo_pedidos, sheet_name='Pedidos')
            df_itens = pd.read_excel(self.arquivo_pedidos, sheet_name='Itens')
            
            # Localizar o pedido
            idx = df_pedidos[df_pedidos["Numero_Pedido"] == numero_pedido].index[0]
            
            # Atualizar informações
            df_pedidos.at[idx, "Status"] = novo_status
            df_pedidos.at[idx, "Ultima_Atualizacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')
            df_pedidos.at[idx, "Responsavel_Atualizacao"] = responsavel
            
            # Fazer backup antes de salvar
            self._fazer_backup()
            
            # Salvar alterações
            with pd.ExcelWriter(self.arquivo_pedidos, engine='openpyxl') as writer:
                df_pedidos.to_excel(writer, sheet_name='Pedidos', index=False)
                df_itens.to_excel(writer, sheet_name='Itens', index=False)
                
        except Exception as e:
            raise Exception(f"Erro ao atualizar status: {str(e)}")

    @staticmethod
    @st.cache_data
    def filtrar_dados(pedidos: List[Pedido], cliente: Optional[str] = None, 
                     rack: Optional[str] = None) -> List[Pedido]:
        """Filtra os dados com cache"""
        resultado = pedidos
        if cliente:
            cliente = cliente.lower()
            resultado = [p for p in resultado if p.cliente.lower() == cliente]
        if rack:
            rack = rack.lower()
            resultado = [p for p in resultado if p.rack.lower() == rack]
        return resultado

    def buscar_por_cliente(self, cliente: str) -> List[Pedido]:
        """Busca pedidos por cliente (case-insensitive)"""
        return self.filtrar_dados(self.pedidos, cliente=cliente)

    def buscar_por_rack(self, rack: str) -> List[Pedido]:
        """Busca pedidos por rack (case-insensitive)"""
        return self.filtrar_dados(self.pedidos, rack=rack)

    def buscar_por_cliente_e_rack(self, cliente: str, rack: str) -> List[Pedido]:
        """Busca pedidos por cliente e rack (case-insensitive)"""
        return self.filtrar_dados(self.pedidos, cliente=cliente, rack=rack)

    def imprimir_pedido(self, numero_pedido: str):
        """Gera um arquivo PDF do pedido e envia para impressão"""
        try:
            # Buscar detalhes do pedido
            detalhes = self.get_pedido_detalhes(numero_pedido)
            
            # Gerar HTML para impressão
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ text-align: center; margin-bottom: 20px; }}
                    .info {{ margin-bottom: 20px; }}
                    .item {{ margin-bottom: 10px; }}
                    .signatures {{ margin-top: 50px; text-align: center; }}
                    .signature-line {{ 
                        width: 200px; 
                        border-top: 1px solid black; 
                        margin: 50px auto 10px auto; 
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Pedido de Requisição #{numero_pedido}</h1>
                    <p>Data: {detalhes['info']['Data']}</p>
                </div>
                
                <div class="info">
                    <h2>Informações do Pedido</h2>
                    <p><strong>Cliente:</strong> {detalhes['info']['Cliente']}</p>
                    <p><strong>RACK:</strong> {detalhes['info']['RACK']}</p>
                    <p><strong>Localização:</strong> {detalhes['info']['Localizacao']}</p>
                    <p><strong>Solicitante:</strong> {detalhes['info']['Solicitante']}</p>
                    <p><strong>Status:</strong> {detalhes['status']}</p>
                </div>
                
                <div class="items">
                    <h2>Itens</h2>
            """
            
            # Adicionar itens
            for idx, item in enumerate(detalhes['itens'], 1):
                html += f"""
                    <div class="item">
                        <h3>Item {idx}</h3>
                        <p><strong>CÓD Yazaki:</strong> {item['cod_yazaki']}</p>
                        <p><strong>Código Cabo:</strong> {item['codigo_cabo']}</p>
                        <p><strong>Seção:</strong> {item['seccao']}</p>
                        <p><strong>Cor:</strong> {item['cor']}</p>
                        <p><strong>Quantidade:</strong> {item['quantidade']}</p>
                    </div>
                """
            
            # Adicionar área de assinaturas
            html += """
                </div>
                
                <div class="signatures">
                    <div>
                        <div class="signature-line"></div>
                        <p>Solicitante</p>
                    </div>
                    
                    <div>
                        <div class="signature-line"></div>
                        <p>Aprovação</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Salvar HTML temporário
            temp_html = f"temp_{numero_pedido}.html"
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html)
            
            # Enviar para impressão usando o navegador padrão
            os.startfile(temp_html, "print")
            
            # Aguardar um pouco e remover arquivo temporário
            import time
            time.sleep(5)
            os.remove(temp_html)
            
        except Exception as e:
            raise Exception(f"Erro ao imprimir pedido: {str(e)}")