#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de geração de relatório PDF para o Laboratório 3 de MLOps:
"Rodando a API de Intent Classifier na sua máquina e em um container Docker"
Discente: Matheus Vinicius Silva Freire de Castro
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running header (only on pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 810, "IMD3005 - MLOps 2026.2 | Lab 3: API Intent Classifier em Docker")
            self.drawRightString(559, 810, "Discente: Matheus V. S. F. de Castro")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 804, 559, 804)

        # Running footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 42, 559, 42)

        self.drawString(36, 30, "UFRN / IMD — Engenharia de Machine Learning")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(559, 30, page_str)
        self.restoreState()

def build_pdf(pdf_path, swagger_img_path, logs_img_path, controller_code_path):
    # A4: 595.27 x 841.89 pt. Margins: left=36, right=36, top=44, bottom=48 -> usable width = 523.27 pt
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    caption_style = ParagraphStyle(
        'CaptionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        alignment=1, # Center
        textColor=colors.HexColor("#64748B"),
        spaceBefore=4,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B")
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.8,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # =========================================================================
    # PÁGINA 1: Identificação, Visão Geral e Arquitetura MLOps
    # =========================================================================
    story.append(Paragraph("Laboratório 3: Rodando a API de Intent Classifier na sua máquina e em um container Docker", title_style))
    story.append(Paragraph("IMD3005 - Engenharia de Machine Learning (MLOps) · 2026.2", subtitle_style))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>Docente:</b> Prof. Dr. Adelson de Araújo Silva Júnior<br/><b>Instituição:</b> Instituto Metrópole Digital (IMD / UFRN)<br/><b>Disciplina:</b> IMD3005 - Engenharia de Machine Learning", body_style),
            Paragraph("<b>Discente:</b> Matheus Vinicius Silva Freire de Castro<br/><b>GitHub:</b> <font color='#2563EB'>Matheus-dCastro</font><br/><b>Weights & Biases:</b> <font color='#2563EB'>matheus-dcastro</font>", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[255, 268])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Visão Geral da Atividade e Objetivos", h1_style))
    p1 = (
        "O presente relatório documenta a entrega formal do <b>Laboratório 3</b> da disciplina de MLOps. "
        "O objetivo central foi colocar em operação, tanto localmente quanto encapsulada em um container Docker, "
        "a API de classificação de intenções (<i>Intent Classifier</i>) desenvolvida ao longo da unidade curricular. "
        "A aplicação é construída sobre o framework <b>FastAPI</b> e atua como uma camada de inferência e persistência que integra:"
    )
    story.append(Paragraph(p1, body_style))

    pillars = (
        "<b>1. Gerenciamento e Versionamento de Artefatos:</b> Consumo do modelo de deep learning treinado "
        "(<code>model.keras</code> e metadados <code>model_config.yml</code>) hospedado no registro de artefatos do <i>Weights & Biases (W&B)</i>, "
        "identificado como <code>matheus-dcastro/mlops-2026-2/confusion-clf:v0</code>.<br/>"
        "<b>2. Camada de Embeddings Pré-treinados:</b> Utilização do <i>Universal Sentence Encoder (USE)</i> da biblioteca TensorFlow Hub "
        "para vetorização de sentenças textuais em representações densas de 512 dimensões.<br/>"
        "<b>3. Persistência NoSQL e Auditoria:</b> Armazenamento de cada mensagem submetida e das predições inferidas em banco "
        "MongoDB (coleção <code>predictions</code>), garantindo rastreabilidade histórica e monitoramento de <i>data drift</i>.<br/>"
        "<b>4. Conteinerização e Reprodutibilidade:</b> Empacotamento completo do runtime (Python 3.11, TensorFlow 2.19, Keras 3.13) "
        "via <code>Dockerfile</code> e orquestração por <code>docker-compose.yml</code> com isolamento de credenciais em arquivo <code>.env</code>."
    )
    p_box = Table([[Paragraph(pillars, callout_style)]], colWidths=[523])
    p_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#93C5FD")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(p_box)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Arquitetura da Solução e Fluxo de Execução", h1_style))
    p_arch = (
        "A solução adota uma arquitetura em camadas orientada a serviços desacoplados:<br/>"
        "• <b>Fase de Inicialização (Cold Start):</b> Ao subir o container <code>mlops-container</code>, o Uvicorn dispara a inicialização do FastAPI. "
        "O módulo <code>service.py</code> autentica no Weights & Biases via <code>WANDB_API_KEY</code>, verifica a existência do artefato informado em <code>WANDB_MODELS</code>, "
        "baixa os arquivos para o cache local do container e carrega o modelo Keras em memória, acompanhado pelo módulo do TF-Hub.<br/>"
        "• <b>Fase de Inferência (POST /predictions):</b> O cliente submete um payload JSON validado pelo modelo Pydantic <code>Mensagem</code> "
        "(contendo <code>id</code>, <code>nome</code> e <code>text</code>). A requisição é encaminhada para <code>service.predict_all()</code>, "
        "que gera a distribuição de probabilidades e a classe com maior confiança. Em seguida, a mensagem original é incorporada ao dicionário "
        "de saída e registrada no MongoDB via <code>prediction_collection.insert_one()</code>. O identificador <code>_id</code> é removido para compatibilidade "
        "com a serialização JSON e a resposta é devolvida ao cliente com <b>Status Code 200 OK</b>."
    )
    story.append(Paragraph(p_arch, body_style))

    # =========================================================================
    # PÁGINA 2: Item 1 - Print do Swagger (POST /predictions)
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("3. Item 1: Print do Swagger (POST /predictions)", h1_style))
    p_sw_text = (
        "Conforme requisitado no item 1 das orientações de entrega, foi executada a requisição ao endpoint <code>POST /predictions</code> "
        "através da interface Swagger UI (<code>http://localhost:8000/docs</code>). No corpo da requisição, foi utilizado o nome completo do aluno "
        "no campo <code>nome</code> (<b>Matheus Vinicius Silva Freire de Castro</b>) e um exemplo representativo de texto. "
        "A <b>Figura 1</b> comprova o retorno da requisição com <b>Server response 200</b> e o corpo da resposta contendo o resultado da inferência do modelo."
    )
    story.append(Paragraph(p_sw_text, body_style))
    story.append(Spacer(1, 4))

    # Swagger Image
    # Image aspect ratio: 1229x1426 -> 0.862 width/height.
    # We want max height ~540 pt so it fits with text and caption on this single page.
    # width = 450, height = 450 * 1426 / 1229 = 522 pt.
    if os.path.exists(swagger_img_path):
        img_swagger = Image(swagger_img_path, width=450, height=522)
        story.append(img_swagger)
        story.append(Paragraph("<b>Figura 1:</b> Interface interativa do Swagger UI (FastAPI) em <code>/docs</code> evidenciando a execução do <code>POST /predictions</code> com código HTTP 200 OK, nome do aluno e resposta do classificador de intenção.", caption_style))
    else:
        story.append(Paragraph("<b>[ERRO: Imagem print_swagger.png não encontrada]</b>", body_style))

    # =========================================================================
    # PÁGINA 3: Item 2 - Conteúdo de controller.py
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("4. Item 2: Conteúdo de controller.py", h1_style))
    p_ctrl_intro = (
        "Em observância rigorosa às diretrizes da atividade (que estipulam: <i>'No PDF: o código colado como texto (não como imagem)'</i>), "
        "transcreve-se abaixo o conteúdo integral e fidedigno do arquivo <code>src/modules/intent_classifier/controller.py</code> "
        "utilizado para a orquestração dos endpoints e integração com o MongoDB."
    )
    story.append(Paragraph(p_ctrl_intro, body_style))

    with open(controller_code_path, 'r', encoding='utf-8') as f:
        code_raw = f.read()

    # Formatted code table
    code_table = Table([[Paragraph(f"<pre>{code_raw}</pre>", code_style)]], colWidths=[523])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(code_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Análise Técnica e Justificativa de Engenharia do Código:", h2_style))
    p_analysis = (
        "• <b>Injeção de Metadados e Gravação Atômica (linhas 15-17):</b> "
        "A função <code>service.predict_all(msg.text)</code> processa o texto e retorna o mapa de intenções inferidas. "
        "Antes da chamada de banco, o comando <code>outputs['message'] = msg.model_dump()</code> consolida os dados submetidos pelo usuário "
        "(incluindo o timestamp gerado automaticamente pelo Pydantic), criando uma estrutura única e autocontida para fins de auditoria.<br/>"
        "• <b>Tratamento do ObjectId do PyMongo (linha 18):</b> "
        "A operação <code>prediction_collection.insert_one(outputs)</code> muta diretamente o dicionário passado como parâmetro, injetando a chave <code>_id</code> "
        "com uma instância de <code>bson.objectid.ObjectId</code>. Como este tipo BSON não possui serializador JSON nativo no padrão FastAPI/Pydantic, "
        "a chamada <code>outputs.pop('_id', None)</code> remove essa chave antes do retorno da função, evitando erros de serialização (código HTTP 500) e garantindo uma resposta JSON válida.<br/>"
        "• <b>Consulta Histórica com Projeção e Ordenação (linhas 21-27):</b> "
        "O endpoint <code>GET /predictions</code> disponibiliza a consulta com limite configurável (<code>limit: int = 20</code>). "
        "A projeção <code>{'_id': 0}</code> no método <code>.find()</code> suprime eficientemente o identificador BSON em nível de banco, "
        "enquanto <code>.sort('message.timestamp', -1)</code> garante que as predições mais recentes sejam entregues prioritariamente."
    )
    story.append(Paragraph(p_analysis, body_style))

    # =========================================================================
    # PÁGINA 4: Item 3 - Print dos Logs do Docker & Checklist
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("5. Item 3: Print dos Logs do Container Docker", h1_style))
    p_log_intro = (
        "Conforme requisitado no item 3, foi executado o monitoramento dos logs do container em execução através do comando "
        "<code>docker logs -f mlops-container</code>. A <b>Figura 2</b> evidencia o terminal com o registro em tempo real "
        "da requisição <code>POST /predictions HTTP/1.1</code> respondida com o código <b>200 OK</b>, originada da submissão realizada no Swagger UI."
    )
    story.append(Paragraph(p_log_intro, body_style))
    story.append(Spacer(1, 4))

    # Logs Image
    # Image is 1150x589 -> aspect ratio 1.95. Width 490, height = 490 * 589 / 1150 = 251 pt.
    if os.path.exists(logs_img_path):
        img_logs = Image(logs_img_path, width=490, height=251)
        story.append(img_logs)
        story.append(Paragraph("<b>Figura 2:</b> Terminal capturado em tempo real com o comando <code>docker logs -f mlops-container</code>, evidenciando o registro do método HTTP POST respondido com 200 OK.", caption_style))
    else:
        story.append(Paragraph("<b>[ERRO: Imagem print_logs.png não encontrada]</b>", body_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("6. Checklist de Verificação e Protocolo de Sigilo", h1_style))
    p_sec = (
        "Em estrito atendimento às recomendações de segurança da disciplina, <b>o arquivo <code>.env</code> não faz parte da entrega</b>, "
        "não foi incluído no pacote ZIP nem no PDF e está devidamente configurado no <code>.gitignore</code>. "
        "Adicionalmente, nenhuma chave privada do Weights & Biases nem credenciais de acesso do MongoDB foram exibidas em logs ou capturas de tela."
    )
    story.append(Paragraph(p_sec, body_style))

    # Checklist Table
    chk_rows = [
        [Paragraph("<b>Item Avaliado</b>", body_bold), Paragraph("<b>Situação</b>", body_bold), Paragraph("<b>Evidência / Detalhes de Conformidade</b>", body_bold)],
        [
            Paragraph("Ambiente Conda / Python 3.11", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("Ambiente <code>mlops-2026-2</code> com TF 2.19.1 e Keras 3.13.2", body_style)
        ],
        [
            Paragraph("Artefato no W&B (model.keras + config)", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("<code>matheus-dcastro/mlops-2026-2/confusion-clf:v0</code> publicado", body_style)
        ],
        [
            Paragraph("Segurança do <code>.env</code> e chaves", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("Totalmente protegido; ausente no PDF, ZIP e prints", body_style)
        ],
        [
            Paragraph("Swagger UI: POST /predictions 200 OK", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("Nome 'Matheus Vinicius Silva Freire de Castro' (Figura 1)", body_style)
        ],
        [
            Paragraph("Execução em Container Docker", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("Subido via Docker Compose (container <code>mlops-container</code>)", body_style)
        ],
        [
            Paragraph("Logs do Container com 200 OK", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("Terminal <code>docker logs -f mlops-container</code> (Figura 2)", body_style)
        ],
        [
            Paragraph("Código <code>controller.py</code> em texto", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("Transcrito integralmente na Seção 4 como texto pesquisável", body_style)
        ],
        [
            Paragraph("Padrão de Nome do Arquivo", body_style),
            Paragraph("<font color='#16A34A'><b>CONCLUÍDO</b></font>", body_style),
            Paragraph("Nomeado rigorosamente como <code>lab_api_Matheus_Castro.pdf</code>", body_style)
        ]
    ]

    chk_table = Table(chk_rows, colWidths=[165, 75, 283])
    chk_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (1,1), (1,-1), 'CENTER'),
    ]))
    story.append(chk_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Build concluído com sucesso: {pdf_path}")

if __name__ == '__main__':
    base_dir = "/home/alomy/Projetos/UFRN_06/MLOPS/lista unidade 2"
    entrega_dir = os.path.join(base_dir, "entrega_lab3")
    swagger_img = os.path.join(entrega_dir, "print_swagger.png")
    logs_img = os.path.join(entrega_dir, "print_logs.png")
    ctrl_file = os.path.join(entrega_dir, "controller.py")

    output_pdf1 = os.path.join(base_dir, "lab_api_Matheus_Castro.pdf")
    output_pdf2 = os.path.join(base_dir, "lab_api_Matheus_Vinicius_Silva_Freire_de_Castro.pdf")

    build_pdf(output_pdf1, swagger_img, logs_img, ctrl_file)
    build_pdf(output_pdf2, swagger_img, logs_img, ctrl_file)
