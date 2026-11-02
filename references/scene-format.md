# Cena v2: formas, funções e acabamento

O renderer usa Python 3 e biblioteca padrão. Crie cenas com `version: 2`, `id` slug, `title`, `viewBox: [x,y,width,height]`, `seed` opcional e `layers` em ordem de trás para frente. `background` é uma cor opcional; omita para transparência.

## Perfil da cena

```json
{
  "version": 2,
  "id": "my-scene",
  "title": "Minha cena",
  "viewBox": [0, 0, 1000, 1000],
  "style": {
    "profile": "neutral",
    "drawing": {"faces": "Nariz definido por sombra, sem contorno preto."},
    "construction": {"kind": "layered", "thickness": 0.8, "border": {"width": 0, "color": "#ffffff"}},
    "finish": {
      "texture": false,
      "surfaceShading": false,
      "edgeColor": "#27232d",
      "edgeOpacity": 0.3,
      "rim": {"width": 0, "color": "#fff8e7", "opacity": 0.36},
      "shadow": {"enabled": true, "dx": 1, "dy": 2, "blur": 1.2, "color": "#251f32", "opacity": 0.18, "hardOpacity": 0.14}
    }
  },
  "layers": []
}
```

O exemplo omite as camadas de propósito: adicione geometrias para renderizar. Todos os campos do perfil são opcionais e mesclados com a base escolhida. `drawing` é orientação registrada para o agente, não uma transformação automática das geometrias. Leia [style-profiles.md](style-profiles.md) para referências e padrão fixo.

`construction.kind` aceita `layered`, `cutout` e `origami`. A construção das faces é autoral. `border.width` é a extensão da borda externa em unidades do viewBox; zero desliga. A borda é um fundo geométrico branco/colorido sob a união das peças de um mesmo `cutout` (ou `assembly` como fallback). Não usa dilatação raster nem borda nos detalhes impressos. Grupos intercalados no DOM exigem inspecionar a oclusão; esse fundo é inserido na primeira peça do grupo. Vazios muito estreitos podem fechar pela largura escolhida.

## Papel e sombra por peça

```json
{
  "id": "raised-flap",
  "label": "Aba levantada",
  "role": "paper",
  "assembly": "character",
  "cutout": "whole-character",
  "pivot": [500, 400],
  "thickness": 1.2,
  "castsShadow": true,
  "receivesShadow": true,
  "finish": {
    "texture": true,
    "rim": {"width": 0.3},
    "shadow": {"enabled": true, "dx": 5, "dy": 9, "blur": 5, "opacity": 0.28, "hardOpacity": 0.22, "color": "#453752"}
  },
  "shapes": [{"tag": "path", "d": "M500 400L620 310L590 440Z", "fill": "#dc765f"}]
}
```

A sombra de cada papel tem seus próprios parâmetros, sem obrigação de usar os valores do perfil. `dx`/`dy` indicam deslocamento, `blur` controla difusão e `opacity` intensidade na versão suave. `hardOpacity` é a intensidade da alternativa sem filtros. Para uma peça encostada, experimente distância e desfoque pequenos; para uma aba afastada, maiores, mantendo coerência da luz. Valores são unidades da cena, não pixels fixos de saída.

`elevation` continua disponível como atalho opcional: inicializa dx=.5+e*.22, dy=1+e*.6, blur=.55+e*.34. Depois, `finish.shadow` da peça prevalece campo a campo. Não é obrigatório usar elevation. `castsShadow: false` desliga a projeção daquela peça; `receivesShadow: false` exclui a peça da união de receptores automáticos. `finish.shadow.enabled: false` também desliga sua projeção. Não é preciso desabilitar as sombras da cena inteira para tratar uma peça de forma diferente.

Sombras automáticas só caem sobre os papéis anteriores que aceitam projeção. O modelo é 2D e não faz iluminação física nem escolhe o receptor mais próximo em 3D. Elas são efeitos anexados ao papel, não camadas adicionais no manifesto.

