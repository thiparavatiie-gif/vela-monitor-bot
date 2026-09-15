# Notas das lives do Diego Velasques (canal Vela Trader) — para evoluir o Vela Monitor

Este arquivo é o "caderno de anotações" de tudo que eu (Claude) vou tirando das
lives do canal (https://www.youtube.com/@VelaTrader/streams), pra ir alimentando
melhorias no bot ao longo de várias sessões. São **anotações minhas, com minhas
próprias palavras** a partir do que ele fala nas lives — não é transcrição (por
direitos autorais eu não reproduzo o texto literal das lives, só extraio os
conceitos/técnicas e reescrevo).

O canal tem mais de 100 lives (só nos últimos ~2 meses já tinham 30+, cada uma
de 50min a 2h), então isso vai ser processado aos poucos, das mais recentes pra
mais antigas, uma sessão de cada vez. A seção "Progresso" no fim marca até onde
eu já cheguei.

---

## Lives já processadas

### 1) "Trade Ao Vivo: O que fazer no Bitcoin agora?" — 11/09/2026 (streamed), 1h00
`https://www.youtube.com/watch?v=kmdUlbJK-Sc`

Contexto: BTC bateu sobrevenda no 4h, ele já vinha avisando havia mais de uma
semana que isso ia acontecer, e a live acompanha o repique em tempo real (BTC
saindo de ~76.700 até passar de 80.000 na live).

Conceitos/técnicas que aparecem (e o que já existe ou não no bot):

- **RSI em sobrevenda no 4h é o setup mais raro e mais forte que ele opera** —
  ele é explícito: um "1h em sobrevenda" acontece com frequência (~1x por
  semana ou a cada duas semanas), mas um **4h em sobrevenda** é raro de verdade
  (ele cita ter ficado quase um mês sem bater um, e que pode passar até 2 meses
  sem acontecer) — e quando acontece, o repique tende a ser grande. Ele chama
  isso de achar "um pote de ouro" no meio de uma tendência de alta.
  **→ O bot hoje tem primeiro-toque de RSI separado só em 5m (day trade) e 1h
  (swing) — NÃO tem uma versão de 4h.** Isso é uma lacuna real: o setup que ele
  mais valoriza (4h) não tem um sinal dedicado, só entra "de raspão" dentro da
  confluência multi-indicador. Vale considerar um terceiro sinal
  `check_scalp_4h` (ou renomear a família toda), tratado como o de MAIOR
  convicção dos três, com texto/checklist deixando claro que é raro.

- **Gerenciamento de stop pós-movimento**: depois que o preço já deu uma
  "disparada" boa desde a base (ele usa a expressão "grande disparidade do
  fundo"), ele recomenda mover o stop pro preço de entrada ("stop no zero a
  zero") — trava o trade sem risco, deixa o resto correr. **→ o bot não tem
  hoje nenhuma lógica de "sugestão de mover o stop pra zero a zero depois de X%
  de movimento a favor"** — isso é gerenciamento pós-entrada, o bot só manda o
  stop inicial. Poderia virar uma linha extra tipo "depois que o preço andar
  ~Y% a favor, considere mover o stop pra entrada" dentro do próprio cartão, ou
  um aviso futuro tipo "atualização de trade".

- **Rompimento sem continuidade = confirmação de força** — quando o preço
  rompe uma mínima mas não tem sequência de queda nenhuma (reverte rápido com
  volume comprador forte), ele lê isso como sinal de que a base está segura e
  que o próximo movimento mais provável é um fundo ascendente. **→ isso já é
  essencialmente o sinal 6 do bot (Reversão por rompimento falho)** — só
  reforça que a lógica já implementada está alinhada com o que ele ensina.

- **Resistência rompida virando suporte (reteste)** — depois de romper uma
  resistência de canal (1h), ele explicitamente espera/observa se aquele nível
  vira suporte no reteste, como confirmação de continuidade. **→ o bot não tem
  um sinal dedicado de "reteste de nível rompido"** hoje — os pivôs/EMAs
  entram como suporte/resistência genéricos, mas não tem uma lógica que
  acompanha "acabou de romper X, agora tá testando X como suporte". Pode virar
  um sinal futuro (nível 11?), mas exige mais desenho (precisa saber que
  "acabou de romper" recentemente, não é só tocar um nível qualquer).

- **Gestão de risco / alavancagem** — ele é bem enfático (usando um exemplo real
  de aluno que foi liquidado com menos de 1% de movimento contrário) que quem
  não sabe fazer gerenciamento de capital não deveria operar. Isso é mais
  princípio geral do que algo pra codificar, mas reforça que o bot deveria
  continuar sempre deixando claro que é leitura técnica automática, não
  recomendação — o que já faz.

- Bandeira de alta ("bandeira") aparecendo em vários tempos gráficos ao mesmo
  tempo (5m, 1h, até 3 dias) como reforço de continuação — não é uma técnica
  nova (é basicamente o que já motivou a confluência multi-timeframe), mas
  mostra que "bandeira"/flag como padrão de continuação é um vocabulário dele
  que o bot ainda não usa nominalmente (o bot fala em "padrão de equilíbrio"
  pra lateralização, mas não tem um conceito separado pra bandeira de alta
  pós-impulso). Baixa prioridade — anotado pra ver se aparece de novo em outras
  lives antes de decidir se vale um sinal novo.

**Resumo de candidatos a melhoria dessa live**: (1) sinal dedicado de RSI 4h
primeiro-toque como o "sinal mais forte" dos três; (2) sugestão de mover stop
pra zero a zero depois de movimento favorável relevante.

---

### 2) "Trade Ao Vivo: Qual o Melhor Trade a Ser Feito Agora?" — 10/09/2026, 1h11
`https://www.youtube.com/watch?v=j9ydMfLcb2I`

Contexto: um dia antes da live #1 — é literalmente a MESMA correção/repique de
BTC sendo acompanhada desde mais cedo (o "4 horas em sobrevenda" ainda estava
se formando aqui, e na live #1 já tinha virado repique). Isso já mostra como as
lives diárias tendem a se repetir/continuar a mesma história por vários dias
seguidos.

Conceitos que confirmam ou complementam o que já saiu da live #1:

- **Confirma de novo, com outras palavras**: "o primeiro toque no 4 horas
  depois de uma grande movimentação de alta é ponto suporte, é ponto de
  entrada" — dita quase como regra fixa logo no início da live. Reforça o
  candidato (1) da live #1 (sinal dedicado de RSI 4h).

- **Evitar stop/liquidação em número psicológico redondo** — ele foi bem
  específico: nunca deixar o ponto de stop/liquidação logo abaixo de um número
  redondo (tipo 75, 80, 85 mil), porque o preço "gosta" de ir buscar esses
  níveis com um pavio antes de reverter; prefere um stop com mais margem
  abaixo do redondo (exemplo dele: 73.900 em vez de 74.900, pra não ficar colado
  no 75). **→ o bot JÁ TEM isso implementado** (`avoid_round_number_stop`,
  usado nos sinais de scalp) — é uma confirmação de que essa parte do código já
  está alinhada com o que ele ensina, não precisa mudar nada.

- **Sinal de exaustão = rompimento de topo/máxima sem continuidade** — ele usa
  esse critério pra ficar de pé atrás com uma altcoin (ZEC) mesmo ela tendo
  batido "1h em sobrevenda": porque antes daquilo teve um rompimento de máxima
  sem continuidade de alta (sinal de exaustão), o toque de sobrevenda ali tem
  menos confiança pra ele do que um toque que vem depois de uma alta "limpa"
  (sem esse sinal de exaustão prévio). **→ o bot já detecta exaustão (sinal 2)
  separadamente do primeiro-toque de RSI (sinal 3), mas não cruza os dois** —
  ele nunca reduz a convicção de um sinal de RSI se uma exaustão foi detectada
  ali perto antes. Poderia ser um refinamento futuro: se saiu uma exaustão
  recente na mesma direção contrária ao sinal de RSI atual, rebaixar a
  convicção (ou pelo menos citar isso no texto), em vez de tratar os dois
  sinais como independentes.

- **Leitura de "pânico vs. correção normal" pelas altcoins** — ele comenta que,
  como as altcoins não estavam caindo junto (nem tanto) com o BTC nessa queda,
  isso mostra que não tem pânico generalizado no mercado, só uma correção
  normal — porque se fosse pânico de verdade, as altcoins cairiam primeiro/mais
  forte. **→ o bot tem dominância BTC/altseason (sinal 5) mas com outro
  objetivo** (comparar retorno relativo pra achar "quem tá mais forte"), não
  exatamente "pânico vs. correção normal". Candidato de baixa/média prioridade
  pra mais adiante: um indicador de "regime de mercado" que compara o quão mal
  as altcoins estão indo DURANTE uma queda do BTC (não depois).

- Ele também menciona explicitamente que tira o stop enquanto ainda está
  esperando o preço chegar no 4h de sobrevenda (monta a posição sem stop,
  aceitando mais risco de propósito) e só bota o stop depois que confirma o
  repique. Isso é estilo pessoal de gestão de posição dele (mais agressivo) —
  não é algo que o bot deveria replicar (o bot sempre deve mostrar um stop),
  só anotado como contexto de como ele realmente opera.

**Resumo de candidatos a melhoria dessa live**: nenhum candidato NOVO
(reforça os da live #1) — só uma ideia de refinamento futuro (cruzar exaustão
recente com convicção do sinal de RSI) e uma confirmação de que o
`avoid_round_number_stop` já está certo.

---

### 3) "Não Compre Bitcoin Antes de Ver Essa Análise Ao Vivo!" — 01/09/2026, 1h18
`https://www.youtube.com/watch?v=FHURxqrxOFo`

Contexto: cenário diferente das duas primeiras — aqui é uma correção mais leve
(BTC ainda perto das máximas, sem ter batido 4h sobrevenda ainda), com bastante
tempo de perguntas e respostas e ele passeando por várias altcoins (Near, Ena,
Uni, TRX). Boa amostra do lado "educativo/Q&A" das lives, não só
acompanhamento de trade.

Conceitos novos ou reforçados:

- **Ciclo de bull market em 3 fases**: primeiro BTC + "blue chips" (tipo
  Solana), depois altcoins médias, por último memecoins — quando memecoins
  começam a disparar em bloco, isso normalmente marca o FIM do ciclo de alta
  (ele cita o token do Trump como exemplo de "isso aqui foi o fim da festa").
  **→ o bot já tem o "termômetro de fase de ciclo" (sinal 7)**, que compara
  memecoins vs BTC vs alts — a lógica já implementada está alinhada com esse
  framework de 3 fases. Não é candidato novo, é mais uma confirmação de que o
  sinal 7 já modela a ideia certa.

- **Evitar comprar ativo logo depois de um "clímax"** — ele explica que um
  clímax de alta (pico parabólico, tipo o que ouro fez recentemente) tende a
  encerrar o movimento de alta por um bom tempo, então ele evita entrar comprado
  logo depois de ver um clímax formado, preferindo ativos que ainda não
  climaxaram. **→ o bot já detecta clímax de exaustão (sinal 2)** como gatilho
  de reversão — o que essa live acrescenta é a ideia de usar a exaustão também
  como um FILTRO negativo pra sinais de COMPRA subsequentes no mesmo ativo (se
  teve uma exaustão de topo há pouco tempo, reduzir convicção de comprar aquele
  ativo agora) — parecido com o candidato de refinamento já anotado na live #2
  (cruzar exaustão recente com convicção de outros sinais).

- **Só aumenta posição em correção, nunca durante alta** — regra de
  gerenciamento que ele repete: só adiciona mais posição quando o preço cai
  (correção/pânico), nunca quando está subindo. É gerenciamento de posição, não
  geração de sinal — mas poderia virar uma frase padrão nos cartões de sinais
  tipo bottom fishing/reversão leve (que já têm `entry_zone` fracionada),
  reforçando que a fração de baixo deve ser comprada na correção, não perseguindo o preço.

- **Força relativa de um cesto de altcoins como confirmação prévia** — ele
  observa que quanto mais altcoins (tipo Near, Ena) estão segurando suas EMAs
  de 12 períodos e subindo, maior a probabilidade de ETH e BTC fazerem o mesmo
  em seguida — ou seja, um cesto de altcoins "aguentando" funciona como
  indicador antecedente pro BTC/ETH. **→ é parecido com o sinal 5 (dominância/
  altseason) do bot, mas com outro ângulo** (né força relativa de retorno, não
  "quantas altcoins seguram a EMA"). Candidato de prioridade média/baixa pra
  mais pra frente — não é algo óbvio de portar 1:1 pro bot ainda.

- **RSI 1h com alerta em ~31 reafirmado de novo** — ele ensina de novo (agora
  pra um espectador querendo aplicar em outro ativo) a configurar alerta de RSI
  cruzando ~31 no 1h depois de uma alta forte, exatamente a mesma lógica do
  sinal já implementado (`SCALP_1H_RSI_OVERSOLD`). Mais uma confirmação, não
  candidato novo.

**Resumo de candidatos a melhoria dessa live**: nenhum candidato NOVO de sinal
— reforça o refinamento "exaustão recente reduz convicção de sinais de
compra" (já anotado na live #2) e confirma que os sinais 2, 5 e 7 já
capturam os frameworks certos.

---

### 4) "TRADE AO VIVO: URGENTE - BITCOIN DISPARA E LIQUIDA SHORTADOS!" — 20/08/2026, 1h44
`https://www.youtube.com/watch?v=001nDMkrgqo`

Contexto: cenário bem diferente das outras 3 — aqui é uma disparada forte
(short squeeze com continuação), não uma correção. Boa amostra do "outro lado"
do mercado.

Conceitos novos ou reforçados:

- **Stop pra zero a zero em posição "deixar rolar" reforçado de novo** — ele
  comenta explicitamente que, numa posição muito favorável, prefere colocar o
  stop no preço de entrada (zero a zero) e deixar a posição rodar (em vez de
  realizar lucro cedo), pra não perder a chance de um movimento muito maior se
  for o início de um novo ciclo de alta. **Esse é o 2º aparecimento** desse
  conceito (já tinha saído na live #1) — reforça o candidato (2) já anotado
  (sugestão de mover stop pra zero a zero depois de movimento favorável).

- **"Monitor de mercado" (IA treinada com 8 anos de conteúdo dele) validando a
  ideia do bot inteiro** — ele descreve ter um sistema próprio de IA treinado
  no jeito dele analisar (8 anos de vídeos), que fica monitorando o mercado e
  soltando alertas filtrados (não deixa "explodir" 400 sinais de uma vez, só
  os melhores) — é basicamente a mesma ideia por trás do Vela Monitor. Não é
  candidato de código novo, é confirmação de que o conceito geral do bot
  (monitorar + filtrar os melhores sinais) está no caminho certo.

- **Comprar força, não fraqueza (moeda que "ainda não subiu")** — reforça o que
  já saiu na live #3: em início de ciclo, focar nos ativos que JÁ estão fortes
  (BTC, ETH, XRP) em vez de tentar achar uma moeda "esquecida" que ainda não
  subiu, porque essa fraqueza geralmente é sinal de que ela não vai acompanhar.
  **2º aparecimento** desse framework de sequência do ciclo.

- **Scalp pode "virar" swing trade se a estrutura confirmar continuação** —
  quando uma entrada de curto prazo (tipo primeiro toque de RSI no 15m) dá um
  repique forte e o preço rompe novas máximas, ele não necessariamente realiza
  lucro — deixa a posição "virar" um swing trade, movendo o stop pra zero a
  zero. É uma continuação natural do conceito de gestão pós-entrada já
  anotado, mas mostra que pra ele a fronteira entre "scalp" e "swing" é fluida
  (decidida pela estrutura do preço depois da entrada, não fixada de
  antemão). Não é algo fácil de automatizar bem (o bot manda um cartão por
  sinal, não acompanha posições abertas), mas reforça que a sugestão de "mover
  stop pra zero a zero" é o tipo de coisa que ele aplica com bastante
  frequência.

**Resumo de candidatos a melhoria dessa live**: reforça (não adiciona novo)
o candidato "sugestão de mover stop pra zero a zero após movimento favorável"
— agora confirmado em 2 lives — e valida a ideia geral do bot.

---

### 5) "Operando AO VIVO – As Melhores Oportunidades de Hoje" — 14/08/2026, 1h08
`https://www.youtube.com/watch?v=NWXkuTbfpBk`

Contexto: live mais "multi-mercado" — passeia por petróleo, ações americanas
(Amazon, Tesla, SpaceX, Anthropic pré-IPO), Ibovespa, dólar, ouro e só depois
cripto (BTC/ETH/XRP/ONDO). Mostra um lado do canal que foge do escopo do bot
(o bot só cobre cripto via Binance), mas ainda traz conceitos aplicáveis.

Conceitos novos ou reforçados:

- **Hedge com posição contrária ("fazer um head")** — com várias posições
  compradas em altcoins (ETH, XRP, ONDO), ele abre um short pequeno em BTC só
  como seguro: se o mercado cripto desabar, o lucro no short do BTC compensa
  parte da perda nas altcoins; se not, a perda no short é pequena e "paga" o
  seguro. É uma técnica de proteção de portfólio (gestão de posições
  simultâneas), não geração de sinal — não encaixa bem na arquitetura atual do
  bot (que manda cartões por sinal, não acompanha portfólio). Anotado, mas
  baixa prioridade/não óbvio de implementar.

- **Resistência/suporte trocando de papel, de novo** — usado explicitamente pra
  SpaceX ("suporte anterior virou resistência, resistência anterior virou
  suporte", esperando o preço trabalhar entre os dois). **2º aparecimento**
  desse conceito de reteste de nível rompido (já visto na live #1).

- **"Quedas só estancam com volatilidade, altas só terminam com volatilidade"**
  — ideia de que mercado muito comprimido/parado tende a preceder um movimento
  forte, pra qualquer lado. Relacionado ao "padrão de equilíbrio" (sinal 8) que
  já mede compressão de faixa, mas aqui é mais um aviso genérico ("fique de
  olho, vem volatilidade") do que uma condição de entrada. Baixa prioridade.

- **Rompimento sem continuidade reaparece em ONDO** — mesma lógica de exaustão/
  reversão já coberta pelo sinal 6. Mais uma confirmação, não candidato novo.

- **Aviso de gerenciamento em dia de "mercado fraco"** — ele avisa
  explicitamente pra reduzir alavancagem e sempre usar stop quando o cenário
  do dia não está bom — reforça que os textos do bot devem continuar deixando
  claro que é leitura automática, não recomendação (já faz isso).

**Resumo de candidatos a melhoria dessa live**: reforça o "reteste de nível
rompido" (agora 2x, lives #1 e #5) — ainda não maduro o suficiente pra virar
sinal novo (falta desenho de como detectar "acabou de romper" de forma
confiável), mas é o 3º padrão mais recorrente até agora.

---

## Padrões que já apareceram em mais de uma live (mais forte candidato a virar código)

1. **RSI em sobrevenda/sobrecompra no 4h é o setup de maior convicção pra ele**
   — mencionado em 2 das 5 lives processadas até agora como o ponto de entrada
   principal, mais raro e mais forte que o 1h/5m. **✅ IMPLEMENTADO**
   (`check_scalp_4h` / `diagnose_scalp_4h`, estilo SWING, stop 3%) —
   15/09/2026.
2. **Sugestão de mover stop pra zero a zero após movimento favorável relevante**
   — apareceu em 2 lives (#1 e #4). **✅ IMPLEMENTADO** — extensão de
   `_ultima_operacao_texto` na memória da última operação: quando a operação
   ainda está aberta e o preço já andou 1R (`BREAKEVEN_STOP_R_MULT`) a favor,
   sugere mover o stop pra entrada — 15/09/2026.
3. **Reteste de nível rompido (resistência virada suporte e vice-versa)** —
   apareceu em 2 lives (#1 e #5). Ainda precisa de mais desenho técnico (como
   detectar "rompeu recentemente" de forma confiável) antes de virar sinal.
4. **`avoid_round_number_stop` confirmado** — nada a mudar, só validado.
5. **Exaustão recente devia reduzir a convicção de sinais de compra** — apareceu
   em 2 lives (#2 e #3) de formas diferentes (ZEC com rompimento sem
   continuidade, ouro pós-clímax) — candidato de refinamento pra cruzar o sinal
   2 (exaustão) com os outros sinais de COMPRA/VENDA em vez de tratá-los como
   independentes.
6. **Sinais 2, 5, 6, 7 e 8 do bot já capturam frameworks que ele ensina**
   (clímax de exaustão, dominância/altseason, rompimento falho, fase de ciclo
   em 3 etapas, padrão de equilíbrio) — confirmado repetidamente, sem
   necessidade de mudança. A ideia geral do bot (monitorar + filtrar os
   melhores sinais) também foi validada pelo "monitor de mercado" que ele
   descreve usar (live #4).

---

## Progresso

- Processadas: 5 de ~30+ (últimos ~2 meses) — canal tem mais de 100 lives no
  total, indo bem mais pra trás no tempo. Amostragem espalhada no tempo (não
  só lives consecutivas): 11/09, 10/09, 01/09, 20/08 e 14/08/2026 — cobrindo
  correção/lateralização, disparada forte de alta, e uma live mais
  multi-mercado (ações americanas, Ibovespa, dólar, ouro, além de cripto).
- Candidata seguinte (ainda não processada): "Trade Ao Vivo! Análise do
  Bitcoin, Altcoins e Mercado Internacional!" (ncl4n0dfK1Y, ~2 meses atrás).
- 15/09/2026: implementados os 2 candidatos mais maduros — (1) sinal 4h de
  primeiro toque de RSI (`check_scalp_4h`) e (2) sugestão de stop zero a zero
  na memória da última operação. Os candidatos (3) reteste de nível rompido e
  (5) cruzar exaustão com os outros sinais de compra/venda seguem em aberto,
  pra quando aparecerem em mais lives ou o Thiago pedir pra avançar com eles.
- Observação de processo: as duas primeiras lives processadas eram
  basicamente a MESMA correção de BTC sendo acompanhada em dias seguidos — ou
  seja, lives vizinhas tendem a ser bem repetitivas entre si. Amostragem
  espalhada no tempo (a partir da live #3) trouxe cenários mais variados com
  menos lives processadas.
