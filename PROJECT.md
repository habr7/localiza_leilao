# Projeto: Garimpo de Leilões com Assimetria de Atenção

> Sistema para identificar leilões de imóveis localizados em **São Paulo** conduzidos por **leiloeiros matriculados em outras Juntas Comerciais (não-JUCESP)**, com foco inicial em **leilões extrajudiciais**, onde a tese de menor concorrência é mais provável.

---

## 1. Contexto e Tese de Investimento

### 1.1 A oportunidade
Leilões de imóveis no Brasil sofrem de **fragmentação de canais de divulgação**. Cada leiloeiro mantém seu próprio site, publica editais em jornais e Diários Oficiais do seu estado, e nem sempre seus lotes aparecem em agregadores nacionais. Quando um leiloeiro de fora de SP (ex.: matriculado em MG, RJ, RS) conduz um leilão de imóvel localizado em SP, a tese é:

- A divulgação tende a ficar mais concentrada no estado de origem do leiloeiro
- Investidores paulistas (público-alvo natural do imóvel) podem não tomar conhecimento
- Menos lances disputados → menor ágio sobre o preço mínimo → potencial desconto

### 1.2 Por que extrajudicial primeiro
- **Judicial:** edital padronizado, publicado nos portais dos TJs (e-Saj, PJe), distribuição regional do leiloeiro via credenciamento ou sorteio. Pouca assimetria.
- **Extrajudicial:** credor (banco, securitizadora, fundo, particular) escolhe livremente o leiloeiro. Edital sai em sites do leiloeiro + jornal + DOE de qualquer estado. **Fragmentação máxima = assimetria máxima.**

### 1.3 Marco regulatório
- **Decreto-Lei 21.981/1932:** profissão de leiloeiro
- **IN DREI 52/2022 (revogou a IN 72/2019):** regulamenta matrícula e atuação
- **Lei 9.514/1997:** alienação fiduciária de imóveis (a principal fonte de leilões extrajudiciais)
- **Regra-chave:** leiloeiro só pode atuar fora da UF de matrícula em leilão eletrônico, ou quando os bens estão dispersos em mais de uma UF. Em ambos os casos, é obrigatória a **comunicação prévia** à Junta Comercial onde o bem se localiza (no nosso caso, JUCESP).

### 1.4 Hipóteses a validar (Fase 1)
H1. Leilões extrajudiciais de imóveis em SP conduzidos por leiloeiros de fora têm número médio de lances por lote **menor** que leilões equivalentes com leiloeiros JUCESP.
H2. O ágio médio (preço de arremate / preço mínimo) é menor.
H3. A taxa de lotes "desertos" (sem lance) é maior.

**Se H1, H2 e H3 forem falsas, o projeto morre na Fase 1.** Não construir infra antes de validar.

---

## 2. Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│  FASE 1 - VALIDAÇÃO MANUAL (planilha + scripts ad-hoc)      │
│  Objetivo: confirmar/refutar a tese com ~50 leilões         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 2 - CADASTRO DE LEILOEIROS                            │
│  Base de dados de leiloeiros matriculados por UF            │
│  (JUCERJA, JUCEMG, JUCEPAR, JUCESC, JUCERGS, JUCEDF, etc.)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 3 - INGESTÃO MULTI-FONTE                              │
│  ├─ Agregadores (Mega, Sold, Zuk, Superbid, etc.)           │
│  ├─ Sites próprios de leiloeiros não-SP                     │
│  ├─ Comunicações JUCESP (LAI ou scraping)                   │
│  └─ Diários Oficiais de outros estados (SP-imóveis)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 4 - PIPELINE DE DADOS                                 │
│  Normalização → Deduplicação → Enriquecimento → Scoring     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 5 - INTERFACE E ALERTAS                               │
│  Dashboard FastAPI + WhatsApp/Email para novos lotes        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Stack Técnica

