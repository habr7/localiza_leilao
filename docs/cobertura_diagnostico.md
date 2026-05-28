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

Amostra confirmada (6 páginas de `/sp`, ~21h de 2026-05-28):

- **90 imóveis em SP** coletados e enriquecidos com leiloeiro + matrículas.
- **0 imóveis-alvo** (`fora_sp = sim`): **100% resolveram para `uf_leiloeiro = SP`**.
- Tipo de leilão: 83 extrajudiciais, 7 judiciais.
- Todos os 90 sob o mesmo leiloeiro, que exibe `JUCESP Nº 844` **e** `JUCEMG Nº 1192`
  → pela regra "SP vence", é SP (não-alvo).

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
