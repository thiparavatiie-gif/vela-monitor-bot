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

### 6) Live "ao vivo" de 16/09/2026 (transcrição colada direto pelo Thiago no
chat, sem título/URL — não veio de uma busca no canal)

Contexto: BTC batendo na média de 200 períodos (diário) depois de uma queda
no início da semana, formando uma bandeira de baixa — ele espera romper
77.200 com volume pra invalidar essa bandeira. Pano de fundo do dia: decisão
de juros dos EUA às 15h30 e o Clarity Act (projeto de regulação cripto) não
aprovado no Senado no dia anterior, o que ele trata como ruído de curto
prazo político (ligado à disputa partidária por causa dos ganhos do Trump em
cripto), não como mudança de tendência de fundo.

Conceitos/técnicas que aparecem (e o que já existe ou não no bot):

- **Confirmação direta da estratégia de 4h em sobrevenda + parcial + stop no
  zero a zero** — ele descreve a própria estratégia dele explicitamente:
  entrar no primeiro toque do RSI de 4h em sobrevenda, fazer parciais
  conforme o preço sobe, e mover o stop pro zero a zero, garantindo o lucro
  já feito e deixando o resto correr. **→ bate exatamente com o que já foi
  implementado nesta sessão** (`check_scalp_4h` + a sugestão de zero a zero
  em `_ultima_operacao_texto`) — validação forte de que a leitura das lives
  anteriores estava certa, sem precisar de nenhuma mudança de código.

- **Mínima perdida sem continuidade de queda = bandeira de alta segue viva**
  — ele repete explicitamente essa leitura no BTC do dia: perdeu a mínima
  anterior, mas sem sequência de queda nenhuma, então trata isso como
  confirmação de que a estrutura de alta (bandeira) continua válida — só
  mudaria de leitura se confirmasse um novo rompimento de baixa com
  continuidade. **→ já coberto, é a mesma lógica do sinal 6 do bot
  (`check_failed_breakout_reversal`, reversão por rompimento falho)** —
  primeira vez foi na live #1, reforçado também na #5 (com ONDO), e agora
  de novo aqui, sempre alinhado com o que já está implementado.

- **Segundo toque de RSI no 4h também vira suporte, mas o "movimento grande"
  é sempre no primeiro toque** — ele comenta que o BTC bateu sobrevenda no
  4h de novo (depois de já ter tido o primeiro toque antes), e que esse
  novo toque também serve de referência de suporte, mas a estratégia dele
  foca no primeiro toque porque é ali que historicamente vem o movimento
  maior. **→ já coberto**: como `check_scalp_4h` não guarda estado entre
  execuções, ele já dispara de novo naturalmente em qualquer novo primeiro
  toque (o RSI saindo e voltando a entrar na zona conta como novo evento) —
  não precisa de mudança.

- **"Compra-se no pânico, numa tendência de alta"** — ideia de que notícia
  negativa (tipo o Clarity Act falhando) que derruba o preço sem mudar a
  estrutura de fundo é oportunidade de compra, não motivo de saída. É mais
  filosofia de gestão/timing do que uma condição técnica objetiva — não dá
  pra virar sinal sem um jeito de medir "pânico" de forma confiável
  (poderia usar volume + RSI extremo, que já é parecido com o clímax de
  exaustão, sinal 2). Anotado, sem ação imediata.

- **Ombro-cabeça-ombro invertido citado como setup especulativo em tempos
  gráficos curtos (2-5min)** — primeira menção desse padrão clássico de
  reversão nas lives processadas até agora. Não está implementado (nenhum
  sinal do bot detecta H&S/H&S invertido) — precisaria de bem mais desenho
  técnico pra detectar de forma confiável (é um padrão de 3 pernas com
  "neckline"). 1ª aparição, ainda não é candidato maduro.

- **Triângulo ascendente citado como setup em TRX** — "forma base, não
  perde a base" — parecido em espírito com o padrão de equilíbrio (sinal 8),
  mas com a variação de que o fundo vai subindo em vez de ficar lateral.
  1ª aparição, não é candidato maduro ainda (e além disso está fora do
  escopo atual, que é só BTC/ETH por causa do `SOMENTE_CORE_SYMBOLS`).

