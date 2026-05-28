# Catálogo de Fontes (Fase 3)

> Estrutura HTML e peculiaridades de cada portal. Preencher ao implementar cada
> scraper na sessão com rede liberada.

## Aprendizados de coleta (importantes)

- **O produto opera sobre leilões ABERTOS.** Não dependemos de preço de arremate
  nem de número de lances (quase nunca públicos). Campos que importam: imóvel em SP,
  lance mínimo, leiloeiro + UF, datas de praça, ocupação.
- **Anti-bot:** os portais retornam 403 para clientes automatizados sem navegador.
  Em produção pode ser preciso UA de navegador / proxy. Respeitar `robots.txt`,
  throttling (≥ 1s/domínio) e UA identificável (seção 7 do PROJECT.md).
- **Rede:** o ambiente precisa de **Network access = Full** (ou Custom com os
  domínios). A mudança só vale em **sessão nova** (rebuilda o cache).
- **Descoberta dinâmica:** não manter allowlist fixa de domínios de leiloeiro — os
  sites saem do cadastro das Juntas (Fase 2) e dos agregadores. Por isso Full.
- **Agregador = leiloeiro "da casa" (achado da ingestão Mega):** no Mega Leilões,
  todos os lotes SP de uma amostra de 20 são conduzidos pelo mesmo leiloeiro oficial
  da plataforma (Fernando José Cerello, JUCESP 844). Ou seja, **0 lotes não-SP** —
  a assimetria é ~nula em agregadores grandes, confirmando que o valor da tese está
  nos **sites próprios de leiloeiros não-SP** (Fase 3.2) e nas comunicações JUCESP.
  O agregador serve de baseline e de descobridor de leiloeiros.

## Agregadores (baseline + descoberta de leiloeiros)
Para cada um: listar imóveis `uf=SP`, extrair leilão (tipo, datas, edital), lote
(endereço, cidade, tipo, lances mínimos, fotos, ocupação) e **leiloeiro (nome +
matrícula)**. Cruzar com o cadastro via `LeiloeiroResolver` e marcar `uf_leiloeiro`.

| Portal | Domínio | Notas de estrutura | Status |
|---|---|---|---|
| Mega Leilões | megaleiloes.com.br | Listagem SP em `/imoveis/sp` (cards `div.card.open`). Leiloeiro só no detalhe (`.author.item .value`: nome + linhas "JUCExx Nº N"). Tipo em `.batch-type`; praças em `.instance.first`/segundo; avaliação/localização em blocos `.item`. | ✅ feito |
| Sodré Santoro / Sold | sodresantoro.com.br | — | a fazer |
| Zukerman / Zuk | zukerman.com.br, portalzuk.com.br | leiloeiros JUCESP (719/744) | a fazer |
| Superbid | superbid.net | — | a fazer |
| Leilão VIP | leilaovip.com.br | — | a fazer |
| Frazão | frazaoleiloes.com.br | — | a fazer |
| Biasi | biasileiloes.com.br | — | a fazer |
| Lance Já | — | — | a fazer |

## Sites próprios de leiloeiros não-SP (ALTA assimetria — prioridade do produto)
Para cada leiloeiro não-SP do cadastro com `site_oficial`, varrer "leilões em
andamento" e filtrar imóveis SP. `fonte_tipo = 'site_proprio'` (pontua mais no score).

### Estratégia: scraper POR PLATAFORMA (não por leiloeiro)
Sondando os ~189 `site_oficial` do cadastro, eles se agrupam em poucas plataformas
(CMS/white-label) compartilhadas — então um scraper por plataforma cobre muitos
leiloeiros (escalável para sites pequenos/obscuros, que é onde está a oportunidade).
Clusters encontrados (por assinatura de assets):

| Plataforma | Sites (na amostra) | Acesso aos dados | Status |
|---|---|---|---|
| **Suporte Leilões** | ~14 | `GET /api/buscadorMount?categoria=2` (JSON: imóveis por UF) + `GET /buscador?categoria=2&uf=SP&pagina=N` com header `X-Requested-With: XMLHttpRequest` (HTML renderizado, 12 lotes/página) | ✅ feito |
| **vLance** (`/v3/js/vlance/…`) | ~28 | API `/core/api/get-leiloes` (JSON de EVENTOS, com `uf`, `categorias`, `tp_judicial_extrajudicial`, `vl_lanceinicial`). Lotes ficam dentro do evento; busca de lote por UF não exposta na API. | identificado; lote-SP pendente |
| **Superbid white-label** (`api.s4bdigital.net`) | ~11 | API Superbid; porém são white-labels do agregador (lotes também na Superbid → menos assimetria) | adiar |
| Wix / outros | ~6 | heterogêneo | a fazer |

> **Achado da Suporte Leilões (survey via buscadorMount):** 6 sites de leiloeiros
> não-SP com imóveis em SP — liderleiloes (150), e-confianca (45), valeroleiloes
> (32), marcoantonio (2), rodrigo (2). A carga ao vivo persistiu **179 lotes-alvo**
> de 4 desses sites (liderleiloes 143, valero 32, marco 2, rodrigo 2); e-confianca
> caiu por timeout intermitente (retentar). Os lotes-alvo (imóvel SP + leiloeiro
> não-SP) entram com `fonte_tipo='site_proprio'` e são consultados via
> `src/scripts/consultar_lotes_alvo.py` (CSV em `data/lotes_alvo.csv`).
> Observação: nesta amostra todos vieram como `judicial` (eventos tipo TRT); filtrar
> `--tipo extrajudicial` para focar na maior assimetria da tese.

> **vLance (28 sites no cadastro):** API de eventos mapeada, mas **nenhum evento
> tem `uf=SP`** — são leilões regionais (MG/GO/SC). Lotes-SP só existiriam *dentro*
> de eventos não-SP, e a API não expõe busca de lote por UF (precisaria varrer a
> página de cada evento). Baixo retorno imediato; adiado em favor de cobrir mais
> sites Suporte Leilões. Infra de descoberta (fingerprint) já identifica os 28.

## Comunicações à JUCESP (fonte de ouro)
Leiloeiro de fora é obrigado a comunicar leilão de bem em SP. Investigar lista
pública; se não houver, protocolar LAI pedindo a relação mensal.

## Diários Oficiais de outros estados
Buscar editais em DOE-MG/RJ/RS mencionando imóveis em SP (termos: "São Paulo/SP",
"comarca de São Paulo", CEPs 01000-000–19999-999).
