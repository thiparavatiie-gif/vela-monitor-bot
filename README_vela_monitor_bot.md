# Vela Monitor — bot de varredura no Telegram

Esse pacote faz a varredura automática das moedas do watchlist na Binance,
procurando o padrão de pullback (correção até o Fibonacci 0.382, com
fundos/topos ascendentes/descendentes e checagem de volume) e manda um
alerta formatado no seu Telegram, no estilo do "VELA MONITOR" que você
mostrou.

**Importante sobre onde isso roda:** tanto o container de nuvem do Claude
quanto a VM do bridge que conecta ao seu Mac têm acesso bloqueado à Binance
e ao Telegram por política da organização — então o Claude não consegue
rodar essa varredura sozinho, nem daqui nem através do seu computador via
essa ponte. Por isso o script foi feito pra você rodar diretamente no seu
Mac (fora do sandbox do Claude) ou, de forma mais confiável, em segundo
plano no GitHub Actions (gratuito, roda mesmo com o Mac desligado). As duas
opções estão abaixo.

Arquivos deste pacote:
- `vela_monitor_bot.py` — o script (não usa nenhuma biblioteca externa, só
  Python padrão — não precisa instalar nada).
- `vela_monitor.yml` — workflow do GitHub Actions pra rodar de 1 em 1 hora.

---

## Passo 1 — Criar o bot no Telegram (@BotFather)

1. No Telegram, procure por **@BotFather** (é o bot oficial de criação de
   bots, tem o selo verificado azul).
2. Envie `/newbot`.
3. Escolha um nome pro bot (ex.: `Vela Monitor`).
4. Escolha um username único, terminando em `bot` (ex.: `vela_monitor_bot`
   — se já existir, tente outro).
5. O BotFather vai te dar um **token**, parecido com:
   `123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`
   Guarde esse token — é o `TELEGRAM_BOT_TOKEN`.

## Passo 2 — Pegar o seu chat_id

1. No Telegram, procure pelo bot que você acabou de criar (pelo username
   que escolheu) e envie qualquer mensagem pra ele, tipo "oi".
2. No navegador, acesse (troque `SEU_TOKEN` pelo token do passo 1):
   `https://api.telegram.org/botSEU_TOKEN/getUpdates`
3. Vai aparecer um JSON. Procure por `"chat":{"id":` — o número ali é o
   seu `TELEGRAM_CHAT_ID` (ex.: `987654321`).
   - Se aparecer vazio, confirme que você mandou a mensagem pro bot
     recentemente e recarregue a página.

## Passo 3 — Escolher onde rodar

### Opção A — GitHub Actions (recomendado, roda sozinho de hora em hora)

1. Crie um repositório novo no GitHub (pode ser privado).
2. Suba os dois arquivos:
   - `vela_monitor_bot.py` na raiz do repositório.
   - `vela_monitor.yml` dentro da pasta `.github/workflows/` (crie essa
     pasta se não existir).
3. No repositório, vá em **Settings → Secrets and variables → Actions →
   New repository secret** e cadastre dois secrets:
   - `TELEGRAM_BOT_TOKEN` = o token do Passo 1
   - `TELEGRAM_CHAT_ID` = o chat_id do Passo 2
   - `NEWS_API_KEY` (opcional) = uma chave gratuita de
     [newsapi.org](https://newsapi.org/register) (cadastro grátis, plano
     "Developer"). Sem esse secret, o bot funciona normalmente — só não
     manda as manchetes da Reuters quando não acha nenhum setup na hora.
   - `CMC_API_KEY` (opcional) = uma chave gratuita de
     [coinmarketcap.com/api](https://coinmarketcap.com/api/) (cadastro
     grátis, plano "Basic"). Usada só no relatório categorizado (ver
     abaixo) pra saber quais são as 10 maiores moedas por market cap no
     momento. Sem esse secret, o bot usa uma lista fixa aproximada das 10
     maiores moedas de hoje, que pode ficar desatualizada se o ranking
     mudar bastante.
