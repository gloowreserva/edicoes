---
name: edicao-video
description: Editar vídeos curtos verticais (TikTok) no padrão Gloow, nos estilos de edição 1, 2, 3 e 4 (4 = anúncio UGC de marca copiando a edição de uma referência da marca) (1 e 2 para vídeos falados: hook na tela, cortes de respiro, sobreposições em janela, selo de comentário; 1 com legenda e zoom, 2 limpo e sem legenda; 3 para B-roll sem fala: texto na tela e música do início ao fim). Use quando o Vitor mandar vídeos brutos no Google Drive para editar.
---

# Edição de vídeo — Estilos de edição 1, 2 e 3

## Regras que valem para os dois estilos

1. **Hook obrigatório.** Nenhum vídeo sai sem hook. Topo, primeiros ~4s, texto branco com contorno preto grosso, 3 linhas curtas.
   - Polêmico, mas sem restrição: não promete ganho, não parece venda.
   - Usar algo que a pessoa fala no vídeo como gancho. Escrever "ttk" no lugar de "TikTok".
2. **Começa sempre na fala.** Nada de trecho parado no início (o script corta até a primeira palavra).
3. **Corta respiros e pausas**, e também frases repetidas, tentativas refeitas e tropeços (via `remove` no config).
   - **Repetição/travada (estilos 1 e 2):** quando a pessoa trava e repete a palavra ou a frase, fica **só a última tentativa** (a mais firme) e o corte liga direto nela. Margem mínima de erro.
   - A transcrição (`scripts/transcribe.py`) é literal, mantém repetições; rodar `python3 -I scripts/dedupe.py transcricao.json` para listar as repetições e colocar cada uma em `remove`.
   - O transcritor às vezes ainda junta duas tentativas numa só: onde houver vão estranho entre palavras, retranscrever o trecho com `python3 -I scripts/trecho.py audio.wav INICIO FIM` antes de decidir o corte.
   - Depois de cortar, conferir o trecho no vídeo editado (retranscrever) para garantir que a frase sai uma vez só.
4. **Selo rosa** "comenta PALAVRA" quando a pessoa pede o comentário.
5. **Sobreposições no momento da fala que combina** (quando fala do app, das marcas, da comunidade).
   - Vídeo de tela do app → **janela no topo** (`"type": "pip"`), nunca tela cheia. Gravação de tela que muda rápido vira quadro parado da tela certa.
   - Janela: borda arredondada + sombra, no topo, do lado da cabeça (pode pegar no rosto), bem visível, dentro da área segura do TikTok (abaixo de "Seguindo | Para você", longe dos botões da direita). Padrão: `"size": [560, 600], "y": 220`. Pessoa muito perto da câmera: janela menor no canto (`"size": [420, 450], "x": 50, "y": 200`).
   - Se no vídeo bruto a pessoa já mostra o app no celular, deixar rodar sem cobrir.
   - Não colocar print de prova social de outra pessoa logo depois de alguém falar do próprio faturamento (parece que é dele).
   - Perfil só da própria pessoa do vídeo (perfil "Samuca Sem Dores" só em vídeo do Samuca).
6. Sinalizar ao Vitor promessas de ganho ou de saúde que estejam na fala (ex.: "300 reais em 10 dias") — podem dar restrição.
7. Vídeo que não é de venda (conversa solta, sem chamada) fica de fora e é avisado.

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

## Estilo de edição 3 (B-roll)

Para vídeos **sem fala** (a pessoa só aparece fazendo algo, posando etc.). Não precisa transcrever nem analisar o áudio.

