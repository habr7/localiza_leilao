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

## Agregadores (baseline + descoberta de leiloeiros)
Para cada um: listar imóveis `uf=SP`, extrair leilão (tipo, datas, edital), lote
(endereço, cidade, tipo, lances mínimos, fotos, ocupação) e **leiloeiro (nome +
matrícula)**. Cruzar com o cadastro via `LeiloeiroResolver` e marcar `uf_leiloeiro`.

| Portal | Domínio | HTTP (teste ao vivo) | Notas de estrutura | Status |
|---|---|---|---|---|
| Mega Leilões | megaleiloes.com.br | 200 | Listagem SP em `/sp?pagina=N` (cards `.card`); detalhe com `.batch-type` e blocos `.author.item` (Comitente/Leiloeiro). Leiloeiro exibe N matrículas. | **feito** (`agregadores/megaleiloes.py`) |
| Sodré Santoro / Sold | sodresantoro.com.br | **403** | anti-bot: exige navegador/proxy | a fazer (exceção) |
| Zukerman / Zuk | portalzuk.com.br | 200 | leiloeiros JUCESP (719/744) | a fazer |
| Superbid | superbid.net | 200 | — | a fazer |
| Leilão VIP | leilaovip.com.br | 200 | — | a fazer |
| Frazão | frazaoleiloes.com.br | 200 | — | a fazer |
| Biasi | biasileiloes.com.br | 200 | — | a fazer |
| Lance Já | — | — | — | a fazer |

> **Achado importante (multi-matrícula).** No Mega Leilões, o mesmo leiloeiro
> costuma exibir VÁRIAS matrículas — tipicamente uma **JUCESP** e outra de fora
> (ex.: "JUCESP Nº 844" + "JUCEMG Nº 1192"). Pela tese, ter JUCESP ⇒ é SP (pode
> atuar livremente, sem assimetria). Resolvido em `uf_efetiva_de_matriculas`
> ("SP vence"). Efeito prático: **quase nenhum alvo não-SP sai dos agregadores
> grandes** — os alvos estão em sites próprios/regionais. Ver
> `docs/cobertura_diagnostico.md`.

## Sites próprios de leiloeiros não-SP (ALTA assimetria — prioridade do produto)
Para cada leiloeiro não-SP do cadastro com `site_oficial`, varrer "leilões em
andamento" e filtrar imóveis SP. `fonte_tipo = 'site_proprio'` (pontua mais no score).

## Comunicações à JUCESP (fonte de ouro)
Leiloeiro de fora é obrigado a comunicar leilão de bem em SP. Investigar lista
pública; se não houver, protocolar LAI pedindo a relação mensal.

## Diários Oficiais de outros estados
Buscar editais em DOE-MG/RJ/RS mencionando imóveis em SP (termos: "São Paulo/SP",
"comarca de São Paulo", CEPs 01000-000–19999-999).