4. Pronto — o workflow já está configurado pra rodar automaticamente a
   cada hora (`cron: "0 * * * *"`), mais 3 horários extras pro relatório
   categorizado (ver seção própria abaixo). Você também pode disparar
   manualmente em **Actions → Vela Monitor - varredura horária → Run
   workflow** pra testar na hora.

### Opção B — Rodar localmente no seu Mac (cron)

1. Abra o Terminal (fora do Claude) e confirme que tem Python 3:
   `python3 --version`
2. Salve `vela_monitor_bot.py` em uma pasta, ex.: `~/vela_monitor/`.
3. Defina as variáveis de ambiente e teste rodando uma vez:
   ```
   export TELEGRAM_BOT_TOKEN="seu_token_aqui"
   export TELEGRAM_CHAT_ID="seu_chat_id_aqui"
   python3 ~/vela_monitor/vela_monitor_bot.py
   ```
4. Se aparecer "sem setup no momento" pras moedas, está funcionando — só
   não tem nenhum padrão ativo agora. Quando tiver, a mensagem chega no
   Telegram.
5. Pra rodar de hora em hora automaticamente, adicione ao crontab
   (`crontab -e`):
   ```
   0 * * * * TELEGRAM_BOT_TOKEN="seu_token" TELEGRAM_CHAT_ID="seu_chat_id" /usr/bin/python3 ~/vela_monitor/vela_monitor_bot.py >> ~/vela_monitor/log.txt 2>&1
   ```
   (Isso só roda enquanto o Mac estiver ligado e não em suspensão — por
   isso o GitHub Actions é a opção mais confiável se quiser rodar 24/7.)

---

## O que o script considera "setup"

- Timeframe usado: **4h** (estrutura e confirmação).
- Identifica a última perna de impulso (fundo → topo ou topo → fundo) por
  pivôs (fractals) no gráfico de 4h.
- Verifica se o preço está dentro de ~0,6% do nível de **Fibonacci 0.382**
  dessa perna.
- Confirma que os últimos 2 fundos (numa perna de alta) ou topos (numa
  perna de baixa) da correção estão ascendentes/descendentes.
- Compara o volume do candle atual com a média dos últimos 20 candles de
  4h — se estiver abaixo, o alerta ainda sai, mas com o aviso de "volume
  abaixo da média".

## Filtros de qualidade de entrada (valem pra todo sinal)

Dois critérios dos vídeos do Diego que agora se aplicam a **qualquer**
sinal COMPRAR/VENDER, de qualquer uma das estratégias — não é mais um
detalhe isolado de um sinal específico:

- **Risco/retorno mínimo de 1:2** — o lucro potencial até o alvo técnico
  tem que valer pelo menos o dobro do risco até o stop (`MIN_REWARD_RISK_RATIO`
  no topo do script). Um sinal que bate todos os critérios técnicos mas
  onde o alvo está perto demais do stop (por exemplo, arriscar 1% pra
  mirar só 1% de lucro) não é enviado — mensagem por mensagem, o lucro
  precisa compensar o risco, senão não vale a entrada mesmo acertando
  menos da metade das vezes.
- **Tendência majoritária do mercado, cruzando 3 tempos gráficos** —
  calculada a partir do BTC no **diário, semanal e mensal** (cada um com
  seu próprio par de EMAs) uma vez por rodada, e vale pra todas as moedas.
  O diário dá o veredito ("alta" se preço e EMA rápida estão acima da EMA
  lenta; "baixa" no inverso); o semanal e o mensal precisam CONCORDAR com
  ele — se um dos dois discordar, o resultado vira "neutra" (sem filtro).
  Isso segue o que o Diego explica nos vídeos: "você nunca vai querer
  shortar um ativo que está numa tendência de alta em todos os tempos
  gráficos" (e o inverso pra topo). Um sinal de VENDER com o mercado em
  tendência de alta (ou de COMPRAR com o mercado em tendência de baixa) é
  suprimido — "remar contra a maré" tende a dar errado mesmo quando o setup
  técnico local parece certo.

