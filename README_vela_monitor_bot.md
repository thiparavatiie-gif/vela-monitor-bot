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

## Mensagens mais diretas: checklist, alvo e sem duplicidade

Cada alerta de sinal agora vem num formato mais enxuto — ação e moeda logo
no topo, os números (entrada/alvo/stop) embaixo, e um **checklist** (✅/❌)
mostrando o que confirmou aquele setup (RSI, volume, estrutura, e a EMA21
como item extra de contexto). Os sinais de clímax de exaustão e cascata de
scalp, que antes só davam stop, agora também trazem um **alvo técnico**
(o próximo topo/fundo relevante no timeframe do sinal).

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

**Importante sobre execuções manuais**: o relatório categorizado completo
(seção abaixo) só dispara automaticamente pelo relógio — testar manualmente
perto de um dos 6 horários não empilha mais o relatório inteiro em cima da
varredura completa e do diagnóstico, o que antes deixava a execução manual
bem mais pesada e demorada.

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

- **Diagnóstico de proximidade** — mesmo quando nenhuma moeda bateu um
  critério de verdade, o script calcula quais moedas do watchlist estão
  mais perto de bater algum (ex.: "RSI a 6 pontos do gatilho de exaustão",
  "a 1,8% da zona de Fibonacci"). Não é um alerta de entrada, é só pra você
  saber o que vale acompanhar de perto.
- **Consulta por moeda** — no botão **Run workflow** tem um campo opcional
  chamado `symbol`. Preenchendo com uma moeda (ex.: `SOLUSDT`) você recebe
  uma análise detalhada só dela: se algum sinal está ativo agora, qual está
  mais perto de disparar, e um pouco de contexto (se ela está mais forte ou
  mais fraca que o BTC nos últimos dias). Deixe o campo em branco pra pular
  essa parte.

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