- **Texto na tela do primeiro ao último quadro**, sem fade: variante nova a partir do banco `hooks.md` (não reutilizar os de referência; não mencionar "2 mil seguidores") (formato viral, 2–3 frases, terminando com chamada tipo "Entra no meu perfil"). **No topo, dentro da área segura do TikTok**: começa ~300px abaixo do topo (abaixo de "Seguindo | Para você"), margem esquerda 90px e direita 150px (longe da foto de perfil, curtir, comentar), branco com contorno preto, mesmo tamanho. Nem colado no topo, nem no meio da tela. Sem emoji (a fonte não desenha). "ttk" no lugar de TikTok quando aparecer.
- **Música embutida no arquivo, do primeiro ao último segundo**, já no volume cheio (pular silêncio/introdução da faixa). Os vídeos vão para uma pasta de postagem automática, então a música tem que estar no arquivo.
- **Música**: não só inglesa — priorizar música brasileira que combine com o contexto (sertanejo, sons virais do TikTok). Se o Vitor subir MP3s numa pasta `Músicas` no Drive, usar esses. Sem isso, usar faixa livre de direitos do Mixkit (`mixkit.co`, licença livre para redes sociais; hosts `mixkit.co` e `assets.mixkit.co` liberados no ambiente).
- Script: `python3 -I scripts/broll.py VIDEO MUSICA SAIDA "TEXTO" INICIO_MUSICA`.
- Exemplos de frases base do Vitor:
  - "Enquanto você tá aí só assistindo a vida dos outros, tem gente com menos de 100 seguidores fazendo venda todo dia no app rosa só de copiar e colar vídeos prontos com 1 clique e postar. Pra entender como, entra no meu perfil."
  - "Antes de ficar esperando o Shop pra começar de verdade no ttk, entra no meu perfil pra entender uma coisa: enquanto você tá aí parada achando que depende de 2000 seguidores pra vender, tem gente começando no app rosa com menos de 100 seguidores fazendo venda sem esperar liberar nada."

## Estilo de edição 4 (UGC para marcas — copia a referência)

Vídeos que vão para donos de marca. Cada bruto segue o roteiro de um dos vídeos de referência da marca e a edição **copia o modelo daquela referência**. Material bruto e análise: `referencias/estilo4/ANALISE.md` (referências da Nulle: pasta do 1º Drive do Vitor, só leitura; sobreposições na subpasta `Sobreposições`).

1. **Casar bruto ↔ referência** pelo roteiro (transcrição) e pelos gestos. Ex.: "Como o CORTISOL mudou sua aparência" = 05/07; "Será que isso aqui funciona mesmo?" = 06; "O que acontece se você tomar magnésio" = 01; "O impacto real do cortisol… 30%" = 08; "Cortisol alto, cortisol regulado" = 03.
2. **Sem fala → 4C** (`scripts/estilo4c.py`): cenas no pico do gesto, cortes na batida da música (BPM detectado), texto estilo TikTok clássico com emoji, música da referência, sobreposições em cartão.
3. **Com fala → 4 falado** (`scripts/estilo4f.py`):
   - Brutos têm muitas tomadas repetidas e trechos lidos olhando pro lado. **Só entra tomada olhando pra câmera**: rodar `scripts/olhar.py VIDEO olhar.json` e `scripts/frases.py` (OpenCV, detector frontal a 5 fps; precisa `opencv-python-headless<5`) e conferir ≥85% de frente em cada trecho.
   - Melhor tomada de cada frase (normalmente a última e mais firme); respiros > 0,28s cortados automaticamente.
   - Legenda conforme a referência: `palavra` (1 palavra, caixa alta, ref. 01/06/09), `destaque` (2–4 palavras com palavra-chave amarela, ref. 02/03), `nenhuma` + `keywords` verdes (ref. 08). Tela dividida com foto em cima e % grande (`split`, ref. 08).
   - Hook em caixa branca estilo TikTok + imagem de antes/depois quando a referência tem (01/06).
   - Música baixinha só quando a referência tem (08: lo-fi do Mixkit a −26 dB).
   - Trechos mal transcritos: `fix.py` (retranscreve com o modelo medium e junta no json) e `word_fix` no config.