- **Alavancagem "de permissão" vs. alavancagem efetiva** — explicação de que
  o número de alavancagem que você configura na corretora é só um limite
  permitido, não a alavancagem de verdade (que depende de quanto do
  capital total da conta está realmente em uso). É educação de gestão de
  risco, não vira sinal — mas é uma boa nota pra qualquer texto educativo
  futuro do bot/README.

**Resumo de candidatos a melhoria dessa live**: nenhum candidato novo pronto
pra código — o ponto mais importante foi a **validação direta** de que o
sinal de 4h + zero a zero implementados nesta sessão batem exatamente com a
estratégia real do canal. H&S invertido e triângulo ascendente ficam
anotados como candidatos em potencial, mas com só 1 aparição cada (e H&S
precisa de desenho técnico bem mais elaborado).

---

### 7) Live "ao vivo" de 17/09/2026 (transcrição colada direto pelo Thiago no
chat, sem título/URL — pedido explícito de estudar a fundo e registrar
qualquer regra ainda não anotada, "tudo é importante")

Contexto: mercado americano subiu forte depois do anúncio de juros dos EUA
(ao contrário do que todo mundo esperava), mas o cripto abriu puxando novas
mínimas. Bandeira de alta seguindo intacta no 3 dias e no semanal, apesar de
uma vela feia (martelo invertido) no 4h. Ele reforça bastante a visão de
"não estamos mais em bear market" e mistura análise técnica com contexto
macro (petróleo, eleições americanas, Trump) e várias perguntas de gestão de
capital/alavancagem de alunos.

Conceitos/técnicas que aparecem (e o que já existe ou não no bot):

- **Regra objetiva pra classificar bandeira de alta vs. bandeira de baixa,
  usando Fibonacci + direção do volume** — essa é a regra nova mais
  concreta da live, explicada com bastante precisão técnica: uma bandeira
  de BAIXA exige que a correção (pull-back) do movimento fique **dentro
  de até 0.382 de Fibonacci** da perna anterior, **com volume descendente**
  durante a formação e **sem continuidade** nos rompimentos de baixa. Se a
  correção passar de 0.382 (ele usa um caso concreto passando pra 0.5) E o
  volume nos rompimentos virar **ascendente/comprador**, isso descaracteriza
  a bandeira de baixa — na prática, o padrão passa a ser lido como bandeira
  de ALTA. **→ o bot não tem esse classificador hoje.** O `check_pullback`
  (sinal 1) já usa a perna de impulso + retração de 0.382, mas não classifica
  "bandeira de alta" vs "bandeira de baixa" como rótulos distintos, e não
  cruza a profundidade da retração com a direção do volume da forma como ele
  descreve aqui. Seria um sinal novo (ou uma extensão do pullback) que: (1)
  mede se a correção ainda está contida em 0.382 ou já passou disso, e (2)
  checa se o volume nos candles de rompimento da faixa de correção é a favor
  ou contra a tendência anterior. **1ª aparição com esse nível de detalhe —
  candidato forte, vale considerar pra próxima leva de implementação.**

- **RSI de 4h extremo e prolongado (>90, por semanas seguidas) como leitor
  de "regime" bull vs. bear market** — ele usa o histórico do RSI de 4h do
  BTC (voltando ao bear market anterior inteiro, e ao de 2022) pra mostrar
  que nunca se viu o RSI de 4h bater e SEGURAR em extremos tão altos (94,
  24 dias consecutivos) durante um bear market — isso só aconteceu em
  janeiro de 2023, que foi exatamente a virada pro bull market atual. A
  leitura dele: RSI de 4h muito esticado por MUITOS dias seguidos (não só
  um pico isolado) é sinal de mudança de regime de mercado (bear→bull ou
  o contrário), diferente do clímax de exaustão (sinal 2, que é sobre um
  pico pontual reverter). **→ o bot não tem nada parecido** — o
  `detect_market_trend` atual é 100% baseado em cruzamento de EMAs no
  diário/semanal/mensal, não olha pra duração/extremos do RSI de 4h. Seria
  um indicador de contexto adicional (não um sinal de entrada — ele mesmo
  não opera baseado nisso diretamente, usa como leitura de fundo), tipo um
  "termômetro de regime" parecido em espírito com o termômetro de fase de
  ciclo (sinal 7) que já existe, mas usando RSI de 4h esticado por muitos
  dias em vez de comparar memecoins/alts/BTC. **1ª aparição — candidato
  interessante, mas de baixa prioridade imediata** (é mais leitura de
  contexto macro do que gatilho de entrada).

