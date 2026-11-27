---
name: edicao-video
description: Editar vídeos curtos verticais (TikTok) no padrão Gloow, nos estilos de edição 1, 2, 3 e 4 (1, 2 e 4 para vídeos falados; 4 = começa com o trecho mais impactante do vídeo como gancho, hook em caixa rosa, zoom nas falas importantes, sem legenda: hook na tela, cortes de respiro, sobreposições em janela, selo de comentário; 1 com legenda e zoom, 2 limpo e sem legenda; 3 para B-roll sem fala: texto na tela e música do início ao fim). Use quando o Vitor mandar vídeos brutos no Google Drive para editar.
---

# Edição de vídeo — Estilos de edição 1, 2, 3 e 4

## Regras que valem para os dois estilos

1. **Hook obrigatório.** Nenhum vídeo sai sem hook. Topo, primeiros ~4s, texto branco com contorno preto grosso, 3 linhas curtas.
   - **Instantâneo**: o hook já aparece inteiro e no tamanho final no primeiro quadro (sem fade nem animação de entrada); só some com fade no fim.
   - **Sem exceção**: mesmo quando a pessoa abre o vídeo mostrando algo (app, celular, placa, produto), o hook entra no início. Antes de entregar, conferir o quadro 0 de cada vídeo: hook presente e legível (cuidado com fundo claro, ex. céu).
   - Polêmico, mas sem restrição: não promete ganho, não parece venda.
   - Usar algo que a pessoa fala no vídeo como gancho. Escrever "ttk" no lugar de "TikTok".
   - **Quando a pessoa já fala um hook no começo (geralmente apontando pra cima, pro lugar do texto), o hook na tela é essa frase**, resumida em até 3 linhas, e fica na tela enquanto ela fala (`dur` até o fim da frase). **Cada estilo tem um hook diferente** (nunca o mesmo texto nas 3 versões do mesmo bruto): o estilo 1 usa a frase falada; os estilos 2 e 4 ganham hooks novos (o 4 em formato de pergunta). Quando o vídeo não abre com frase de gancho, criar 3 hooks diferentes.
2. **Começa sempre na fala.** Nada de trecho parado no início (o script corta até a primeira palavra).
3. **Corta respiros e pausas**, e também frases repetidas, tentativas refeitas e tropeços (via `remove` no config).
   - **Fala corrida entre takes:** os cortes seguem as palavras da transcrição, não o silêncio. Entre um take e outro sobra só uma folga mínima (`tail` 0,06s depois da última palavra + `lead` 0,03s antes da próxima), então a emenda soa como a pessoa falando sem parar, sem respiro nem olhada pra baixo. Pausas dentro da frase maiores que `gap_max` (0,25s) também são cortadas. Ajustáveis no config: `gap_max`, `lead`, `tail` (e `speech_db` para o nível de voz, se o áudio for muito baixo ou ruidoso).
   - O áudio é montado de uma vez, amostra por amostra, alinhado ao quadro, com micro-fade de 4 ms em cada emenda: sem soluço, sem estalo e sem dessincronizar.
   - **Repetição/travada (estilos 1 e 2):** quando a pessoa trava e repete a palavra ou a frase, fica **só a última tentativa** (a mais firme) e o corte liga direto nela. Margem mínima de erro.
   - A transcrição (`scripts/transcribe.py`) é literal, mantém repetições; rodar `python3 -I scripts/dedupe.py transcricao.json` para listar as repetições e colocar cada uma em `remove`.
   - O transcritor às vezes ainda junta duas tentativas numa só: onde houver vão estranho entre palavras, retranscrever o trecho com `python3 -I scripts/trecho.py audio.wav INICIO FIM` antes de decidir o corte.
   - Se o Whisper **pulou um trecho de fala** (vão grande sem texto) ou errou o tempo das primeiras palavras, corrigir a transcrição com `python3 -I scripts/retrecho.py transcricao.json audio.wav INICIO FIM` (retranscreve e substitui as palavras do intervalo). Sem isso, a fala do trecho é cortada do vídeo. Comum em gravação de teleprompter.
   - Depois de cortar, conferir o trecho no vídeo editado (retranscrever) para garantir que a frase sai uma vez só.
