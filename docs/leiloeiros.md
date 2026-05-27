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

### Status das listas públicas (inspeção ao vivo)
- **JUCEMG** ✅ — lista alfabética estática em
  `https://jucemg.mg.gov.br/pagina/140/Leiloeiros+Ordem+Alfabética`. ~228
  leiloeiros, cada um num bloco `<strong>Nome</strong>` + `Matrícula: <n> de <data>`.
  Parser e fixture (`tests/fixtures/jucemg_leiloeiros.html`) prontos.
- **JUCERJA** ⚠️ — lista em `https://www.jucerja.rj.gov.br/AuxiliaresComercio/Leiloeiros`
  (`section.ats-listaLeiloeiros`, itens `li.ats-listaLnks-item`). O servidor
  entrega só a **1ª página (5 leiloeiros)**; as demais carregam via AJAX/JS
  (paginação `data-value`, endpoint ainda não mapeado). Site é intermitente (503).
  Parser/fixture prontos para a 1ª página; o resto vem por LAI ou Playwright.
- **JUCESP** ⛔ — `www.jucesp.sp.gov.br` e `jucesponline.sp.gov.br` retornam **503**
  a clientes automatizados (provável WAF/anti-bot para IP de datacenter). Sem lista
  pública acessível por aqui. Usar `coletar_csv` (LAI) ou reavaliar em produção com
  IP residencial/proxy/navegador.

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