- **Mínima perdida sem continuidade de queda = bandeira de alta segue viva**
  — repetida de novo, tanto pro BTC quanto pro petróleo ("perda de suporte
  sem continuidade de queda... isso é exaustão"). **4ª aparição** (lives
  #1, #5, #6 e agora #7) — segue sendo a leitura mais recorrente de todas,
  e continua 100% coberta pelo sinal 6 (`check_failed_breakout_reversal`).

- **Ombro-cabeça-ombro invertido, 2ª aparição** — de novo citado como o
  "pior cenário (mas ainda bullish)" caso o BTC não confirme o fundo
  ascendente diretamente — agora 2x (lives #6 e #7). Ainda sem desenho
  técnico pronto pra virar sinal (precisa detectar 3 pernas + "neckline" de
  forma confiável), mas já é candidato a ficar de olho se aparecer de novo.

- **Força relativa entre altcoins não segue uma regra fixa de "quem lidera
  quem"** — ele corrige explicitamente um espectador que perguntou se
  altcoins "precificam antes" do BTC: não existe essa regra geral, cada
  altcoin tem sua força relativa própria (ETH mais forte que BTC no momento,
  TRX mais fraco) — quem realmente importa é comparar a força de cada ativo
  individualmente, não assumir uma ordem fixa. Reforça (não contradiz) a
  lógica que o próprio sinal de dominância/altseason (sinal 5) já usa
  (comparação relativa, não ordem fixa de "quem vem primeiro"). Sem ação de
  código.

- **Gestão de posição: acumular no mesmo trade/posição em vez de abrir
  posições separadas** — ao montar swing trade em várias entradas
  (acumulando nas quedas), ele reforça que prefere ir adicionando dentro da
  MESMA posição (o preço médio vai ajustando) em vez de abrir posições
  novas separadas — mais organização de conta do que sinal. Sem ação de
  código, mas reforça que o bot já trata isso bem ao não gerar sinais
  repetidos desnecessários pro mesmo movimento.

**Resumo de candidatos a melhoria dessa live**: a regra de classificação de
**bandeira de alta/baixa via Fibonacci (limite de 0.382) + direção do
volume** é o candidato mais concreto e novo até agora que ainda não virou
código — dá pra transformar num sinal ou numa extensão do pullback. O
"RSI 4h esticado por muitos dias = mudança de regime" é interessante mas
mais pra contexto/leitura macro do que gatilho de entrada, prioridade menor.
"Mínima sem continuidade" segue validando o sinal 6 (4ª vez). H&S invertido
chegou a 2 aparições.

---

## Padrões que já apareceram em mais de uma live (mais forte candidato a virar código)

1. **RSI em sobrevenda/sobrecompra no 4h é o setup de maior convicção pra ele**
   — mencionado em 2 das 5 lives processadas até agora como o ponto de entrada
   principal, mais raro e mais forte que o 1h/5m. **✅ IMPLEMENTADO**
   (`check_scalp_4h` / `diagnose_scalp_4h`, estilo SWING, stop 3%) —
   15/09/2026.
2. **Sugestão de mover stop pra zero a zero após movimento favorável relevante**
   — apareceu em 3 lives agora (#1, #4 e #6 — na #6 ele descreveu a própria
   estratégia dele quase palavra por palavra: primeiro toque no 4h, parcial,
   stop no zero a zero). **✅ IMPLEMENTADO** — extensão de
   `_ultima_operacao_texto` na memória da última operação: quando a operação
   ainda está aberta e o preço já andou 1R (`BREAKEVEN_STOP_R_MULT`) a favor,
   sugere mover o stop pra entrada — 15/09/2026, validado de novo em
   16/09/2026.
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
   (clímax de exaustão, dominância/altseason, rompimento falho — "mínima sem
   continuidade de queda = bandeira de alta viva", confirmado 4x agora (#1,
   #5, #6, #7) —, fase de ciclo em 3 etapas, padrão de equilíbrio) — confirmado
   repetidamente, sem
   necessidade de mudança. A ideia geral do bot (monitorar + filtrar os
   melhores sinais) também foi validada pelo "monitor de mercado" que ele
   descreve usar (live #4).
7. **"Escada de fundo ascendente" — cada tempo gráfico maior forma base
   quando o tempo gráfico imediatamente abaixo entra em sobrevenda/
   sobrecompra** (1M↔1D, 1semana↔4h, 1D↔1h, 4h↔15m, 1h↔5m) — não veio de
   uma live, o Thiago descreveu direto no chat usando o BTC ao vivo como
   exemplo (alta de 58k até quase 82.5k, recuo, RSI do 4h batendo
   sobrevenda e agora retestando o fundo daquela vela, olhando pra formar
   base de fundo ascendente no semanal). **✅ IMPLEMENTADO** o primeiro
   degrau da escada (4h→semanal): `check_retest_4h` detecta o reteste
   depois do 1º toque de RSI no 4h, com stop no fundo/topo do toque
   original, alvo técnico do 4h e (quando dá) um 2º alvo no semanal, mais
   fatores extra de confluência semanal (EMA12 e Fibonacci 0.382) — 15/09/2026.
   Os outros 4 degraus da escada (1M↔1D, 1D↔1h, 15m↔4h, 5m↔1h) ainda não
   foram implementados — mesma lógica, só trocando os tempos gráficos.
8. **Classificador de bandeira de alta/baixa via Fibonacci (limite 0.382) +
   direção do volume** — live #7 (17/09/2026): bandeira de baixa exige
   correção contida até 0.382 de fib COM volume descendente e rompimentos
   sem continuidade; passar de 0.382 com volume ascendente nos rompimentos
   descaracteriza a bandeira de baixa (na prática vira bandeira de alta).
   **✅ IMPLEMENTADO** (`classifica_bandeira`, 17/09/2026) — sinal de
   contexto (status "intacta"/"invalidada"/"indefinida"), mostrado sempre na
   análise detalhada e, no status horário recorrente, só quando a leitura
   não é "indefinida" (pra não poluir a mensagem automática).
9. **RSI de 4h esticado por muitos dias seguidos (>90, semanas) como leitor
   de mudança de regime bull↔bear** — live #7 (17/09/2026): ele usa o
   histórico do RSI de 4h pra mostrar que extremos tão prolongados nunca
   acontecem durante bear market (só na virada pra bull, ex.: jan/2023).
   Mais leitura de contexto macro do que gatilho de entrada — prioridade
   baixa, mas anotado como um possível "termômetro de regime" futuro,
   parecido em espírito com o termômetro de ciclo (sinal 7).
10. **Ombro-cabeça-ombro invertido (OCOi) e clássico (OCO)** — 2 aparições
    em lives (#6 e #7) como cenário especulativo, e depois confirmado de
    forma bem concreta num sinal real do robô do próprio Diego (print
    mandado pelo Thiago em 17/09: BNB rompendo LTB no 4h "abrindo espaço
    pra formação de um OCOi no 4h"). **✅ IMPLEMENTADO** (`check_oco_pattern`,
    17/09/2026) — detecta os 3 pivôs (ombro-cabeça-ombro, cabeça claramente
    mais funda/alta e ombros parecidos) e o rompimento do pescoço, com alvo
    pela distância clássica cabeça↔pescoço e stop além do ombro mais recente.
    Cobre os dois sentidos (OCOi = fundo/alta, OCO = topo/baixa).
11. **Rompimento de linha de tendência diagonal (LTB/LTA)** — mesmo print do
    item 10 (BNB, 17/09): "começa a romper a LTB que vinha funcionando como
    resistência". Até então todo sinal de estrutura do bot só usava níveis
    horizontais (pivô, fibo, EMA) — nunca uma reta diagonal.
    **✅ IMPLEMENTADO** (`check_trendline_breakout`, 17/09/2026) — ajusta a
    reta aos dois pivôs mais distantes que ainda "seguram" o preço entre
    eles, dispara no primeiro fechamento além dela, com alvo no próximo
    pivô e stop além da linha/pivô de referência.

---

## Progresso

- Processadas: 7 de ~30+ (últimos ~2 meses) — canal tem mais de 100 lives no
  total, indo bem mais pra trás no tempo. 11/09, 10/09, 01/09, 20/08, 14/08,
  16/09 e 17/09/2026 (essas duas últimas coladas direto pelo Thiago no chat,
  sem passar por busca/navegação no canal — o Thiago passou a mandar a
  transcrição das lives diárias diretamente) — cobrindo correção/
  lateralização, disparada forte de alta, uma live mais multi-mercado, e
  duas lives "ao vivo" reagindo a notícias do dia (Clarity Act, juros dos
  EUA).
- Candidata seguinte pra buscar no canal, se o Thiago não mandar a próxima
  direto (ainda não processada): "Trade Ao Vivo! Análise do Bitcoin,
  Altcoins e Mercado Internacional!" (ncl4n0dfK1Y, ~2 meses atrás).
- 15/09/2026: implementados os 3 candidatos mais maduros até aqui — (1) sinal
  4h de primeiro toque de RSI (`check_scalp_4h`), (2) sugestão de stop zero a
  zero na memória da última operação, e (3) reteste após o 1º toque de RSI no
  4h (`check_retest_4h`, 1º degrau da "escada de fundo ascendente" que o
  próprio Thiago descreveu). A live #6 (16/09) validou diretamente os itens
  (1) e (2) sem precisar de nenhuma mudança de código. A live #7 (17/09)
  trouxe o candidato novo mais concreto até agora — classificador de
  bandeira de alta/baixa via Fibonacci 0.382 + direção do volume (item 8) —
  além de reforçar "mínima sem continuidade" pela 4ª vez e H&S invertido
  pela 2ª.
- 17/09/2026: implementado o classificador de bandeira (`classifica_bandeira`,
  item 8) — pedido explícito do Thiago, com urgência por causa de mais uma
  live no dia seguinte.
- 17/09/2026 (mesmo dia, sessão seguinte): o Thiago mandou um print de um
  sinal real do robô do Diego em BNB/4h ("bandeira de alta no 3D... começa a
  romper a LTB... pode abrir espaço pra formação de um OCOi no 4h") pra eu
  analisar e comparar com o bot. A análise expôs 2 lacunas reais — sem dados
  de 3D, e sem detecção de linha de tendência diagonal / OCO-OCOi — e o
  Thiago pediu implementação imediata dos três. **✅ IMPLEMENTADOS no mesmo
  dia**: (a) candles de 3D passaram a ser buscados pros símbolos core, com
  o classificador de bandeira rodando tanto no 4h quanto no 3D; (b)
  rompimento de LTB/LTA (`check_trendline_breakout`, item 11); (c) padrão
  ombro-cabeça-ombro clássico e invertido (`check_oco_pattern`, item 10).
  Durante a mesma sessão o Thiago também mandou dois exemplos adicionais de
  validação: um sinal de texto do robô do Diego em ETH ("rompeu a máxima do
  ano... ceu aberto, líder do ciclo confirmado", com volume de confirmação e
  alerta de risco por notícia/Fed — guardado como candidato futuro, ainda
  não implementado, ver observação abaixo) e um comentário ao vivo sobre o
  BTC reagindo à decisão do Fed que confirma na prática a lógica do 3D recém
  implementada: "quando as coisas ficarem extremamente poluídas... observe
  em tempos gráficos maiores, como no 3 dias. Bandeira de alta segue
  intacta" — validação direta do item (a) no mesmo dia em que foi
  implementado.
- Observação (candidato futuro, não implementado): o sinal de ETH acima
  ("rompimento de máxima do ano/52 semanas com volume de confirmação bem
  acima da média, stop no suporte do pullback que segurou, alvos técnicos
  em sequência") é um padrão distinto do que o bot já cobre — mais parecido
  com um "breakout com confirmação de volume" do que com qualquer sinal
  atual. Também notável: esse sinal do Diego veio com um alerta de risco
  ligado a evento macro (reunião do Fed, opções concentradas num strike) —
  o bot hoje não cruza nenhum sinal técnico com calendário de notícias/
  eventos. Os candidatos "reteste de nível rompido genérico" (item 3),
  "cruzar exaustão com os outros sinais" (item 5) e "RSI 4h como termômetro
  de regime" (item 9) seguem em aberto, junto com os 4 degraus restantes da
  escada de fundo ascendente.
- Observação de processo: as duas primeiras lives processadas eram
  basicamente a MESMA correção de BTC sendo acompanhada em dias seguidos — ou
  seja, lives vizinhas tendem a ser bem repetitivas entre si. Amostragem
  espalhada no tempo (a partir da live #3) trouxe cenários mais variados com
  menos lives processadas.