4. **Selo rosa** "comenta PALAVRA" quando a pessoa pede o comentário.
5. **Sobreposições no momento da fala que combina** (quando fala do app, das marcas, da comunidade).
   - Vídeo de tela do app → **janela no topo** (`"type": "pip"`), nunca tela cheia. Gravação de tela que muda rápido vira quadro parado da tela certa.
   - Janela: borda arredondada + sombra, no topo, do lado da cabeça (pode pegar no rosto), bem visível, dentro da área segura do TikTok (abaixo de "Seguindo | Para você", longe dos botões da direita). Padrão: `"size": [560, 600], "y": 220`; com o Samuca (rosto mais alto no quadro) usar `"size": [520, 540], "y": 200` pra não pegar nos óculos. Pessoa muito perto da câmera: janela menor no canto (`"size": [420, 450], "x": 50, "y": 200`) — é o caso do Mat.
   - Cartão de imagem larga (ícones, print baixo): `"maxw": 760, "y": 130`, pra ficar acima dos olhos.
   - Se no vídeo bruto a pessoa já mostra o app no celular, deixar rodar sem cobrir.
   - **Quando a pessoa aponta/fala "esse resultado aqui" (ou mostra algo que não aparece no bruto)**, colocar sobreposição naquele momento, mesmo durante o hook, logo abaixo do texto do hook. Resultado/valor: usar `assets/print_saldo.png` (print do app com "Saldo disponível", sem o nome) numa janela larga só com o card do saldo: `"crop": [0, 0, 1, 0.3], "size": [700, 250], "x": 190, "y": 580`. Telas do app por dentro: quadros da gravação de tela.
   - Fora esse caso, nenhuma sobreposição durante o hook (primeiros ~4,5 s do vídeo editado): lembrar que o vídeo começa na 1ª palavra, então somar o início da fala ao tempo do original.
   - Não colocar print de prova social de outra pessoa logo depois de alguém falar do próprio faturamento (parece que é dele).
   - Perfil só da própria pessoa do vídeo (perfil "Samuca Sem Dores" só em vídeo do Samuca).
6. Sinalizar ao Vitor promessas de ganho ou de saúde que estejam na fala (ex.: "300 reais em 10 dias") — podem dar restrição.
7. Vídeo que não é de venda (conversa solta, sem chamada) fica de fora e é avisado.
8. **Duração livre**: o importante é não sobrar erro nem repetição. Se depois de todos os cortes o vídeo der 2 min, fica com 2 min (não cortar conteúdo só pra encurtar).

## Estilo de edição 1

- **Legenda da fala**: 2–3 palavras por vez, branca com contorno preto, terço de baixo, entrada com "pop".
  - Corrigir erros da transcrição via `replace` (ex.: "tiktok"→"ttk", "chat ept"→"ChatGPT", "de ar"→"de IA", "built"→"bio", "Nuri"/"Nulli"→"Nulle", "glow"→"GLOOW").
- **Zoom de 10% alternado** a cada corte.
- **Sobreposições**: 4 a 7. Prints de prova social como cartão inclinado subindo com quique (`"type": "card"`); telas do app em janela no topo (`"type": "pip"`).
- Exemplo: `exemplos/estilo1_IMG_7421.json`.

## Estilo de edição 2

- **Sem legenda da fala** (`"captions": false`).
- **Sem zoom** (`"zoom": 1.0`).
- **Menos informação**: 2 a 3 sobreposições, só as realmente necessárias, todas em janela no topo (`"type": "pip"`).
- Hook e selo de comentário iguais ao estilo 1.
- Exemplo: `exemplos/estilo2_IMG_7486.json`.

## Estilo de edição 4 (gancho com o trecho mais impactante)

Mesma base dos estilos 1 e 2 (começa na fala, cortes de respiro/repetição, selo de comentário). O que muda:

- **Gancho = o trecho mais impactante do próprio vídeo**: ler a transcrição, escolher a frase mais forte (a revelação, o número, a virada, a frase polêmica) e repetir esse trecho (vídeo + áudio, com zoom) nos **primeiros ~5 s**; depois o vídeo começa normalmente do início. Config: `"teaser": [ini, fim]` em tempo do original, ou vários trechos `[[ini, fim], [ini, fim]]` (frase forte + complemento curto).
  - **Aprovado pelo Vitor (26/11, Samuca 7607):** gancho de ~5–6 s com a ideia **inteira** ("Essas marcas me entregam vídeos prontos pra eu postar e eu não tomo restrição de postar esses vídeos"). Gancho curto de 3 s que corta no finalzinho foi reprovado.
  - Aprovados também (27/11, Mat 6960/6962): ganchos de ~5,2 s montados com 2 trechos (pergunta + resposta, ou frase cortada no meio de uma pausa).
  - **Fim da palavra:** o Whisper às vezes marca o fim da última palavra 0,3–0,4 s antes do real. Medir o áudio (RMS em janelas de 50 ms) no fim do gancho e usar o fim real; se precisar, `"ext": 0.45` no config (quanto a borda pode avançar pelo áudio, padrão 0,2). Conferir retranscrevendo os primeiros 6 s do vídeo pronto.