Um sinal suprimido por qualquer um dos dois não simplesmente some: ele vira
uma linha no diagnóstico ("bateu os critérios técnicos de X, mas..."),
tanto no status horário quanto na consulta manual por moeda — pra você
sempre saber por que uma leitura que parecia boa não virou alerta. A
tendência majoritária também aparece no topo da mensagem de status, do
relatório categorizado e da consulta por moeda, sempre que estiver definida
(alta/baixa).

## Ajustes que você pode fazer direto no código

- `WATCHLIST` — lista de moedas (linha ~35 do script).
- `FIB_LEVEL` / `FIB_TOLERANCE` — qual fibonacci monitorar e a margem de
  tolerância.
- `PIVOT_LEN` — quão "forte" precisa ser um pivô pra contar como fundo/topo.
- `MIN_ASCENDING_BOTTOMS` — quantos fundos ascendentes exigir pra confirmar.
- O cron do `vela_monitor.yml` — pra mudar a frequência (ex.: de 15 em 15
  minutos: `*/15 * * * *`, lembrando que o GitHub Actions pode atrasar
  alguns minutos em horários de pico da plataforma).

## Confluência multi-indicador (novo sinal)

Além dos sinais já existentes, tem um novo tipo — **confluência
multi-indicador** — pensado pro tipo de leitura manual que junta vários
fatores ao mesmo tempo (ex.: "RSI em sobrevenda no 15m, perto da EMA200 no
15m, e aproximando da EMA12 no 4h"). Em vez de cada indicador precisar
disparar sozinho, esse sinal soma quantos dos fatores abaixo estão
alinhados na mesma direção ao mesmo tempo:

- Fibonacci 0.382, 0.5 **ou** 0.618 da última perna de 4h.
- EMA 12, 21, 50 **ou** 200 — tanto no 4h quanto no 15m.
- Suporte/resistência **recente** no 4h e no 1h — o fundo (ou topo) dos
  últimos 20 candles, mesmo antes disso virar um pivô confirmado (pivô
  sempre atrasa, porque exige velas de confirmação dos dois lados). É o
  tipo de "suporte no 4h em tal preço" que dá pra ver olhando o gráfico na
  hora.
- RSI em sobrevenda/sobrecompra no 15m, no 1h **e** no 5m (limite mais
  apertado no 5m — 20/80 em vez de 35/65 — por ser "sobrevenda/sobrecompra
  extrema" de timeframe curto).

Com 3 ou mais fatores alinhados, vira sinal de verdade ("Confluência
multi-indicador — possível fundo ascendente/topo descendente se
formando"); com 2, aparece como near-miss no status core e no diagnóstico
manual. A mensagem do sinal também traz uma linha de **invalidação**,
lembrando que romper o stop tende a acelerar o movimento em direção ao
próximo suporte/resistência (ainda não automático — é um aviso pra você
olhar o gráfico e achar esse próximo nível). Isso deve pegar bem mais dos
cenários "vários indicadores batendo ao mesmo tempo" que antes passavam
batido — incluindo leituras como "suporte no 4h + 5m em sobrevenda extrema
+ suporte também no 1h".

## Plano B: próximo ponto técnico se o stop for rompido

Todo sinal COMPRAR/VENDER com stop agora tenta calcular um "plano B"
(linha 🗺️ no cartão): romper o stop não significa necessariamente que a
tendência maior acabou — pode ser só o preço procurando um fundo
ascendente (ou topo descendente) um degrau abaixo. Em vez de deixar isso
vago, o bot aponta o próximo nível técnico de verdade (`adiciona_plano_b` /
`_plano_b_texto`):

- **No mesmo tempo gráfico do sinal** — a EMA ou o suporte/resistência
  anterior mais próximo, além do stop.
- **Num "zoom out" pro diário** — EMA26/EMA50 do 1d e o pivô de suporte/
  resistência anterior, pra ver se a correção maior ainda cabe dentro da
  tendência mais ampla.

Isso não usa o RSI pra achar um preço — RSI não converte de volta num
preço futuro com confiança (o preço é que leva a um RSI, não o contrário).
O texto só cita, como referência de contexto, que essas regiões
historicamente tendem a coincidir com RSI em sobrevenda/sobrecompra no
tempo gráfico maior — deixando claro que não é um cálculo, é orientação de
onde olhar.

Quando o bot não consegue achar nenhum nível técnico nos dados que já tem
(EMA ou pivô insuficiente), a linha 🗺️ simplesmente não aparece — em vez de
uma resposta vaga ou inventada.

### Pressão de volume — "o volume é a gasolina do mercado"

Um suporte ou resistência não rompe sozinho — precisa de volume empurrando.
`analisa_pressao_volume` compara o volume médio dos candles vermelhos
(baixa) e verdes (alta) nos últimos candles contra os anteriores: se o
volume do lado **contrário à posição** (vendedor pra quem comprou perto de
um suporte, comprador pra quem vendeu perto de uma resistência) está
crescendo (`VOLUME_PRESSURE_GROWTH_MULT`, 15%+ de aumento por padrão), o
bot considera que o nível tende a ceder com mais força — "como faca na
manteiga" — em vez de aos poucos.

Quando isso acontece:

- Vira um **🚨 Alerta** no próprio sinal — é um risco pra entrada agora,
  não só uma questão futura.
- Deixa o **🗺️ Plano B** mais enfático — o texto abre avisando que o
  rompimento fica mais provável antes de explicar os próximos níveis.

## Memória da última operação enviada (mensagem fixada no Telegram)

Antes disso, o status de toda rodada só mostrava um diagnóstico solto ("mais
perto de bater") sem nenhum vínculo com a última operação de verdade que o
bot já tinha mandado — dava pra saber que o RSI estava perto de sobrevenda,
mas não quando foi a última compra/venda real, nem como o preço andou desde
lá. Isso mudou sem precisar guardar nada no repositório nem depender do
cache do GitHub Actions (que expira): o bot usa o **próprio Telegram como
memória**.

Como funciona:

- Toda vez que sai uma operação de verdade (COMPRAR/VENDER) pra BTC ou ETH,
  o bot grava os dados dela (ação, título, tempo gráfico, entrada, stop,
  alvo, data/hora) numa mensagem e **fixa** ela no seu chat
  (`atualiza_memoria_ultima_operacao`).
- Na rodada seguinte, antes de montar o status, ele pergunta pro Telegram
  qual é a mensagem fixada agora (`getChat` / `get_memoria_pinned`) — essa
  resposta já vem com os dados de volta, sem o bot precisar guardar nada em
  lugar nenhum.
- Se sai uma operação nova, ele **edita a mesma mensagem fixada** (em vez de
  fixar uma nova a cada vez, que ia acumulando pin antigo) — BTC e ETH ficam
  registrados nela ao mesmo tempo, cada um com o próprio histórico mais
  recente.
- Quando não sai operação nova pra um símbolo naquela rodada, o status
  daquele símbolo passa a trazer um bloco **📍 Última operação enviada**
  com: qual foi, quando (e há quanto tempo), os valores dela, e como o
  preço andou desde então — inclusive avisando se o preço já passou do stop
  ou do alvo daquela operação (`_ultima_operacao_texto`).

Importante: **não apague nem desafixe** essa mensagem de memória no
Telegram — é ela que o bot usa pra lembrar da última operação de cada
moeda. Se ela for apagada, o bot simplesmente recomeça do zero (próxima
operação vira a primeira registrada) — não trava nem dá erro, só perde o
histórico anterior.

### Sugestão de mover o stop pra zero a zero

Esse mesmo bloco de memória agora também sugere proteger o lucro quando faz
sentido: se a operação ainda está **em aberto** (não passou nem do stop nem
do alvo) e o preço já andou pelo menos **1x a distância entrada→stop (1R)**
a favor, aparece uma linha extra sugerindo mover o stop pra zero a zero (o
preço de entrada) — trava o risco em zero sem precisar sair da operação e
sem abrir mão do resto do movimento até o alvo. O limiar de 1R é o valor de
`BREAKEVEN_STOP_R_MULT`, caso queira ajustar pra mais ou menos exigente.

## Cardápio de trade: sinais separados de 5m (day trade), 1h (swing) e 4h (setup raro)

O sinal de "Cascata de RSI" antigo exigia RSI de 15m **e** de 1h em zona de
extremo ao mesmo tempo. Depois de revisar um vídeo do Diego sobre o
"cardápio de trade" dele, isso virou **três sinais independentes**, por
tempo gráfico, cada um disparando só no **primeiro toque** do RSI na zona
de extremo (o RSI acabou de cruzar pra dentro da zona nesta vela — não
estava lá na vela anterior). Isso evita repetir o mesmo aviso vela após
vela enquanto o RSI continua esticado no mesmo movimento:

- **Primeiro toque no 5m** (`SCALP_5M_RSI_OVERSOLD`/`OVERBOUGHT`, 30/70) —
  janela **rápida** de repique/correção (day trade), não troca de
  tendência maior.
- **Primeiro toque no 1h** (`SCALP_1H_RSI_OVERSOLD`/`OVERBOUGHT`, 31/69 —
  o Diego comenta um alarme de RSI em ~31 configurado no 1h) — tratado como
  ponto de entrada de **swing**, porque tende a coincidir com o diário
  formando uma base de preço quando os tempos gráficos maiores estão
  alinhados na mesma direção.
- **Primeiro toque no 4h** (`SCALP_4H_RSI_OVERSOLD`/`OVERBOUGHT`, 30/70,
  `check_scalp_4h`) — o mais **raro** dos três: o RSI de um tempo gráfico
  tão largo só chega nesses extremos depois de várias semanas de movimento.
  Por isso, revendo as lives, esse é tratado como o setup de **maior
  convicção** do cardápio — mesmo assim continua exigindo stop e passando
  pelos mesmos filtros de qualidade que qualquer outro sinal (não é
  garantia de acerto, só de raridade/peso maior quando aparece).

Os três passam pelos mesmos filtros de qualidade de todo sinal (risco/
retorno mínimo de 1:2 e tendência majoritária do mercado).

## Tendência em 3 tempos gráficos (diário + semanal + mensal)

O filtro de tendência majoritária do mercado (ver seção de filtros acima)
agora cruza o BTC em **três** tempos gráficos em vez de só o diário — o
mesmo princípio que o Diego repete nos vídeos: "você nunca vai querer
shortar um ativo que está numa tendência de alta em todos os tempos
gráficos" (e vice-versa pra topo). O diário continua sendo quem dá o
veredito; o semanal e o mensal precisam concordar com ele, senão o
resultado vira "neutra" (sem filtro).

## Alvo maior em rompimento de range longo (padrão de equilíbrio)

O sinal que antes se chamava "Mercado em consolidação / range" (ver
`check_range_market`) virou **"Padrão de equilíbrio"** — mesmo critério
técnico, mas o texto explicativo (🧠) agora usa o vocabulário do Diego em
vez de uma descrição genérica de range: preço alternando entre fundo e
topo (fundo, topo, fundo ascendente, topo descendente) sem conseguir
romper; a entrada é sempre a partir de uma das bordas do padrão (fundo pra
compra, topo pra venda), com o stop logo além do último fundo/topo
formado, mirando o lado oposto.

O alvo também não é sempre só a borda oposta: `check_range_market` só
olhava pra `RANGE_LOOKBACK` candles fixos pra achar a faixa. Agora, seguindo
o "padrão de equilíbrio" do Diego — **"quanto mais tempo lateralizado,
maior o impulso durante o rompimento"** — o bot olha além dessa janela
mínima pra ver há quanto tempo o preço já está realmente contido na mesma
faixa (até um teto de `RANGE_BREAKOUT_MAX_LOOKBACK_MULT` vezes a janela
mínima). Se a consolidação já dura bem mais que o mínimo, o título vira
"Padrão de equilíbrio — rompimento longo" e o alvo estende além da borda
oposta — proporcional ao tempo extra lateralizado, com um teto
(`RANGE_BREAKOUT_EXTENSION_CAP`) pra não virar um alvo fantasioso numa
consolidação muito longa.

## Mensagens mais diretas: checklist, alvo e sem duplicidade

Cada alerta de sinal agora vem no formato de **"cartão de operação"** — o
mesmo estilo enxuto de ação + entrada + stop + alvo(s) + o porquê, pensado
pra ler em poucos segundos:

```
VELA MONITOR

🟢 COMPRAR AGORA — BTC (Pullback (alta, 67.000 → 82.283))
────────────────────────
📍 Entrada: A mercado — ponto técnico específico, não precisa fracionar.
🔴 Stop corretora: 74.500
🎯 Alvos: 82.283 > 86.440 > 91.728
   (bateu um alvo: considere realizar parcial e segurar o resto — swing
   pensa no lucro a longo prazo, não precisa sair tudo de uma vez)
📊 Risco/retorno: 1:2.5
💡 Corrigiu ao 0.382 da perna 67.000→82.283 (76.445) com fundos ascendentes e o 4h confirmou.
💰 Preço agora: 76.720

🧠 O BTC vem recuando desde a máxima de 82.283, testando a região de
76.445 após a perna 67.000 → 82.283. Corrigiu até a zona de Fibonacci
0.382 dessa perna com fundos ascendentes confirmando no 4h — o pullback
confirmado sugere possível retomada da tendência de alta vigente.

🚨 Alerta: Volume atual está 55% da média — volume abaixo da média
enfraquece o setup.

🗺️ Se o stop for rompido: Romper o stop não invalida necessariamente a
tendência maior — pode ser só o preço procurando um fundo ascendente um
degrau abaixo: no mesmo tempo gráfico, o próximo nível é a EMA50 em
73.100; dando um zoom out pro diário, o próximo é o suporte anterior em
71.800. Historicamente essas regiões tendem a coincidir com RSI em
sobrevenda/sobrecompra no tempo gráfico maior, mas isso é só referência de
contexto (RSI não dá pra converter de volta num preço calculado).

Checklist:
  ✅ Preço na zona de Fibonacci 0.382
  ✅ Estrutura de fundos ascendentes confirmada
  ❌ Volume no candle atual acima da média
```

📍 **entrada** — não é sempre "a mercado": quando o próprio sinal já mira
uma ZONA (bottom fishing e reversão com base, que miram um range de fundos
ascendentes), o texto muda pra "fracionada (compra escalonada) entre X e
Y", sugerindo montar a posição aos poucos em vez de tudo de uma vez; scalp
(5m) pede urgência, porque a janela é curta. 🔴 **stop da corretora**. 🎯
**alvo** (ou os 3 alvos progressivos, só no pullback — com a nota de
realizar parcial/segurar o resto, porque bater o primeiro alvo num swing
não significa que a operação acabou). 📊 o risco/retorno calculado (ver
seção de filtros acima), 💡 o motivo técnico resumido numa linha, 💰 o
preço agora, 🧠 um parágrafo de contexto mais completo (o que o preço andou
fazendo, não só o critério que bateu), 🚨 um alerta quando tiver algo que
enfraquece o setup, e o **checklist** (✅/❌) do que confirmou aquele setup
(RSI, volume, estrutura, e a EMA21 como item extra de contexto) fechando a
mensagem. Os sinais de clímax de exaustão e primeiro toque de RSI (5m/1h),
que antes só davam stop, agora também trazem um **alvo técnico** (o
próximo topo/fundo relevante no
timeframe do sinal).

Quando a mesma moeda bate **duas estratégias ao mesmo tempo**, o bot manda
uma única mensagem explicando isso ("bateu 2 estratégias"), com um aviso se
as duas estratégias sugerirem lados opostos (compra x venda) — em vez de
duas mensagens cheias repetidas, que davam a impressão de "operação
clonada".

**A varredura de toda hora não manda mais uma mensagem solta por moeda —
e agora, por padrão, só analisa BTC e ETH.** A varredura completa do
watchlist (50 moedas x ~5 chamadas cada) estava deixando toda rodada
demorada, então agora ela só roda:

- Nos 6 horários do relatório categorizado (seção abaixo).
- Numa execução manual (**Run workflow**).

Fora desses momentos, toda rodada horária normal é rápida: analisa só
`CORE_SYMBOLS` (por padrão `["BTCUSDT", "ETHUSDT"]`) e manda **uma
mensagem só** ("🔭 VELA MONITOR — STATUS"), mostrando o sinal ativo de cada
um se tiver, ou o **near-miss** dele (o que antes só aparecia numa
execução manual — ex.: "2 fatores já alinhados pra um possível fundo
ascendente: RSI do 15m em sobrevenda; RSI do 1h em sobrevenda") junto com
os cenários de alta/baixa quando não tem nada disparado nem perto.

Pra voltar a incluir XRP e 2 altcoins em destaque (como era antes), edite
`CORE_SYMBOLS` e `CORE_EXTRA_ALTS_N` no topo do script — só que aí a
varredura completa do watchlist volta a rodar toda hora (mais lento de
novo), porque é dela que vem a escolha das melhores altcoins.

## Restrito a só BTC/ETH por enquanto (`SOMENTE_CORE_SYMBOLS`)

Por pedido, tem uma trava temporária ligada por padrão (`SOMENTE_CORE_SYMBOLS
= True`, perto de `CORE_SYMBOLS` no topo do script) que faz o bot não
analisar — nem mandar qualquer mensagem de — nenhuma moeda fora de
`CORE_SYMBOLS`. Diferente da otimização de performance acima (que só
adiava a varredura completa pros horários certos), essa trava desliga a
varredura completa de vez enquanto estiver ligada:

- A varredura completa do watchlist (scalp/altcoins pequenas/bottom
  fishing/dominância BTC-altseason/termômetro de ciclo) nem roda, mesmo nos
  horários de relatório ou numa execução manual sem moeda específica.
- O relatório categorizado (seção abaixo) manda só a seção "Swing
  Principal" (BTC/ETH) — as seções de swing secundário (XRP + top 10
  CoinMarketCap), altcoins pequenas, scalp e bottom fishing aparecem como
  "pausadas", sem buscar dado nenhum de outra moeda.
- A consulta manual por uma moeda específica (campo `symbol`) continua
  funcionando normalmente pra qualquer par — a trava é só sobre o que o bot
  varre/manda sozinho, não sobre o que você pode perguntar.

Pra voltar a cobrir o resto do mercado, é só colocar `SOMENTE_CORE_SYMBOLS
= False` de novo.

**Importante sobre execuções manuais**: o relatório categorizado completo
(seção abaixo) só dispara automaticamente pelo relógio — testar manualmente
perto de um dos 6 horários não empilha mais o relatório inteiro em cima da
varredura completa e do diagnóstico, o que antes deixava a execução manual
bem mais pesada e demorada.

**Preenchendo o campo `symbol` numa execução manual, a varredura completa do
watchlist nem roda** — o bot pula direto pra análise só daquela moeda
(status de BTC/ETH + a análise detalhada da moeda pedida), bem mais rápido.
A varredura completa (e o diagnóstico de proximidade do watchlist inteiro)
só roda numa execução manual **sem** preencher o campo `symbol`.

## Relatório categorizado (6x por dia)

Além dos alertas soltos de cada sinal, o bot manda um relatório organizado
por horizonte de operação em 6 horários fixos do dia (horário da Irlanda,
horário de verão/IST): **06:00, 14:00, 14:30, 19:45, 20:15 e 23:00**
(ligados à rotina do mercado americano — abertura, meio do pregão, 20h e
fechamento do candle diário). Esse relatório é bem mais enxuto que uma
lista de todas as moedas — ele filtra pra:

- **Swing principal**: BTC e ETH sempre aparecem. Se tiver sinal de swing
  ativo, mostra ele. Se não tiver, mostra dois cenários (um de alta, um de
  baixa) com faixa de preço de entrada, baseados no último topo/fundo
  confirmado no diário e na comparação de volume — pra você ter uma leitura
  mesmo sem sinal disparado.
- **Swing secundário**: XRP + as 10 maiores moedas por market cap do
  momento — só entram na lista as que tiverem sinal ativo.
- **Altcoins pequenas em setup**: até 5 moedas de menor porte (proxy de
  volume) com algum sinal ativo.
- **Scalp**: até 2 moedas com sinal de scalp ativo.
- **Bottom fishing**: até 2 moedas, priorizando as de maior porte/liquidez.

Isso substitui a ideia de mandar cada sinal solto pra você conseguir ver
tudo organizado numa mensagem só, sem precisar rolar dezenas de alertas.
Petróleo, ouro e mercado americano (S&P 500) ainda não entram nessa versão
— a Binance só tem dados de cripto, então esses três ficariam de fora até
adicionarmos uma fonte de dados separada.

**Sobre o horário**: a Irlanda muda de fuso duas vezes por ano (horário de
verão IST = UTC+1, horário de inverno GMT = UTC+0), e o cron do GitHub
Actions só entende UTC fixo. Os horários acima valem pro horário de verão
(a maior parte do ano) — no horário de inverno, tudo sai 1h mais cedo do
que o pretendido. Se isso incomodar, me avisa quando mudar o horário de
inverno (geralmente final de outubro) que eu ajusto o cron.

## Diagnóstico e consulta por moeda (execução manual)

Toda vez que você roda o workflow manualmente (**Actions → Run workflow**),
além da mensagem de teste chegam mais duas coisas no Telegram:

- **Diagnóstico de proximidade** — só quando o campo `symbol` fica em
  branco: mesmo que nenhuma moeda tenha batido um critério de verdade, o
  script calcula quais moedas do watchlist estão mais perto de bater algum
  (ex.: "RSI a 6 pontos do gatilho de exaustão", "a 1,8% da zona de
  Fibonacci"). Não é um alerta de entrada, é só pra você saber o que vale
  acompanhar de perto — mas exige a varredura completa, então só roda
  quando você não pediu uma moeda específica.
- **Consulta por moeda** — no botão **Run workflow** tem um campo opcional
  chamado `symbol`. Preenchendo com uma moeda (ex.: `SOLUSDT`) você recebe
  uma análise detalhada só dela: se algum sinal está ativo agora, qual está
  mais perto de disparar, e um pouco de contexto (se ela está mais forte ou
  mais fraca que o BTC nos últimos dias) — e, preenchendo esse campo, o bot
  pula a varredura completa do watchlist (ela não é necessária pra
  responder sobre uma moeda só), então essa execução é rápida. Deixe o
  campo em branco pra pular essa parte e ver o diagnóstico geral do
  watchlist inteiro.

A análise por moeda também traz uma seção **"Última entrada e próximo
ponto de interesse"**: a última virada de estrutura confirmada no 4h (o
pivô — fundo ou topo — que deu início ao movimento atual, com data/hora) e
o nível técnico mais próximo do preço atual que ainda não foi tocado
(fibonacci, EMA de 4h, ou o suporte/resistência anterior à perna atual) —
se o preço chegar perto desse nível, é um fator a mais de confluência.
Isso é calculado na hora a partir dos candles que o bot já busca, sem
precisar guardar histórico entre execuções (cada rodada do GitHub Actions
começa do zero).

Importante: essa análise por moeda é uma leitura automática baseada nas
mesmas regras dos sinais — o script não chama nenhum modelo de IA pra gerar
opinião, é a aplicação mecânica das regras, só que explicada em texto. E o
setup que faz mais sentido muda junto com o cenário de mercado — não é uma
recomendação fixa.

## Aviso importante

Isso é um **scanner técnico baseado em regras** (fibonacci + estrutura +
volume) — não é um robô de execução de ordens e não garante nada. É uma
ferramenta de apoio pra te avisar quando um padrão aparecer, do mesmo jeito
que o indicador no TradingView já faz visualmente. A decisão de operar
continua sendo sua.
