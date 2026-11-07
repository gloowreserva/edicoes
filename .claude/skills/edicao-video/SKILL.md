---
name: edicao-video
description: Editar vídeos curtos verticais (TikTok) no padrão Gloow — "estilo de edição 1": corta respiros, começa na fala, hook na tela, legenda animada, zoom alternado, sobreposições e selo de comentário. Use quando o Vitor mandar um link do Google Drive com vídeos brutos para editar.
---

# Edição de vídeo — Estilo de edição 1

Padrão aprovado pelo Vitor nos 4 primeiros vídeos (IMG_7421, IMG_7423, IMG_7897, IMG_7923).
O **estilo 2** (menos informação, às vezes sem legenda) ainda está sendo definido e **não** está aqui.

## Regras do estilo 1

1. **Começa sempre na fala.** Nada de trecho parado no início (o script corta até a primeira palavra).
2. **Corta respiros e pausas**, e também frases repetidas / tropeços (via `remove` no config).
3. **Hook** no topo, nos primeiros ~4s: texto branco, contorno preto grosso, 3 linhas curtas.
   - Polêmico, mas sem restrição: não promete ganho, não parece venda.
   - Usar algo que a pessoa fala no vídeo como gancho.
   - Escrever "ttk" no lugar de "TikTok".
4. **Legenda da fala**: 2–3 palavras por vez, branca com contorno preto, terço de baixo, entrada com "pop".
   - Corrigir erros da transcrição via `replace` (ex.: "tiktok"→"ttk", "chat ept"→"ChatGPT", "de ar"→"de IA", "built"→"bio", "Nuri"→"Nulle", "glow"→"GLOOW").
5. **Zoom de 10% alternado** a cada corte.
6. **Sobreposições** (4 a 7), cada uma no momento da fala que combina:
   - prints de prova social → cartão inclinado subindo com quique;
   - vídeos de tela do app → tela cheia com fade.
   - Não colocar print de prova social de outra pessoa logo depois de alguém falar do próprio faturamento (parece que é dele).
   - Perfil só da própria pessoa do vídeo (perfil do Samuca só em vídeo do Samuca).
7. **Selo rosa** "comenta PALAVRA" quando a pessoa pede o comentário.
8. Sinalizar ao Vitor promessas de ganho que estejam na fala (ex.: "300 reais em 10 dias") — podem dar restrição.

## Passo a passo

1. **Rede**: o ambiente precisa liberar `drive.google.com`, `drive.usercontent.google.com`, `docs.google.com`, `www.googleapis.com` e os hosts do Hugging Face (`huggingface.co`, `cdn-lfs.huggingface.co`, `cdn-lfs.hf.co`, `cdn-lfs-us-1.hf.co`, `cas-bridge.xethub.hf.co`, `us.aws.cdn.hf.co`, `cas-server.xethub.hf.co`).
2. **Instalar**: `pip install gdown faster-whisper pillow-heif`.
3. **Listar a pasta do Drive** (gdown só para listar; o download via gdown falha no proxy):
   ```python
   import gdown
   for f in gdown.download_folder(URL_DA_PASTA, skip_download=True, quiet=True): print(f.id, f.path)
   ```
4. **Baixar cada arquivo com curl**:
   `curl -sSL -o ARQUIVO "https://drive.usercontent.google.com/download?id=ID&export=download&confirm=t"`
   - Imagens `.PNG` do iPhone às vezes são HEIC: converter com `pillow_heif` antes de usar.
5. **Transcrever**: `ffmpeg -i VIDEO -vn -ac 1 -ar 16000 audio.wav` e depois
   `HF_HUB_DISABLE_XET=1 python3 -I scripts/transcribe.py audio.wav transcricao.json medium`.
6. **Escrever o config** (ver `exemplos/IMG_7421.json`): vídeo, transcrição, `remove`, `replace`, `hook`, `stickers`, `overlays` (tempos do vídeo **original**; o script remapeia).
7. **Editar**: `python3 -I scripts/edit.py config.json` (corta trecho por trecho para não estourar memória; ~2–5 min por vídeo).
8. **Conferir quadros** (hook legível, sobreposição certa, legenda) antes de mandar ao Vitor.

## Material de apoio no Drive (pasta do Vitor)

- `Provas Sociais/`: prints do Telegram ("primeira venda").
- `Sobreposições/`: ícones com o Gloow App circulado, perfil "Samuca Sem Dores", vídeo do perfil, gravação de tela do app.
- Gravação de tela do app (`copy_3AAD4AD4-...mov`, 94s): 0–5s home "Olá Samuca"; 6–8s "Marcas Virais"; 8–10s página da Nulle; 10–12s e 16–21s links de afiliação com comissão; 13–15s e 22–31s site da Nulle (magnésio).