4. **Sobreposições obrigatórias**, em lugares parecidos com a referência, com leve mudança; nunca em cima do rosto nem do produto.
5. **Cor**: brutos de iPhone são HDR (HLG/BT.2020). O `estilo4f.py` detecta e faz **conversão de verdade (tone mapping hable) pra BT.709** + toque leve de luz (`eq=brightness=0.05:contrast=1.05`). Sem isso a pele fica pálida/acinzentada ("ar de fantasma", feedback do Samuel) ou estourada. Não usar mais ajuste de gamma/brilho por cima. Conferir com `signalstats` (saturação média ~11–12 no 7537; antes 7,5).
6. **Padrão de qualidade (feedback do Vitor): zero erro.**
   - **Presença**: só entra take com ele firme, olhando pra câmera, com energia. Nada de mexer no cabelo, balançar a cabeça, olhar pro roteiro/pacote, cara de "pensando" — nem no começo/fim do trecho. Se a frase tem uma tomada melhor (mais presença), usar ela.
   - **Corte nunca no meio da palavra.** O corte é feito pelo detector de voz (Silero VAD) dentro dos trechos marcados; emenda entre palavras coladas usa borda exata `[ini, fim, "x"]` no ponto de menor volume.
   - Antes de renderizar, rodar o config com `"dry": true` e os dois verificadores, e corrigir até zerar:
     - `scripts/checa_cortes.py BRUTO.wav work/segs.json transcricao.json` → 0 cortes com voz no ponto.
     - `scripts/checa_presenca.py BRUTO work/segs.json` → olhar cada quadro suspeito (`previa`/quadro avulso): gesto de fala fica; olhar pra baixo/lado, cabelo, balanço sai (borda exata ou outra tomada).
   - Depois de renderizar: retranscrever o final (frase repetida/cortada) e ver um quadro de cada cena.
   - Giro de cabeça de 0,2–0,3s no começo/fim da fala (começa a falar ainda virando pra câmera): não cortar a palavra — usar `"segura_imagem": [{"v0": t}]` / `[{"v1": t}]` (áudio inteiro, imagem segura o 1º/último quadro de frente).
   - `scripts/previa.py BRUTO work/segs.json saida.jpg` = mosaico de tudo que vai entrar (3 quadros/s) pra revisão visual.
   - Feedback 7537 (v3): imagem do iPhone fica **estourada/branca** → o script aplica por padrão `eq=gamma=0.8:contrast=1.12:brightness=-0.05:saturation=1.15` (`"grade"` troca, `"nenhum"` desliga). **Cortar colado no fim da fala**; o script segura a imagem sozinho (≤0,3s) onde ele já vira o rosto no começo/fim do trecho. Tela dividida **sem número de %** (foto cortada pela base com `"crop_y": "base"` pra esconder o selinho).
   - Conferir sempre que **áudio e vídeo têm a mesma duração** (`ffprobe`): música + voz em taxas diferentes encurtava o áudio e o final "travava".
   - Feedback 7538: corte **nem colado nem largo** — respiro natural de ~0,15s depois da última palavra (`respiro_fim`). O Samuel vira o rosto pro roteiro em quase todo fim de frase e o detector automático NÃO pega giro de olhar: revisar **toda ponta** com `scripts/pontas.py BRUTO work/segs.json folha.jpg` (fazer em folhas de 7 trechos pra enxergar) e marcar `segura_imagem` `{"v1": último quadro de frente}`. Se ele fala uma palavra inteira já virado (>0,4s), usar **corte pro produto** em tela cheia: overlay `{"at": t, "ate_fim": true, "cheia": true, "file": foto do produto}`.
   - Depois de renderizar: `scripts/fins.py FINAL work/segs.json saida` (últimos 0,6s de cada trecho, no vídeo final) e ler o texto da legenda inteiro procurando frase repetida/tropeço ("Ele já vem com… e ele já vem com") — o VAD junta o tropeço com a tomada boa se estiverem no mesmo trecho marcado.
   - **Fluxo sem travada (feedback do Vitor: "tem que deslizar como água")**: nunca congelar a imagem pra esconder giro de rosto. Onde ele vira depois de falar, o trecho termina no último quadro de frente e o próximo take entra direto; se ainda está terminando a palavra, congela no máx. 0,1s (`congela_max`). Conferir com `freezedetect=n=0.002:d=0.15` → tem que dar **0 congelamentos**.
7. Rodar UMA análise/render por vez (4 em paralelo estoura a memória da máquina).

## Alternância nos lotes

Num lote, alternar na ordem dos arquivos do Drive: 1º estilo 1, 2º estilo 2, 3º estilo 1, 4º estilo 2...
Continuar a alternância de onde o lote anterior parou.

## Pessoas

- **Mat (Matheus)**: barbudo, olhos claros.
- **Samuca**: cara limpa, cabelo grande.

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

- `Provas Sociais/`: prints do Telegram ("primeira venda").
- `Sobreposições/`: ícones com o Gloow App circulado, perfil "Samuca Sem Dores", vídeo do perfil, gravação de tela do app.
- Gravação de tela do app (`copy_3AAD4AD4-...mov`, 94s) — bons quadros parados: 6,5s "Marcas Virais"; 9s página da Nulle (com "Vídeos Prontos"); 11s links de afiliação com comissão; 23s site da Nulle ("regular seu cortisol").
