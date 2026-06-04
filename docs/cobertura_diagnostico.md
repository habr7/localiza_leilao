# Diagnóstico de Cobertura — "por que o CSV só tem um site?"

> Resposta à pergunta: *"o CSV praticamente só tem leilões do site Líder Leilões.
> Por quê? Faz sentido ter encontrado imóveis em praticamente um site só?"*

**Não, não faz sentido como retrato do mercado.** A concentração num único site é
um **artefato de cobertura** (mais um filtro da própria tese), não a realidade. O
mercado de leilões de imóveis em SP está pulverizado em muitos portais. Abaixo, o
diagnóstico em três camadas, com evidências coletadas ao vivo nesta sessão.

## 1. Causa principal: havia só uma fonte sendo coletada de fato

O repositório versionado **não tinha nenhum scraper de agregador implementado**
(`src/ingestao/agregadores/` só tinha `__init__.py`) e os scrapers de Junta estavam
com `_parse` pendente. Ou seja: qualquer CSV gerado antes vinha de **uma única
fonte que por acaso funcionou** — daí "praticamente só Líder Leilões". Isso **deixou
sites para trás**: os grandes agregadores nacionais nunca foram varridos.

### Teste de alcance dos portais (feito nesta sessão)

A rede do ambiente está liberada e **a maioria dos portais responde** — não é
"o mercado que só tem um site", é que os outros nunca foram coletados:

| Portal | Domínio | HTTP | Observação |
|---|---|---|---|
| Mega Leilões | megaleiloes.com.br | **200** | varrido nesta sessão |
| Superbid | superbid.net | 200 | a implementar |
| Zuk / Zukerman | portalzuk.com.br | 200 | a implementar (leiloeiros JUCESP) |
| Leilão VIP | leilaovip.com.br | 200 | a implementar |
| Frazão | frazaoleiloes.com.br | 200 | a implementar |
| Biasi | biasileiloes.com.br | 200 | a implementar |
| Sodré Santoro | sodresantoro.com.br | **403** | anti-bot: precisa de navegador/proxy |

> Conclusão da camada 1: **sim, deixamos sites para trás.** Só o Sodré Santoro
> realmente bloqueia (403); os demais estão acessíveis e simplesmente não tinham
> coletor. Cobrir um agregador (Mega) já multiplica a base por centenas de lotes.

## 2. Causa estrutural: o filtro da tese elimina quase tudo dos agregadores

Aqui está a parte não óbvia. Mesmo varrendo o maior agregador (Mega Leilões), o
número de **imóveis-alvo** (imóvel em SP + leiloeiro **não-JUCESP**) é baixíssimo.

Motivo: nos grandes portais, quase todo leilão de imóvel em SP é conduzido por um
leiloeiro que **tem matrícula JUCESP** — muitas vezes além de outra de fora. Ex.
real coletado no Mega:

```
Leiloeiro: Fernando José Cerello G. Pereira
  JUCESP Nº 844  - Leiloeiro Oficial no Estado de São Paulo
  JUCEMG Nº 1192 - Leiloeiro Oficial no Estado de Minas Gerais
```

Pela regra de ouro do projeto, **basta ter JUCESP para ser tratado como SP**
(pode atuar livremente no estado → não há assimetria). Implementamos isso em
`uf_efetiva_de_matriculas` ("SP vence"). Resultado da coleta no Mega Leilões
(imóveis em SP): **praticamente 100% resolvem para `uf_leiloeiro = SP`** — ou seja,
**zero (ou quase zero) alvos** vindos do agregador.

> Conclusão da camada 2: o agregador é ótimo como **baseline e descobridor de
> leiloeiros**, mas é **fraco em alvos** — exatamente porque os leiloeiros grandes
> têm JUCESP. É esperado que o alvo da tese **não** apareça em peso nos agregadores.

## 3. Por que um site pequeno (tipo "Líder") domina os alvos

Juntando 1 + 2: os alvos verdadeiros (leiloeiro **exclusivamente** de fora, imóvel
em SP) tendem a aparecer justamente nos **sites próprios de leiloeiros não-SP** e em
**portais pequenos/regionais** — que é onde a assimetria de atenção existe. Logo, um
CSV de alvos dominado por um site pequeno **é coerente com a tese**, MAS só vale se
os grandes também tiverem sido varridos e descartados pelo filtro (camada 2). Sem
varrer os grandes, não dá para afirmar nada — vira viés de amostragem.

## 4. O que fica para trás e precisa entrar (prioridade)

1. **Sites próprios de leiloeiros não-SP** (`fonte_tipo='site_proprio'`) — maior
   assimetria; é onde moram os alvos. Depende do cadastro das Juntas (Fase 2).
2. **Comunicações à JUCESP** — leiloeiro de fora é obrigado a comunicar leilão de
   bem em SP. "Fonte de ouro": pega o que nem está nos agregadores.
3. **Mais agregadores** (Superbid, Zuk, Leilão VIP, Frazão, Biasi) — baseline e
   descoberta de novos leiloeiros não-SP.
