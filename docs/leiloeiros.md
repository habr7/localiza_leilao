# Notas sobre Juntas Comerciais e Cadastro de Leiloeiros (Fase 2)

## Objetivo
Saber a **UF de matrícula** de cada leiloeiro. É o gatilho da tese: imóvel em SP +
leiloeiro **não-JUCESP** = oportunidade. JUCESP serve só para a **lista de exclusão**.

## Como a UF é determinada (ordem de confiança)
Implementado em `src/leiloeiros/resolver.py` + `src/leiloeiros/matricula.py`:
1. **Matrícula** (ex.: "JUCERJA 123") → UF direto pelo prefixo da Junta. Confiança alta
   quando também casa com um leiloeiro do cadastro pela matrícula.
2. **Nome** casado no cadastro (match exato → fuzzy ≥ 0.87) → UF do cadastro. Confiança média.
3. Nada reconhecido → UF nula, confiança baixa (não afirmamos "não-SP" sem base).

> **Regra de ouro:** a UF vem da matrícula/cadastro, **nunca** da marca do site.
> Ex.: "Zukerman" é associado ao RJ, mas seus leiloeiros são JUCESP (719, 744) → é SP.

## Estratégia de coleta por Junta
`src/leiloeiros/juntas/` — uma subclasse de `JuntaScraper` por Junta:
- **Com lista pública** → preencher `url_lista` e implementar `_parse(html)`.
- **Sem lista pública** → pedido **LAI/e-SIC** pedindo o cadastro em CSV; carregar com
  `coletar_csv(path)` (já funciona offline). Template de pedido LAI: ver abaixo.
- **JUCESP** → coletar para excluir quem é de SP.

### Cobertura nacional (sessão de expansão)

Cobertura atual: **SP (exclusão) + 18 UFs não-SP com parser ao vivo**. Carga típica:
~2.700 leiloeiros (623 JUCESP + ~2.080 não-SP), ~700 com site oficial.

| UF | Junta | Estrutura | Site | UF | Junta | Estrutura | Site |
|---|---|---|---|---|---|---|---|
| SP | JUCESP | PDF (D.O.E.) | — | PR | JUCEPAR | acordeão | sim |
| GO | JUCEG | texto-bloco | sim | MT | JUCEMAT | cards | sim |
| PB | JUCEPB | rotulada | sim | PI | JUCEPI | rotulada | sim |
| RJ | JUCERJA | AJAX paginado | nao | MG | JUCEMG | tabela | nao |
| RS | JUCISRS | POST | sim | SC | JUCESC | tabela | nao |
| DF | JUCEDF | blocos `<p>` | sim | AM | JUCEA | rotulada | sim |
| BA | JUCEB | tabela | sim | CE | JUCEC | tabela | sim |
| RO | JUCER | `<dl>` | sim | SE | JUCESE | `<li>` | sim |
| AC | JUCEAC | cards | parc. | ES | JUCEES | cards | sim |
| MS | JUCEMS | rotulada | sim | PA | JUCEPA | rotulada | sim |

**Faltam (servidor fora do ar / SPA inacessível no momento):** AL (JUCEAL 503),
AP (JUCAP 503), MA (JUCEMA 503), RN (JUCERN 503 no proxy), TO (JUCETINS 503 no
proxy), PE (JUCEPE — SPA com API na porta `:3005` bloqueada), RR (JUCERR — Ninja
Tables via `admin-ajax.php`, a implementar). Reexecutar quando os servidores
voltarem; o registro já está pronto para recebê-las.

### Status dos parsers de Junta (ao vivo)
Investigadas as listas públicas das Juntas não-SP. **5 Juntas com parser ao vivo**
(todas publicam o site oficial do leiloeiro — o que a Fase 3 precisa):

| Junta | UF | Lista pública | Parser | Leiloeiros | Com site |
|---|---|---|---|---|---|
| **JUCEPAR** | PR | acordeão HTML (`.collapsible-item`) | **feito** | 172 | 127 |
| **JUCEG** | GO | texto corrido (`NOME (Matrícula: …)`) | **feito** | 156 | 35 |
| **JUCEMAT** | MT | cartões (`.featured-box` + `ul.list-icons`) | **feito** | 135 | 63 |
| **JUCEPB** | PB | texto rotulado (`Matrícula:`/`Site:`) | **feito** | 46 | 13 |
| **JUCEPI** | PI | texto rotulado (`Matrícula:`/`Site:`) | **feito** | 26 | 3 |
| JUCERJA | RJ | sem tabela navegável (JS) | pendente | — | — |
| JUCEMG | MG | tabelas, mas sem site do leiloeiro | pendente | — | — |
| JUCISRS | RS | conteúdo via JS / PDF (manual) | pendente | — | — |
| JUCESC | SC | subportal (frame) | pendente | — | — |
| JUCISDF | DF | WordPress comprometido (spam) | pendente | — | — |

> Total no banco: **~530 leiloeiros não-SP em 5 UFs, ~240 com site oficial**.
> Rodar: `uv run python -m src.scripts.fase2_cadastrar_leiloeiros`.
> Juntas sem site na lista (JUCEMAT/JUCEES tinham nome+matrícula sem URL em
> alguns layouts; RJ/MG/RS/SC/DF em JS/PDF) seguem por LAI/CSV ou parser dedicado.

As demais Juntas (sem lista navegável com site) seguem pelo caminho LAI/CSV
(`coletar_csv`) ou exigem PDF/JS — documentado para a próxima sessão.

Homepages de referência:
- JUCESP — https://www.jucesp.sp.gov.br (lista de exclusão; pendente)
- JUCERJA — https://www.jucerja.rj.gov.br/AuxiliaresComercio/Leiloeiros
- JUCEMG — https://jucemg.mg.gov.br/pagina/139/leiloeiros-oficiais
- JUCEPAR — https://www.juntacomercial.pr.gov.br/Pagina/LEILOEIROS-OFICIAIS-HABILITADOS
- JUCEG — https://goias.gov.br/juceg/leiloeiros/

### Prioridade de UFs (de onde mais saem leiloeiros que atuam em SP)
RJ, MG, PR, RS, SC, DF, GO primeiro; demais depois.

## Template de pedido LAI (e-SIC)
> "Solicito, com base na Lei 12.527/2011, a relação dos leiloeiros oficiais
> matriculados nesta Junta Comercial, em formato CSV, contendo: nome completo,
> número de matrícula, data de matrícula, situação (ativo/inativo) e, se houver,
> site oficial. Solicito o envio por meio eletrônico."

## Formato do CSV de import (`importar_csv`)
Colunas: `nome, matricula, uf_matricula, junta_comercial, cpf, site_oficial,
plataformas, aliases, fonte_cadastro`. `plataformas` e `aliases` separados por `;`.
`uf_matricula`/`junta_comercial` são derivados da matrícula se omitidos.
