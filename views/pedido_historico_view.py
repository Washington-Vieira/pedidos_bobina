import streamlit as st
from controllers.pedido_controller import PedidoController
from datetime import datetime
import pandas as pd
import os
import tempfile
import time
from fpdf import FPDF
from utils.print_manager import PrintManager

class PedidoHistoricoView:
    def __init__(self, controller: PedidoController):
        self.controller = controller
        self._aplicar_estilos()

    def _aplicar_estilos(self):
        """Aplica estilos CSS personalizados"""
        st.markdown("""
        <style>
            /* Status tags */
            .status-pendente {
                background-color: #ffd700;
                color: black;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 14px;
            }
            
            .status-concluido {
                background-color: #90EE90;
                color: black;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 14px;
            }
            
            .status-processando {
                background-color: #87CEEB;
                color: black;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 14px;
            }

            /* Tabela responsiva */
            .tabela-pedidos {
                width: 100%;
                max-width: 100%;
                overflow-x: auto;
                display: block;
                white-space: nowrap;
                border-collapse: collapse;
                margin: 0.5rem 0;
            }

            .tabela-pedidos table {
                width: 100%;
                border-collapse: collapse;
            }

            .tabela-pedidos th {
                background-color: #f0f2f6;
                padding: 8px 15px;
                text-align: left;
                font-weight: bold;
                border-bottom: 2px solid #ddd;
                font-size: 13px;
            }

            .tabela-pedidos td {
                padding: 6px 15px;
                border-bottom: 1px solid #ddd;
                font-size: 13px;
                line-height: 1.2;
            }

            .tabela-pedidos tr:hover {
                background-color: #f5f5f5;
            }

            /* Ajuste para telas menores */
            @media screen and (max-width: 768px) {
                .tabela-pedidos {
                    font-size: 12px;
                }
                .tabela-pedidos td, .tabela-pedidos th {
                    padding: 5px 8px;
                }
            }
        </style>
        """, unsafe_allow_html=True)

    def mostrar_interface(self):
        """Mostra a interface do histórico de pedidos"""
        st.markdown("### 📋 Histórico de Pedidos")
        
        # Filtro de Status
        status_filtro = st.selectbox(
            "Status do Pedido",
            ["Todos", "Pendente", "Concluído", "Em Processamento"]
        )
        
        try:
            # Buscar pedidos
            df_pedidos = self.controller.buscar_pedidos(
                status=None if status_filtro == "Todos" else status_filtro
            )
            
            if not df_pedidos.empty:
                # Mostrar total de pedidos
                st.write(f"Total: {len(df_pedidos)} pedidos encontrados")
                
                # Formatar DataFrame para exibição
                df_display = df_pedidos[[
                    "Numero_Pedido", "Data", "Cliente", "RACK", 
                    "Localizacao", "Solicitante", "Status",
                    "Ultima_Atualizacao", "Responsavel_Atualizacao"
                ]].copy()
                
                # Renomear colunas
                df_display.columns = [
                    "Número", "Data", "Cliente", "RACK",
                    "Localização", "Solicitante", "Status",
                    "Última Atualização", "Responsável"
                ]
                
                # Formatar status com cores
                def formatar_status(status):
                    cores = {
                        "Pendente": "status-pendente",
                        "Concluído": "status-concluido",
                        "Em Processamento": "status-processando"
                    }
                    classe = cores.get(status, "")
                    return f'<span class="{classe}">{status}</span>'
                
                df_display["Status"] = df_display["Status"].apply(formatar_status)
                
                # Mostrar tabela
                st.markdown(
                    f'<div class="tabela-pedidos">{df_display.to_html(escape=False, index=False)}</div>',
                    unsafe_allow_html=True
                )
                
                # Detalhes do Pedido
                st.markdown("### Detalhes do Pedido")
                
                # Seleção do pedido
                pedido_selecionado = st.selectbox(
                    "Selecione um pedido",
                    [""] + df_pedidos["Numero_Pedido"].tolist()
                )
                
                if pedido_selecionado:
                    # Buscar detalhes do pedido
                    detalhes = self.controller.get_pedido_detalhes(pedido_selecionado)
                    
                    # Informações
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Informações")
                        st.write(f"**Número:** {detalhes['info']['Numero_Pedido']}")
                        st.write(f"**Data:** {detalhes['info']['Data']}")
                        st.write(f"**Cliente:** {detalhes['info']['Cliente']}")
                        st.write(f"**RACK:** {detalhes['info']['RACK']}")
                        st.write(f"**Localização:** {detalhes['info']['Localizacao']}")
                        st.write(f"**Solicitante:** {detalhes['info']['Solicitante']}")
                        st.write(f"**Status:** {detalhes['status']}")
                        
                        # Botão de impressão simplificado
                        if st.button("🖨️", help="Imprimir pedido"):
                            try:
                                self.imprimir_pedido(pedido_selecionado)
                            except Exception as e:
                                st.error("Erro ao processar impressão")
                    
                    with col2:
                        st.markdown("#### Item")
                        for idx, item in enumerate(detalhes['itens'], 1):
                            st.write(f"**CÓD Yazaki:** {item['cod_yazaki']}")
                            st.write(f"**Código Cabo:** {item['codigo_cabo']}")
                            st.write(f"**Seção:** {item['seccao']}")
                            st.write(f"**Cor:** {item['cor']}")
                            st.write(f"**Quantidade:** {item['quantidade']}")
                    
                    # Atualização de Status
                    st.markdown("#### Atualizar Status")
                    
                    # Seleção de status
                    novo_status = st.selectbox(
                        "Novo Status",
                        ["Pendente", "Em Processamento", "Concluído"],
                        index=["Pendente", "Em Processamento", "Concluído"].index(detalhes['status'])
                    )
                    
                    # Campo de responsável logo abaixo
                    responsavel = st.text_input(
                        "Responsável",
                        value="",
                        placeholder="Seu nome completo"
                    )
                    
                    # Botão de confirmação centralizado
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("✅ Confirmar Atualização", use_container_width=True):
                            if not responsavel:
                                st.error("⚠️ Por favor, informe o nome do responsável!")
                            elif novo_status == detalhes['status']:
                                st.warning("ℹ️ O status selecionado é igual ao atual.")
                            else:
                                try:
                                    # Atualizar status
                                    self.controller.atualizar_status_pedido(
                                        pedido_selecionado,
                                        novo_status,
                                        responsavel
                                    )
                                    
                                    # Mostrar mensagem de sucesso
                                    st.success(f"✅ Status atualizado com sucesso para {novo_status}!")
                                    
                                    # Recarregar dados após um breve delay
                                    time.sleep(0.5)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao atualizar status: {str(e)}")

                    # Mostrar histórico de atualizações
                    if detalhes['info'].get('Ultima_Atualizacao'):
                        st.markdown("---")
                        st.markdown("#### Última Atualização")
                        st.info(
                            f"🕒 {detalhes['info']['Ultima_Atualizacao']} por "
                            f"{detalhes['info']['Responsavel_Atualizacao']}"
                        )
            else:
                st.info("Nenhum pedido encontrado")
                
        except Exception as e:
            st.error(f"""
            ❌ Erro ao carregar histórico:
            
            {str(e)}
            
            Por favor, tente novamente ou contate o suporte.
            """)

    def formatar_pedido_para_impressao(self, pedido: dict) -> str:
        """Formata o pedido para impressão"""
        info = pedido["info"]
        itens = pedido["itens"]
        
        texto = f"""
=================================================
            PEDIDO DE REQUISIÇÃO
=================================================
Número: {info['Numero_Pedido']}
Data: {info['Data']}
Status: {pedido['status']}

INFORMAÇÕES:
-------------------------------------------------
Cliente: {info['Cliente']}
RACK: {info['RACK']}
Localização: {info['Localizacao']}
Solicitante: {info['Solicitante']}

OBSERVAÇÕES:
{info['Observacoes']}

ITENS:
-------------------------------------------------"""

        for item in itens:
            texto += f"""
CÓD Yazaki: {item['cod_yazaki']}
Código Cabo: {item['codigo_cabo']}
Secção: {item['seccao']}
Cor: {item['cor']}
Quantidade: {item['quantidade']}
-------------------------------------------------"""
        
        texto += "\n\n"
        texto += "Assinatura: _____________________________\n"
        texto += f"Impresso em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        
        return texto

    def _criar_pdf(self, texto: str) -> str:
        """Cria um arquivo PDF com o conteúdo do pedido"""
        pdf = FPDF()
        pdf.add_page()
        
        # Usar fonte padrão
        pdf.set_font('Helvetica', size=11)
        
        # Adicionar texto
        for linha in texto.split('\n'):
            pdf.cell(0, 5, txt=linha, ln=True)
        
        # Salvar PDF
        nome_arquivo = f"pedido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # No Streamlit Cloud, salvar na pasta temporária
        if os.getenv('IS_STREAMLIT_CLOUD', '0') == '1':
            caminho_pdf = os.path.join('/tmp', nome_arquivo)
        else:
            caminho_pdf = os.path.join(os.path.expanduser("~"), "Downloads", nome_arquivo)
            
        pdf.output(caminho_pdf)
        return caminho_pdf

    def imprimir_pedido(self, numero_pedido: str):
        """Gera um PDF do pedido"""
        try:
            # Obter dados do pedido
            pedido = self.controller.get_pedido_detalhes(numero_pedido)
            texto = self.formatar_pedido_para_impressao(pedido)
            
            # Gerar PDF
            caminho_pdf = self._criar_pdf(texto)
            
            # Mostrar link para download
            if os.path.exists(caminho_pdf):
                with open(caminho_pdf, 'rb') as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="📥 Baixar PDF do Pedido",
                    data=pdf_bytes,
                    file_name=os.path.basename(caminho_pdf),
                    mime="application/pdf"
                )
            
        except Exception as e:
            raise Exception(f"Erro ao processar pedido: {str(e)}") 