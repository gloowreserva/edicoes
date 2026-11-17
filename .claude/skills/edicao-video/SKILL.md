---
name: edicao-video
description: Editar vídeos curtos verticais (TikTok) no padrão Gloow, nos estilos de edição 1, 2, 3 e 4 (1, 2 e 4 para vídeos falados; 4 = vídeo longo, hook em caixa, zoom só nas falas importantes, sem legenda: hook na tela, cortes de respiro, sobreposições em janela, selo de comentário; 1 com legenda e zoom, 2 limpo e sem legenda; 3 para B-roll sem fala: texto na tela e música do início ao fim). Use quando o Vitor mandar vídeos brutos no Google Drive para editar.
---

# Edição de vídeo — Estilos de edição 1, 2, 3 e 4

## Regras que valem para os dois estilos

1. **Hook obrigatório.** Nenhum vídeo sai sem hook. Topo, primeiros ~4s, texto branco com contorno preto grosso, 3 linhas curtas.
   - **Instantâneo**: o hook já aparece inteiro e no tamanho final no primeiro quadro (sem fade nem animação de entrada); só some com fade no fim.
   - Polêmico, mas sem restrição: não promete ganho, não parece venda.
   - Usar algo que a pessoa fala no vídeo como gancho. Escrever "ttk" no lugar de "TikTok".
2. **Começa sempre na fala.** Nada de trecho parado no início (o script corta até a primeira palavra).
3. **Corta respiros e pausas**, e também frases repetidas, tentativas refeitas e tropeços (via `remove` no config).
   - **Fala corrida entre takes:** os cortes seguem as palavras da transcrição, não o silêncio. Entre um take e outro sobra só uma folga mínima (`tail` 0,06s depois da última palavra + `lead` 0,03s antes da próxima), então a emenda soa como a pessoa falando sem parar, sem respiro nem olhada pra baixo. Pausas dentro da frase maiores que `gap_max` (0,25s) também são cortadas. Ajustáveis no config: `gap_max`, `lead`, `tail` (e `speech_db` para o nível de voz, se o áudio for muito baixo ou ruidoso).
   - O áudio é montado de uma vez, amostra por amostra, alinhado ao quadro, com micro-fade de 4 ms em cada emenda: sem soluço, sem estalo e sem dessincronizar.
   - **Repetição/travada (estilos 1 e 2):** quando a pessoa trava e repete a palavra ou a frase, fica **só a última tentativa** (a mais firme) e o corte liga direto nela. Margem mínima de erro.
   - A transcrição (`scripts/transcribe.py`) é literal, mantém repetições; rodar `python3 -I scripts/dedupe.py transcricao.json` para listar as repetições e colocar cada uma em `remove`.
   - O transcritor às vezes ainda junta duas tentativas numa só: onde houver vão estranho entre palavras, retranscrever o trecho com `python3 -I scripts/trecho.py audio.wav INICIO FIM` antes de decidir o corte.
   - Depois de cortar, conferir o trecho no vídeo editado (retranscrever) para garantir que a frase sai uma vez só.
4. **Selo rosa** "comenta PALAVRA" quando a pessoa pede o comentário.
5. **Sobreposições no momento da fala que combina** (quando fala do app, das marcas, da comunidade).
   - Vídeo de tela do app → **janela no topo** (`"type": "pip"`), nunca tela cheia. Gravação de tela que muda rápido vira quadro parado da tela certa.
   - Janela: borda arredondada + sombra, no topo, do lado da cabeça (pode pegar no rosto), bem visível, dentro da área segura do TikTok (abaixo de "Seguindo | Para você", longe dos botões da direita). Padrão: `"size": [560, 600], "y": 220`; com o Samuca (rosto mais alto no quadro) usar `"size": [520, 540], "y": 200` pra não pegar nos óculos. Pessoa muito perto da câmera: janela menor no canto (`"size": [420, 450], "x": 50, "y": 200`) — é o caso do Mat.
   - Cartão de imagem larga (ícones, print baixo): `"maxw": 760, "y": 130`, pra ficar acima dos olhos.
   - Se no vídeo bruto a pessoa já mostra o app no celular, deixar rodar sem cobrir.
   - Nenhuma sobreposição durante o hook (primeiros ~4,5 s do vídeo editado): lembrar que o vídeo começa na 1ª palavra, então somar o início da fala ao tempo do original.
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

## Estilo de edição 4 (vídeo longo)

Para vídeos falados mais longos. Mesma linha dos estilos 1 e 2 (começa na fala, cortes de respiro/repetição, selo de comentário), com estas diferenças:

- **Hook diferente**: caixa branca com texto preto no topo (`"hook": {"style": "box", ...}`), frase em formato de pergunta/curiosidade, 2–3 linhas curtas.
- **Zoom só nas falas importantes** (`"zoom_at": [[ini, fim], ...]` em tempo do original, `"zoom": 1.15`): a frase-chave, o número, a virada, a chamada. Fora disso, sem zoom.
- **Sem legenda** (`"captions": false`).
- **Sobreposições só o suficiente**: 1 a 3, em janela no topo (`"type": "pip"`).
- Legenda (estilo 1): erro de palavra que o `replace` não pega (frase quebrada entre blocos) corrige com `"word_fix": {"inicio_da_palavra": "texto"}` ("" apaga).

