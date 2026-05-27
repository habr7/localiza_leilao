# Plano de Desenvolvimento — Fases 2 a 5

> Continuação do projeto **Garimpo de Leilões com Assimetria de Atenção**.
> A Fase 1 (validação estatística retrospectiva) foi **deliberadamente pulada** por
> decisão do Humberto: assumimos a tese como válida e partimos para construir o
> produto. Este documento é o plano de implementação completo das fases seguintes.

---

## 0. Reafirmação do objetivo

Encontrar **imóveis localizados em São Paulo (UF = SP)** cujo leilão é conduzido por
**leiloeiro NÃO matriculado na JUCESP** — com prioridade para **leiloeiros e sites
pequenos / pouco divulgados**, onde a assimetria de atenção (e portanto o desconto
potencial) é maior. Foco inicial em **extrajudicial** (alienação fiduciária).

### 0.1 Virada conceitual: operamos sobre leilões ABERTOS

A Fase 1 precisava de dados *retrospectivos* (preço de arremate, nº de lances) que
quase não são públicos. **O produto não precisa disso.** Ele monitora leilões
**em andamento / a abrir** e ranqueia oportunidades. Os campos que realmente
importam para o produto são:

- imóvel em SP (filtro duro),
- lance mínimo (1ª/2ª praça),
- leiloeiro + UF da matrícula (≠ SP = sinal),
- tamanho/obscuridade da fonte (site próprio pequeno > agregador nacional),
- desconto vs. avaliação, ocupação, datas de praça.

`resultados` (arremate, ágio, nº de lances) continua existindo, mas vira **backtest
opcional** alimentado quando/se conseguirmos os dados — nunca um bloqueio do produto.

### 0.2 O que já existe (Sessão 1)

- Estrutura de pastas, projeto `uv`, lint/type-check/test configurados.
- Modelos ORM (`leiloeiros`, `leiloes`, `lotes`, `resultados`) + schemas Pydantic.
- `config.py`, `db.py`, migration inicial do Alembic.
- Script da Fase 1 (mantido como ferramenta de backtest; fora do caminho crítico).

---

## 1. Princípios de engenharia (válidos para todas as fases)

1. **Scraping disciplinado:** uma classe `BaseScraper` (httpx async + selectolax),
   com rate limiting por domínio (≤ 1 req/s), respeito a `robots.txt`, User-Agent
   identificável, retries com backoff. Playwright **somente** onde o JS for
   indispensável (custo alto, usar como exceção).
2. **Idempotência:** toda escrita é `upsert` (`ON CONFLICT DO UPDATE`) por chave
   natural / `hash_dedup`. Rodar o coletor 2x não duplica.
3. **Observabilidade:** `structlog` em todas as coletas, logando no mínimo
   `fonte`, `lotes_encontrados`, `lotes_novos`, `erros`.
4. **Migrations:** qualquer mudança de schema passa por Alembic (autogenerate +
   revisão manual).
5. **Configuração e segredos:** tudo via `.env` + `pydantic-settings`. Nenhuma
   chave em código.
6. **Testes:** cada parser tem ≥ 1 fixture HTML salva em `tests/fixtures/` para
   detectar quebra estrutural do site.
7. **CI (repo agora público):** GitHub Actions rodando `ruff`, `mypy`, `pytest`
   em cada push/PR.
8. **Idioma:** código em inglês; comentários/docstrings em pt-BR.

---

## 2. Evoluções de schema necessárias

Aplicar via Alembic, idealmente no início da Sessão 2.

### 2.1 `leiloeiros` (ajustes)
- `aliases TEXT[]` — variações de nome encontradas em portais (ajuda o matcher).
- `fonte_cadastro TEXT` — de onde veio ("jucerja_site", "lai_jucemg", ...).
- `visto_em TIMESTAMPTZ` — última vez que apareceu numa coleta.

### 2.2 `leiloes` (ajuste de desempenho)
- `uf_leiloeiro CHAR(2)` **desnormalizado** (copiado do leiloeiro no momento da
  ingestão) — permite filtrar "não-SP" sem JOIN e preserva o valor histórico.
- `fonte_tipo TEXT` — `'agregador'` | `'site_proprio'` | `'jucesp_comunicacao'` |
  `'doe'`. Essencial para o sinal "fonte pequena/obscura".

