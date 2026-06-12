# RFI — Request For Information
## Contratação de fornecedor de listas restritivas e dados para qualificação de pessoas e empresas (PLD/FT)

---

## 1. Objetivo da RFI

- Obter informações do mercado sobre soluções de fornecimento de **listas restritivas, sancionatórias e de dados cadastrais/judiciais** para suporte aos processos de **Prevenção à Lavagem de Dinheiro e Financiamento do Terrorismo (PLD/FT)**.
- Avaliar capacidades técnicas, cobertura de bases, modelos de integração e atualização **diária** das informações.
- Subsidiar futura RFP (Request For Proposal); esta RFI **não constitui compromisso de contratação**.

## 2. Escopo da solução — Cobertura de bases de dados

### 2.1 Listas restritivas e sancionatórias internacionais
- OFAC — SDN List e Consolidated Sanctions List (EUA);
- ONU / Conselho de Segurança das Nações Unidas (UNSC Consolidated List);
- União Europeia — EU Consolidated Financial Sanctions List;
- Reino Unido — OFSI / HMT Consolidated List;
- Listas de outros órgãos relevantes (UK, Canadá — OSFI, Austrália — DFAT, Suíça — SECO, etc.);
- Interpol (Red Notices e demais difusões públicas);
- Listas de terrorismo e proliferação de armas de destruição em massa (incl. resoluções CSNU 1267, 1373, 1718, 2231);
- Países e jurisdições de alto risco (listas GAFI/FATF — *high-risk and monitored jurisdictions*, paraísos fiscais conforme IN RFB).

### 2.2 Listas restritivas nacionais
- CEIS — Cadastro de Empresas Inidôneas e Suspensas (CGU);
- CNEP — Cadastro Nacional de Empresas Punidas (CGU);
- CEPIM — Cadastro de Entidades Privadas Sem Fins Lucrativos Impedidas;
- CADIN — Cadastro Informativo de Créditos não Quitados do Setor Público Federal;
- Lista de inidôneos e inabilitados do TCU;
- CNJ — Cadastro Nacional de Condenações Cíveis por Ato de Improbidade Administrativa e Inelegibilidade;
- Lista de trabalho escravo / trabalho análogo ao de escravo ("lista suja" — MTE);
- Embargos do IBAMA e autuações ambientais;
- Sanções aplicadas por reguladores (BACEN, CVM, SUSEP, PREVIC, COAF — Processos Administrativos Sancionadores);
- Resoluções do COAF de indisponibilidade de ativos (Lei nº 13.810/2019).

### 2.3 Pessoas Politicamente Expostas (PEP)
- Base de PEPs nacional conforme normativos vigentes (Circular BACEN nº 3.978/2020, Resolução COAF nº 40/2021 e correlatas), incluindo titulares de mandatos, ocupantes de cargos relevantes dos três poderes, dirigentes de estatais e partidos;
- PEPs internacionais (chefes de estado/governo, altos funcionários, dirigentes de organizações internacionais);
- **Relacionados a PEP**: familiares (até 2º grau), estreitos colaboradores e empresas vinculadas;
- Identificação da função/cargo que gerou a classificação, data de início/fim do mandato e período de manutenção da condição de PEP após desligamento;
- Histórico de condição PEP (PEP ativo vs. ex-PEP).

### 2.4 Consultas judiciais e processuais
- Módulo de consulta a **processos judiciais** em tribunais estaduais, federais, trabalhistas e superiores (capilaridade nacional), com indicação dos tribunais cobertos;
- Classificação de processos por natureza/assunto (criminal, lavagem de dinheiro, corrupção, organização criminosa, crimes financeiros, execuções fiscais, etc.);
- Identificação do polo (autor/réu) e fase processual;
- Consulta a inquéritos e ações de improbidade quando disponíveis publicamente;
- Certidões e distribuições (quando aplicável);
- Frequência de atualização da base processual e mecanismo de monitoramento de novos processos.

### 2.5 Dados cadastrais e societários para qualificação (KYC)
- Situação cadastral de CPF e CNPJ junto à Receita Federal;
- Quadro Societário e de Administradores (QSA), com histórico de alterações;
- Identificação de **beneficiário final (UBO)** e cadeia societária/grupo econômico, incluindo participações indiretas;
- Vínculos entre pessoas físicas e jurídicas (sócios em comum, endereços, participações);
- Dados de óbito (SISOBI/base equivalente);
- Porte, CNAE, faturamento presumido, data de constituição;
- Endereços, contatos e dados complementares de enriquecimento cadastral.

### 2.6 Mídia negativa (Adverse Media)
- Monitoramento de mídia negativa nacional e internacional associada a crimes de lavagem de dinheiro, corrupção, fraude, terrorismo e crimes precedentes;
- Classificação por categoria de risco e fonte da notícia;
- Idiomas cobertos e critérios de curadoria/desambiguação.

## 3. Requisitos técnicos da solução

### 3.1 Integração e disponibilização **diária** das bases
- **Atualização mínima diária** de todas as listas restritivas, com indicação da frequência real por base (diária, intradiária, tempo real);
- Disponibilização das bases por múltiplos canais:
  - **API REST** (consulta online, síncrona, registro a registro);
  - **API/arquivo batch** para processamento em lote de grandes volumes;
  - **Transferência de arquivos** (SFTP ou equivalente) com carga completa (*full load*) e cargas incrementais (*delta*) diárias;
  - Possibilidade de **download das bases completas** para internalização no ambiente do contratante;
- Formatos estruturados de dados (JSON, XML, CSV/Parquet), com dicionário de dados e layout documentado;
- **Webhooks/notificações push** para alertas de inclusão/alteração de registros monitorados;
- Versionamento das bases e identificação de data/hora da última atualização de cada lista (*timestamp* por registro);
- Mecanismo de verificação de integridade dos arquivos (checksums/hash).