Alinhada com o stack já em uso pelo Humberto (delta one dashboard, bot de arbitragem):

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Backend | **Python 3.11+** + FastAPI | Já dominado; assíncrono; bom para scraping |
| Scraping | **httpx** (assíncrono) + **selectolax** (parser HTML rápido); **Playwright** apenas onde JS for indispensável | Performance > Selenium; Playwright só quando necessário (custo alto) |
| Banco | **PostgreSQL** (Supabase) | Já em uso; bom suporte a JSONB para dados semi-estruturados de lotes |
| Agendamento | **APScheduler** dentro do FastAPI (Fase 3); **GitHub Actions cron** para Fase 1/2 | Simples; não precisa de Celery/Redis nessa escala |
| Frontend | **HTML + Alpine.js + Tailwind** (sem Node.js) | Mesmo padrão do dashboard delta one |
| Hospedagem | **Railway** ou **Render** | 24/7, já avaliado em projetos anteriores |
| Notificações | **WhatsApp via Z-API** ou **Telegram Bot** + e-mail (Resend/SES) | WhatsApp tem melhor UX para mobile |
| LLM auxiliar | **Claude API** para extrair dados estruturados de editais PDF/imagem quando regex falhar | Fallback inteligente |

**Princípio:** começar com a ferramenta mais simples que resolve. Não introduzir Celery, Redis, Kafka ou Docker Swarm sem necessidade comprovada.

---

## 4. Estrutura de Pastas

```
leiloes-assimetria/
├── PROJECT.md                  # este arquivo
├── README.md                   # como rodar
├── .env.example
├── pyproject.toml              # uv ou poetry
├── docs/
│   ├── fontes.md               # catálogo de portais e estrutura HTML
│   ├── leiloeiros.md           # notas sobre Juntas Comerciais
│   └── tese_validacao.md       # resultado da Fase 1
├── src/
│   ├── core/
│   │   ├── models.py           # SQLAlchemy + Pydantic
│   │   ├── db.py
│   │   └── config.py
│   ├── leiloeiros/
│   │   ├── juntas/             # um módulo por Junta Comercial
│   │   │   ├── jucesp.py
│   │   │   ├── jucerja.py
│   │   │   ├── jucemg.py
│   │   │   └── ...
│   │   └── cadastro.py         # consolida base de leiloeiros
│   ├── ingestao/
│   │   ├── agregadores/        # um módulo por portal
│   │   │   ├── megaleiloes.py
│   │   │   ├── sold.py
│   │   │   ├── zukerman.py
│   │   │   ├── superbid.py
│   │   │   └── ...
│   │   ├── sites_proprios/     # scraping por leiloeiro individual
│   │   ├── doe/                # Diários Oficiais
│   │   └── jucesp_comunicacoes.py
│   ├── pipeline/
│   │   ├── normalize.py        # padroniza endereço, preço, datas
│   │   ├── dedup.py            # identifica lote duplicado entre fontes
│   │   ├── enrich.py           # geocoding, valor venal IPTU, etc.
│   │   └── score.py            # score de "oportunidade"
│   ├── api/
│   │   ├── main.py             # FastAPI app
│   │   ├── routes.py
│   │   └── templates/          # Jinja + Alpine.js
│   ├── alerts/
│   │   ├── whatsapp.py
│   │   └── email.py
│   └── scripts/
│       ├── fase1_validar_tese.py
│       └── exportar_planilha.py
├── tests/
└── migrations/                 # alembic
```

---

## 5. Modelo de Dados (Núcleo)

### 5.1 Tabela `leiloeiros`
```sql
CREATE TABLE leiloeiros (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    matricula TEXT NOT NULL,
    uf_matricula CHAR(2) NOT NULL,             -- 'RJ', 'MG', etc. NUNCA 'SP' nesta query
    junta_comercial TEXT NOT NULL,             -- 'JUCERJA', 'JUCEMG', ...
    cpf TEXT,
    site_oficial TEXT,
    plataformas TEXT[],                        -- ['megaleiloes.com.br', 'leilaovip.com.br']
    ativo BOOLEAN DEFAULT TRUE,
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(matricula, uf_matricula)
);
CREATE INDEX idx_leiloeiros_uf ON leiloeiros(uf_matricula);
```