### 2.3 Nova tabela `lote_fontes` (dedup multi-fonte)
Um imóvel físico pode aparecer em N portais. Mantemos **um** `lote` e várias fontes:
```
lote_fontes(id, lote_id FK, fonte_origem, fonte_url, fonte_tipo, coletado_em,
            dados_extras JSONB, UNIQUE(lote_id, fonte_url))
```

### 2.4 Nova tabela `alertas_enviados` (idempotência de notificação)
```
alertas_enviados(id, lote_id FK, canal TEXT, enviado_em TIMESTAMPTZ,
                 UNIQUE(lote_id, canal))
```

### 2.5 Nova tabela `favoritos` (Fase 5)
```
favoritos(id, lote_id FK, criado_em, nota TEXT, UNIQUE(lote_id))
```

### 2.6 Índices
- `leiloes(uf_leiloeiro)`, `leiloes(fonte_tipo)`, `leiloes(status)`.
- `lotes(score_oportunidade DESC)`, `lotes(cidade)`, `lotes(tipo_imovel)`.

---

## 3. Fase 2 — Cadastro de Leiloeiros (a peça-chave)

**Por que primeiro:** sem saber *quem* é não-SP, não há como filtrar. O cadastro é
o que transforma "leiloeiro X" em "leiloeiro de fora de SP".

### 3.1 Arquitetura
- `src/leiloeiros/juntas/<junta>.py` — um módulo por Junta Comercial, com interface
  comum:
  ```python
  class JuntaScraper(Protocol):
      junta: str            # "JUCERJA"
      uf: str               # "RJ"
      async def coletar(self) -> list[LeiloeiroRaw]: ...
  ```
- `src/leiloeiros/cadastro.py` — consolida todas as juntas, normaliza e faz upsert.
- `src/leiloeiros/resolver.py` — **resolvedor**: dado `(nome, matrícula_str)`
  extraído de um portal, devolve o `leiloeiro` do cadastro e a UF.

### 3.2 Estratégia por junta (graus de dificuldade diferentes)
1. **Lista pública navegável** → scraper direto (ex.: várias juntas publicam a
   relação de leiloeiros).
2. **Sem lista pública** → gerar **pedido LAI/e-SIC** (template em
   `docs/leiloeiros.md`) pedindo o cadastro em CSV; carregar manualmente quando
   chegar (prazo legal ~20 dias).
3. **JUCESP** → coletar também, mas para montar a **lista de exclusão** (quem é de SP).

Prioridade de UFs (de onde mais saem leiloeiros que atuam em SP):
**RJ, MG, PR, RS, SC, DF, GO** primeiro; demais depois.

### 3.3 O resolvedor de leiloeiro (`resolver.py`) — coração do matching
Regra de resolução, em ordem:
1. Se a matrícula traz a Junta/UF (reaproveitar `parse_uf_matricula` da Fase 1) →
   UF derivada direto, com **alta confiança** mesmo sem cadastro completo.
2. Casar `(nome normalizado, matrícula)` contra o cadastro (match exato → fuzzy por
   nome com limiar). Anexar metadados (site oficial, junta).
3. Sem matrícula e sem match → marcar `uf_leiloeiro = NULL` + `confianca='baixa'`
   e logar para revisão (não descartar o lote, mas não afirmar não-SP).

### 3.4 Enriquecimento
- Site oficial (busca automatizada) e plataformas onde aparece (cross-check Fase 3).

### 3.5 Testes e aceite
- Fixtures HTML por junta; testes de parsing + do resolvedor (nomes com acento,
  matrícula com espaço/hífen, homônimos).
- **Aceite:** `leiloeiros` populada com ≥ 5 UFs não-SP + JUCESP; consulta
  "leiloeiros não-SP ativos" retorna base utilizável.

---

## 4. Fase 3 — Ingestão Multi-Fonte

Reordenada segundo a ênfase do Humberto (**fonte pequena = mais assimetria**), mas
mantendo agregadores como baseline de cobertura e como **descobridor de leiloeiros**.

### 4.1 Infra de scraping (`src/ingestao/base.py`)
- `BaseScraper`: cliente httpx async compartilhado, `RateLimiter` por domínio,
  leitura de `robots.txt`, parsing utilitário (selectolax), normalização de URL,
  retries/backoff, hook de logging estruturado.
- Contrato por fonte:
  ```python
  class FonteScraper(Protocol):
      fonte_origem: str
      fonte_tipo: str
      async def listar_lotes_sp(self) -> list[LoteRaw]: ...
  ```