- **Texto do hook** = essa frase, na **caixa rosa** com texto branco (`"hook": {"style": "box_rosa", "dur": 0}`; `dur` 0 = dura o gancho inteiro).
- Visual próprio: imagem mais viva (`"look": "vivo"`), **barra de progresso rosa** embaixo (`"progress": "0xFF14B4"`), **zoom só nas falas importantes** (`"zoom_at"`, `"zoom": 1.15`).
- **Sem legenda** (`"captions": false`). Sobreposições só o suficiente (1 a 3, janela no topo), nenhuma durante o gancho.
- Legenda (estilo 1): erro de palavra que o `replace` não pega (frase quebrada entre blocos) corrige com `"word_fix": {"inicio_da_palavra": "texto"}` ("" apaga).

## Lotes com vários estilos do mesmo bruto

**Padrão atual (26/11): cada bruto falado vira 4 vídeos**: estilo 1, estilo 2, **"estilo 3" do Vitor = hook colorido** (caixa rosa com pergunta, `look` vivo, barra rosa, `zoom_at`, sem gancho repetido; arquivo `_estilo3`) e estilo 4 (gancho). Ex.: 2 brutos → 8 vídeos. Se os brutos forem B-roll (sem fala), os 4 viram 4 versões do B-roll (arquivo `_estilo3`, `_v2`…). Quando o Vitor pedir, cada bruto é editado nos estilos 1, 2 e 4 (3 versões do mesmo vídeo, com hooks diferentes). Lotes grandes vão em remessas de 6 brutos (18 vídeos). Se o Vitor pedir só 2 edições por vídeo sem dizer quais, usar estilos 1 e 4 (os mais diferentes entre si); B-roll sai em 2 versões do estilo 3 (texto e música diferentes, `_v2`). Bruto que já foi editado antes ganha versões novas com hooks diferentes (`_v2`).

## Estilo de edição 3 (B-roll)

Para vídeos **sem fala** (a pessoa só aparece fazendo algo, posando etc.). Não precisa transcrever nem analisar o áudio.
- Num lote misturado, B-roll sai no estilo 3 e não conta na alternância 1/2. Sinal de B-roll na transcrição: o Whisper devolve só o próprio prompt ("Transcreva literalmente...") ou "É, é, eu, eu".