4. **Sodré Santoro** — exige navegador/proxy (403). Tratar como exceção.

## 5. O que foi feito nesta sessão

- **+5 Juntas** no cadastro (Fase 2): JUCEPAR (PR), JUCERGS (RS), JUCESC (SC),
  JUCEDF (DF), JUCEG (GO) — somadas a JUCERJA/JUCEMG e à JUCESP (exclusão).
- **Infra de ingestão** (`src/ingestao/base.py`): `BaseScraper` (httpx async, rate
  limit por domínio, robots.txt, retries) + `LoteRaw`.
- **Agregador Mega Leilões** (`src/ingestao/agregadores/megaleiloes.py`) com parsing
  testado por fixtures e a regra multi-matrícula ("JUCESP vence").
- **Script `fase3_identificar_imoveis`** que coleta, resolve a UF do leiloeiro e
  exporta `data/imoveis_sp.csv` (tudo) e `data/imoveis_alvo.csv` (só não-SP).

### Resultado da coleta (Mega Leilões, imóveis SP)

Varredura completa de `/sp` (todas as páginas, 2026-05-28):

- **394 imóveis em SP** coletados e enriquecidos com leiloeiro + matrículas.
- **0 imóveis-alvo** (`fora_sp = sim`): **392 resolveram para `uf_leiloeiro = SP`**
  e apenas 2 ficaram sem matrícula reconhecida (revisão manual).
- Apenas **3 leiloeiros distintos** em 394 lotes — concentração altíssima, todos
  com matrícula JUCESP (um deles exibe `JUCESP Nº 844` **e** `JUCEMG Nº 1192` →
  pela regra "SP vence", é SP).
- Tipo de leilão: 161 extrajudiciais, 233 judiciais.

Isto confirma empiricamente a camada 2: **o maior agregador nacional não produz
alvos da tese** — não porque falte imóvel em SP, mas porque os leiloeiros desses
portais têm matrícula JUCESP. Reproduzível com:

```bash
uv run python -m src.scripts.fase3_identificar_imoveis --max-paginas 20
```

> Portanto, um CSV "praticamente só de um site" pequeno é **esperado para os
> alvos** — desde que os grandes tenham sido varridos e descartados pelo filtro
> (o que agora acontece). O próximo ganho real de cobertura vem dos **sites
> próprios de leiloeiros não-SP** e das **comunicações à JUCESP**, não de mais
> agregadores.

## 6. Sites próprios de leiloeiros não-SP — o que a varredura achou

Cadastro populado a partir das Juntas (JUCEPAR + JUCEG): **328 leiloeiros não-SP,
162 com site oficial**. A varredura heurística (`fase3_sites_proprios`) dos 162
sites achou **571 indícios de SP em 37 sites**.

### "Líder Leilões" desmistificado

O site que dominava o CSV original — **`liderleiloes.com.br`** — é da leiloeira
**CAROLINE DE SOUSA RIBAS, matriculada na JUCEPAR (PR)**. Ou seja: **não era
artefato — é um verdadeiro alvo da tese** (leiloeira de fora com lotes em SP). O
problema nunca foi "só ter o Líder"; foi **não ter os outros sites como o Líder**.
A varredura encontrou mais 8 leiloeiros não-SP tocando em SP:

| Leiloeiro | UF | Site | Cidades SP detectadas |
|---|---|---|---|
| Caroline de Sousa Ribas | PR | liderleiloes.com.br | Campinas, Santos, Guarujá, Santo André, S.B. Campo, Mauá, Diadema… |
| Mauricio Sambugari A. | PR | andraleiloes.com.br | Andradina |
| Spencer D'Avila Fogagnoli | PR | spencerleiloes.com.br | Diadema |
| Catia F. Alievi Toporoski | PR | aleiloeira.leilao.br | Santo André |
| Guilherme E. Stutz Toporoski | PR | topoleiloes.com.br | Santo André |
| Felipe Guimarães Carrijo | GO | leilo.com.br | São Carlos (dados estruturados!) |
| Davi Borges de Aquino | GO | alfaleiloes.com | Guarujá |
| Edilson Lopes Rocha | GO | leilo.com.br | São Carlos |

### Ressalva honesta: os indícios brutos precisam de triagem

A heurística é boa para **descobrir** sites, não para extrair lote final. Os 571
indícios misturam três coisas que ainda precisam ser separadas por um parser
dedicado por site:

1. **Imóvel real em SP** (o alvo) — ex.: `leilo.com.br` expõe JSON
   `"localizacao":{"cidade":"SÃO CARLOS","estado":"SP"}`.
2. **Endereço do próprio leiloeiro** — ex.: Andra Leilões "com escritório na
   cidade de Andradina/SP" (ele é do PR, mas atua de SP — interessante, mas não é
   um lote).
3. **Lote de veículo/equipamento em SP** — ex.: no Líder, "Mauá-SP" era uma
   *carregadeira Caterpillar*, não um imóvel.

### Próximo passo recomendado (alto ROI)