- Pipeline de ingestão: `listar → resolver leiloeiro → upsert leilao/lote/lote_fontes`.

### 4.2 (3.1) Agregadores — baseline + descoberta
Um módulo por portal em `src/ingestao/agregadores/`. Cada um lista imóveis `uf=SP`
e extrai: dados do leilão (tipo, modalidade, datas de praça, edital), do lote
(endereço, cidade, bairro, tipo, lance mínimo 1ª/2ª, avaliação, fotos, descrição,
ocupação) e do **leiloeiro (nome + matrícula)**. Cruza com o cadastro → marca
não-SP. Ordem: Mega Leilões, Sold/Sodré Santoro, Zukerman, Superbid, Leilão VIP,
Frazão, Biasi, Lance Já.

> Função extra dos agregadores: alimentar o cadastro da Fase 2 com leiloeiros novos
> e descobrir **quais leiloeiros não-SP** estão ativos em imóveis paulistas.

### 4.3 (3.2) Sites próprios de leiloeiros não-SP — **alta assimetria**
Para cada leiloeiro não-SP do cadastro com site próprio, varrer "leilões em
andamento" e filtrar imóveis SP. `fonte_tipo='site_proprio'` (pontua mais no score).
Aqui mora a maior parte do valor do produto.

### 4.4 (3.3) Comunicações à JUCESP — **fonte de ouro**
Investigar se há lista pública navegável de comunicações de leilão recebidas pela
JUCESP (leiloeiro de fora é **obrigado** a comunicar quando o bem está em SP). Se
não houver: protocolar **LAI** pedindo a relação mensal (leiloeiro + UF + bem).
Captura lotes que talvez nem estejam nos portais nacionais.

### 4.5 (3.4) Diários Oficiais de outros estados — baixa cobertura, alta assimetria
Buscar editais em DOE-MG/RJ/RS (e Imprensa Nacional) mencionando imóveis em SP:
termos `"São Paulo/SP"`, `"comarca de São Paulo"`, `"imóvel sito em São Paulo"`,
faixa de CEP `01000-000`–`19999-999`.

### 4.6 Operação e testes
- Cada fonte: upsert idempotente, logs estruturados, fixture HTML, alerta quando
  `lotes_encontrados == 0` inesperadamente (provável quebra de parser).
- **Aceite:** ≥ 3 agregadores + ≥ 3 sites próprios não-SP coletando diariamente;
  lotes com `uf_leiloeiro` preenchido e `fonte_tipo` correto.

---

## 5. Fase 4 — Pipeline (Normalização → Dedup → Enriquecimento → Score)

`src/pipeline/`

### 5.1 Normalização (`normalize.py`)
- Endereço → componentes (rua, número, complemento, bairro, cidade, UF, CEP).
- **ViaCEP** para validar CEP e completar bairro/cidade.
- Preços → numérico puro. Datas → ISO 8601 com timezone `America/Sao_Paulo`.

### 5.2 Deduplicação (`dedup.py`)
- `hash_dedup` por `matricula_imovel` quando houver; senão
  `hash(endereco_normalizado + area_m2)`.
- Mesmo lote em 3 portais → 1 `lote` + 3 linhas em `lote_fontes`.

### 5.3 Enriquecimento (`enrich.py`)
- Geocoding (Nominatim/OSM grátis; Google opcional para qualidade).
- Cruzamento com **valor venal IPTU** (dados abertos da Prefeitura de SP).
- Descontos teóricos: `1 - lance_min_2/avaliacao` e `1 - lance_min_2/valor_venal`.

### 5.4 Score de oportunidade (`score.py`) — calibrável via config
Base na fórmula do PROJECT.md, com pesos em `.env`/config:
```
score = w1 * desconto_vs_avaliacao
      + w2 * raridade_de_publico            # heurística: fonte pequena / poucas fontes
      + w3 * indicador_leiloeiro_fora_sp    # 0/1 (gatilho central da tese)
      + w4 * indicador_fonte_pequena        # site_proprio/obscuro > agregador
      + w5 * (1 - ocupado)
```
Persistir `score_oportunidade` + componentes em `dados_extras` (para auditoria).
- **Aceite:** rodar o pipeline produz lotes ranqueados; testes de normalize/dedup/score.

---

## 6. Fase 5 — Interface e Alertas

### 6.1 Dashboard FastAPI (`src/api/`)
- `main.py` (app), `routes.py`, `templates/` (Jinja + **Alpine.js + Tailwind via CDN**,
  sem Node), mobile-first.