### 3.2 Funcionalidades de consulta e matching
- Busca por CPF, CNPJ, nome completo/razão social e variações;
- **Fuzzy matching** com score de similaridade configurável (tratamento de grafias alternativas, abreviações, transliterações de nomes estrangeiros);
- Tratamento de homônimos e desambiguação (data de nascimento, filiação, documentos);
- Consulta unitária e em lote (descrever limites de registros por requisição);
- **Monitoramento contínuo de carteira** (*ongoing screening*): reavaliação automática diária da base de clientes contra as listas, com geração de alertas apenas para mudanças (*delta de alertas*);
- Parametrização de regras de triagem por lista, score e tipo de pessoa;
- Retorno estruturado com fonte, lista de origem, data de inclusão e detalhamento do registro encontrado (evidência para trilha de auditoria).

### 3.3 Requisitos de API e desempenho
- Documentação completa da API (OpenAPI/Swagger) e portal do desenvolvedor;
- Ambiente de **homologação/sandbox** disponível durante avaliação e após contratação;
- Autenticação segura (OAuth 2.0, API Keys com rotação, mTLS — descrever opções);
- SLA de disponibilidade (mínimo desejado: **99,5%**) e de tempo de resposta (latência média e p99 por tipo de consulta);
- Capacidade de volumetria: informar limites de requisições por segundo (*rate limits*) e capacidade de processamento batch (registros/hora);
- Política de versionamento de API e prazo de depreciação de versões.

### 3.4 Segurança da informação e privacidade
- Conformidade com a **LGPD** (Lei nº 13.709/2018): base legal de tratamento, papel do fornecedor (operador/controlador), DPA — acordo de tratamento de dados;
- Criptografia em trânsito (TLS 1.2+) e em repouso;
- Certificações de segurança (ISO 27001, SOC 2 Type II ou equivalentes) — informar quais possui;
- Política de retenção e descarte de dados das consultas realizadas;
- Logs e **trilha de auditoria** completa das consultas (usuário, data/hora, parâmetros, resultado), com retenção mínima de 5 anos (alinhada à regulamentação de PLD/FT);
- Segregação de ambientes e controle de acesso por perfil (RBAC);
- Localização dos data centers e jurisdição de armazenamento dos dados;
- Plano de continuidade de negócios e recuperação de desastres (RTO/RPO).

### 3.5 Interface e relatórios
- Portal/console web para consultas manuais e gestão de alertas (descrever funcionalidades);
- Workflow de tratamento de alertas (análise, classificação como falso positivo, justificativa, aprovação) — informar se disponível;
- Relatórios gerenciais e extração de evidências para atender auditorias e reguladores (BACEN, COAF);
- Gestão de usuários com perfis de acesso e SSO (SAML/OIDC).

## 4. Requisitos regulatórios e de conformidade

- Aderência aos normativos brasileiros de PLD/FT: **Lei nº 9.613/1998**, **Lei nº 13.810/2019**, **Circular BACEN nº 3.978/2020**, **Resoluções COAF** e demais regulamentações aplicáveis ao segmento do contratante;
- Aderência às recomendações do **GAFI/FATF**;
- Procedimento e prazo de incorporação de **novas listas/resoluções** (ex.: determinações de indisponibilidade de bens do CSNU — exigência de bloqueio "sem demora");
- Comprovação da origem/licenciamento das fontes de dados e legalidade da coleta;
- Histórico de atendimento a instituições reguladas (bancos, fintechs, seguradoras, leiloeiros, etc.).

## 5. Implantação, suporte e níveis de serviço

- Prazo e metodologia de implantação/onboarding;
- Suporte técnico: canais, horários (desejável 24x7 para incidentes críticos), idioma e SLAs de atendimento por severidade;
- Gerente de conta dedicado e suporte especializado em compliance/PLD;
- Treinamento das equipes (técnica e de compliance);
- Roadmap do produto e frequência de evolução;
- Política de comunicação de mudanças nas bases, layouts e APIs.

## 6. Informações comerciais solicitadas

- Modelos de precificação disponíveis (por consulta, por pacote/franquia, assinatura por base, licenciamento para internalização, monitoramento de carteira por CPF/CNPJ ativo);
- Custos de implantação/setup e de integrações;
- Política de reajuste e prazos contratuais mínimos;
- Possibilidade de **POC (Prova de Conceito)** gratuita ou de baixo custo, com escopo e duração;
- Condições de escalonamento de volume (degraus de preço).

## 7. Qualificação do fornecedor

- Apresentação institucional: tempo de mercado, porte, estrutura;
- Principais clientes e casos de uso em PLD/FT (referências verificáveis, preferencialmente em instituições reguladas);
- Certificações da empresa e da equipe (ACAMS, CAMS ou equivalentes na área de compliance);
- Saúde financeira e ausência de impedimentos legais (declaração);
- Subcontratação: indicar se há terceiros na cadeia de fornecimento dos dados.

## 8. Instruções para resposta

- Responder ponto a ponto aos requisitos das seções 2 a 7, indicando: **Atende / Atende parcialmente / Não atende / Em roadmap** (com prazo);
- Anexar documentação técnica das APIs, layouts de arquivos e lista completa das fontes/bases cobertas com a respectiva frequência de atualização;
- Indicar premissas e dependências relevantes;
- Prazo para envio das respostas: **[definir data]**;
- Contato para dúvidas: **[definir e-mail/responsável]**;
- As informações recebidas serão tratadas como confidenciais e utilizadas exclusivamente para fins de avaliação.