- **Texto na tela do primeiro ao último quadro**, sem fade: variante nova a partir do banco `hooks.md` (não reutilizar os de referência; não mencionar "2 mil seguidores") (formato viral, 2–3 frases, terminando com chamada tipo "Entra no meu perfil"). **No topo, dentro da área segura do TikTok**: começa ~300px abaixo do topo (abaixo de "Seguindo | Para você"), margem esquerda 90px e direita 150px (longe da foto de perfil, curtir, comentar), branco com contorno preto, mesmo tamanho. Nem colado no topo, nem no meio da tela. Sem emoji (a fonte não desenha). "ttk" no lugar de TikTok quando aparecer.
- **Música embutida no arquivo, do primeiro ao último segundo**, já no volume cheio (pular silêncio/introdução da faixa). Os vídeos vão para uma pasta de postagem automática, então a música tem que estar no arquivo.
- **Música**: não só inglesa — priorizar música brasileira que combine com o contexto (sertanejo, sons virais do TikTok). Se o Vitor subir MP3s numa pasta `Músicas` no Drive, usar esses. Sem isso, usar faixa livre de direitos do Mixkit (`mixkit.co`, licença livre para redes sociais; hosts `mixkit.co` e `assets.mixkit.co` liberados no ambiente).
- **Reaproveitar B-roll:** o Vitor pode pedir nova versão do mesmo B-roll com texto novo + música nova (salvar como `_v2`). Não repetir faixa nem texto da versão anterior.
- **B-roll com a Nulle (sachê azul)**: quando o produto aparecer, o texto fala da Nulle, misturando os hooks de `hooks_nulle.md` com o app rosa (ver regras lá) e colocando 1 sobreposição da Nulle. Adaptar o gênero ao criador e sinalizar frases de saúde de risco alto. Vídeo falado sobre a Nulle também ganha sobreposição da marca.
- **Pelo menos 4 versões de cada B-roll**, cada uma com **texto diferente, música diferente e selo final diferente** (cor e frase), pra não parecer vídeo repetido no ttk: `_v2`, `_v3`, `_v4`… Cores do selo (7º argumento do `broll.py`): `rosa`, `verde`, `azul`, `amarelo`, `roxo`, `vermelho`. Frases do selo: "GRUPO GRÁTIS / NA BIO", "LINK DO GRUPO / NA BIO", "GRUPO GRATUITO / NA BIO", "ENTRA NO GRUPO / DA BIO". Não repetir faixa de música dentro do mesmo lote. Antes de usar uma faixa nova, medir onde ela fica alta (algumas começam em silêncio por 5–90 s) e passar esse tempo como `INICIO_MUSICA`; conferir que as versões saem com volume parecido (~-16 dB médio).
- **B-roll com pedido de corte** (a pessoa fala tipo "corta essa parte do começo"): cortar esse trecho e também pontas com chão/câmera balançando antes de montar o B-roll.
- **Clipe curto de "Saiba Mais"** (a pessoa só fala "clica em Saiba Mais / vai no grupo gratuito", ~8 s): é final de anúncio. Juntar com um B-roll do mesmo lote: B-roll com texto e música (sem o selo) + o clipe com legenda e selo "clica em SAIBA MAIS" → `Pessoa_NUM_anuncio_com_NUM.mp4`. Fotos do lote viram 2–3 s de B-roll (zoom lento) antes do clipe.
- **Selo final chamativo**: no último ~1 s o texto sai e entra "GRUPO GRÁTIS / NA BIO" grande, amarelo em caixa rosa, com pop e tremida (6º argumento do script).
- Clipes curtos de B-roll (5–10 s) que vierem no meio de um lote de vídeos falados também saem no estilo 3, com texto curto (1–2 frases).
- Cor: o `broll.py` detecta bruto HDR do iPhone (HLG) e faz a conversão de verdade pra BT.709 (tone mapping), senão a pele fica pálida.
- Faixas do Mixkit já usadas (lote 26/11, Eliton 1674/1675): 339, 284, 1086, 1165, 1140, 1077, 872, 989 — escolher outras no próximo lote.
- Script: `python3 -I scripts/broll.py VIDEO MUSICA SAIDA "TEXTO" INICIO_MUSICA $'GRUPO GRÁTIS\nNA BIO'`.
- Exemplos de frases base do Vitor:
  - "Enquanto você tá aí só assistindo a vida dos outros, tem gente com menos de 100 seguidores fazendo venda todo dia no app rosa só de copiar e colar vídeos prontos com 1 clique e postar. Pra entender como, entra no meu perfil."
  - "Antes de ficar esperando o Shop pra começar de verdade no ttk, entra no meu perfil pra entender uma coisa: enquanto você tá aí parada achando que depende de 2000 seguidores pra vender, tem gente começando no app rosa com menos de 100 seguidores fazendo venda sem esperar liberar nada."

## Alternância nos lotes

Num lote, alternar na ordem dos arquivos do Drive: 1º estilo 1, 2º estilo 2, 3º estilo 1, 4º estilo 2...
Continuar a alternância de onde o lote anterior parou.

## Pessoas

- **Eliton**: barbudo, de óculos, cabelo raspado (subpasta "Eliton" no Stand By).
- **Mat (Matheus)**: o "alemão", barbudo, olhos claros, sem óculos (subpasta "Matheus" no Stand By). Brutos em 4K HDR; ele costuma andar pela casa mostrando as coisas (não cobrir). Sobreposição em janela pequena no canto.
- **Samuca (Samuel)**: cara limpa, cabelo grande (subpasta "Samuel" no Stand By).

## Nome dos arquivos

Salvar cada vídeo editado com o nome da pessoa na frente, pra facilitar subir no Drive: `Pessoa_NUMERO_estiloN.mp4` (ex.: `Eliton_1628_estilo1.mp4`, `Samuca_7617_estilo3_v2.mp4`).

## Passo a passo