## Lotes com vários estilos do mesmo bruto

Quando o Vitor pedir, cada bruto é editado nos estilos 1, 2 e 4 (3 versões do mesmo vídeo, com hooks diferentes). Lotes grandes vão em remessas de 6 brutos (18 vídeos).

## Estilo de edição 3 (B-roll)

Para vídeos **sem fala** (a pessoa só aparece fazendo algo, posando etc.). Não precisa transcrever nem analisar o áudio.
- Num lote misturado, B-roll sai no estilo 3 e não conta na alternância 1/2. Sinal de B-roll na transcrição: o Whisper devolve só o próprio prompt ("Transcreva literalmente...") ou "É, é, eu, eu".

- **Texto na tela do primeiro ao último quadro**, sem fade: variante nova a partir do banco `hooks.md` (não reutilizar os de referência; não mencionar "2 mil seguidores") (formato viral, 2–3 frases, terminando com chamada tipo "Entra no meu perfil"). **No topo, dentro da área segura do TikTok**: começa ~300px abaixo do topo (abaixo de "Seguindo | Para você"), margem esquerda 90px e direita 150px (longe da foto de perfil, curtir, comentar), branco com contorno preto, mesmo tamanho. Nem colado no topo, nem no meio da tela. Sem emoji (a fonte não desenha). "ttk" no lugar de TikTok quando aparecer.
- **Música embutida no arquivo, do primeiro ao último segundo**, já no volume cheio (pular silêncio/introdução da faixa). Os vídeos vão para uma pasta de postagem automática, então a música tem que estar no arquivo.
- **Música**: não só inglesa — priorizar música brasileira que combine com o contexto (sertanejo, sons virais do TikTok). Se o Vitor subir MP3s numa pasta `Músicas` no Drive, usar esses. Sem isso, usar faixa livre de direitos do Mixkit (`mixkit.co`, licença livre para redes sociais; hosts `mixkit.co` e `assets.mixkit.co` liberados no ambiente).
- **Reaproveitar B-roll:** o Vitor pode pedir nova versão do mesmo B-roll com texto novo + música nova (salvar como `_v2`). Não repetir faixa nem texto da versão anterior.
- **Selo final chamativo**: no último ~1 s o texto sai e entra "GRUPO GRÁTIS / NA BIO" grande, amarelo em caixa rosa, com pop e tremida (6º argumento do script).
- Clipes curtos de B-roll (5–10 s) que vierem no meio de um lote de vídeos falados também saem no estilo 3, com texto curto (1–2 frases).
- Script: `python3 -I scripts/broll.py VIDEO MUSICA SAIDA "TEXTO" INICIO_MUSICA $'GRUPO GRÁTIS\nNA BIO'`.
- Exemplos de frases base do Vitor:
  - "Enquanto você tá aí só assistindo a vida dos outros, tem gente com menos de 100 seguidores fazendo venda todo dia no app rosa só de copiar e colar vídeos prontos com 1 clique e postar. Pra entender como, entra no meu perfil."
  - "Antes de ficar esperando o Shop pra começar de verdade no ttk, entra no meu perfil pra entender uma coisa: enquanto você tá aí parada achando que depende de 2000 seguidores pra vender, tem gente começando no app rosa com menos de 100 seguidores fazendo venda sem esperar liberar nada."

## Alternância nos lotes

Num lote, alternar na ordem dos arquivos do Drive: 1º estilo 1, 2º estilo 2, 3º estilo 1, 4º estilo 2...
Continuar a alternância de onde o lote anterior parou.

## Pessoas

- **Eliton**: barbudo, de óculos (subpasta "Eliton" no Stand By).
- **Mat (Matheus)**: sem óculos.
- **Samuca**: cara limpa, cabelo grande.

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

- Subir os vídeos editados com a ferramenta `create_file` do conector Google Drive (`base64Content` = referência `sha256:<hash>:<caminho absoluto>`, `contentMimeType` `video/mp4`, `disableConversionToGoogleType: true`).
- **Regra do Vitor: não mexer em nada no Drive** (não mover, renomear, apagar nem editar). Só **subir** os vídeos editados na pasta certa.
- Destino: pasta **"00 - ⏯️ POSTAGEM STAND BY (AGUARDANDO)"** (id `1Cx4WfPwmhR2UsuNGzEoPPcBaroDLofm4`, dentro da pasta raiz `1BEtIt9SzaappmPbInoOwEcDdHEVJ568n`), na subpasta da pessoa do vídeo:
  - Matheus (Mat): `14uHGLQTCvyS5E96B3aqG3u_zRXVVDabt`
  - Samuel (Samuca): `1fAuehTadroP1ovpUnmM9PaVB5a9fDvf8`
  - Claudio: `1Rv8F_dwkssWDNYMhzY2aL9DiYNGHHxh8`
  - Eliton: `1_vve7NIW_zznkj_r__lf6UgkVlZrU4v_`
  - Universo.glow: `1BhfIYAN-fU8NSddeFWwwYT7Z54_Oh75d`
- As outras pastas da raiz ("00 - Gravação Bruta", "00 - ▶️ POSTAGEM ON", "00 - Frases prontas", "Referências App rosa") não são tocadas.