Escrever **parsers dedicados** para os leads mais promissores — começar por
`leilo.com.br` (tem dados estruturados em JSON) e `liderleiloes.com.br` — extraindo
o lote (endereço, tipo, lance, praça) e promovendo de "indício" a `lote` no banco,
com `fonte_tipo='site_proprio'` (pontua mais no score). Esses são os imóveis-alvo
de verdade da tese.

Reproduzível com:
```bash
uv run python -m src.scripts.fase2_cadastrar_leiloeiros
uv run python -m src.scripts.fase3_sites_proprios
```

## 7. Expansão: +3 Juntas (MT, PB, PI) e varredura de 240 sites

Adicionadas 3 Juntas com parser ao vivo (todas publicam o **site** do leiloeiro):
**JUCEMAT (MT)**, **JUCEPB (PB)**, **JUCEPI (PI)** — somadas a JUCEPAR (PR) e
JUCEG (GO). Cadastro: **~530 leiloeiros não-SP em 5 UFs, ~240 com site oficial**.

Varredura dos **240 sites**: **1.327 indícios de SP em 53 sites**. Filtrando por
cidade paulista confirmada e **removendo os agregadores nacionais** (cujos
leiloeiros costumam ter também JUCESP — megaleiloes, portalzuk, lanceja, sfrazao),
sobram **14 sites próprios genuínos** de leiloeiros de fora com imóvel em SP:

| UF | Site | Leiloeiro | nº cidades SP |
|---|---|---|---|
| MT | leiloariasmart.com.br | Lucas Andreatta de Oliveira | **25** |
| MT | webleiloes.com.br | Tiago Tessler Blecher | **21** |
| PR | liderleiloes.com.br | Tatiana/Caroline (Líder) | 10 |
| PR | valeroleiloes.com.br | José Valéro Santos Junior | 6 |
| PR | e-confianca.com.br | Marilaine Borges de Paula | 2 |
| PR | aleiloeira.leilao.br | Catia F. Alievi Toporoski | 1 |
| PR | topoleiloes.com.br | Guilherme Stutz Toporoski | 1 |
| PR | andraleiloes.com.br | Mauricio Sambugari | 1 |
| PR | spencerleiloes.com.br | Spencer D'Avila Fogagnoli | 1 |
| GO | alfaleiloes.com | Davi Borges de Aquino | 1 |
| GO | leilo.com.br | Sérgio Fleury Batista | 1 |
| MT | bastonleiloes.com.br | Mouzar Baston Filho | 1 |
| MT | leilomaster.com.br | Sergio Fleury Batista | 1 |
| MT | leilaobrasil.com.br | Irani Flores | 1 |

> **Mato Grosso foi o achado**: `leiloariasmart` e `webleiloes` estão carregados de
> imóveis em SP. A varredura cobre **todos** os sites do cadastro (não só os
> promissores), conforme pedido.

## 8. Cross-check de JUCESP — o filtro que separa o alvo puro

Um leiloeiro pode estar numa Junta de fora **e também** na JUCESP — e aí não há
assimetria. A forma confiável de saber é o **próprio site do leiloeiro**, que lista
todas as matrículas ("JUCESP nº ..., JUCEMAT nº ..."). Implementado em
`src/ingestao/sites_proprios/verificacao.py` (`pagina_tem_jucesp`) e integrado ao
pipeline (`fase3_sites_dedicados` pula quem tem JUCESP; `fase3_verificar_jucesp`
marca cada site).

### Resultado da verificação dos 14 sites genuínos

**TÊM JUCESP (excluídos — não são alvo):**

| Site | Matrículas observadas |
|---|---|
| webleiloes.com.br | …JUCEMAT, **JUCESP n°1098**, … (≈20 juntas) |
| valeroleiloes.com.br | JUCESP, JUCEMG, JUCEPAR, JUCESC |
| e-confianca.com.br | JUCESP, JUCEMG, JUCEPAR |
| bastonleiloes.com.br | JUCEMS, JUCEMG, **JUCESP**, JUCESC, JUCEMAT, JUCEG |

**SEM JUCESP (alvos puros):** leiloariasmart (JUCISRS/RS), liderleiloes,
aleiloeira, topoleiloes, andraleiloes, spencerleiloes (PR), alfaleiloes,
leilo.com.br (GO), leilomaster, leilaobrasil (MT).

> Impacto: o maior volume (webleiloes, 19 imóveis SP) **caiu** por ter JUCESP — a
> suspeita do Humberto estava certa. Entre os limpos, cada site tem **poucos**
> imóveis em SP no momento (ex.: leiloariasmart = 2, leilo.com.br = 2): o ruído da
> heurística inflava a contagem. O `fase3_sites_dedicados` agora só persiste os
> imóveis de sites **verificados sem JUCESP**.

### Próximo passo

Parser dedicado para os demais sites **limpos** com imóveis (leilo.com.br tem JSON;
liderleiloes), e completar a lista de exclusão com o scraper da própria JUCESP.