1. **Rede**: o ambiente precisa liberar `drive.google.com`, `drive.usercontent.google.com`, `docs.google.com`, `www.googleapis.com` e os hosts do Hugging Face (`huggingface.co`, `cdn-lfs.huggingface.co`, `cdn-lfs.hf.co`, `cdn-lfs-us-1.hf.co`, `cas-bridge.xethub.hf.co`, `us.aws.cdn.hf.co`, `cas-server.xethub.hf.co`).
2. **Instalar**: `pip install gdown faster-whisper pillow-heif`.
3. **Listar a pasta do Drive** (gdown só para listar; o download via gdown falha no proxy):
   ```python
   import gdown
   for f in gdown.download_folder(URL_DA_PASTA, skip_download=True, quiet=True): print(f.id, f.path)
   ```
4. **Baixar cada arquivo com curl** (se vier um HTML de erro 503, baixar de novo):
   `curl -sSL -o ARQUIVO "https://drive.usercontent.google.com/download?id=ID&export=download&confirm=t"`
   - Imagens `.PNG` do iPhone às vezes são HEIC: converter com `pillow_heif` antes de usar.
5. **Transcrever**: `ffmpeg -i VIDEO -vn -ac 1 -ar 16000 audio.wav` e depois
   `HF_HUB_DISABLE_XET=1 python3 -I scripts/transcribe.py audio.wav transcricao.json medium`.
6. **Escrever o config** (ver `exemplos/`): vídeo, transcrição, `remove`, `replace`, `hook`, `stickers`, `overlays`, e no estilo 2 `captions`/`zoom`. Tempos sempre do vídeo **original**; o script remapeia.
   - `pip`: `file` (imagem ou vídeo), `crop` [x, y, largura, altura] em frações, `size`, `y`, `x` opcional, `from` para vídeo.
7. **Editar**: `python3 -I scripts/edit.py config.json` (corta trecho por trecho para não estourar memória; ~2–5 min por vídeo; rodar um vídeo por vez).
8. **Conferir quadros** (hook legível, janela com a tela certa e sem cobrir os olhos, legenda) antes de mandar ao Vitor.

## Material de apoio no Drive (pasta do Vitor)

- Link da pasta (compartilhada por link): https://drive.google.com/drive/folders/1F5pPZWobbu1MBXVk02zgwwoMP2AhnKVS — os brutos novos também chegam aqui.

- `Provas Sociais/`: prints do Telegram ("primeira venda").
- `Sobreposições/`: ícones com o Gloow App circulado, perfil "Samuca Sem Dores", vídeo do perfil, gravação de tela do app.
- Gravação de tela do app (`copy_3AAD4AD4-...mov`, 94s) — bons quadros parados: 6,5s "Marcas Virais"; 9s página da Nulle (com "Vídeos Prontos"); 11s links de afiliação com comissão; 23s site da Nulle ("regular seu cortisol").

## Entrega no Google Drive

- ⚠️ Upload pelo conector Google Drive (`create_file`, `base64Content` = `sha256:<hash>:<caminho>`, `video/mp4`, `disableConversionToGoogleType: true`): **limite de ~3,1 MB por arquivo** (cada chamada ao conector tem teto de 4,2 MB; antes era 10 MB). Quase nenhum vídeo cabe: entregar na conversa (B-roll de 10 s fica com ~7–8 MB a 6 Mbps) para o Vitor arrastar na pasta do Drive do PC. Vídeos falados (40–150 MB) também não sobem por aqui: entregar na conversa para o Vitor arrastar na pasta do Drive do PC. B-rolls curtos (< 10 MB) podem subir direto.
- **Regra do Vitor: não mexer em nada no Drive** (não mover, renomear, apagar nem editar). Só **subir** os vídeos editados na pasta certa.
- Destino: pasta **"00 - ⏯️ POSTAGEM STAND BY (AGUARDANDO)"** (id `1Cx4WfPwmhR2UsuNGzEoPPcBaroDLofm4`, dentro da pasta raiz `1BEtIt9SzaappmPbInoOwEcDdHEVJ568n`), na subpasta da pessoa do vídeo:
  - Matheus (Mat): `14uHGLQTCvyS5E96B3aqG3u_zRXVVDabt`
  - Samuel (Samuca): `1fAuehTadroP1ovpUnmM9PaVB5a9fDvf8`
  - Claudio: `1Rv8F_dwkssWDNYMhzY2aL9DiYNGHHxh8`
  - Eliton: `1_vve7NIW_zznkj_r__lf6UgkVlZrU4v_`
  - Universo.glow: `1BhfIYAN-fU8NSddeFWwwYT7Z54_Oh75d`
- As outras pastas da raiz ("00 - Gravação Bruta", "00 - ▶️ POSTAGEM ON", "00 - Frases prontas", "Referências App rosa") não são tocadas.