## Detalhes e efeitos independentes

`role` aceita `paper` (default), `ink`, `contour`, `shadow` e `highlight`. As quatro últimas funções não recebem textura, espessura, filete, gradiente automático ou sombra própria. Cor e opacidade continuam sob autoria. São exportadas como SVGs próprios.

```json
{
  "id": "nose-shadow",
  "role": "shadow",
  "follows": "nose",
  "clipTo": "face",
  "opacity": 0.24,
  "shapes": [{"tag": "path", "d": "M510 420Q535 442 550 428L530 460Z", "fill": "#a65d61"}]
}
```

O exemplo pressupõe `face` antes dessa sombra e uma camada `nose` em qualquer posição válida. `follows` herda a transformação da peça emissora; `clipTo` limita a sombra à geometria do rosto na pose atual. A sombra não é tratada como uma folha escura. Ajuste `castsShadow` do nariz quando essa sombra gráfica já representa seu volume para evitar duplicação.

Para nariz representado apenas por sombra, não é obrigatório desenhar uma peça de nariz: a sombra pode seguir `face`. Um traço preto pode ser `role: contour`, com `fill: none` e `stroke`, e seguir o rosto. Um olho pode ser `ink`; um brilho pode ser `highlight`. Não force uma camada de contorno em estilos definidos por sombra ou cor.

`follows` é opcional para detalhes soltos e obrigatório para `shadow`, assim como `clipTo`. O alvo de clipTo deve existir antes da camada na pintura; follows pode apontar para uma peça posterior, mas ciclos são recusados. Vincule detalhes ao suporte para que não se soltem na animação. É um vínculo rígido de transformação 2D; `assembly` sozinho continua sendo organização, não uma árvore de rig.

O SVG individual de um detalhe/sombra inclui a geometria receptora apenas em defs, para manter o recorte sem pintar o suporte. Ao animar arquivos individuais externamente, o host deve preservar esses vínculos; o componente completo gerado já os aplica.

## Geometria e compatibilidade

IDs são únicos e seguem `[a-z][a-z0-9-]*`. `pivot` usa coordenadas globais. `shapes` aceita path, circle, ellipse, rect, polygon, polyline e line, com atributos geométricos usuais. Cores fill/stroke são #rrggbb ou none; são aceitos stroke-width, stroke-linecap, stroke-linejoin, fill-rule e opacity. Para vazados, use subcontornos e evenodd. Não são aceitos SVG arbitrário, fontes ou imagens.

Uma camada pode conter múltiplas formas de uma mesma função. Use ink/contour separados se não devem ganhar espessura junto da peça. `geometryStatus` aceita authored, visible-only e reconstructed. A extração raster começa com visible-only e exige revisão semântica.

Cenas v1 sem perfil preservam os defaults originais: todos os itens sem role são papel. Elas não ganham classificação semântica automática. Para migrar, use version 2, declare papéis/vínculos e remova antigos valores globais `texture`/`surfaceShading` se desejar herdar o perfil; esses aliases explícitos continuam sobrepondo o perfil por compatibilidade. A camada pode usar `finish` sem migrar todo o desenho para experimentar sombras individuais.

## Saídas

- scene.json com resolvedStyle, para preservar a configuração resolvida.
- art.svg com acabamento; art.flat.svg sem efeitos de material/sombra/borda; art.vector.svg sem filtros, com sombras duras.
- layers/id.svg para todas as funções, com viewBox comum.
- manifest.json com role, follows, clipTo, parâmetros por peça e ordem.
- PaperScene.tsx, componente React com frame, explode e instanceId; IDs de defs são prefixados por instância.
- preview.html inline, abrindo por file://, com acabamento, fundo, textura, frame, separação e isolamento.

O renderer recusa pasta não vazia salvo --overwrite explícito. Preserve edições manuais antes de regenerar.
