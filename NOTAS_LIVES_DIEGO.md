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
(o bot só cobre cripto via Bybit), mas ainda traz conceitos aplicáveis.

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

### 8) Live "ao vivo" de 18/09/2026 (transcrição colada direto pelo Thiago no
chat, sem título/URL — pedido de estudar a fundo e anotar tudo, "para não
perder nada e melhorar o bot e as análises")

Contexto: continuação forte de alta no BTC rumo a novas máximas do
movimento, reforçando um mês inteiro de "compra na queda" desde 23/08. Ele
revisita vários trades já fechados (INJ, ETH, XRP, ONDO) como prova de
resultado, e acompanha ao vivo o rompimento de uma bandeira de alta no
3D/semanal em tempo real durante a própria live, além de temas de gestão de
risco/psicológico (alavancagem, "trade da vingança", segurar lucro) e um
aviso sobre um canal fake se passando por ele no Telegram.

Conceitos/técnicas que aparecem (e o que já existe ou não no bot):

- **Confirmação de rompimento de bandeira em DOIS tempos gráficos ao mesmo
  tempo (3D e semanal)** — ele acompanha o preço rompendo a mesma bandeira
  de alta simultaneamente no 3D e no semanal ao vivo, tratando isso como
  reforço mútuo (não é só o 3D confirmando, o semanal também). **→ parcialmente
  implementado**: o bot já roda `classifica_bandeira` no 4h e no 3D (feature
  de ontem), mas ainda não no semanal, apesar de já buscar `candles_w` em
  `analyze_symbol` e `build_symbol_deep_dive`. **Implementado nesta sessão**
  (ver Progresso) — passou a rodar também no semanal.

- **Zona de resistência nomeada "banho gelado"** — ele usa um apelido fixo
  pra maior zona de resistência do momento (nesse caso, ~80.500–82.800,
  entre o fundo anterior ao topo e o próprio topo), reforçando que romper
  essa zona destrava caminho livre até a próxima grande cifra redonda
  (100.000). Não é uma técnica nova — é a mesma lógica de zona de pivôs
  relevante que o bot já usa (`find_pivots`, alvo técnico nos sinais) — só
  reforça que vale destacar essa zona com mais clareza nos textos gerados
  (ex.: no "Fique de olho" ou na análise detalhada), já que é a referência
  que ele mais repete quando o preço tá subindo.

- **Cruzamento de médias (EMA) no semanal como confirmação rara de alta
  convicção** — ele menciona que esse é o primeiro cruzamento de médias no
  semanal desde 2023 (a última vez foi bem antes do início do bull market
  atual), tratando isso como um evento raro e forte o bastante pra montar
  posição pra segurar meses. **→ o bot não tem isso hoje** —
  `detect_market_trend` já cruza EMAs no diário/semanal/mensal pra decidir
  a tendência majoritária, mas não dispara um AVISO específico só quando
  esse cruzamento acabou de acontecer (é só usado como filtro de fundo,
  silencioso). Candidato novo: um sinal de contexto tipo "primeiro toque"
  (dispara só na vela em que o cruzamento acontece) pro cruzamento de EMA
  12/26 no semanal — parecido em espírito com `check_scalp_4h` (evento raro
  = alta convicção), mas pra cruzamento de médias em vez de RSI.

- **Não shortar ativo forte — procurar força relativa contra o BTC pra
  achar candidatos de short** — ele reforça (com a metáfora da corrida de
  cavalos) que não faz sentido shortar o ativo mais forte do mercado, e que
  a forma certa de procurar candidatos de short é olhar pares cotados em
  BTC (não em USDT) pra achar os ativos mais fracos que o próprio BTC. **→
  parcialmente coberto**: o filtro de tendência majoritária
  (`_alinhado_com_tendencia`) já bloqueia sinais de VENDA contra a tendência
  geral do BTC, mas o bot não tem um screener específico de "moedas mais
  fracas que o BTC" (o sinal de dominância/altseason, sinal 5, compara o
  watchlist inteiro como grupo, não teria pontuado ativos individualmente).
  Candidato de baixo/médio esforço: um ranking de performance relativa
  individual de cada moeda do watchlist contra o BTC, reaproveitando o
  `pct_return` que o sinal 5 já usa.

- **RSI esticado por muito tempo sem correção = força extrema do
  mercado, mesmo contra notícia macro (juros subindo)** — ele reforça que o
  mercado ignorando alta de juros dos EUA (que teoricamente derrubaria
  ativos de risco) e continuando a subir é evidência de força extrema.
  Reforça (3ª/4ª vez, contando a live #7) o candidato "RSI de 4h esticado
  por muitos dias = leitor de regime bull/bear" (item 9 da lista abaixo) —
  dado o quanto ele volta nesse tema, vale subir a prioridade desse
  candidato.

- **"Perda de suporte sem continuidade + volume vendedor caindo =
  exaustão da força vendedora"** — ele detalha de novo o raciocínio por
  trás da bandeira de alta (mesma lógica do classificador implementado
  ontem), agora explicando o "porquê" psicológico com mais profundidade:
  poucos vendedores restantes depois de uma explosão de alta, recuperação
  rápida em V sempre que o suporte é perdido. **Confirma novamente** (não
  muda nada) o `classifica_bandeira` já implementado.

- **Ombro-cabeça-ombro invertido confirmado num ativo real, ao vivo** —
  ele cita explicitamente um OCOi confirmado ao vivo numa altcoin. **Valida
  em produção** o `check_oco_pattern` implementado ontem.

- **Zona ideal de compra (INJ) e caso de trader que operou day trade um
  setup de swing** — dois casos que só reforçam frameworks já cobertos: a
  zona de compra ideal é a mesma lógica de zona de fibo/pullback (sinal 1),
  e o aviso de "não confunda estilo scalp vs swing" já é refletido no bot
  pelo campo `estilo` de cada sinal (SCALP tem stop apertado e é tratado
  como janela curta; SWING não). Sem ação de código.

- **Psicologia: "trade da vingança" (shortar por raiva de ter perdido a
  alta) e dificuldade de segurar lucro** — conceitos comportamentais, sem
  tradução direta em código — mais um lembrete pros textos de aviso do bot
  não incentivarem operar contra a tendência por impulso (o filtro de
  tendência já cobre isso tecnicamente).

**Resumo de candidatos a melhoria dessa live**: o mais concreto e de menor
esforço é rodar o classificador de bandeira também no semanal (já
implementado nesta sessão, ver Progresso). Os outros dois candidatos novos
— cruzamento de EMA no semanal como sinal de contexto raro, e um ranking de
força relativa individual contra o BTC pra achar candidatos de short —
ficam registrados como próximos passos, ainda não implementados. "RSI 4h
esticado por dias = regime" (item 9) ganhou mais uma confirmação forte e
deveria subir de prioridade.

---

### 9) Live "ao vivo" de 19/09/2026 (transcrição colada direto pelo Thiago no
chat, sem título/URL, ~7min — BTC se aproximando de US$ 82.000)

