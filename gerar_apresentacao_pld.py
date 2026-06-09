# -*- coding: utf-8 -*-
"""
Gerador da apresentacao executiva:
"Principais Topologias e Cenarios de Lavagem de Dinheiro, Financiamento do
Terrorismo e Proliferacao de Armas de Destruicao em Massa em Adquirentes no Brasil"

Tema corporativo azul, pronto para comites executivos e auditorias.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

# ----------------------------------------------------------------------------
# Paleta corporativa (tons de azul)
# ----------------------------------------------------------------------------
NAVY      = RGBColor(0x0F, 0x25, 0x40)   # azul marinho profundo
PRIMARY   = RGBColor(0x1F, 0x4E, 0x79)   # azul institucional
SECONDARY = RGBColor(0x2E, 0x75, 0xB6)   # azul medio
ACCENT    = RGBColor(0x4A, 0x90, 0xD2)   # azul claro de destaque
ICE       = RGBColor(0xEA, 0xF2, 0xFB)   # azul gelo (fundo de caixas)
LIGHT     = RGBColor(0xD6, 0xE4, 0xF0)   # azul claro
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
GRAYTXT   = RGBColor(0x3A, 0x3A, 0x3A)
LIGHTGRAY = RGBColor(0xF4, 0xF6, 0xF9)
RED       = RGBColor(0xC0, 0x39, 0x2B)   # red flag
GREEN     = RGBColor(0x1E, 0x7A, 0x4D)
AMBER     = RGBColor(0xC9, 0x8A, 0x1B)

FONT = "Calibri"
FONT_H = "Calibri"

# 16:9
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def slide():
    return prs.slides.add_slide(BLANK)


def _set_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def rect(s, x, y, w, h, color, line=None, line_w=None, shape_type=MSO_SHAPE.RECTANGLE):
    shp = s.shapes.add_shape(shape_type, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = line_w or Pt(1)
    shp.shadow.inherit = False
    return shp


def textbox(s, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    return tb, tf


def add_par(tf, text, size=14, color=GRAYTXT, bold=False, italic=False,
            align=PP_ALIGN.LEFT, font=FONT, space_after=4, space_before=0,
            level=0, first=False, line_spacing=1.0):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    p.level = level
    p.space_after = Pt(space_after)
    p.space_before = Pt(space_before)
    if line_spacing:
        p.line_spacing = line_spacing
    r = p.add_run()
    r.text = text
    f = r.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = font
    f.color.rgb = color
    return p


def bullet(tf, text, size=13, color=GRAYTXT, bold=False, level=0, first=False,
           marker="• ", space_after=4, mcolor=None):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.level = level
    p.space_after = Pt(space_after)
    p.line_spacing = 1.02
    rm = p.add_run()
    rm.text = marker
    rm.font.size = Pt(size)
    rm.font.bold = True
    rm.font.name = FONT
    rm.font.color.rgb = mcolor or SECONDARY
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = FONT
    r.font.color.rgb = color
    return p


def page_header(s, kicker, title, idx=None):
    """Faixa superior padrao das paginas de conteudo."""
    rect(s, 0, 0, SW, Inches(1.15), PRIMARY)
    rect(s, 0, Inches(1.15), SW, Inches(0.06), ACCENT)
    # barra lateral
    rect(s, 0, 0, Inches(0.18), Inches(1.15), ACCENT)
    tb, tf = textbox(s, Inches(0.55), Inches(0.12), Inches(11.8), Inches(0.95),
                     anchor=MSO_ANCHOR.MIDDLE)
    if kicker:
        add_par(tf, kicker.upper(), size=11.5, color=LIGHT, bold=True, first=True,
                space_after=2)
        add_par(tf, title, size=21, color=WHITE, bold=True, space_after=0)
    else:
        add_par(tf, title, size=23, color=WHITE, bold=True, first=True)
    if idx is not None:
        tbn, tfn = textbox(s, Inches(12.4), Inches(0.0), Inches(0.9), Inches(1.15),
                           anchor=MSO_ANCHOR.MIDDLE)
        add_par(tfn, idx, size=30, color=ACCENT, bold=True, align=PP_ALIGN.CENTER,
                first=True)


def footer(s, n):
    tb, tf = textbox(s, Inches(0.45), Inches(7.06), Inches(9), Inches(0.35))
    add_par(tf, "PLD/FT/FPADM  |  Adquirencia  |  Documento confidencial - uso interno",
            size=8.5, color=RGBColor(0x90, 0x9C, 0xAC), first=True)
    tb2, tf2 = textbox(s, Inches(12.2), Inches(7.06), Inches(0.9), Inches(0.35))
    add_par(tf2, str(n), size=9, color=SECONDARY, bold=True, align=PP_ALIGN.RIGHT,
            first=True)


_pageno = {"n": 0}
def newpage(kicker, title, idx=None):
    _pageno["n"] += 1
    s = slide()
    rect(s, 0, 0, SW, SH, WHITE)
    page_header(s, kicker, title, idx)
    footer(s, _pageno["n"])
    return s


def card(s, x, y, w, h, header, color=PRIMARY, header_color=WHITE, body_fill=ICE):
    """Caixa com cabecalho colorido. Retorna o text_frame do corpo."""
    rect(s, x, y, w, h, body_fill, line=LIGHT, line_w=Pt(0.75))
    hh = Inches(0.42)
    rect(s, x, y, w, hh, color)
    tbh, tfh = textbox(s, x + Inches(0.12), y, w - Inches(0.24), hh,
                       anchor=MSO_ANCHOR.MIDDLE)
    add_par(tfh, header, size=12.5, color=header_color, bold=True, first=True)
    tb, tf = textbox(s, x + Inches(0.14), y + hh + Inches(0.06),
                     w - Inches(0.28), h - hh - Inches(0.14))
    return tf


def flow_box(s, x, y, w, h, title, sub=None, color=SECONDARY, tcolor=WHITE,
             tsize=11.5, rounded=True):
    st = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = rect(s, x, y, w, h, color, shape_type=st)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = title
    r.font.size = Pt(tsize); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = tcolor
    if sub:
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = sub
        r2.font.size = Pt(8.5); r2.font.name = FONT; r2.font.color.rgb = tcolor
    return shp


def arrow(s, x1, y1, x2, y2, color=PRIMARY, w=Pt(2.25)):
    cn = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    cn.line.color.rgb = color
    cn.line.width = w
    line = cn.line._get_or_add_ln()
    head = line.makeelement(qn('a:tailEnd'),
                            {'type': 'triangle', 'w': 'med', 'len': 'med'})
    line.append(head)
    return cn


def chip(s, x, y, w, text, color=SECONDARY, tcolor=WHITE, h=Inches(0.34), size=10.5):
    shp = rect(s, x, y, w, h, color, shape_type=MSO_SHAPE.ROUNDED_RECTANGLE)
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = tcolor
    return shp


def style_table(table, header_fill=PRIMARY, header_color=WHITE, body_size=9.5,
                header_size=10, zebra=ICE, col_aligns=None):
    tbl = table._tbl
    # remover estilo padrao bandado
    for tblPr in tbl.iter(qn('a:tblPr')):
        tblPr.set('firstRow', '1')
        tblPr.set('bandRow', '0')
    nrows = len(table.rows)
    ncols = len(table.columns)
    for r in range(nrows):
        for c in range(ncols):
            cell = table.cell(r, c)
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if r == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if (r % 2 == 1) else zebra
            for p in cell.text_frame.paragraphs:
                p.line_spacing = 1.0
                if col_aligns and r > 0:
                    p.alignment = col_aligns[c]
                elif r == 0:
                    p.alignment = PP_ALIGN.LEFT
                for run in p.runs:
                    run.font.name = FONT
                    run.font.size = Pt(header_size if r == 0 else body_size)
                    run.font.bold = (r == 0)
                    run.font.color.rgb = header_color if r == 0 else GRAYTXT


def set_cell(table, r, c, text, color=None, bold=None, size=None, align=None):
    cell = table.cell(r, c)
    cell.text = text
    p = cell.text_frame.paragraphs[0]
    if align is not None:
        p.alignment = align
    for run in p.runs:
        if color is not None:
            run.font.color.rgb = color
        if bold is not None:
            run.font.bold = bold
        if size is not None:
            run.font.size = Pt(size)


def prio_color(p):
    return {"Critica": RED, "Alta": AMBER, "Media": SECONDARY, "Baixa": GREEN}.get(p, GRAYTXT)


# ============================================================================
# SLIDE 1 - CAPA
# ============================================================================
s = slide()
rect(s, 0, 0, SW, SH, NAVY)
# faixas decorativas
rect(s, 0, 0, SW, Inches(0.28), ACCENT)
rect(s, 0, Inches(5.55), SW, Inches(0.10), ACCENT)
# bloco lateral de grafismo
for i, cl in enumerate([PRIMARY, SECONDARY, ACCENT]):
    rect(s, Inches(0), Inches(0.28) + Inches(0.0), Inches(0.0), Inches(0.0), cl)
rect(s, Inches(10.7), 0, Inches(2.63), SH, PRIMARY)
rect(s, Inches(10.4), 0, Inches(0.10), SH, ACCENT)
# barras "transacionais" decorativas no bloco lateral
import random
random.seed(7)
by = Inches(1.1)
for i in range(11):
    hh = Inches(0.18 + (i % 5) * 0.12)
    rect(s, Inches(10.95), Inches(0.9) + Emu(int(i * 460000)), hh, Inches(0.10),
         ACCENT if i % 2 else SECONDARY)

tb, tf = textbox(s, Inches(0.7), Inches(1.2), Inches(9.4), Inches(0.6))
add_par(tf, "APRESENTACAO EXECUTIVA  |  COMPLIANCE - RISCOS - PLD/FT",
        size=13, color=ACCENT, bold=True, first=True)

tb, tf = textbox(s, Inches(0.7), Inches(1.95), Inches(9.4), Inches(2.9))
add_par(tf, "Principais Topologias e Cenarios de Lavagem de Dinheiro, "
            "Financiamento do Terrorismo e Proliferacao de Armas de Destruicao em Massa",
        size=30, color=WHITE, bold=True, first=True, line_spacing=1.05, space_after=8)
add_par(tf, "em Adquirentes no Brasil", size=30, color=ACCENT, bold=True,
        line_spacing=1.05)

tb, tf = textbox(s, Inches(0.7), Inches(5.85), Inches(9.4), Inches(1.4))
add_par(tf, "Mapeamento de riscos, tipologias AML/CFT, red flags, controles "
            "preventivos e detectivos e regras de monitoramento transacional",
        size=13.5, color=LIGHT, first=True, space_after=6, line_spacing=1.1)
add_par(tf, "Merchant Acquirer  -  Subadquirentes  -  Facilitadores de Pagamento  -  Marketplaces",
        size=11.5, color=ACCENT, bold=True)
add_par(tf, "Documento confidencial - uso interno  |  Comites Executivos e Auditoria",
        size=10, color=RGBColor(0x9A, 0xB4, 0xCE))


# ============================================================================
# SLIDE 2 - CONTEXTO REGULATORIO
# ============================================================================
s = newpage("Fundamentos", "Contexto Regulatorio e Abordagem Baseada em Risco", "01")

col_w = Inches(3.95)
gap = Inches(0.25)
x0 = Inches(0.45)
y0 = Inches(1.5)
ch = Inches(2.55)

tf = card(s, x0, y0, col_w, ch, "Marco Legal Nacional", color=PRIMARY)
bullet(tf, "Lei 9.613/1998 - tipifica lavagem de dinheiro; cria o COAF e o dever de "
           "comunicacao de operacoes suspeitas (atualizada pela Lei 12.683/2012).",
       size=10.5, first=True, space_after=5)
bullet(tf, "Lei 13.260/2016 - tipifica o terrorismo e seu financiamento (FT).", size=10.5, space_after=5)
bullet(tf, "Lei 13.810/2019 - cumprimento de sancoes do CSNU e indisponibilidade "
           "imediata de ativos (FT/FPADM).", size=10.5, space_after=5)
bullet(tf, "Lei 12.846/2013 e LGPD (13.709/2018) como vetores correlatos de "
           "integridade e tratamento de dados.", size=10.5)

tf = card(s, x0 + col_w + gap, y0, col_w, ch, "Regulacao do Banco Central", color=SECONDARY)
bullet(tf, "Circular BCB 3.978/2020 - politica de PLD/FT, ABR, KYC, monitoramento, "
           "selecao, analise e comunicacao de operacoes.", size=10.5, first=True, space_after=5)
bullet(tf, "Resolucao BCB 119/2021 - estende deveres de FT/FPADM e sancoes.", size=10.5, space_after=5)
bullet(tf, "Res. Conj. 6/2023 - troca de informacoes para prevencao a fraudes.", size=10.5, space_after=5)
bullet(tf, "Arranjos de pagamento: Lei 12.865/2012 e Resolucoes BCB 80/150 "
           "(instituicoes de pagamento, credenciadoras e subcredenciadoras).", size=10.5)

tf = card(s, x0 + 2*(col_w + gap), y0, col_w, ch, "Padroes Internacionais", color=ACCENT, header_color=WHITE)
bullet(tf, "40 Recomendacoes do GAFI/FATF, com enfase na R.1 (ABR), R.10-12 (CDD/PEP), "
           "R.16 (travel rule) e R.20 (STR).", size=10.5, first=True, space_after=5)
bullet(tf, "Listas de sancoes: CSNU, OFAC, UE, Reino Unido.", size=10.5, space_after=5)
bullet(tf, "Padroes das bandeiras (Visa VIRP / Mastercard BRAM) para "
           "transaction laundering e merchants de risco.", size=10.5, space_after=5)
bullet(tf, "Guidance FATF para o setor de meios de pagamento e novos modelos de negocio.", size=10.5)

# faixa ABR
y1 = Inches(4.35)
rect(s, x0, y1, Inches(12.43), Inches(2.3), ICE, line=LIGHT, line_w=Pt(0.75))
rect(s, x0, y1, Inches(12.43), Inches(0.45), NAVY)
tbh, tfh = textbox(s, x0 + Inches(0.15), y1, Inches(12), Inches(0.45), anchor=MSO_ANCHOR.MIDDLE)
add_par(tfh, "ABORDAGEM BASEADA EM RISCO (ABR) - PILAR ESTRUTURANTE", size=12.5,
        color=WHITE, bold=True, first=True)
steps = [
    ("1. Avaliacao Interna de Risco", "Mapear produtos, clientes, canais e geografias; classificar EC por MCC, porte e historico."),
    ("2. Politicas e Governanca", "Diretoria responsavel, AIR documentada, segregacao de funcoes, treinamento e avaliacao de efetividade."),
    ("3. Controles Proporcionais", "Intensidade de KYC/KYB, DDR e monitoramento calibrados ao risco do estabelecimento."),
    ("4. Monitoramento Continuo", "Reavaliacao de risco, monitoramento transacional, selecao, analise e comunicacao ao COAF."),
]
cw = Inches(3.0)
cx = x0 + Inches(0.12)
for i, (t, d) in enumerate(steps):
    bx = x0 + Inches(0.12) + i * Inches(3.07)
    rect(s, bx, y1 + Inches(0.6), Inches(2.92), Inches(1.55), WHITE, line=LIGHT, line_w=Pt(0.75))
    rect(s, bx, y1 + Inches(0.6), Inches(0.10), Inches(1.55), ACCENT)
    tb, tcf = textbox(s, bx + Inches(0.18), y1 + Inches(0.7), Inches(2.65), Inches(1.4))
    add_par(tcf, t, size=11, color=PRIMARY, bold=True, first=True, space_after=4, line_spacing=1.0)
    add_par(tcf, d, size=9.3, color=GRAYTXT, line_spacing=1.02)


# ============================================================================
# SLIDE 3 - CADEIA DA ADQUIRENCIA (DIAGRAMA)
# ============================================================================
s = newpage("Ecossistema", "Cadeia da Adquirencia e Pontos Vulneraveis para AML/CFT", "02")

# Fluxo principal
fy = Inches(1.85)
bw, bh = Inches(1.62), Inches(0.95)
xs = Inches(0.5)
nodes = [
    ("Portador", "Cardholder", SECONDARY),
    ("Estab.\nComercial", "Merchant", SECONDARY),
    ("Subadquirente\n/ Facilitador", "Sub / PayFac", ACCENT),
    ("Gateway", "Captura", SECONDARY),
    ("PSP /\nAdquirente", "Credenciadora", PRIMARY),
    ("Bandeiras", "Schemes", SECONDARY),
    ("Banco\nLiquidante", "Settlement", PRIMARY),
]
n = len(nodes)
gap_x = (Inches(12.4) - bw) / (n - 1)
centers = []
for i, (t, sub, cl) in enumerate(nodes):
    x = xs + i * gap_x
    flow_box(s, x, fy, bw, bh, t.replace("\n", " "), sub, color=cl, tsize=10.5)
    centers.append((x + bw, fy + bh / 2, x, x + bw / 2))

for i in range(n - 1):
    x_end = centers[i][0]
    x_next = centers[i + 1][2]
    arrow(s, x_end, fy + bh / 2, x_next, fy + bh / 2, color=PRIMARY, w=Pt(2))

# legenda fluxo
tb, tf = textbox(s, Inches(0.5), fy + bh + Inches(0.05), Inches(12.4), Inches(0.3))
add_par(tf, "Fluxo de autorizacao, captura, compensacao e liquidacao financeira",
        size=9.5, color=SECONDARY, italic=True, align=PP_ALIGN.CENTER, first=True)

# Pontos vulneraveis
vy = Inches(3.55)
rect(s, Inches(0.45), vy, Inches(12.45), Inches(0.42), RED)
tbh, tfh = textbox(s, Inches(0.6), vy, Inches(12), Inches(0.42), anchor=MSO_ANCHOR.MIDDLE)
add_par(tfh, "PONTOS VULNERAVEIS PARA LAVAGEM DE DINHEIRO E FT/FPADM", size=12,
        color=WHITE, bold=True, first=True)

vulns = [
    ("Onboarding de EC", "KYB fragil, laranjas e beneficiario final oculto; merchants fantasma."),
    ("Subadquirencia / PayFac", "Visibilidade reduzida do EC final; agregacao de risco e MCC mascarado."),
    ("Marketplaces", "Sellers de baixa diligencia; transaction laundering e produtos ilicitos."),
    ("Liquidacao / Cash-out", "Antecipacao de recebiveis e contas de destino diversas do titular."),
    ("MCC e classificacao", "Miscoding para esconder ramo de alto risco (apostas, cripto, adulto)."),
    ("Cross-border", "Pagamentos internacionais e exposicao a jurisdicoes e sancoes."),
]
cardw = Inches(4.02)
cardh = Inches(1.18)
gx = Inches(0.13)
gy = Inches(0.12)
sx = Inches(0.45)
sy = vy + Inches(0.55)
for i, (t, d) in enumerate(vulns):
    r = i // 3
    c = i % 3
    x = sx + c * (cardw + gx)
    y = sy + r * (cardh + gy)
    rect(s, x, y, cardw, cardh, ICE, line=LIGHT, line_w=Pt(0.75))
    rect(s, x, y, Inches(0.09), cardh, RED)
    tb, tcf = textbox(s, x + Inches(0.18), y + Inches(0.07), cardw - Inches(0.3), cardh - Inches(0.14))
    add_par(tcf, t, size=11, color=PRIMARY, bold=True, first=True, space_after=2)
    add_par(tcf, d, size=9.5, color=GRAYTXT, line_spacing=1.0)


# ============================================================================
# AGENDA DE TIPOLOGIAS
# ============================================================================
s = newpage("Roteiro", "Tipologias Priorizadas para Adquirentes", "03")
tb, tf = textbox(s, Inches(0.5), Inches(1.4), Inches(12.3), Inches(0.5))
add_par(tf, "Priorizacao de riscos especificos de adquirentes, subadquirentes, "
            "facilitadores de pagamento e marketplaces:", size=13, color=GRAYTXT, first=True)

tipos = [
    ("T1", "Transaction Laundering", "Processamento de vendas ilicitas por merchant aparentemente legitimo."),
    ("T2", "Bust-out & Fraude de Chargeback", "EC inflaciona volume e desaparece antes da liquidacao/contestacao."),
    ("T3", "MCC Miscoding & Factoring", "Mascaramento de ramo e processamento de terceiros (4a parte)."),
    ("T4", "Structuring / Smurfing em POS", "Fracionamento de valores para evadir thresholds e monitoramento."),
    ("T5", "Merchants Fantasma & Laranjas", "EC de fachada, beneficiario final oculto e contas de passagem."),
    ("T6", "Subadquirentes & Marketplaces", "Agregacao que obscurece o EC final e o seller de alto risco."),
    ("T7", "Front Companies de Alto Risco", "Apostas ilegais, cripto, esquemas de investimento e adulto."),
    ("T8", "Financiamento do Terrorismo (FT)", "Baixos valores, NPO, captacao difusa e contas-funil."),
    ("T9", "FPADM & Evasao de Sancoes", "Burla a listas do CSNU/OFAC e dual-use goods via cartoes."),
]
cw = Inches(3.97)
chh = Inches(1.18)
gx = Inches(0.16)
gy = Inches(0.16)
sx = Inches(0.5)
sy = Inches(2.05)
for i, (code, t, d) in enumerate(tipos):
    r = i // 3
    c = i % 3
    x = sx + c * (cw + gx)
    y = sy + r * (chh + gy)
    rect(s, x, y, cw, chh, WHITE, line=LIGHT, line_w=Pt(1))
    rect(s, x, y, Inches(0.85), chh, PRIMARY)
    tbc, tcc = textbox(s, x, y, Inches(0.85), chh, anchor=MSO_ANCHOR.MIDDLE)
    add_par(tcc, code, size=20, color=WHITE, bold=True, align=PP_ALIGN.CENTER, first=True)
    tb, tcf = textbox(s, x + Inches(0.97), y + Inches(0.1), cw - Inches(1.1), chh - Inches(0.2))
    add_par(tcf, t, size=12, color=PRIMARY, bold=True, first=True, space_after=3, line_spacing=1.0)
    add_par(tcf, d, size=9.3, color=GRAYTXT, line_spacing=1.0)


# ============================================================================
# Função para slide de tipologia (estrutura obrigatoria 1-8)
# ============================================================================
def tipologia_slide(code, nome, idx, descricao, fluxo, uso, red_flags,
                    prevent, detect, regras, exemplo):
    s = newpage("Tipologia " + code, nome, idx)

    # Coluna esquerda: descricao + fluxo + uso
    lx = Inches(0.45)
    lw = Inches(5.55)
    y = Inches(1.45)

    tf = card(s, lx, y, lw, Inches(1.30), "1. Descricao da tipologia", color=PRIMARY)
    add_par(tf, descricao, size=9.6, color=GRAYTXT, first=True, line_spacing=1.0)

    y2 = y + Inches(1.40)
    # Fluxo operacional - mini fluxograma
    rect(s, lx, y2, lw, Inches(1.45), ICE, line=LIGHT, line_w=Pt(0.75))
    rect(s, lx, y2, lw, Inches(0.40), SECONDARY)
    tbh, tfh = textbox(s, lx + Inches(0.12), y2, lw - Inches(0.2), Inches(0.40), anchor=MSO_ANCHOR.MIDDLE)
    add_par(tfh, "2. Fluxo operacional", size=12, color=WHITE, bold=True, first=True)
    fbw = (lw - Inches(0.3) - Inches(0.3) * (len(fluxo) - 1)) / len(fluxo)
    fbx = lx + Inches(0.15)
    fby = y2 + Inches(0.55)
    fbh = Inches(0.72)
    cs = []
    for i, step in enumerate(fluxo):
        x = fbx + i * (fbw + Inches(0.3))
        flow_box(s, x, fby, fbw, fbh, step, color=PRIMARY if i % 2 == 0 else ACCENT, tsize=8.5)
        cs.append((x, x + fbw))
    for i in range(len(fluxo) - 1):
        arrow(s, cs[i][1], fby + fbh / 2, cs[i + 1][0], fby + fbh / 2, color=SECONDARY, w=Pt(1.75))

    y3 = y2 + Inches(1.53)
    tf = card(s, lx, y3, lw, Inches(1.58), "3. Como a adquirente pode ser utilizada", color=NAVY)
    for u in uso:
        bullet(tf, u, size=9.4, first=(u == uso[0]), space_after=2)

    y4 = y3 + Inches(1.66)
    tf = card(s, lx, y4, lw, Inches(0.94), "8. Exemplo pratico (observado no setor)",
              color=GREEN, body_fill=RGBColor(0xEC, 0xF6, 0xF0))
    add_par(tf, exemplo, size=9.0, color=GRAYTXT, italic=True, first=True, line_spacing=1.0)

    # Coluna direita
    rx = Inches(6.15)
    rw = Inches(6.72)
    ry = Inches(1.45)

    tf = card(s, rx, ry, rw, Inches(1.55), "4. Indicadores de alerta (red flags)",
              color=RED, body_fill=RGBColor(0xFB, 0xEC, 0xEA))
    for rf in red_flags:
        bullet(tf, rf, size=9.6, first=(rf == red_flags[0]), space_after=2, mcolor=RED)

    ry2 = ry + Inches(1.65)
    half = (rw - Inches(0.2)) / 2
    tf = card(s, rx, ry2, half, Inches(1.7), "5. Controles preventivos", color=SECONDARY)
    for p in prevent:
        bullet(tf, p, size=9.2, first=(p == prevent[0]), space_after=2)
    tf = card(s, rx + half + Inches(0.2), ry2, half, Inches(1.7), "6. Controles detectivos", color=ACCENT)
    for d in detect:
        bullet(tf, d, size=9.2, first=(d == detect[0]), space_after=2)

    ry3 = ry2 + Inches(1.8)
    tf = card(s, rx, ry3, rw, Inches(1.7), "7. Regras de monitoramento sugeridas", color=PRIMARY)
    for rg in regras:
        bullet(tf, rg, size=9.4, first=(rg == regras[0]), space_after=3)
    return s


# ---- T1 Transaction Laundering ----
tipologia_slide(
    "T1", "Transaction Laundering (Lavagem Transacional via Merchant)", "04",
    "Modalidade de merchant-based laundering na qual um estabelecimento comercial regularmente "
    "credenciado processa transacoes de cartao referentes a vendas de um negocio ilicito ou nao "
    "declarado (drogas, armas, fraude, conteudo proibido), 'emprestando' seu MID. Tambem chamado de "
    "transaction laundering, factoring ou pass-through processing.",
    ["EC legitimo", "Recebe vendas\nde terceiro ilicito", "Processa no\nMID proprio", "Liquidacao\nlimpa"],
    ["Merchant legitimo aceita processar vendas de um 'merchant invisivel' nao credenciado.",
     "URLs/checkout ocultos redirecionam pagamentos para o MID emprestado.",
     "PayFac/marketplace sem visibilidade do EC final permite o repasse.",
     "Funnel accounts agregam recebiveis de multiplos sites ilicitos."],
    ["Volume e ticket incompativeis com o MCC, o porte e a localizacao do EC.",
     "Trafego de IP/dispositivo e BIN de cartoes inconsistentes com o publico esperado.",
     "Picos de venda noturna, cross-border anormal e produtos genericos.",
     "URLs do site sem correspondencia com o produto declarado; conteudo oculto.",
     "Multiplos EC com mesmo IP, conta de liquidacao, telefone ou beneficiario final."],
    ["KYB robusto com verificacao de site, produto e URL real",
     "Validacao de MCC e teste de compra (mystery shopping)",
     "Beneficiario final e cruzamento de cadastros",
     "Visita / geolocalizacao do EC"],
    ["Web crawling e content matching do site do EC",
     "Modelos de ML para outliers de volume/MCC",
     "Analise de rede (devices, IP, conta de credito)",
     "Monitoramento de chargeback e refund"],
    ["Desvio do ticket medio vs. peer group do MCC (> X desvios-padrao).",
     "Mismatch entre conteudo do site e MCC declarado.",
     "Compartilhamento de IP/conta de liquidacao entre >=N MIDs.",
     "Crescimento de volume > X% em <30 dias pos-onboarding."],
    "Caso eNom/RG (EUA) e investigacoes da Visa: redes de transaction laundering "
    "processaram vendas de drogas e produtos ilegais por MIDs de e-commerce legitimos, "
    "movimentando centenas de milhoes de dolares antes da deteccao por content matching.",
)

# ---- T2 Bust-out ----
tipologia_slide(
    "T2", "Bust-out e Fraude de Chargeback", "05",
    "Estabelecimento e credenciado com perfil aparentemente normal e, apos construir historico, "
    "infla subitamente o volume com transacoes fraudulentas (cartoes roubados, vendas ficticias ou "
    "autocompras) e desaparece antes da liquidacao ou da janela de contestacao, deixando prejuizo de "
    "chargeback e recebiveis ja sacados/antecipados.",
    ["Onboarding\n'limpo'", "Historico\nnormal", "Pico subito\nde vendas", "Cash-out e\ndesaparece"],
    ["EC usa antecipacao de recebiveis para sacar antes do chargeback.",
     "Autocompras com cartoes proprios/laranjas para gerar liquidez.",
     "Marketplace/subadquirente com reserva financeira insuficiente.",
     "Troca de conta bancaria de liquidacao as vesperas do cash-out."],
    ["Aumento abrupto de faturamento sem sazonalidade que o justifique.",
     "Alta taxa de chargeback/contestacao (acima do limite das bandeiras).",
     "Concentracao de transacoes em poucos cartoes ou BINs.",
     "Pedido de antecipacao total logo apos pico de vendas.",
     "Alteracao de dados bancarios proxima a saques relevantes."],
    ["Reserva financeira / rolling reserve por risco",
     "Limites de processamento por fase de maturidade",
     "Re-KYC ao alterar conta de liquidacao",
     "Score de risco no onboarding"],
    ["Monitoramento de chargeback ratio em tempo quase real",
     "Velocity de transacoes e de cartoes distintos",
     "Alertas de mudanca de comportamento",
     "Hold de liquidacao por regra de risco"],
    ["Chargeback ratio > 0,9% ou contagem > limiar da bandeira.",
     "Crescimento de volume diario > X% vs. media movel de 30d.",
     "Antecipacao >= Y% do volume em janela de Z dias.",
     "Mudanca de conta bancaria + pico de vendas em 72h."],
    "Padrao recorrente em adquirentes globais ('merchant bust-out'): ECs de e-commerce "
    "geram milhoes em vendas ficticias em dias, antecipam recebiveis e encerram operacao, "
    "transferindo o prejuizo de chargeback para o adquirente/subadquirente.",
)

# ---- T3 MCC miscoding ----
tipologia_slide(
    "T3", "MCC Miscoding e Factoring (Processamento de Terceiros)", "06",
    "Manipulacao do Merchant Category Code para mascarar a verdadeira atividade economica "
    "(ex.: apostas/cripto/adulto classificados como varejo), e factoring/4-party processing, em que "
    "um EC processa transacoes de outro nao habilitado, contornando regras de bandeira e a ABR da adquirente.",
    ["Atividade real\nde alto risco", "Cadastro com\nMCC 'limpo'", "Processa via\nMID de terceiro", "Evita controles\ne regras"],
    ["EC declara MCC de baixo risco para escapar de DDR e limites.",
     "Factoring: lojista 'aluga' MID para negocio nao credenciado.",
     "Subadquirente agrega ramos distintos sob um unico MCC.",
     "Split de MCC para diluir verticais proibidas pela adquirente."],
    ["Produtos/site incompativeis com o MCC declarado.",
     "Tickets, sazonalidade e chargeback tipicos de outro ramo.",
     "Mesma razao social/BF operando varios MCCs.",
     "MCC de alto risco logo apos recodificacao recente.",
     "Descricao do soft descriptor divergente do MCC."],
    ["Validacao de MCC contra atividade e CNAE",
     "KYB com verificacao de site e produto",
     "Regras de bandeira (BRAM/VIRP) embutidas",
     "Aprovacao reforcada para troca de MCC"],
    ["Reclassificacao automatica por perfil transacional",
     "Comparacao MCC vs. peer behavior",
     "Deteccao de soft descriptor inconsistente",
     "Alertas de mudanca de MCC"],
    ["MCC declarado vs. MCC inferido por ML diverge (flag).",
     "Padrao de chargeback/ticket tipico de MCC de risco.",
     "Troca de MCC para vertical sensivel < 90d.",
     "BF/CNPJ raiz associado a MCC de alto risco em outro EC."],
    "Operadoras de apostas e cripto sem licenca recorrentemente se cadastram como "
    "varejo/servicos genericos para acessar a rede; programas BRAM/VIRP multam adquirentes "
    "que falham em detectar miscoding e transaction laundering.",
)

# ---- T4 Structuring ----
tipologia_slide(
    "T4", "Structuring / Smurfing em Ambiente de POS e E-commerce", "07",
    "Fracionamento deliberado de valores em multiplas transacoes de menor porte (em um ou varios EC, "
    "cartoes, terminais ou dias) para permanecer abaixo de thresholds regulatorios e de monitoramento, "
    "dificultando a deteccao e a comunicacao de operacoes ao COAF.",
    ["Recurso de\norigem ilicita", "Fracionamento\nem N transacoes", "Multiplos POS\n/ cartoes", "Recebiveis\nconsolidados"],
    ["Multiplas compras logo abaixo de limites de alerta/comunicacao.",
     "Uso de varios cartoes/portadores no mesmo EC (cash-in).",
     "Distribuicao do volume entre terminais e dias.",
     "Subadquirente concentra recebiveis fracionados de varios sellers."],
    ["Sequencia de transacoes em valores 'redondos' logo abaixo de thresholds.",
     "Repeticao de tickets quase identicos em curto intervalo.",
     "Muitos cartoes distintos para o mesmo EC em janela curta.",
     "Cancelamentos/estornos parciais que reconfiguram valores.",
     "Padrao 24/7 incompativel com horario comercial."],
    ["Definicao de thresholds dinamicos por perfil",
     "KYC do portador em canais aplicaveis",
     "Limites por terminal e por ciclo",
     "Politica de agregacao por BF/CNPJ raiz"],
    ["Agregacao de valores por janela movel (dia/semana)",
     "Deteccao de padroes just-below-threshold",
     "Velocity por EC, terminal e cartao",
     "Analise comportamental de series temporais"],
    ["Soma diaria por EC >= R$ X via N+ transacoes individuais < limiar.",
     "K+ transacoes em [limiar-10%, limiar] na mesma janela.",
     "M+ cartoes distintos por EC/dia acima do baseline.",
     "Indice de fracionamento (n. txn / valor medio) anomalo."],
    "Tipologia classica destacada pelo COAF/FATF: valores fracionados logo abaixo dos "
    "limites de comunicacao para evitar STR, adaptada ao ambiente de adquirencia por meio de "
    "multiplos terminais, cartoes e sellers de subadquirentes.",
)

# ---- T5 Merchants fantasma ----
tipologia_slide(
    "T5", "Merchants Fantasma, Laranjas e Beneficiario Final Oculto", "08",
    "Constituicao de EC de fachada (shell merchants) ou uso de interpostas pessoas (laranjas) cujo "
    "beneficiario final real esta oculto, com a finalidade de injetar e movimentar recursos ilicitos, "
    "frequentemente combinada a contas de passagem e laranjas no fluxo de liquidacao.",
    ["Empresa de\nfachada", "Laranja como\nrepresentante", "Vendas ficticias\n/ ilicitas", "Liquidacao p/ BF\noculto"],
    ["EC sem operacao real recebendo volume relevante de cartao.",
     "Conta de liquidacao de titular diverso do EC.",
     "Mesmo BF controlando uma teia de EC fantasmas.",
     "Onboarding 100% digital sem verificacao fisica."],
    ["Endereco inexistente, virtual ou compartilhado por varios EC.",
     "Socios sem capacidade economica compativel (laranjas).",
     "Documentacao societaria recente e generica.",
     "Conta de liquidacao em nome de terceiro.",
     "Ausencia de presenca digital/fisica verificavel."],
    ["KYB e identificacao do beneficiario final",
     "Validacao cadastral e biometria",
     "Geolocalizacao e visita ao estabelecimento",
     "Screening de socios e BF"],
    ["Analise de rede de BF/socios/contas",
     "Deteccao de EC inativos com pico de volume",
     "Cruzamento conta de liquidacao x titular",
     "Verificacao de endereco e presenca"],
    ["Conta de liquidacao com CPF/CNPJ != titular do EC.",
     "N+ EC com mesmo BF, endereco, telefone ou IP.",
     "EC ativo < 90d com volume > R$ X.",
     "Socio com flag de laranja em base interna/externa."],
    "Esquemas de evasao e lavagem usam redes de empresas de fachada com socios laranjas "
    "para 'limpar' recursos via maquininhas; a quebra do sigilo do beneficiario final e o cruzamento "
    "de cadastros sao os principais vetores de deteccao.",
)

# ---- T6 Subadquirentes/marketplaces ----
tipologia_slide(
    "T6", "Subadquirentes, Facilitadores e Marketplaces (Agregacao)", "09",
    "Modelos de PayFac, subadquirencia e marketplace agregam multiplos sellers sob um unico relacionamento "
    "com a adquirente, reduzindo a visibilidade do EC final. Sellers de baixa diligencia podem realizar "
    "transaction laundering, venda de produtos ilicitos e estruturacao sob o 'guarda-chuva' do agregador.",
    ["Adquirente", "Subadquirente\n/ PayFac", "Marketplace\nagrega sellers", "Seller final\n(opaco)"],
    ["Subadquirente repassa risco sem KYB equivalente dos sellers.",
     "Marketplace onboarda sellers com diligencia minima.",
     "EC final invisivel a adquirente (nested merchants).",
     "Liquidacao agregada dificulta rastrear o seller de risco."],
    ["Sub/marketplace sem politica de PLD ou KYC de seller fraca.",
     "Crescimento explosivo de sellers em curto periodo.",
     "Alta dispersao de MCC e geografias sob um unico CNPJ.",
     "Chargeback e fraude concentrados em poucos sellers.",
     "Recusa em fornecer dados do EC final (look-through)."],
    ["Due diligence reforcada do subadquirente/PayFac",
     "Exigencia contratual de KYC de seller e look-through",
     "Avaliacao do programa de PLD do parceiro",
     "Direito de auditoria e reporte de sellers"],
    ["Monitoramento no nivel do seller (quando disponivel)",
     "Monitoramento de concentracao por sub/marketplace",
     "Deteccao de nested/affiliated merchants",
     "Acompanhamento de chargeback por parceiro"],
    ["Seller individual com volume/chargeback acima de limiar.",
     "Sub/marketplace com taxa de fraude agregada > X%.",
     "Crescimento de sellers > Y% sem reforco de KYB.",
     "Sellers compartilhando IP/conta entre marketplaces."],
    "FATF e as bandeiras alertam que PayFacs e marketplaces sao alvos preferenciais de "
    "transaction laundering por nested merchants; programas exigem que a adquirente garanta a "
    "diligencia e a visibilidade ('look-through') sobre o EC final.",
)

# ---- T7 Front companies alto risco ----
tipologia_slide(
    "T7", "Front Companies de Alto Risco (Apostas, Cripto e Investimentos)", "10",
    "Empresas de fachada ou disfarcadas que canalizam, via adquirencia, receitas de atividades de "
    "alto risco ou ilegais no Brasil: apostas/jogos nao autorizados, exchanges de cripto irregulares, "
    "esquemas de piramide/Ponzi e conteudo adulto, frequentemente combinadas a MCC miscoding e gateways offshore.",
    ["Atividade de\nalto risco", "Front company\n/ MCC mascarado", "Captura via\ngateway/PSP", "Liquidacao e\ncross-border"],
    ["Operacao de apostas/cripto sem licenca processada como varejo.",
     "Esquemas de investimento captando via cartao de credito.",
     "Gateways e PSP intermediando fluxo para offshore.",
     "Liquidacao cross-border para jurisdicoes de risco."],
    ["MCC/CNAE incompativel com indicios de apostas/cripto/investimento.",
     "Soft descriptor com termos de jogo, 'bet', 'invest', 'crypto'.",
     "Reembolsos/ganhos pagos a portadores (payout) atipicos.",
     "Tickets altos e recorrentes de captacao de 'investidores'.",
     "Concentracao de fluxo para gateways/contas no exterior."],
    ["KYB setorial e checagem de licenca/autorizacao",
     "Politica de aceitacao por vertical de risco",
     "DDR para apostas, cripto e investimentos",
     "Screening de sancoes e midia adversa"],
    ["Deteccao de palavras-chave em descriptor/site",
     "Monitoramento de payouts e fluxo bidirecional",
     "Analise de exposicao cross-border",
     "Monitoramento de reputacao/midia negativa"],
    ["Soft descriptor/URL com termos de aposta/cripto/investimento.",
     "Razao txn de payout/credito atipica para o MCC.",
     "Fluxo cross-border > X% para jurisdicao de risco.",
     "EC vinculado a alerta de midia adversa ou de regulador."],
    "Investigacoes recentes no Brasil ('bets' e pirâmides) revelaram operadores ilegais "
    "captando via maquininhas e gateways sob MCC de varejo; a checagem de licenca e a deteccao de "
    "descriptor/URL sao controles decisivos.",
)

# ---- T8 Financiamento do Terrorismo ----
tipologia_slide(
    "T8", "Financiamento do Terrorismo (FT)", "11",
    "Uso da infraestrutura de pagamentos para arrecadar, movimentar ou disponibilizar recursos a "
    "individuos/organizacoes terroristas. Caracteriza-se por baixos valores, possivel origem licita dos "
    "fundos, captacao difusa (crowdfunding, doacoes), uso de NPO de fachada e contas-funil, exigindo "
    "screening de sancoes e nexo com listas do CSNU.",
    ["Captacao\n(doacoes/vendas)", "EC/NPO de\nfachada", "Contas-funil\nde agregacao", "Repasse a\nbeneficiario alvo"],
    ["EC ou ONG de fachada arrecadando 'doacoes' via cartao.",
     "Crowdfunding/venda de itens simbolicos como captacao.",
     "Contas-funil concentrando microdoacoes pulverizadas.",
     "Repasse cross-border para jurisdicoes de conflito."],
    ["EC vinculado a pessoa/entidade em listas de sancoes (match).",
     "Doacoes pulverizadas de muitas origens para um mesmo EC.",
     "Nexo geografico com zonas de conflito/jurisdicoes de risco.",
     "ONG sem transparencia de finalidade e destino dos recursos.",
     "Baixos valores recorrentes com beneficiario final sensivel."],
    ["Screening de sancoes (CSNU/OFAC/UE) no onboarding",
     "Identificacao de BF e finalidade de ONG/NPO",
     "DDR para entidades sem fins lucrativos de risco",
     "Bloqueio imediato (Lei 13.810/2019)"],
    ["Screening continuo contra listas atualizadas",
     "Monitoramento de microdoacoes e crowdfunding",
     "Analise de exposicao geografica",
     "Deteccao de contas-funil"],
    ["Match de EC/BF/contraparte com listas de sancoes (qualquer valor).",
     "N+ doacoes pulverizadas para EC/ONG em janela curta.",
     "Transacoes com nexo a jurisdicao de conflito.",
     "Beneficiario/keyword em watchlist de FT."],
    "FATF destaca que o FT envolve valores baixos e fundos por vezes licitos, o que torna o "
    "screening de sancoes e a analise de nexo (geografia, contraparte, NPO) mais relevantes que limiares "
    "de valor; comunicacao ao COAF independe de montante.",
)

# ---- T9 FPADM ----
tipologia_slide(
    "T9", "FPADM e Evasao de Sancoes (Proliferacao)", "12",
    "Financiamento da Proliferacao de Armas de Destruicao em Massa envolve burlar sancoes do CSNU para "
    "obter bens, tecnologia e financiamento ligados a programas nucleares, quimicos, biologicos e de misseis. "
    "No contexto de adquirencia, materializa-se por evasao de sancoes, dual-use goods e ocultacao de "
    "contrapartes/jurisdicoes sancionadas via cartoes e gateways.",
    ["Comprador/EC\nvinculado a alvo", "Ocultacao de\ncontraparte/pais", "Compra de bens\ndual-use", "Pagamento via\ncartao/gateway"],
    ["EC ou comprador vinculado a entidade/pais sancionado.",
     "Aquisicao de bens dual-use mascarada por MCC generico.",
     "Trade-based: super/subfaturamento em transacoes de cartao.",
     "Gateways e intermediarios ocultando jurisdicao real."],
    ["Match com listas de proliferacao/sancoes (CSNU/OFAC).",
     "Nexo com jurisdicoes de proliferacao (alto risco).",
     "Mercadorias dual-use ou de controle de exportacao.",
     "Estruturas societarias opacas e intermediarios em offshore.",
     "Inconsistencia entre valor, mercadoria e rota de pagamento."],
    ["Screening de sancoes e listas de proliferacao",
     "Identificacao de BF e estrutura societaria",
     "Triagem geografica de jurisdicoes alvo",
     "Bloqueio/indisponibilidade imediata de ativos"],
    ["Screening continuo e por contraparte cross-border",
     "Deteccao de dual-use goods por descriptor/produto",
     "Analise de trade-based (over/under-invoicing)",
     "Monitoramento de jurisdicoes sancionadas"],
    ["Match de EC/BF/contraparte com listas de proliferacao.",
     "Transacao com nexo a jurisdicao alvo (qualquer valor).",
     "Descriptor/produto associado a bens dual-use.",
     "Desvio de preco vs. referencia (indicio de mis-invoicing)."],
    "Reports do FATF e da ONU mostram uso de empresas de fachada e intermediarios em "
    "terceiros paises para burlar sancoes a programas de ADM; a indisponibilidade imediata de ativos "
    "(Lei 13.810/2019) e mandatoria ao identificar match com listas.",
)


# ============================================================================
# SECAO - MONITORAMENTO TRANSACIONAL (TABELAS)
# ============================================================================
def section_divider(numtxt, title, subtitle):
    s = slide()
    rect(s, 0, 0, SW, SH, NAVY)
    rect(s, 0, Inches(2.9), SW, Inches(1.7), PRIMARY)
    rect(s, 0, Inches(2.9), Inches(0.22), Inches(1.7), ACCENT)
    tb, tf = textbox(s, Inches(0.9), Inches(2.3), Inches(11), Inches(0.6))
    add_par(tf, numtxt, size=15, color=ACCENT, bold=True, first=True)
    tb, tf = textbox(s, Inches(0.9), Inches(3.0), Inches(11.5), Inches(1.0), anchor=MSO_ANCHOR.MIDDLE)
    add_par(tf, title, size=30, color=WHITE, bold=True, first=True)
    tb, tf = textbox(s, Inches(0.9), Inches(4.75), Inches(11), Inches(0.8))
    add_par(tf, subtitle, size=13.5, color=LIGHT, first=True, line_spacing=1.1)
    rect(s, Inches(0.9), Inches(4.55), Inches(3.5), Inches(0.05), ACCENT)
    return s

section_divider("SECAO 1", "Monitoramento Transacional",
                "Cenarios, logica analitica, fontes de dados, frequencia, thresholds e priorizacao "
                "de risco por tipologia - base para a esteira de alertas da adquirente.")

def monitor_table(idx, title, rows):
    s = newpage("Monitoramento Transacional", title, idx)
    cols = ["Tipologia / Cenario", "Logica analitica", "Fonte de dados", "Freq.", "Threshold sugerido", "Prior."]
    widths = [Inches(2.5), Inches(3.4), Inches(2.05), Inches(0.95), Inches(2.6), Inches(0.95)]
    nrows = len(rows) + 1
    left = Inches(0.4)
    top = Inches(1.45)
    total_w = sum(widths, Emu(0))
    height = Inches(5.2)
    gtbl = s.shapes.add_table(nrows, len(cols), left, top, total_w, height)
    table = gtbl.table
    for i, w in enumerate(widths):
        table.columns[i].width = w
    for c, h in enumerate(cols):
        table.cell(0, c).text = h
    aligns = [PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER]
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            table.cell(r, c).text = val
    style_table(table, body_size=8.8, header_size=9.5, col_aligns=aligns)
    # destacar prioridade
    for r, row in enumerate(rows, start=1):
        set_cell(table, r, 5, row[5], color=prio_color(row[5]), bold=True, align=PP_ALIGN.CENTER)
        set_cell(table, r, 0, row[0], bold=True, color=PRIMARY, align=PP_ALIGN.LEFT)
    # ajustar altura linha cabecalho
    table.rows[0].height = Inches(0.4)
    return s

rows1 = [
    ["T1 Transaction Laundering", "Outlier de volume/ticket vs. peer group do MCC; mismatch site x MCC; content matching",
     "Autorizacao, cadastro EC, crawling de site, MCC", "Diaria", "Desvio > 3 sigma do MCC ou mismatch de conteudo", "Critica"],
    ["T2 Bust-out / Chargeback", "Spike de volume vs. media movel 30d + chargeback ratio + antecipacao",
     "Autorizacao, chargeback, antecipacao, cadastro", "Tempo real / Diaria", "Volume +X% e CB > 0,9% ou antecip. >= Y%", "Critica"],
    ["T3 MCC Miscoding / Factoring", "MCC declarado vs. MCC inferido por ML; descriptor inconsistente",
     "Cadastro EC, MCC, soft descriptor, transacoes", "Semanal", "Divergencia MCC declarado x inferido", "Alta"],
    ["T4 Structuring / Smurfing", "Agregacao por janela movel; deteccao just-below-threshold; velocity",
     "Autorizacao, terminal, cartao (BIN/token)", "Diaria", "Soma >= R$ X via N+ txn < limiar de comunicacao", "Alta"],
]
monitor_table("13", "Cenarios de Monitoramento - Tipologias T1 a T4", rows1)

rows2 = [
    ["T5 Merchants Fantasma", "Cruzamento conta de liquidacao x titular; analise de rede de BF/IP/endereco",
     "Cadastro, BF, conta liquidacao, KYC", "Diaria / no onboarding", "Conta != titular ou N+ EC mesmo BF/IP", "Critica"],
    ["T6 Sub / Marketplaces", "Concentracao por parceiro; nested merchants; chargeback agregado por seller",
     "Cadastro sub, dados de seller, liquidacao", "Diaria", "Fraude agregada > X% ou seller > limiar", "Alta"],
    ["T7 Front Companies Risco", "Keyword em descriptor/URL; razao de payout; exposicao cross-border",
     "Descriptor, URL, payouts, fluxo internacional", "Diaria", "Keyword de risco ou payout/cross-border > X%", "Alta"],
    ["T8 Financiamento Terrorismo", "Screening de sancoes; microdoacoes pulverizadas; nexo geografico",
     "Listas CSNU/OFAC/UE, transacoes, geolocalizacao", "Tempo real / continuo", "Match em lista (qualquer valor) ou N+ doacoes", "Critica"],
    ["T9 FPADM / Sancoes", "Screening de proliferacao; dual-use; jurisdicoes alvo; mis-invoicing",
     "Listas de sancoes, contraparte, produto, rota", "Tempo real / continuo", "Match em lista ou nexo a jurisdicao alvo", "Critica"],
]
monitor_table("14", "Cenarios de Monitoramento - Tipologias T5 a T9", rows2)


# ============================================================================
# SECAO - CONTROLES
# ============================================================================
section_divider("SECAO 2", "Arquitetura de Controles",
                "Linhas de defesa preventivas e detectivas calibradas pela Abordagem Baseada em Risco "
                "para o ciclo de vida do estabelecimento comercial.")

# Controles preventivos
s = newpage("Controles", "Controles Preventivos (Antes / Onboarding e Reavaliacao)", "15")
prev_items = [
    ("KYC", "Know Your Customer: identificacao e verificacao do cliente/portador, com validacao documental e biometria nos canais aplicaveis."),
    ("KYB", "Know Your Business: identificacao do EC, atividade real, CNAE/MCC, site, produto e capacidade operacional."),
    ("Beneficiario Final", "Identificacao da cadeia societaria ate a pessoa natural que controla o EC; quebra de estruturas opacas."),
    ("Screening de Sancoes", "Triagem contra listas CSNU, OFAC, UE e UK no onboarding e de forma continua; bloqueio imediato em caso de match."),
    ("Screening PEP", "Identificacao de Pessoas Expostas Politicamente e relacionados, com aprovacao em alcada superior e DDR."),
    ("Due Diligence Reforcada", "DDR para EC/parceiros de alto risco (apostas, cripto, NPO, cross-border) com aprovacao e monitoramento intensificados."),
    ("Validacao Cadastral", "Conferencia de CNPJ, situacao na Receita, conta de liquidacao x titular, telefone, e-mail e endereco."),
    ("Geolocalizacao", "Validacao de localizacao do EC/terminal e coerencia com a atividade declarada e o padrao transacional."),
    ("Visita ao Estabelecimento", "Verificacao fisica (presencial ou remota) para EC de risco e mystery shopping para confirmar a operacao real."),
]
sx = Inches(0.45); sy = Inches(1.45)
cw = Inches(4.05); chh = Inches(1.7); gx = Inches(0.13); gy = Inches(0.13)
for i, (t, d) in enumerate(prev_items):
    r = i // 3; c = i % 3
    x = sx + c * (cw + gx); y = sy + r * (chh + gy)
    rect(s, x, y, cw, chh, ICE, line=LIGHT, line_w=Pt(0.75))
    rect(s, x, y, cw, Inches(0.45), SECONDARY)
    tbh, tfh = textbox(s, x + Inches(0.12), y, cw - Inches(0.2), Inches(0.45), anchor=MSO_ANCHOR.MIDDLE)
    add_par(tfh, t, size=12.5, color=WHITE, bold=True, first=True)
    tb, tf = textbox(s, x + Inches(0.15), y + Inches(0.52), cw - Inches(0.3), chh - Inches(0.6))
    add_par(tf, d, size=10, color=GRAYTXT, first=True, line_spacing=1.05)

# Controles detectivos
s = newpage("Controles", "Controles Detectivos (Durante / Monitoramento Continuo)", "16")
det_items = [
    ("Monitoramento Transacional", "Esteira de regras e cenarios sobre autorizacao, captura e liquidacao para gerar, selecionar e analisar alertas (Circular 3.978)."),
    ("Machine Learning", "Modelos supervisionados e nao supervisionados para deteccao de anomalias, scoring de risco e reducao de falsos positivos."),
    ("Analise Comportamental", "Perfilizacao do EC e deteccao de desvios do baseline (volume, ticket, sazonalidade, mix de cartoes)."),
    ("Monitoramento de Chargeback", "Acompanhamento de chargeback/fraude ratio vs. limites de bandeira; sinal antecedente de bust-out e laundering."),
    ("Monitoramento de Concentracao", "Concentracao de volume por cartao, BIN, terminal, BF, conta de liquidacao, sub/marketplace e geografia."),
    ("Monitoramento de Liquidacao", "Reservas, antecipacao de recebiveis, conta de destino x titular e holds de risco antes do cash-out."),
]
sx = Inches(0.45); sy = Inches(1.5)
cw = Inches(4.05); chh = Inches(2.45); gx = Inches(0.13); gy = Inches(0.15)
for i, (t, d) in enumerate(det_items):
    r = i // 3; c = i % 3
    x = sx + c * (cw + gx); y = sy + r * (chh + gy)
    rect(s, x, y, cw, chh, WHITE, line=LIGHT, line_w=Pt(1))
    rect(s, x, y, cw, Inches(0.45), ACCENT)
    rect(s, x, y + Inches(0.45), cw, Inches(0.05), PRIMARY)
    tbh, tfh = textbox(s, x + Inches(0.12), y, cw - Inches(0.2), Inches(0.45), anchor=MSO_ANCHOR.MIDDLE)
    add_par(tfh, t, size=12, color=WHITE, bold=True, first=True)
    tb, tf = textbox(s, x + Inches(0.15), y + Inches(0.6), cw - Inches(0.3), chh - Inches(0.7))
    add_par(tf, d, size=10.2, color=GRAYTXT, first=True, line_spacing=1.08)


# ============================================================================
# RECOMENDACOES DE MITIGACAO
# ============================================================================
s = newpage("Conclusao", "Recomendacoes de Mitigacao e Proximos Passos", "17")
recs = [
    ("Fortalecer KYB e look-through em PayFac/marketplaces",
     "Exigir contratualmente KYC de seller, visibilidade do EC final e avaliacao do programa de PLD dos parceiros.", RED, "Critica"),
    ("Implementar deteccao de transaction laundering",
     "Web crawling, content matching e modelos de MCC inferido vs. declarado, com mystery shopping para EC de risco.", RED, "Critica"),
    ("Screening de sancoes continuo (FT/FPADM)",
     "Cobertura CSNU/OFAC/UE/UK no onboarding e em tempo real, com processo de bloqueio imediato (Lei 13.810/2019).", RED, "Critica"),
    ("Calibrar esteira de monitoramento por risco",
     "Thresholds dinamicos, agregacao por BF/CNPJ raiz e cenarios por tipologia; governanca de tuning e backtesting.", AMBER, "Alta"),
    ("Reforcar controles de liquidacao e chargeback",
     "Rolling reserve por risco, re-KYC em troca de conta, holds e monitoramento de chargeback ratio em tempo quase real.", AMBER, "Alta"),
    ("Maturar analytics (ML e analise de rede)",
     "Modelos de anomalia, link analysis de BF/IP/conta e reducao de falsos positivos com explicabilidade para auditoria.", SECONDARY, "Media"),
    ("Governanca, AIR e cultura",
     "Avaliacao Interna de Risco periodica, indicadores de efetividade, treinamento e reporte tempestivo ao COAF.", SECONDARY, "Media"),
]
sy = Inches(1.5)
rh = Inches(0.74)
gap = Inches(0.08)
for i, (t, d, cl, prio) in enumerate(recs):
    y = sy + i * (rh + gap)
    rect(s, Inches(0.45), y, Inches(12.45), rh, ICE if i % 2 == 0 else WHITE, line=LIGHT, line_w=Pt(0.5))
    rect(s, Inches(0.45), y, Inches(0.12), rh, cl)
    # numero
    rect(s, Inches(0.7), y + Inches(0.12), Inches(0.5), Inches(0.5), cl, shape_type=MSO_SHAPE.OVAL)
    tbn, tfn = textbox(s, Inches(0.7), y + Inches(0.12), Inches(0.5), Inches(0.5), anchor=MSO_ANCHOR.MIDDLE)
    add_par(tfn, str(i + 1), size=15, color=WHITE, bold=True, align=PP_ALIGN.CENTER, first=True)
    tb, tf = textbox(s, Inches(1.4), y + Inches(0.05), Inches(9.6), rh - Inches(0.1), anchor=MSO_ANCHOR.MIDDLE)
    add_par(tf, t, size=12, color=PRIMARY, bold=True, first=True, space_after=1, line_spacing=1.0)
    add_par(tf, d, size=9.5, color=GRAYTXT, line_spacing=1.0)
    chip(s, Inches(11.35), y + Inches(0.2), Inches(1.35), prio, color=prio_color(prio), size=10)


# ============================================================================
# ENCERRAMENTO
# ============================================================================
s = slide()
rect(s, 0, 0, SW, SH, NAVY)
rect(s, 0, Inches(3.2), SW, Inches(0.08), ACCENT)
rect(s, Inches(10.7), 0, Inches(2.63), SH, PRIMARY)
rect(s, Inches(10.4), 0, Inches(0.10), SH, ACCENT)
tb, tf = textbox(s, Inches(0.8), Inches(2.5), Inches(9.3), Inches(1.2))
add_par(tf, "Sintese", size=14, color=ACCENT, bold=True, first=True, space_after=6)
add_par(tf, "A adquirencia concentra pontos criticos de exposicao a LD/FT/FPADM:\n"
            "onboarding, agregacao (sub/marketplace), classificacao de MCC e liquidacao.",
        size=18, color=WHITE, bold=True, line_spacing=1.15)
tb, tf = textbox(s, Inches(0.8), Inches(4.3), Inches(9.3), Inches(1.6))
add_par(tf, "A mitigacao efetiva combina controles preventivos robustos (KYC/KYB, "
            "beneficiario final, screening de sancoes/PEP, DDR e validacao cadastral) com "
            "controles detectivos analiticos (monitoramento transacional, ML, analise de rede, "
            "chargeback, concentracao e liquidacao), sob uma Abordagem Baseada em Risco "
            "alinhada a Circular BCB 3.978/2020 e as recomendacoes do GAFI/FATF.",
        size=12.5, color=LIGHT, first=True, line_spacing=1.2)
tb, tf = textbox(s, Inches(0.8), Inches(6.5), Inches(9.3), Inches(0.6))
add_par(tf, "Documento confidencial - uso interno  |  Compliance, Riscos e PLD/FT",
        size=10, color=RGBColor(0x9A, 0xB4, 0xCE), first=True)


# ----------------------------------------------------------------------------
out = "/home/user/localiza_leilao/Apresentacao_PLD_FT_FPADM_Adquirencia.pptx"
prs.save(out)
print("Slides:", len(prs.slides._sldIdLst))
print("Arquivo salvo em:", out)