### 5.2 Tabela `leiloes`
```sql
CREATE TABLE leiloes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leiloeiro_id UUID REFERENCES leiloeiros(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('judicial', 'extrajudicial')),
    modalidade TEXT,                           -- 'alienacao_fiduciaria', 'particular', 'falencia', ...
    comitente TEXT,                            -- banco/fundo/credor
    data_1praca TIMESTAMPTZ,
    data_2praca TIMESTAMPTZ,
    edital_url TEXT,
    fonte_origem TEXT NOT NULL,                -- 'megaleiloes', 'site_proprio:xyz', 'doe_mg', ...
    fonte_url TEXT NOT NULL,
    coletado_em TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'aberto'               -- 'aberto', 'realizado', 'cancelado', 'suspenso'
);
```

### 5.3 Tabela `lotes`
```sql
CREATE TABLE lotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leilao_id UUID REFERENCES leiloes(id),
    numero_lote TEXT,
    tipo_imovel TEXT,                          -- 'apartamento', 'casa', 'terreno', 'comercial', 'rural'
    endereco_completo TEXT,
    cep TEXT,
    cidade TEXT NOT NULL,
    uf CHAR(2) NOT NULL CHECK (uf = 'SP'),     -- filtro duro do projeto
    bairro TEXT,
    matricula_imovel TEXT,                     -- matrícula do RI
    area_m2 NUMERIC,
    avaliacao NUMERIC,                         -- valor de avaliação
    lance_minimo_1 NUMERIC,                    -- 1ª praça
    lance_minimo_2 NUMERIC,                    -- 2ª praça
    ocupado BOOLEAN,
    divida_iptu NUMERIC,
    divida_condominio NUMERIC,
    fotos JSONB,                               -- array de URLs
    descricao TEXT,
    coordenadas POINT,                         -- após geocoding
    hash_dedup TEXT,                           -- hash(matricula_imovel + endereco) para dedup
    score_oportunidade NUMERIC,
    dados_extras JSONB,                        -- campo flexível por fonte
    UNIQUE(hash_dedup, leilao_id)
);
CREATE INDEX idx_lotes_cidade ON lotes(cidade);
CREATE INDEX idx_lotes_dedup ON lotes(hash_dedup);
```