Contexto: vídeo curto, focado num único momento — BTC testando por baixo
uma zona de resistência formada pela fusão de um fundo anterior com um topo
anterior (~82.800–83.000), com leitura de força extrema (RSI esticado sem
corrigir) e uma tese explícita de que esse comportamento não é típico de
bear market. Ele também compara o momento atual ao cruzamento de médias no
semanal que antecedeu a virada pro bull market de 2023.

Conceitos/técnicas que aparecem (e o que já existe ou não no bot):

- **RSI esticado sem corrigir, mesmo perto de resistência forte, como sinal
  de força extrema (bear market não se comporta assim)** — reforça pela
  5ª vez (contando as lives #7 e #8) o candidato "RSI de 4h esticado por
  muitos dias = leitor de regime bull/bear" (item 9 da lista abaixo).
  **Confirma de novo**, sem mudança de código — mas com esse volume de
  confirmações (agora 3 lives seguidas citando o mesmo padrão), esse
  candidato já deveria ser tratado como prioridade alta pra virar sinal
  próprio, não só um "termômetro de contexto" passivo.

- **Zona de resistência formada pela fusão de um fundo anterior com um topo
  anterior, com alvo técnico numa faixa (95–97 mil) se romper** — mesma
  lógica de zona de pivôs relevante que o bot já usa (`find_pivots`),
  reforçando de novo (como na live #8, zona "banho gelado") que vale
  destacar esse tipo de zona combinada com mais clareza nos textos gerados.
  Sem sinal novo — já coberto conceitualmente.

- **Cruzamento de médias no semanal (EMA12/26, comparado explicitamente ao
  cruzamento de março/2023 que "destravou" o bull market atual) e o mensal
  andando acima das mesmas médias** — essa foi a informação mais importante
  técnica dessa live: ele nomeia o par de médias (12 e 26) do cruzamento que
  trata como confirmação de bull market. **🔧 CORREÇÃO IMPORTANTE**: o
  sinal `check_weekly_ema_cross`, implementado ontem (item 12) a partir da
  live #8, tinha reaproveitado por engano o par EMA50/EMA200 (o mesmo que
  `detect_market_trend` usa pra tendência majoritária) — mas o cruzamento
  que o Diego de fato acompanha é o de EMA12/26. **✅ CORRIGIDO nesta
  sessão** — `check_weekly_ema_cross` passou a usar constantes próprias
  (`WEEKLY_EMA_CROSS_FAST=12`, `WEEKLY_EMA_CROSS_SLOW=26`), independentes do
  par 50/200 que `detect_market_trend` continua usando. Efeito prático: como
  EMA12/26 cruza com bem mais frequência que EMA50/200, esse aviso vai
  disparar mais vezes do que antes — deixou de ser um evento "uma vez a cada
  vários anos" pra ser um evento raro, mas não tão raro assim.

- **Posição pessoal do apresentador (alocação/alavancagem, stop movido pro
  zero a zero) e exemplo de moeda específica com alta forte em menos de 48h
  como evidência contra a tese de bear market** — contexto/validação
  pessoal dele, sem técnica nova: a lógica de mover stop pro zero a zero já
  existe no bot (memória da última operação, item 2 da lista abaixo), e o
  exemplo de força individual reforça (sem gerar sinal novo) a ideia geral
  de força extrema de mercado já capturada pelo item 9.

- **Filosofia de realização parcial de lucro variando conforme o nível de
  alavancagem usado** — conceito de gestão de risco/psicológico, sem
  tradução direta em sinal técnico (o bot não gerencia posição alavancada
  do usuário, só analisa preço). Sem ação de código.

**Resumo de candidatos a melhoria dessa live**: nenhum sinal novo — o ganho
real foi a **correção** do sinal de cruzamento de EMA semanal (item 12,
agora EMA12/26 em vez de EMA50/200), motivada por essa live citar o par de
médias de forma explícita e comparável a um evento histórico real (o
cruzamento de 2023). "RSI 4h esticado por dias = regime" (item 9) segue
acumulando confirmações e continua como candidato de prioridade alta pra
virar sinal com peso próprio.

---

### 10) Vídeo curto colado direto pelo Thiago no chat, sem título/URL,
~5min30 (BTC rompendo US$ 85.000 em tempo real)

Contexto: vídeo de acompanhamento ao vivo do rompimento dos US$ 85.000,
com o apresentador reafirmando a tese de bull market e revisando as
posições pessoais dele (BTC, ETH, XRP). Bastante conteúdo é revisão/
validação de padrões já notados em lives anteriores — poucos conceitos
realmente novos.

Conceitos/técnicas que aparecem (e o que já existe ou não no bot):

- **Fundo ascendente confirmado no tempo gráfico de 3 meses**, segurando a
  EMA26, com rompimento de um nível técnico específico (~83.150) — e a tese
  de que, historicamente, nunca houve caso do Bitcoin confirmar esse
  rompimento no 3 meses e depois voltar a perder os fundos. É a mesma ideia
  da "tendência em 3 tempos gráficos" que o bot já usa (`detect_market_trend`,
  hoje cruzando diário+semanal+mensal), só que citando o 3 meses como leitura
  extra de "zoom out" — parecido em espírito com o 3D já implementado pra
  cenário "poluído" (ver seção correspondente no README), mas numa escala
  bem maior. Não é uma técnica nova de detecção, mais uma validação de que
  olhar tempos gráficos maiores pra confirmar a tendência de fundo é algo
  que ele faz em várias escalas, não só diário/semanal/mensal. Sem ação de
  código — não vale esticar `detect_market_trend` pra 3 meses só por causa
  de uma menção, mas fica registrado como possível 4º tempo gráfico se
  aparecer de novo em lives futuras.

- **Cruzamento de EMA12/26 confirmado, citado de novo como o mesmo tipo de
  evento que historicamente "destravou" o início do bull market** —
  reforça o item 12 (`check_weekly_ema_cross`, já corrigido pra EMA12/26 na
  live #9), sem informação nova o bastante pra saber com certeza se ele tá
  falando do cruzamento no semanal (como nas lives #8/#9) ou no 3 meses
  (tempo gráfico que ele estava olhando nesse trecho específico) — ambíguo
  pelo contexto do vídeo. Sem ação de código por enquanto; vale prestar
  atenção se uma live futura deixar claro que o cruzamento importante
  também é olhado no 3 meses, não só no semanal.

- **RSI de 4h nunca ficando muito tempo em sobrecompra durante bear
  market (só "pequenos tiros" que não sustentam), contra ficar esticado por
  muito tempo em sobrecompra como characterísitca de bull market** — é
  literalmente a mesma tese do item 9 ("RSI de 4h esticado por muitos dias
  como leitor de regime bull/bear"), agora explicada com mais detalhe
  (o contraste explícito bear vs. bull, não só "RSI esticado = força").
  Já são pelo menos 4 lives citando essa ideia (#7, #8, #9 e agora essa) —
  o candidato mais validado e ainda não implementado da lista. Nenhuma
  mudança de código nessa sessão, mas o volume de confirmações reforça que
  vale priorizar isso quando o Thiago quiser seguir com algo novo.

- **"Perda de mínima sem continuidade de queda" citada de novo**, dessa vez
  a respeito da região de 60–61 mil onde as baleias acumularam durante o
  pânico mais extremo do movimento — mais uma confirmação (já iam 4, essa é
  a 5ª) do padrão do item 6 ("mínima sem continuidade de queda = bandeira
  de alta viva"), já coberto conceitualmente pelos sinais existentes
  (bandeira, item 8). Sem ação de código.

- **Validação em tempo real do degrau 30m↔12h da escada, implementado
  ontem**: "a gente viu 30 minutos batendo um nível de sobrevenda numa
  correção durante o final de semana" — é exatamente o cenário que
  `check_retest_30m` (item 7, degrau novo de 21/09/2026) foi feito pra
  capturar: sobrevenda no 30m durante uma correção dentro de uma tendência
  de alta maior, like entrada pra quem "ficou atrasado". Validação direta
  e sem precisar de nenhuma mudança — o degrau acabou de ser implementado e
  já bate com o que ele descreve fazendo ao vivo.

- **Stop movido pro zero a zero há vários dias, como parte da gestão de
  risco da posição** — reforça de novo (sem mudança) o item 2, já
  implementado desde 15/09/2026.

- **Filosofia de gerenciamento**: "errar e não reconhecer o erro é o pior
  erro", buscar novas entradas mesmo depois de ter perdido o movimento
  inicial (ex.: sobrevenda no 30m/1h como "última oportunidade" pra quem
  ficou de fora), e a matemática de R:R por trás de "quem tá errado não
  perde nada, quem apostou contra perde o início do bull market" — filosofia
  de gestão/psicológica, sem tradução direta em sinal técnico novo. Mesmo
  tipo de conteúdo não-acionável já visto nas lives #2, #3 e #9.

**Resumo de candidatos a melhoria dessa live**: nenhum sinal novo pra
implementar — foi, na prática, uma live de validação. O destaque real é a
**validação em tempo real do degrau 30m↔12h** implementado ontem
(`check_retest_30m`), e mais uma (a 4ª) confirmação do candidato "RSI 4h
esticado por dias = regime" (item 9), que segue como o candidato mais
maduro ainda sem implementação — vale perguntar ao Thiago se ele quer
seguir com esse quando tiver uma folga.

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
   apareceu em 2 lives (#1 e #5). **✅ IMPLEMENTADO**
   (`check_retest_broken_level`, 22/09/2026) — varre os pivôs horizontais
   mais recente primeiro, procurando o rompimento decisivo mais recente
   (fechamento a pelo menos 1,5% além do nível) que ainda "segura" do lado
   novo por pelo menos 2 candles sem fechar de volta do lado antigo
   (`_find_nivel_rompido_segurando`); dispara quando o preço volta a
   retestar exatamente esse nível sem romper de novo, com stop logo além
   dele. Diferente da escada de fundo ascendente (item 7, que exige toque
   de RSI extremo) e do LTB/LTA (item 11, reta diagonal, não nível
   horizontal). Roda no 4h.
4. **`avoid_round_number_stop` confirmado** — nada a mudar, só validado.
5. **Exaustão recente devia reduzir a convicção de sinais de compra** — apareceu
   em 2 lives (#2 e #3) de formas diferentes (ZEC com rompimento sem
   continuidade, ouro pós-clímax) — candidato de refinamento pra cruzar o sinal
   2 (exaustão) com os outros sinais de COMPRA/VENDA em vez de tratá-los como
   independentes. **✅ IMPLEMENTADO** (`adiciona_alerta_exaustao`,
   22/09/2026) — mesmo padrão de pós-processamento de `adiciona_plano_b`/
   `adiciona_referencia_ema200_diaria`: quando o RSI de 4h já está esticado
   perto (ou dentro) da zona de exaustão de topo/fundo, acrescenta uma linha
   de alerta (⚠️) em `detalhes` de qualquer sinal COMPRAR/VENDER na direção
   contrária, reduzindo a convicção sem mudar ação/entrada/stop/alvo.
   Reaproveita os mesmos limiares do clímax de exaustão (`CLIMAX_RSI_HIGH`/
   `CLIMAX_RSI_LOW`, `EXHAUSTION_DIAG_RSI_BAND`, `CLIMAX_VOLUME_RATIO`).
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

   **Reformulação complementar (21/09/2026)**, também do próprio Thiago, não
   de nenhuma live: "em tendência de alta as melhores entradas são sempre em
   fundos ascendentes em tempos gráficos maiores — se um tempo gráfico menor
   perder o último fundo (fundo descendente), é porque algum tempo gráfico
   maior está buscando sua própria base." É a mesma escada, só descrita "de
   cima pra baixo": em vez de olhar o tempo menor tocando RSI extremo e
   confirmar a base do tempo maior (como o item 7 original e o comentário do
   grupo do Diego sobre 4h↔15m — ver Progresso 21/09), essa formulação
   parte do sintoma inverso (estrutura do tempo menor quebrando) pra
   perguntar qual tempo gráfico de cima está em correção. O mais próximo que
   o Diego já disse nas lives processadas até agora é o princípio de
   tendência multi-tempo-gráfico ("nunca shortar um ativo em alta em todos
   os tempos gráficos", já implementado em `detect_market_trend`) — não a
   formulação específica de "fundo descendente = sintoma de base maior em
   formação". **✅ IMPLEMENTADO** (`diagnose_fundo_descendente_busca_base`,
   22/09/2026) — reaproveita o mesmo mapeamento menor→maior dos degraus da
   escada (`_ESCADA_MAPA_MENOR_MAIOR`), olhando o sintoma inverso: quando o
   fundo mais recente de um tempo gráfico menor é mais baixo que o pivô de
   fundo anterior (fundo descendente, quebrando a estrutura ascendente), o
   diagnóstico aponta qual tempo gráfico maior provavelmente está buscando
   base. Não é sinal de entrada — é diagnóstico de contexto (mesmo formato
   dos outros `diagnose_*`), rodando sobre 4h, 15m, 1h e 1D.

   **✅ IMPLEMENTADOS mais 3 degraus (21/09/2026)**: 15m↔4h (motivado por um
   comentário do grupo do Diego sobre correção no 4h abrindo entrada via
   sobrevenda no 15m, esperando novas bases do 4h pra seguir com rompimento
   de topo), 30m↔12h e 2h↔2D (pedido direto do Thiago). A lógica de
   `check_retest_4h` virou genérica (`_check_retest_ladder`), com
   `check_retest_4h`/`check_retest_15m`/`check_retest_30m`/`check_retest_2h`
   como wrappers finos — mesmo comportamento, só troca o par de tempos
   gráficos e os limiares de RSI. Precisou de suporte a mais intervalos na
   Bybit: "30m"/"2h"/"12h" mapeiam direto, e "2D" (sem intervalo nativo)
   passou a reaproveitar a mesma agregação de candles diários que já
   existia só pro "3D" (`_fetch_klines_dias_agregados`, generalizada de
   `_fetch_klines_3d_agregado`).

   **✅ IMPLEMENTADOS os 3 degraus restantes (22/09/2026)**: 5m↔1h, 1h↔1D e
   1D↔mensal (`check_retest_5m`/`check_retest_1h`/`check_retest_1d`) —
   completando a escada inteira. Uma checagem nesse dia revelou que a nota
   acima ("os degraus 1M↔1D e 1D↔1h ainda não foram implementados") estava
   incompleta: faltavam 3 degraus, não 2 — o 5m↔1h nunca tinha sido feito
   (só existia o sinal de 1º toque sem reteste, `check_scalp_5m`), erro que
   ficou documentado direto no código como correção.
8. **Classificador de bandeira de alta/baixa via Fibonacci (limite 0.382) +
   direção do volume** — live #7 (17/09/2026): bandeira de baixa exige
   correção contida até 0.382 de fib COM volume descendente e rompimentos
   sem continuidade; passar de 0.382 com volume ascendente nos rompimentos
   descaracteriza a bandeira de baixa (na prática vira bandeira de alta).
   **✅ IMPLEMENTADO** (`classifica_bandeira`, 17/09/2026) — sinal de
   contexto (status "intacta"/"invalidada"/"indefinida"), mostrado sempre na
   análise detalhada e, no status horário recorrente, só quando a leitura
   não é "indefinida" (pra não poluir a mensagem automática). Roda no 4h e
   no 3D desde 17/09; **desde 18/09 roda também no semanal**, depois da live
   #8 mostrar ao vivo o rompimento da mesma bandeira confirmando ao mesmo
   tempo no 3D e no semanal.
9. **RSI de 4h esticado por muitos dias seguidos (>90, semanas) como leitor
   de mudança de regime bull↔bear** — live #7 (17/09/2026): ele usa o
   histórico do RSI de 4h pra mostrar que extremos tão prolongados nunca
   acontecem durante bear market (só na virada pra bull, ex.: jan/2023).
   Reforçado de novo na live #8 (18/09/2026), agora ligando isso ao mercado
   ignorando a alta de juros dos EUA como evidência de força extrema, na
   live #9 (19/09/2026) e no vídeo #10 (22/09/2026, "pequenos tiros" em
   bear market vs. sustentação longa em bull) — 4 confirmações ao todo.
   **✅ IMPLEMENTADO** (`check_regime_rsi_4h_esticado`, 22/09/2026) — sinal
   de contexto/regime (`MACRO`/`OBSERVAR`, símbolo `"MERCADO"`, mesmo
   padrão do sinal de dominância): só dispara quando o RSI de 4h do BTC já
   está no território mais extremo (80/20, `REGIME_RSI4H_OVERBOUGHT`/
   `REGIME_RSI4H_OVERSOLD`) E ficou sustentado (sem resetar abaixo/acima do
   70/30 clássico) por pelo menos `REGIME_RSI4H_MIN_CANDLES` (42 candles de
   4h, ~7 dias) — a contagem de sustentação é o que distingue um "pequeno
   tiro" isolado (não confirma nada) de uma sequência de verdade. Espelha a
   mesma lógica pro lado de baixa (sobrevenda sustentada = regime de
   fraqueza/bear) por simetria, já que ele só deu exemplo do lado de alta.
   Nova função auxiliar `_compute_rsi_series` (devolve a série inteira de
   RSI, não só o valor mais recente) reutilizável por qualquer sinal futuro
   que precise de histórico de RSI.
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
12. **Cruzamento de EMA no semanal como sinal de contexto raro** — live #8
    (18/09/2026): primeiro cruzamento de médias no semanal desde 2023,
    tratado como evento raro de alta convicção pra montar posição de meses.
    **✅ IMPLEMENTADO** (`check_weekly_ema_cross`, 18/09/2026) — mesmo padrão
    de "primeiro toque" já usado em outros sinais; sinal de contexto raro,
    sem repetir na vela seguinte ao cruzamento. **🔧 CORRIGIDO em 19/09/2026**
    (live #9): a implementação original reaproveitou por engano o par
    EMA50/EMA200 (mesmo par de `detect_market_trend`), mas a live #9 deixou
    explícito que o cruzamento que o Diego de fato acompanha nesse contexto
    é o de **EMA12/26** no semanal — par próprio e independente, via novas
    constantes `WEEKLY_EMA_CROSS_FAST`/`WEEKLY_EMA_CROSS_SLOW` (12/26), sem
    mexer no EMA50/200 que `detect_market_trend` continua usando pra
    tendência majoritária.
13. **Ranking de força relativa individual contra o BTC (screener de
    short)** — live #8 (18/09/2026): pra achar candidatos de short, ele não
    olha o ativo isoladamente, olha o par cotado em BTC pra achar quem tá
    mais fraco que o próprio BTC. **✅ IMPLEMENTADO** um primeiro passo
    (`rank_relative_weakness_vs_btc`, 18/09/2026) — reaproveita os retornos
    em USDT que o sinal 5 (dominância/altseason) já calcula pra rankear
    cada moeda individualmente contra o retorno do BTC no mesmo período
    (screener de contexto, não é o gráfico do par BTC ainda — ver item 14).
14. **Achar candidatos fortes analisando o PAR CONTRA BTC de verdade**
    (não só diferença de retorno em USDT) — pedido direto do Thiago em
    18/09/2026, cobrando a mesma lógica do item 13 só que pro lado
    contrário (achar altcoin forte pra comprar, não fraca pra vender): "vai
    ter que analisar contra o par BTC como ele sempre faz" — ou seja, rodar
    os checks de estrutura DIRETO no candle do par `{MOEDA}BTC`, igual o
    item 13 descreve o canal fazendo, em vez de só comparar % de retorno em
    USDT. **✅ IMPLEMENTADO** (`find_altcoin_do_dia`, 18/09/2026) — a
    "altcoin do dia" (ver README) converte cada altcoin do watchlist pro
    par contra BTC, roda pullback/LTA/OCOi direto nesse par, usa a bandeira
    (item 8) como confirmação extra, e escolhe uma recomendação de estudo
    por dia com o melhor risco/retorno.
15. **OCOi/OCO "em formação" (ombro 1 + cabeça já prontos, ombro 2 ainda se
    formando, pescoço ainda não rompido)** — análise de uma operação real do
    robô do Diego em MANTA (19/09/2026, gráfico de 4h com uma projeção
    desenhada à mão do ombro 2 e do pescoço esperado). **✅ IMPLEMENTADO**
    (`diagnose_oco_pattern`, 19/09/2026) — versão "quase lá" do
    `check_oco_pattern` (mesmo espírito do `diagnose_confluence`), cobrindo
    dois estágios: (a) os 3 pivôs já prontos mas o pescoço ainda não
    rompeu (reaproveita `_find_oco_estrutura` direto), e (b) só ombro 1 +
    cabeça confirmados, com o preço já recuperando de volta pra dentro da
    faixa onde o ombro 2 precisaria se formar. Só dispara quando o preço já
    está a até `OCO_DIAG_MAX_NECKLINE_DIST_PCT` (8%) do nível do pescoço,
    plugado tanto no fluxo normal (`analyze_symbol`) quanto na análise
    detalhada (`build_symbol_deep_dive`).
16. **Screener de "moedas atrasadas" (candidatas a compra por rotação/
    catch-up)** — mesma live/análise de MANTA: o próprio texto do robô do
    Diego chama a moeda de "atrasada em relação a várias outras que já
    tiveram movimentos mais fortes", tratando isso como parte da tese de
    compra (rotação de capital ainda por vir). **✅ IMPLEMENTADO**
    (`rank_moedas_atrasadas`, 22/09/2026) — espelho do item 13
    (`rank_relative_weakness_vs_btc`) pro lado comprado: em vez de rankear
    moedas mais fracas que o BTC (short), rankeia moedas que subiram menos
    que a média do grupo de altcoins do watchlist, só durante tendência de
    alta confirmada (`market_trend == "alta"`, sem sugerir "atrasada" num
    mercado de baixa geral). Reaproveita os mesmos retornos que os sinais
    5/13 já calculam. Sinal de contexto/screener (`OBSERVAR`), sem
    entrada/stop/alvo.
17. **Cunha descendente (falling wedge) na base, no par contra BTC, como
    setup de rotação de capital** — análise real de uma operação do robô do
    Diego em VIRTUAL (colada pelo Thiago em 22/09/2026, print do
    VIRTUALUSDT no TradingView + texto do robô): no par VIRTUALBTC (não no
    USDT — ver observação abaixo), o preço está "na base de uma cunha
    descendente", com a tese de que, quando o BTC encontrar um topo e
    começar a lateralizar, a dominância dele (subindo no momento) deve
    voltar a corrigir, beneficiando VIRTUAL com entrada de capital
    rotacional. Entrada na região atual, stop abaixo de 0,57 (base do
    semanal), alvos acima do pivô de alta do semanal, condicionados ao
    rompimento de 0,86 primeiro. Candidato de 2 partes — **ambas
    ✅ IMPLEMENTADAS em 22/09/2026**:

    (a) **Detecção de cunha genérica** (`check_wedge_pattern`, +
    `_fit_channel_line`, uma generalização do `_fit_trendline` que não força
    o sentido da inclinação, necessária porque as duas retas de uma cunha
    podem inclinar no MESMO sentido). Exige as duas retas (topo via
    pivot_highs, fundo via pivot_lows) inclinando no mesmo sentido e
    convergindo de verdade (a distância entre elas precisa encolher pelo
    menos `WEDGE_MIN_CONVERGENCE_PCT`, 35%, do início pro fim do trecho
    comum — senão é só um canal paralelo). Cunha descendente (as duas caem)
    dispara `COMPRAR` no rompimento da reta superior; cunha ascendente (as
    duas sobem) dispara `VENDER` no rompimento da inferior — cobre os dois
    sentidos, não só o descendente do exemplo original. Reaproveita os
    mesmos limiares de toque/rompimento/stop do LTB/LTA (item 11). Roda no
    4h.

    (b) **Aviso antecipado de rotação** (`check_rotacao_antecipada_dominancia`,
    22/09/2026) — cruza a exaustão do PRÓPRIO BTC no 4h (RSI perto/dentro da
    zona de clímax de topo, mesmos limiares do sinal 2/exaustão) com o
    cenário de a divergência de dominância AINDA NÃO ter aparecido nos
    retornos dos últimos `DOMINANCE_LOOKBACK_DAYS` dias — se já tivesse
    aparecido, o sinal de dominância/altseason (item 5, reativo) já teria
    disparado sozinho, o que tornaria esse aqui redundante (por isso só
    dispara quando o reativo não dispararia). Sinal de contexto/screener
    (`OBSERVAR`), calculado uma vez por rodada de varredura completa.

**Observação**: o texto do robô do Diego fala do par **VIRTUALBTC**
("no par com o BTC"), mas o print que o Thiago mandou é do **VIRTUALUSDT**
(perpétuo) — provavelmente só o gráfico que ele tinha aberto na hora, não
o par que embasou a análise. Vale ter isso em mente: o preço/EMAs/RSI
visíveis no print (0,7261, RSI(4) neutro por volta de 50-55) são do par
USDT, não necessariamente batem com a leitura técnica feita no par BTC que
o texto descreve.

**Observação**: a mesma análise de MANTA também reforça, sem exigir código
novo, dois comportamentos já implementados — o filtro de risco/retorno (o
próprio robô do Diego evita perseguir o preço atual por causa de R:R ruim,
mesma filosofia do `MIN_REWARD_RISK_RATIO`) e o stop com margem além de
nível redondo (`avoid_round_number_stop`, "evitar uma simples varrida do
suporte"). O gráfico diário mostrado pelo Thiago também confirma
visualmente a correção de EMA12/26 feita hoje (item 12): as próprias EMAs
12 e 26 do TradingView aparecem quase coladas (0,05944 vs 0,05939) prestes
a cruzar, e a EMA200 diária (0,07375) bate exatamente com a zona de alvo
intermediário ("0,073–0,075 — região da EMA 200 diária") que o robô do
Diego citou — ou seja, ele usa EMA200 diária como referência explícita de
alvo. **✅ IMPLEMENTADO** (`adiciona_referencia_ema200_diaria`,
19/09/2026) — sem virar critério de entrada nem mudar o alvo calculado por
nenhum sinal, acrescenta uma linha em `detalhes` citando a EMA200 diária
sempre que ela cair entre o preço de entrada e o alvo técnico de qualquer
sinal COMPRAR/VENDER, tanto no fluxo normal quanto na análise detalhada.
Efeito colateral técnico: os candles diários buscados por `analyze_symbol`/
`build_symbol_deep_dive` passaram de 200 pra `MARKET_TREND_EMA_SLOW + 20`
(220) — com exatamente 200 candles o "EMA200" virava só a média simples da
janela inteira, sem nenhuma iteração de convergência exponencial de
verdade (mesmo ajuste de folga que `detect_market_trend` já usa pro BTC).

O item 16 (screener de moedas atrasadas/rotação pro lado comprado) foi
implementado em 22/09/2026 — ver acima.

---

## Progresso

- Processadas: 10 de ~30+ (últimos ~2 meses) — canal tem mais de 100 lives no
  total, indo bem mais pra trás no tempo. 11/09, 10/09, 01/09, 20/08, 14/08,
  16/09, 17/09, 18/09, 19/09 e 22/09/2026 (a partir da #6, todas coladas direto
  pelo Thiago no chat, sem passar por busca/navegação no canal — passou a
  mandar a transcrição das lives diárias diretamente) — cobrindo correção/
  lateralização, disparada forte de alta, uma live mais multi-mercado, quatro
  lives "ao vivo" reagindo a notícias/preço do dia (Clarity Act, juros dos
  EUA, resistência dos 82 mil, rompimento dos 85 mil).
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
- Observação — candidato do sinal de ETH acima ("rompimento de máxima do
  ano/52 semanas com volume de confirmação bem acima da média, stop no
  suporte do pullback que segurou, alvos técnicos em sequência"), um padrão
  distinto do que o bot já cobria na época — mais parecido com um "breakout
  com confirmação de volume" do que com qualquer sinal que existia até
  então. **✅ IMPLEMENTADO** (`check_breakout_maxima_periodo_volume`,
  22/09/2026) — usa candles diários dos últimos `BREAKOUT_MAXIMA_LOOKBACK_DIAS`
  (365, ~52 semanas); dispara no primeiro fechamento que rompe de forma
  decisiva a máxima do período, exigindo volume da vela de rompimento pelo
  menos `BREAKOUT_MAXIMA_VOLUME_RATIO` (1,8x) a média do período; stop no
  pivô de fundo mais recente antes do rompimento (o "suporte do pullback
  que segurou" do sinal original); alvos projetados por distância medida
  (altura do pullback até a máxima rompida, com uma 2ª extensão em 1,618x),
  já que por definição não existe resistência histórica real acima de uma
  nova máxima de período. Só cobre o lado de compra — é exatamente o padrão
  do sinal original; um espelho pro lado de venda ficaria especulativo sem
  um exemplo real equivalente pra validar.

  Também notável: esse sinal do Diego veio com um alerta de risco ligado a
  evento macro (reunião do Fed, opções concentradas num strike) — o bot
  **não** cruza nenhum sinal técnico com calendário de notícias/eventos
  agendados (decisão consciente, avaliada e não implementada em 22/09/2026:
  falta uma fonte de dados gratuita e confiável de calendário econômico —
  reuniões de Fed, CPI etc. — que valesse a pena integrar; diferente do
  contexto de guerra BTC x petróleo, que é notícia via NewsAPI, já
  integrada por outro motivo, não calendário agendado). Documentado como
  lacuna consciente, não esquecida.
- Observação de processo: as duas primeiras lives processadas eram
  basicamente a MESMA correção de BTC sendo acompanhada em dias seguidos — ou
  seja, lives vizinhas tendem a ser bem repetitivas entre si. Amostragem
  espalhada no tempo (a partir da live #3) trouxe cenários mais variados com
  menos lives processadas.
- 18/09/2026: processada a live #8 (transcrição colada direto pelo Thiago),
  trazendo bastante conteúdo novo. Implementados no mesmo dia: bandeira
  (item 8) passou a rodar também no semanal, além do 4h/3D já existentes;
  cruzamento de EMA50/EMA200 no semanal (item 12, `check_weekly_ema_cross`);
  e um primeiro ranking de força relativa individual contra o BTC (item 13,
  `rank_relative_weakness_vs_btc`, ainda em cima de retorno % em USDT).
- 18/09/2026 (mesmo dia, sessão seguinte): pedido de mudança de agenda e de
  uma recomendação diária de altcoin. O Thiago perguntou por que não tinha
  recebido sinal num dia (resposta: comportamento normal do cron/tolerância
  de horário, não é bug) e pediu pra (1) checar o mercado em 8 horários
  fixos no horário da Irlanda (03:00, 06:00, 13:30, 14:40, 18:45, 19:30,
  20:40, 22:00), (2) ficar quieto quando não é sinal de verdade nesses
  horários, e (3) escolher uma altcoin por dia entre as ~50 maiores pra
  mandar como recomendação de estudo. Depois de eu confirmar fuso (horário
  da Irlanda) e critério (reaproveitar o que o bot já tem), o Thiago ainda
  refinou duas vezes: (a) restringir a varredura a ~50 moedas de maior
  market cap, filtrando pra UMA recomendação só; e (b) o ponto mais
  importante — a análise tem que rodar no **par contra BTC** (ex.: SOLBTC),
  não em % de retorno contra USDT, "do jeito que ele sempre faz" (item 14,
  mesma lógica do item 13 só que pro lado comprado). **✅ IMPLEMENTADO no
  mesmo dia**: (a) os 8 horários viraram `REPORT_TIMES_DUBLIN`, calculados
  com `zoneinfo` (Europe/Dublin) pra já lidar sozinho com a troca de
  horário de verão/inverno da Irlanda, com o cron do GitHub Actions rodando
  a cada 5 minutos só pra conseguir cair certo nesses horários; (b) modo
  silencioso — status core e relatório categorizado só mandam mensagem nos
  horários extra (fora da hora cheia) quando tem sinal de verdade em algo;
  (c) `find_altcoin_do_dia` — varre o watchlist convertendo cada altcoin
  pro par contra BTC de verdade, roda pullback/LTA/OCOi nesse par, usa a
  bandeira como confirmação extra, escolhe uma recomendação por dia com
  dedup via mensagem fixada no Telegram (mesma técnica já usada pra memória
  da última operação, sem precisar de nenhum estado salvo no repositório).
- 18/09/2026 (mesmo dia, terceira sessão): mudança de infraestrutura, não de
  conteúdo de live — o Thiago pediu pra trocar a fonte de dados de Binance
  pra Bybit, porque é onde ele opera de verdade. **✅ IMPLEMENTADO** — toda
  a busca de candle e o ranking de volume do watchlist agora vêm da API
  pública v5 da Bybit (`_bybit_get`, `fetch_klines`, `fetch_top_usdt_symbols`),
  isolados do resto do bot (nenhum sinal precisou mudar). Dois ajustes
  técnicos por causa da troca: o tempo gráfico de 3D (que a Bybit não tem
  nativo) passou a ser montado agregando 3 candles diários; e o histórico
  semanal/mensal ficou mais curto (Bybit tem spot só desde ~2021, contra
  2017 da Binance), o que deixa o EMA200 semanal com menos folga — ainda
  deve funcionar, só com menos margem.
- 18/09/2026 (mesmo dia, quarta sessão): o Thiago perguntou por que o bot
  não achava os pares MSTRUSDT e CLUSDT. Pesquisei e descobri o motivo: os
  dois só existem como **contrato perpétuo** na Bybit (categoria `linear`),
  não como par spot — o bot só buscava em `spot`. Perguntei se ele queria
  que eu adicionasse suporte a isso e ele confirmou. **✅ IMPLEMENTADO** —
  `fetch_klines` agora decide a categoria (spot ou linear) por símbolo via
  `BYBIT_LINEAR_ONLY_SYMBOLS`, e `MSTRUSDT`/`CLUSDT` (MicroStrategy e
  petróleo WTI) entraram em `CORE_SYMBOLS`, então passam a ter status de
  hora em hora, "fique de olho", memória da última operação e entram no
  relatório categorizado igual BTC/ETH — mesma mecânica de sempre, o preço
  é que muda de instrumento. Corrigidos de paralelo alguns lugares que
  tinham "BTC/ETH" fixo no código (`_build_btc_eth_lines`, texto da memória
  fixada) pra usar `CORE_SYMBOLS` de verdade, senão os dois ativos novos
  ficariam de fora dessas telas mesmo estando na lista.
- 19/09/2026: processada a live #9 (transcrição curta, ~7min, colada direto
  pelo Thiago, sem título/URL) sobre o BTC testando a resistência dos ~82
  mil. Reforçou pela 5ª vez o candidato "RSI 4h esticado por dias = regime"
  (item 9) e, mais importante, expôs uma **correção necessária** num sinal
  já implementado: o cruzamento de EMA no semanal (item 12,
  `check_weekly_ema_cross`, implementado ontem a partir da live #8) tinha
  usado por engano o par EMA50/EMA200, mas a live #9 citou explicitamente
  que o cruzamento que o Diego acompanha nesse contexto é o de **EMA12/26**
  (comparando ao cruzamento de março/2023 que precedeu o bull market atual).
  **✅ CORRIGIDO no mesmo dia** — novas constantes `WEEKLY_EMA_CROSS_FAST`
  (12) e `WEEKLY_EMA_CROSS_SLOW` (26), independentes do par 50/200 que
  `detect_market_trend` continua usando pra tendência majoritária; o rótulo
  "golden cross"/"death cross" no texto do sinal ficou restrito a quando o
  par configurado é de fato 50/200 (evita nomear errado um cruzamento de
  EMA12/26 com um termo que tecnicamente é do par 50/200). Efeito colateral
  esperado: como EMA12/26 cruza bem mais vezes que EMA50/200, esse aviso vai
  aparecer com mais frequência do que antes — o Thiago deve notar isso nas
  próximas semanas. Suíte de 21 testes automatizados re-rodada sem
  regressões (incluindo o teste específico desse sinal, que já era
  genérico o bastante pra não depender do par de EMA exato).
- 19/09/2026 (mesmo dia, sessão seguinte): o Thiago mandou uma operação real
  do robô/bot do próprio Diego em MANTA (texto de análise + 2 gráficos, 1D
  e 4h) pra eu estudar e ver o que dava pra acrescentar ao bot. Análise:
  moeda "atrasada" numa grande zona de acumulação (0,050–0,065), R:R ruim
  no preço atual, plano de 3 entradas escalonadas em correções mais
  profundas (cada uma condicionada a sobrevenda no 5/15min), stop
  estrutural com folga além de nível redondo, e 3 alvos em sequência (topo
  da acumulação, depois EMA200 diária, depois extensão da lateralização).
  O gráfico de 1D confirmou visualmente a zona de acumulação e a EMA200
  diária batendo com o alvo intermediário citado; o gráfico de 4h mostrou
  uma projeção desenhada à mão de um OCOi ainda em formação (ombro 1 +
  cabeça prontos, ombro 2/pescoço ainda por vir). Nenhum código novo
  implementado ainda — a análise virou os candidatos 15 (OCOi/OCO "em
  formação", diagnóstico tipo `diagnose_confluence`) e 16 (screener de
  moedas atrasadas/rotação pro lado comprado, espelho do item 13) acima,
  além de validar de novo (sem mudança) o filtro de risco/retorno, o stop
  com folga de nível redondo, e expor que o bot não usa EMA200 diária como
  nível de alvo projetado (só como filtro de tendência/contexto) — ver
  observação acima.
- 19/09/2026 (mesmo dia, sessão seguinte): o Thiago escolheu priorizar 2 dos
  3 candidatos concretos da análise de MANTA — diagnóstico de OCOi/OCO em
  formação (item 15) e EMA200 diária como alvo projetado — deixando de fora,
  por enquanto, o screener de moedas atrasadas (item 16). **✅ IMPLEMENTADOS
  no mesmo dia**: (a) `diagnose_oco_pattern` — cobre os dois estágios "quase
  lá" descritos no item 15, plugado em `analyze_symbol` e
  `build_symbol_deep_dive`; (b) `adiciona_referencia_ema200_diaria` — cita a
  EMA200 diária em `detalhes` sempre que ela cair entre a entrada e o alvo
  de qualquer sinal, sem virar critério de entrada nem mudar o alvo
  calculado; como efeito colateral, o EMA200 diário usado em
  `analyze_symbol`/`build_symbol_deep_dive` passou a ter 20 candles de
  folga (220 no total), porque com exatamente 200 o cálculo virava só a
  média simples da janela (sem convergência exponencial de verdade) — mesmo
  ajuste que `detect_market_trend` já usa pro BTC. Testes novos escritos
  cobrindo os dois estágios do diagnóstico de OCO (inclusive confirmando
  que `check_oco_pattern` continua None enquanto o diagnóstico dispara,
  sem sobreposição) e os casos de EMA200 dentro/fora do range e
  candles/sinal incompletos; suíte completa (22 arquivos agora) re-rodada
  sem regressões.
- 21/09/2026: o Thiago colou um comentário do Diego no grupo dele sobre a
  correção no 4h liberando entradas com 15m em sobrevenda "esperando que
  sejam novas bases do 4h" — validação direta e não solicitada do 2º degrau
  da escada de fundo ascendente (item 7), até então só descrito, nunca
  implementado. Na sequência, o Thiago pediu explicitamente mais 3 degraus:
  30m↔12h ("o fundo ascendente no 12H ocorre normalmente quando o 30 min
  entra em sobrevenda") e 2h↔2D ("o fundo ascendente do 2D ocorre quando o
  2h entra em nível de sobrevenda no RSI"), junto com suporte a 12H/2D como
  tempos gráficos observados pelo bot. **✅ IMPLEMENTADOS no mesmo dia**: o
  `check_retest_4h` original foi generalizado num núcleo único
  (`_check_retest_ladder`), com 4 degraus agora ativos —
  `check_retest_4h` (4h↔semanal), `check_retest_15m` (15m↔4h, motivado pelo
  comentário do Diego), `check_retest_30m` (30m↔12h) e `check_retest_2h`
  (2h↔2D), todos plugados em `analyze_symbol` e `build_symbol_deep_dive`.
  Suporte de tempo gráfico estendido na Bybit (30m/2h/12h nativos) e a
  agregação sintética de 3D generalizada pra também servir o 2D
  (`_fetch_klines_dias_agregados`, parametrizada por número de dias). Um
  teste com múltiplos tempos gráficos e sementes fixas de aleatoriedade
  revelou um caso real de inconsistência ainda não coberto pelo filtro de
  qualidade — um sinal de reteste podia disparar com o preço já do lado
  errado do nível tocado originalmente (ex.: compra com o preço já abaixo
  do fundo), produzindo internamente `stop > entrada`; corrigido com uma
  checagem de lado explícita em `_check_retest_ladder`, sem afetar o
  comportamento do degrau original (4h↔semanal), que segue idêntico.
  Suíte completa re-rodada sem regressões (23 arquivos).
- 21/09/2026 (mesmo dia, sessão seguinte): o Thiago pediu que, sempre que o
  BTC cair e o petróleo subir ao mesmo tempo, o bot busque notícia de
  contexto sobre a guerra — pedido feito logo depois de ele relatar rumores
  de escalada (ataques dos EUA no Irã, Houthis atacando aeroporto na
  Arábia Saudita, Arábia Saudita saindo do mBridge chinês), a maior parte
  confirmada por pesquisa externa na hora. **✅ IMPLEMENTADO no mesmo dia**:
  `detect_queda_btc_alta_petroleo` dispara quando o retorno de 1 dia do BTC
  cai pelo menos 0,5% e o do petróleo (`CLUSDT`) sobe pelo menos o mesmo
  tanto (mesmo `pct_return` já usado noutros pontos do bot); quando
  dispara, `fetch_war_news_headlines` busca manchetes no NewsAPI.org por
  palavras-chave de guerra (Irã/Israel/Houthis/Arábia Saudita/Iêmen), e
  `build_war_news_context_texto` traduz e formata o texto, anexado ao
  status core de hora em hora — não é sinal de trade, é só contexto.
  Reaproveita a mesma chave `NEWS_API_KEY` já usada no fallback de
  manchetes da Reuters. Teste novo cobrindo a lógica de disparo (incluindo
  o limite exato e candles insuficientes) e o fetch/formatação com mock do
  NewsAPI; suíte completa re-rodada sem regressões (24 arquivos).
- Também em 21/09/2026: o Thiago descreveu, com as próprias palavras, uma
  reformulação "de cima pra baixo" da escada de fundo ascendente (se um
  tempo gráfico menor perde o último fundo, é sinal de que algum tempo
  gráfico maior ainda está procurando a própria base) e perguntou se o
  Diego já tinha comentado isso em algum vídeo processado. Resposta
  honesta depois de checar as 9 lives já processadas: essa formulação
  específica **não** foi encontrada atribuída ao Diego — é uma
  reformulação do próprio Thiago em cima do item 7, que já vinha só do
  Thiago desde 15/09. O mais próximo que o Diego de fato diz nos vídeos é
  o princípio de alinhamento de tendência multi-tempo-gráfico (ver item
  "Tendência em 3 tempos gráficos" no README, `detect_market_trend`).
  Guardada no item 7 como candidato futuro (diagnóstico de "qual tempo
  gráfico está buscando sua base agora"), ainda não implementado.
- 22/09/2026: processado o vídeo #10 (curto, ~5min30, colado direto pelo
  Thiago, sem título/URL), sobre o rompimento dos US$ 85.000. Sessão
  majoritariamente de validação, sem nenhum sinal novo pra implementar:
  destaque real foi a confirmação, em tempo real, do degrau 30m↔12h da
  escada (`check_retest_30m`) implementado só um dia antes ("30 minutos
  batendo sobrevenda numa correção de final de semana" bate exatamente com
  o cenário que o sinal foi feito pra capturar), além de mais uma (a 4ª)
  confirmação do candidato ainda não implementado "RSI 4h esticado por dias
  como leitor de regime bull/bear" (item 9) e mais uma (a 5ª) do padrão
  "mínima sem continuidade de queda" (item 6, já coberto). Nenhuma mudança
  de código nesta sessão.
- 22/09/2026 (mesmo dia, sessão seguinte): perguntado se o bot já tinha mais
  algum candidato não implementado, respondi com a lista (itens 3, 5, os 2
  degraus restantes da escada, item 9, item 16, e os 2 candidatos soltos de
  rompimento de máxima com volume/calendário macro), e o Thiago confirmou
  implementar o item 9 agora. **✅ IMPLEMENTADO**
  (`check_regime_rsi_4h_esticado` + `_compute_rsi_series`, 22/09/2026) — ver
  detalhe completo no item 9 acima. Teste novo cobrindo a série de RSI
  ponto a ponto, o regime de força (bull) e de fraqueza (bear) sustentados,
  o cenário de "pequeno tiro" isolado (RSI cruza o limiar de entrada mas
  sem sustentação suficiente — não deveria confirmar regime, e não
  confirmou) e RSI neutro/candles insuficientes; suíte completa re-rodada
  sem regressões (25 arquivos).
- 22/09/2026 (mesmo dia, sessão seguinte): o Thiago mandou uma operação real
  do robô do Diego em VIRTUAL (texto de análise + print do VIRTUALUSDT) pra
  estudar candidatos de sinal futuro. Análise: cunha descendente na base do
  par VIRTUALBTC, tese de rotação de capital antecipando o BTC topar/
  lateralizar e a dominância corrigir. Nenhum código novo implementado —
  virou o item 17 acima (candidato de 2 partes: detecção de cunha
  descendente genérica, e cruzar exaustão do BTC + dominância subindo como
  aviso antecipado de rotação pra alts, antes da divergência aparecer nos
  retornos). Notado também que o print mandado era do par USDT, não do
  BTC que o texto da análise descreve.
- 22/09/2026 (mesmo dia, sessão seguinte): pedido explícito e amplo do
  Thiago — "pode implementar tudo que falta" — cobrindo de uma vez todos os
  candidatos pendentes até então: os 3 degraus restantes da escada de fundo
  ascendente (5m↔1h, 1h↔1D, 1D↔mensal — `check_retest_5m`/
  `check_retest_1h`/`check_retest_1d`), item 3 (reteste de nível horizontal
  rompido genérico, `check_retest_broken_level`), item 5 (cruzar exaustão
  com os outros sinais, `adiciona_alerta_exaustao`), a parte "de cima pra
  baixo" do item 7 (`diagnose_fundo_descendente_busca_base`), item 16
  (screener de moedas atrasadas, `rank_moedas_atrasadas`), as duas partes
  do item 17 (cunha genérica `check_wedge_pattern` + aviso antecipado de
  rotação `check_rotacao_antecipada_dominancia`), e o candidato solto de
  rompimento de máxima de período com volume
  (`check_breakout_maxima_periodo_volume`). **✅ TODOS IMPLEMENTADOS** —
  ver detalhe completo em cada item acima. O único candidato avaliado e
  **conscientemente não implementado** foi cruzar sinais técnicos com
  calendário macro/eventos agendados, por falta de uma fonte de dados
  gratuita e confiável (ver observação no candidato de rompimento de
  máxima acima). Testes novos escritos pra cada função (mocks
  determinísticos de candles, cobrindo o caso principal, os casos-limite
  de "quase mas não dispara" e dados vazios/insuficientes); suíte completa
  re-rodada sem regressões funcionais (32 arquivos — os 25 anteriores +
  7 novos). Um teste pré-existente (`test_mstr_cl_core_symbols.py`) precisou
  de um ajuste: ele dependia de um passeio aleatório sintético consumindo o
  módulo `random` global numa sequência exata, e cada novo sinal que passou
  a fazer mais chamadas `fetch_klines` dentro de `analyze_symbol` desloca
  essa sequência — sem nenhum bug real por trás, só fragilidade do mock.
  Corrigido fixando deterministicamente um sinal de mercado no horário de
  relatório do teste, em vez de depender do passeio aleatório bater algum
  padrão por coincidência (mais robusto a sinais futuros).
