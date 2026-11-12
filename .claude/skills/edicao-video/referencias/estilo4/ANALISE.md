# Estilo 4: referências (material bruto, ainda NÃO é regra)

Origem: pasta do Drive enviada pelo Vitor em 2026-11-12, com exemplos que a marca mandou.
A pasta tem 9 vídeos (o Vitor falou em 10) e mais a subpasta "Sobreposições", que foi ignorada de propósito.
Nada foi alterado no Drive: os arquivos só foram baixados pra leitura.

Todos os exemplos são **anúncios estilo UGC do suplemento de magnésio Nulle**: 5 tipos de magnésio + 2 aminoácidos, sachê, sabor pink lemonade.
Tema central: **cortisol** (rosto inchado, "pochete", sono, ansiedade).
Formato: vertical 9:16 (1080x1920 ou 720x1280), 30fps (um a 60fps).

As transcrições, geradas automaticamente pelo Whisper, estão em `transcricoes/`. Os nomes de produto saem errados às vezes ("Nully", "Anule" = Nulle).

## Visão geral

| # | Arquivo | Duração | Tipo | Legenda / texto na tela | Áudio |
|---|---------|---------|------|-------------------------|-------|
| 01 | E2L | 49s | Falado, talking head, produto na mão | 1 palavra por vez, CAIXA ALTA, branca, fonte serifada pesada, meio da tela | Só voz (pausas em silêncio) |
| 02 | nulle-04-hk4 | 91s | Falado, jaleco de nutri | 2–4 palavras, caixa alta condensada, branco + **palavra-chave em amarelo** | Voz, música baixa |
| 03 | 0902 | 67s | Falado + **iPad desenhando/riscando** um infográfico | 1–3 palavras, caixa alta, branca/amarela, pequena, no meio | Voz contínua, zero respiro |
| 04 | Body1 | 17s | **Sem fala**, música, gestos + imagens sobrepostas | Frase-tópico em caixa branca (estilo nativo do TikTok), imagem ilustrativa abaixo | Só música |
| 05 | ARTUR VIRAL 05 | 37s | **Sem fala**, música viral, "checklist" de sintomas com gestos | Texto nativo do TikTok (caixa branca, minúsculas, emoji) | Música viral |
| 06 | E1C | 76s | Falado (mesma criadora do 01) | Igual ao 01 + print de depoimento real no canto superior | Só voz |
| 07 | Criativo01 Thay | 34s | **Sem fala**, mesmo roteiro do 05 com outra criadora | Fonte arredondada branca com contorno azul, entrando por animação, emojis | Só música |
| 08 | Criativo11 | 67s | Falado, abre com **sequência de fotos 30%→10% de gordura** no topo | Palavras-chave soltas em **verde com contorno** (não legenda contínua) | Voz + música de fundo |
| 09 | D6-HK2 | 113s | Falado, abre com **3 rostos "baixo/médio/alto cortisol"** em PIP | 1 palavra por vez, caixa alta branca (igual ao 01) | Voz + música de fundo |

## Estrutura de roteiro (o que se repete)

1. **Hook nos primeiros 2–5s**: provocação sobre cortisol ou magnésio, quase sempre com um **visual de comparação** (antes/depois, Barbie inchada→fina, % de gordura, rosto baixo/médio/alto cortisol, desenho no iPad).
2. **Lista de sintomas ou benefícios**, numerada ("1, 2, 3", "1º dia / 3º dia / 7º dia", "isso é sinal de cortisol alto" repetido).
3. **Virada pro produto**: "o problema é que existe mais de um tipo de magnésio…" e daí a Nulle junta os 5 tipos + 2 aminoácidos.
4. **Prova e segurança**: Anvisa, "suplemento e não medicamento", depoimentos, "muitas unidades vendidas".
5. **Modo de uso**: um sachê antes de dormir, sabor pink lemonade (em vários aparece **misturando e bebendo**).
6. **CTA com urgência**: link / lojinha / "toque abaixo", promoção, estoque acabando.

## Edição: padrões observados

- **Corte**: talking head com poucos cortes de câmera (o 06 não tem nenhum). Nos sem fala, um corte a cada ~2–3s, um por sintoma.
- **Respiro**: varia. O 03 e o 08 têm zero pausa (bem acelerados). O 01, o 06 e o 09 deixam pausas curtas (<1s).
- **Sobreposições**: imagem pequena em janela ou círculo no canto superior (01, 06), print de depoimento ou de FAQ do site (01, 06, 08), imagens ilustrativas no meio (04).
- **Produto sempre visível**: na mão ou na mesa, praticamente o vídeo inteiro nos falados.
- **CTA visual**: seta vermelha + "TOQUE ABAIXO E SAIBA MAIS" (04). Nos outros o CTA é só falado.
- **Volume**: o 01 e o 06 estão baixos (~-36dB na fala). Os outros, ~-23dB.

## Duplicados e famílias
- O 05 e o 07 têm o mesmo roteiro ("Como o CORTISOL mudou sua aparência"), com criadores e estilos de texto diferentes.
- O 01 e o 06 são da mesma criadora e do mesmo estilo de legenda.
- O 02 e o 09 compartilham o trecho dos "5 tipos de magnésio" quase palavra por palavra.

## Primeira edição de teste (4C, provisória)

- Bruto: `copy_3C9BE62D-....mov` (3min36, sem fala, só gestos), o mesmo roteiro do 05/07.
- Replicado o **05 (ARTUR VIRAL)**: 13 cenas de ~2,5–3s escolhidas do bruto, os mesmos textos e emojis, a música do 05.
- Script: `scripts/estilo4c.py`. Config de exemplo: `exemplos/estilo4c_cortisol_nulle.json`.
- Texto: estilo "clássico" do TikTok (caixa branca arredondada por linha, Inter SemiBold 50, preto, emoji Noto), no meio da tela. Desce quando o produto ou o copo ocupa o meio.
- Leve ajuste de cor (contraste 1,04, saturação 1,12). Música normalizada (-14 LUFS) com fade de 0,6s no fim.
- Aguardando o retorno do Vitor pra virar regra.

### v2: sobreposições (o Vitor pediu: são obrigatórias)
- Vêm da pasta `Sobreposições` do primeiro Drive (da marca, só leitura).
- Ficam em cartão com borda branca, canto arredondado e sombra, no topo ao lado da cabeça. Ficam em **lugares parecidos com a referência, com uma leve mudança** (ex.: no 05 a pochete fica em cima à esquerda; aqui a cabeça está à esquerda, então foi pra direita).
- Mapeamento usado: hook → antes/depois de rosto (IMG_6286); pochete → Apron Belly/FUPA (d0a6c85a); rosto inchado → sequência de mandíbula 30→25→20→15% (745662C4, 6120FB2C, 0AE01E61, 0EFE80F7); preparo → mixer com drink rosa (IMG_6292); final → print de depoimento (IMG_7025).
- Não usados: a gravação de tela (vídeo de outra criadora) e o antes/depois de emagrecimento (IMG_6796, pode parecer promessa de resultado).
- Texto em print precisa de largura ≥ 470px; imagem simples, 320–430px.