### 5.4 Tabela `resultados` (para Fase 1 e backtest contínuo)
```sql
CREATE TABLE resultados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lote_id UUID REFERENCES lotes(id),
    arrematado BOOLEAN,
    preco_arremate NUMERIC,
    num_lances INTEGER,
    agio NUMERIC GENERATED ALWAYS AS (
        CASE WHEN preco_arremate IS NOT NULL AND lance_minimo_2 > 0
        THEN (preco_arremate / lance_minimo_2 - 1) ELSE NULL END
    ) STORED,
    coletado_em TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. Roadmap por Fase

### FASE 1 — Validação da Tese (1–2 semanas)

**Objetivo único:** decidir se vale construir o sistema.

Entregáveis:
1. Script `fase1_validar_tese.py` que coleta manualmente (ou semi-automatizado) **50 leilões extrajudiciais já realizados** de imóveis em SP nos últimos 6 meses.
2. Para cada um, registrar: leiloeiro, UF de matrícula, preço mínimo 2ª praça, preço de arremate (se houve), número de lances.
3. Dividir em dois grupos: SP vs. não-SP.
4. Calcular médias, medianas e fazer teste estatístico simples (Mann-Whitney U para amostras pequenas).
5. Produzir `docs/tese_validacao.md` com o veredito.

Como obter dados retrospectivos:
- Resultados públicos nos sites dos leiloeiros (muitos publicam "leilões realizados")
- Mega Leilões e Sold mostram histórico de lances
- Cartórios de RI eventualmente têm informações sobre arrematação registrada

**Critério de avanço:** diferença de mediana de ágio ≥ 3 pontos percentuais OU diferença de taxa de lote deserto ≥ 10 pp.

---

### FASE 2 — Cadastro de Leiloeiros (1 semana)

Entregáveis:
1. Scraper para a lista pública de leiloeiros de cada Junta Comercial:
   - JUCERJA (RJ), JUCEMG (MG), JUCEPAR (PR), JUCESC (SC), JUCERGS (RS), JUCEDF (DF), JUCEG (GO), JUCEMS (MS), JUCEMA (MA), JUCEC (CE), JUCEBA (BA), JUCEES (ES), JUCEMA (PA)
   - JUCESP também (para identificar quem **é** de SP e excluir)
2. Tabela `leiloeiros` populada.
3. Para cada leiloeiro não-SP, enriquecer com:
   - Site oficial (busca Google automatizada)
   - Plataformas em que aparece (cross-check com Fase 3)

**Atenção:** algumas Juntas não expõem lista pública navegável; nesses casos, **enviar pedido via LAI (e-SIC)** solicitando o cadastro em CSV. É gratuito, com prazo legal de 20 dias.

---

### FASE 3 — Ingestão Multi-Fonte (3–4 semanas)

Ordem de prioridade (do maior ROI para o menor):

**3.1 — Agregadores nacionais (alto volume, baixa assimetria, mas baseline necessário):**
- Mega Leilões
- Sold (Sodré Santoro)
- Zukerman
- Superbid Marketplace
- Leilão VIP
- Frazão Leilões
- Biasi Leilões
- Lance Já

Para cada um: módulo Python que lista lotes com `uf=SP`, extrai leiloeiro, cruza com cadastro Fase 2. Se leiloeiro não-SP → entra na base.

**3.2 — Sites próprios de leiloeiros não-SP (média assimetria):**
Para cada leiloeiro cadastrado na Fase 2 com site próprio, varrer a página de "leilões em andamento" e filtrar imóveis SP.

**3.3 — Comunicações à JUCESP (alta assimetria potencial):**
- Investigar se há lista pública navegável de comunicações de leilão recebidas pela JUCESP
- Caso não: protocolar **LAI** pedindo relação mensal de comunicações de leilão (com identificação do leiloeiro e UF de matrícula)
- Esta é a fonte de ouro: pega lotes que talvez nem estejam em portais nacionais

**3.4 — Diários Oficiais de outros estados (baixa cobertura, mas alta assimetria):**
- Editais publicados em DOE-MG, DOE-RJ, DOE-RS mencionando imóveis em SP
- Implementar busca com termos: `"São Paulo/SP"`, `"comarca de São Paulo"`, `"imóvel sito em São Paulo"`, CEPs do range 01000-000 a 19999-999
- Usar o serviço de busca dos próprios DOEs ou Imprensa Nacional quando aplicável

---

### FASE 4 — Pipeline (2 semanas)

**4.1 Normalização:**
- Endereço → padrão (rua, número, complemento, bairro, cidade, UF, CEP)
- ViaCEP API para validar CEP e extrair bairro/cidade
- Preços → numérico, sem R$, sem separador
- Datas → ISO 8601 com timezone America/Sao_Paulo

**4.2 Deduplicação:**
- Hash de `(matricula_imovel)` se disponível; senão `(endereco_normalizado + area_m2)` 
- Mesmo lote pode aparecer em 3 portais → manter referência cruzada em `fontes[]` mas um único registro de `lote`

**4.3 Enriquecimento:**
- Geocoding (Nominatim/OSM gratuito; Google Maps se precisar de qualidade)
- Cruzamento com tabela de valor venal IPTU de SP (dados abertos da Prefeitura SP — `dados.prefeitura.sp.gov.br`)
- Cálculo automático de desconto teórico: `1 - (lance_min_2 / valor_venal)` e `1 - (lance_min_2 / avaliacao)`

**4.4 Score de oportunidade:**
Função simples ponderada (calibrar após Fase 1):
```
score = 0.4 * desconto_vs_avaliacao
      + 0.3 * (1 / proximidade_de_outros_lances_recentes)  # raridade de público
      + 0.2 * indicador_leiloeiro_fora_sp                  # 0 ou 1
      + 0.1 * (1 - ocupado)                                # imóvel desocupado pontua mais
