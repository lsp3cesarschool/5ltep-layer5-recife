# 5L-TEP Camada 5: Governança e Publicação

[Read in English](README.md) · [Painel](https://lsp3cesarschool.github.io/5ltep-layer5-recife/?lang=pt) ·
![Camada 5](https://img.shields.io/endpoint?url=https%3A%2F%2Flsp3cesarschool.github.io%2F5ltep-layer5-recife%2Fdata%2Fstatus.pt.json)

Camada 5 da Pirâmide de Engenharia da Confiança em Cinco Camadas (5L-TEP, SOFTENG 2026) para dados
abertos governamentais publicados em portais CKAN. Todo dia ela lê o que as Camadas 1 a 4 já publicam
sobre cada conjunto de dados do portal e coloca a evidência lado a lado: até onde cada camada chega, o
que falta, a Pontuação Global de Qualidade (Qs) onde as quatro se encontram e o que já dá para conferir
onde não se encontram.

Esta instância acompanha o portal de dados abertos da Prefeitura do Recife (<https://dados.recife.pe.gov.br>), como caso de aplicação em outro contexto: o código
de [5ltep-layer5](https://github.com/lsp3cesarschool/5ltep-layer5) no commit 5afce44, reutilizado pelo pesquisador
com três arquivos alterados (ver *Como rodar a sua instância*). Não é avaliação do órgão nem ranking.

## O que faz e o que não faz

- **Informa.** Nunca decide se um conjunto é publicado: essa decisão, se houver, acontece nos sistemas
  e procedimentos do próprio órgão. Cada conjunto tem uma ficha imprimível e citável, que pode ser
  anexada a esse procedimento.
- **Sinal** é item a conferir, nunca veredito. **Lacuna** é falta de evidência, nunca nota baixa.
- Depois de um relato, só **observa** o que aconteceu com os dados nas rodadas seguintes (desfecho
  inferido). "Sem mudança" não distingue "viu e aceitou" de "não viu"; uma mudança é "posterior ao
  relato", nunca "por causa dele".
- A revisão humana (HitL) está instrumentada e pronta; os números só aparecem se um gestor adotar o
  fluxo. O autor deste repositório não registra decisão de gestor (seria autoavaliação).

## Como a nota funciona

O artigo define Qs = 0,3·L1 + 0,3·L2 + 0,2·L3 + 0,2·L4, sendo cada Lᵢ a taxa de aprovação de uma
camada, e um limiar θ = 0,85 definido pelo responsável pelos dados (data owner). No painel, θ se chama
**Nota de corte (θ)**. Faixas de alerta: crítico abaixo de 0,70 (o piso crítico), alerta abaixo da nota
de corte, info acima. A Camada 5 mantém essa fórmula e acrescenta o que os portais reais exigem:

- **Dois fluxos.** *Completo*: as quatro camadas têm evidência válida, e o Qs é exatamente a fórmula
  do artigo. *Parcial*: um intervalo em vez de um ponto, com as camadas ausentes contadas como 0
  (limite inferior) e como 1 (limite superior). Retirar evidência só alarga o intervalo; "abaixo da
  nota de corte mesmo no melhor caso" já é informação útil. Um conjunto alcançado só pela Camada 4 não
  tem avaliação de conteúdo nem nota.
- **Competência compensa, integridade não.** Uma mudança dos metadados sem a data de modificação do
  portal avançar (RETRO_ALTER, da taxonomia da Camada 4) multiplica a nota por 0,5 até todas as camadas
  reavaliarem o conjunto. Qualquer fator abaixo do piso crítico dá as mesmas decisões; 0,5 se lê como
  "a evidência vale metade até ser renovada".
- **A evidência vence.** O resumo de uma camada vale por duas vezes a sua cadência (L1 e L2, 14 dias;
  L3, 62 dias; L4, 12 horas). Uma mudança de estrutura (SCHEMA_DRIFT) depois de uma avaliação a deixa
  fora do escopo. Bytes que mudaram sem registro nos metadados (vistos comparando os SHA-256 que as
  camadas registram) viram achado; a avaliação mais antiga continua contando, marcada como de uma versão
  anterior (`unrecorded_change` na política: `finding` por padrão, ou `supersede` para deixar de contá-la).
- **Atingir a nota de corte** também exige que todas as camadas tenham avaliado a versão atual.
- **A Camada 4 na soma** é a fração dos ciclos de monitoramento bem-sucedidos dos últimos 30 dias em
  que o conjunto não teve mudança crítica. Um ciclo que falhou é falta de cobertura, não reprovação.

Tudo isso é parâmetro de [`policy.json`](policy.json) (uma `dqv:QualityPolicy`), versionado e alterado
só por commit.

## De onde vêm os números

Leitura por HTTPS, sem token entre repositórios ([`sources.json`](sources.json)):

| Camada | Repositório | Arquivo lido | Unidade |
|---|---|---|---|
| L1 Contratos estruturais | [5ltep-layer1-recife](https://github.com/lsp3cesarschool/5ltep-layer1-recife) | `results/layer1_summary.json`, `results/validation.json` | arquivos por conjunto |
| L2 Políticas semânticas | [5ltep-layer2-recife](https://github.com/lsp3cesarschool/5ltep-layer2-recife) | `docs/data/layer2.json` | verificações das regras que avaliam o conjunto |
| L3 Detecção de anomalias | [5ltep-layer3-recife](https://github.com/lsp3cesarschool/5ltep-layer3-recife) | `results/<perfil>/layer3_summary.json` | pares série × mês |
| L4 Observabilidade e proveniência | [5ltep-layer4-recife](https://github.com/lsp3cesarschool/5ltep-layer4-recife) | `docs/data/layer4.json`, `cross_check.json`, `data/hash_store.json` | ciclos de monitoramento |

Um resumo que falha nas checagens de consistência (taxas fora de [0, 1], contagens que não fecham,
datas no futuro) é rejeitado por inteiro e aparece como lacuna, com o motivo.

## Saídas

- `docs/data/layer5.json`: o agregado por trás do [painel](https://lsp3cesarschool.github.io/5ltep-layer5-recife/?lang=pt).
- `docs/data/fichas/<conjunto>.json`: uma ficha por conjunto, identificada pelo SHA-256 do seu
  conteúdo, mostrada por `ficha.html?d=<conjunto>` (imprimir ou salvar em PDF).
- `docs/data/quality.jsonld`: medições de qualidade em W3C DQV calculadas sobre o estado exato do
  conjunto registrado pela Camada 4 (a entidade PROV endereçada por conteúdo), derivadas (PROV) dos
  resumos das camadas.
- `docs/data/status.json`, `status.pt.json`: selos. `results/history.json`, `results/state.json`:
  histórico das rodadas e o que a inferência lembra.

## Calendário e alertas

Diário às 05:10 UTC, depois do cross-check da Camada 4 (03:30). A Camada 5 lê o último resumo publicado
de cada camada e nunca espera por nenhuma. A execução falha de propósito (e o GitHub manda e-mail ao
mantenedor) diante de uma nova quebra de integridade ou de um resumo rejeitado, depois de os dados
serem gravados.

## Segurança

- O job que lê outros repositórios tem token só de leitura e só entrega um artefato; o job que grava
  não lê nada externo e aceita só os arquivos esperados (`src/accept.py`).
- Nada de `${{ }}` dentro de `run:`; os valores entram por `env:`.
- Só biblioteca padrão na execução; o painel escapa todos os dados e só segue links http(s).

## Como rodar a sua instância

1. Faça um fork deste repositório e edite três arquivos: [`portal.json`](portal.json) (o portal),
   [`sources.json`](sources.json) (onde estão os seus repositórios das Camadas 1–4) e, se o responsável
   pelos dados quiser, [`policy.json`](policy.json). Uma camada não implantada aparece como lacuna
   estrutural.
2. Habilite Actions e Pages (branch `main`, pasta `/docs`) e rode *Actions → 5L-TEP Layer 5
   Governance → Run workflow*.

Esta instância foi montada assim (reutilização demonstrada pelo pesquisador).

## Rodar localmente

```bash
python main.py --out build                      # read the layers on GitHub, write into build/
python main.py --fixtures tests/fixtures --now 2026-10-09T18:00:00Z --out build   # offline
python -m pytest tests -q
python -m http.server --directory docs          # preview the dashboard (needs docs/data)
```

Números para a pesquisa vêm das execuções do GitHub Actions; execuções locais servem só para teste.

## Como citar

Ver [`CITATION.cff`](CITATION.cff). Framework: Pinheiro et al., *Towards Trust Engineering in Open Data
Systems*, SOFTENG 2026 (IARIA). Camada 4: Pinheiro e Sérgio, *5LTEP-L4*, WFA/WebMedia 2026.

## Licença

MIT (código). Ver [`LICENSE`](LICENSE).