- Endpoints:
  - `GET /` — dashboard com filtros.
  - `GET /api/lotes` — JSON filtrável (cidade, faixa de preço, tipo, **uf_leiloeiro
    (default ≠ SP)**, score mínimo, dias até praça, **só sites pequenos**).
  - `POST /api/favoritos` — favoritar/desfavoritar.
- Cada card: foto, endereço, preço, **leiloeiro + UF**, fonte, link para edital,
  badge "leiloeiro de fora de SP" e "site pequeno", botão favoritar.
- Auth simples (uso pessoal): token/basic auth.

### 6.2 Alertas (`src/alerts/`)
- **APScheduler** (cron diário 7h) dentro do FastAPI.
- Novos lotes com `score > threshold` → **Telegram Bot** (mais simples) e/ou
  **WhatsApp via Z-API**; e-mail (Resend/SES) com resumo semanal top 20.
- `alertas_enviados` garante que não notifica o mesmo lote 2x.

---

## 7. Agendamento, Deploy e Operação

- **Agendamento:** APScheduler no FastAPI (coletas leves frequentes);
  **GitHub Actions cron** para Fase 2 e coletas pesadas.
- **Deploy:** Railway ou Render (24/7); **Supabase** (PostgreSQL); segredos via env.
- **Rede (lição aprendida):** os portais bloqueiam IP de datacenter/sandbox. Em
  produção avaliar proxy/IP residencial onde necessário; sempre respeitar robots e
  throttling. No ambiente de desenvolvimento web, usar política de rede que
  permita os domínios-alvo.
- **CI/CD:** GitHub Actions (lint + mypy + pytest). Alertas de quebra de parser.
- **Monitoramento:** healthcheck + log de cada coleta + alerta de coleta vazia.

---

## 8. Sequência de sessões sugerida (entregáveis claros por sessão)

| Sessão | Entregável |
|---|---|
| **2** | Migrations (§2) + Fase 2: JUCESP (exclusão) + 2-3 juntas não-SP + `resolver.py` + testes. |
| **3** | `BaseScraper` + 2 agregadores + matching com cadastro + `lote_fontes`. CI no GitHub. |
| **4** | +3 agregadores + 2-3 sites próprios não-SP + investigação JUCESP/LAI. |
| **5** | Pipeline: normalize + dedup + enrich + score (com flags de assimetria). |
| **6** | Dashboard FastAPI (filtros, cards, favoritar). |
| **7** | Alertas (Telegram/e-mail) + APScheduler + deploy Railway/Render + Supabase. |

Cada sessão segue o mesmo rito da Sessão 1: passos numerados, commits pequenos e
descritivos, testes verdes, sem feature creep, perguntar quando houver ambiguidade.

---

## 9. Riscos e mitigações (atualizado)

| Risco | Mitigação |
|---|---|
| Portais com anti-bot / allowlist de rede | Proxy/IP adequado em prod; política de rede aberta em dev; Playwright só se indispensável; respeitar robots. |
| Matrícula ausente em alguns portais | Resolver por nome via cadastro; sem match → `uf_leiloeiro=NULL`, confiança baixa, revisão manual. Nunca afirmar "não-SP" sem base. |
| HTML dos sites muda | Fixtures + testes diários + alerta de coleta vazia. |
| Poucos leiloeiros não-SP ativos em SP | Expandir UFs e sites próprios; explorar comunicações JUCESP (fonte de ouro). |
| Falso "de fora": leiloeiro associado a outro estado mas com matrícula JUCESP (ex.: Zukerman = JUCESP) | A UF vem **sempre** da matrícula resolvida pelo cadastro, nunca do "nome/marca" do site. |
| Dados de resultado (arremate/nº lances) escassos | Produto opera em leilões abertos e não depende disso; `resultados` é backtest opcional. |

---

## 10. Definição de pronto (MVP)

- Coleta diária de ≥ 3 agregadores + ≥ 3 sites próprios não-SP, idempotente.
- `leiloeiros` com base não-SP utilizável e resolvedor confiável.
- Pipeline ranqueando por score com flags de assimetria.
- Dashboard filtrável (default: imóvel SP + leiloeiro não-SP) + favoritos.
- Alerta diário/semantal dos lotes de score alto.
- ≥ 5 lotes/semana com leiloeiro não-SP identificados (critério do PROJECT.md §9).