```

---

### FASE 5 — Interface e Alertas (2 semanas)

**5.1 Dashboard FastAPI:**
- Página única, mobile-first, Tailwind + Alpine.js
- Filtros: cidade SP, range de preço, tipo de imóvel, UF do leiloeiro, score mínimo, dias até 1ª praça
- Ordenação por score
- Cada card: foto, endereço, preço, leiloeiro+UF, link para edital, botão "favoritar"

**5.2 Alertas:**
- Cron diário às 7h
- Para cada lote novo com score > threshold (calibrável), enviar WhatsApp/Telegram com link direto
- Resumo semanal por e-mail com top 20

---

## 7. Considerações Jurídicas e Éticas

1. **Scraping:** respeitar `robots.txt`, throttling (1 req/s por domínio), User-Agent identificável. Para sites que bloquearem, recuar e usar fontes alternativas. Não burlar paywall ou CAPTCHA com força bruta.
2. **LGPD:** dados de leiloeiros são públicos (matrícula é registro público). Imóveis estão em editais públicos. Sem problema.
3. **Uso pessoal:** o sistema é para consulta própria. Não redistribuir editais com cobrança.
4. **Veracidade:** sempre linkar de volta ao edital original. O sistema **agrega**, não substitui a leitura do edital pelo arrematante.

---

## 8. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Tese refutada na Fase 1 | Alto | Parar o projeto; documentar aprendizado |
| Sites mudam HTML constantemente | Médio | Testes de scraping diários; alertas quando parser falhar |
| Portais com proteção anti-bot agressiva | Médio | Playwright + delays; em último caso, ignorar fonte |
| Volume baixo de lotes "interessantes" | Alto | Expandir critérios (mais UFs, mais portais); revisitar a tese |
| Leilão judicial entra no escopo cedo demais | Médio | Manter `tipo='extrajudicial'` como filtro duro até Fase 5 estável |

---

## 9. Critérios de Sucesso

- **Fase 1:** tese validada estatisticamente, ou refutada com clareza.
- **MVP (Fase 5):** sistema rodando 24/7, identificando ≥ 5 lotes/semana com score alto.
- **Operacional:** Humberto consegue arrematar pelo menos 1 imóvel via sistema em 6 meses com ágio abaixo da média de mercado.

---

## 10. Instruções para o Claude Code

Ao desenvolver este projeto, siga estas diretrizes:

1. **Leia este arquivo a cada início de sessão.** Ele é a fonte da verdade do escopo.
2. **Não pule fases.** A Fase 1 é validação; sem ela, qualquer código posterior é prematuro.
3. **Commits pequenos e descritivos.** Um commit por scraper de portal, por exemplo.
4. **Testes mínimos:** cada scraper deve ter ao menos um teste com HTML salvo (`tests/fixtures/`) para detectar quebra estrutural.
5. **Logs estruturados:** usar `structlog` com nível INFO em produção. Cada coleta deve logar: fonte, lotes encontrados, lotes novos, erros.
6. **Idempotência:** rodar o scraper duas vezes seguidas não pode duplicar registros. Use `ON CONFLICT DO UPDATE` no Postgres.
7. **Configuração via `.env`:** nada de credencial em código.
8. **Antes de adicionar uma nova fonte, pergunte:** "essa fonte aumenta a cobertura de leiloeiros não-SP, ou só repete o que já temos?"
9. **Idioma:** código em inglês (variáveis, funções), comentários e docstrings em **português brasileiro**.
10. **Quando em dúvida sobre regra de negócio do mercado de leilões**, pergunte ao Humberto antes de assumir.

---

## 11. Próximos Passos Imediatos

Para arrancar com o Claude Code na primeira sessão:

```bash
# 1. Inicializar projeto
mkdir leiloes-assimetria && cd leiloes-assimetria
git init
uv init  # ou poetry init

# 2. Setup básico
uv add fastapi httpx selectolax sqlalchemy alembic psycopg2-binary \
       pydantic-settings structlog python-dotenv
uv add --dev pytest pytest-asyncio ruff mypy

# 3. Primeira tarefa para o Claude Code:
#    "Implemente o script src/scripts/fase1_validar_tese.py.
#     Comece criando um coletor manual: planilha CSV onde eu colo URLs
#     de leilões já realizados, e o script enriquece com UF do leiloeiro
#     consultando a base de leiloeiros (que ainda não temos — então,
#     pegue manualmente neste momento). Calcule as métricas da seção 1.4."
```
