---
name: paper-worlds-svg
description: Crie arte SVG em camadas animáveis, com linguagem de desenho escolhida por referências e construção em recorte, papel empilhado ou origami. Use para personagens, medalhas e dioramas vetoriais, com perfis de estilo e funções distintas para papel, detalhes, contornos, sombras e brilhos.
---

# Pequenos mundos em SVG

Preserve edição e animação por camadas, deixando o desenho responder ao brief. A organização vetorial não impõe anatomia, curvas, rostos, cabelo, paleta nem contornos. Os exemplos incluídos demonstram o contrato técnico; não são um estilo visual aprovado pelo usuário.

## Separe as decisões criativas

Leia [style-profiles.md](references/style-profiles.md) ao definir, selecionar ou fixar um estilo.

- **Desenho:** proporções, silhuetas, angularidade, expressões, olhos, cabelo e representação do volume. Um nariz pode ser definido por contorno, planos de cor, recorte ou sombra. Não transforme todas essas escolhas em contornos escuros ou folhas físicas.
- **Construção:** cutout plano, peças empilhadas ou faces de origami. Borda branca externa é uma escolha independente do estilo do rosto. Origami exige desenhar faces e vincos; não é um filtro sobre um desenho pronto.
- **Acabamento:** textura, espessura, filetes, iluminação e sombras. Pode variar por cena e peça sem alterar o desenho. Não acrescente brilho, fibras ou bordas sem justificativa no perfil/brief.

O padrão para cenas novas é `neutral`, em `settings.json`. `cutout`, `origami` e `layered-card` são bases opcionais, não estilos obrigatórios ou reproduções de franquias. Um pedido explícito prevalece sobre o padrão. Para consistência, registre referências e decisões aprovadas num perfil reutilizável; não promova uma experiência isolada a padrão fixo.

## Escolha o fluxo

**Conceito → formas vetoriais → organização → acabamento** funciona sem gerador de imagens. Use Bézier, polígonos ou primitivas conforme a linguagem escolhida. Preserve a cena JSON como fonte.

**PNG flat → extração → reconstrução semântica → acabamento** é opcional. Leia [flat-to-layers.md](references/flat-to-layers.md) quando houver raster. Cor não identifica peça nem profundidade. Um trace só recupera áreas visíveis e não distingue impressão, contorno e sombra por significado.

## Composição e camadas

Traduza o tema numa ação ou cena com silhueta legível e hierarquia de massas. Use vazios, ritmos e sobreposições. A riqueza pode vir de curvas orgânicas, planos angulares ou detalhes gráficos conforme as referências; não exige excesso de peças ou ornamentos.

Leia [scene-format.md](references/scene-format.md) ao usar o renderer. Cada camada tem função explícita:

- `paper`: peça física; pode receber espessura, textura e sombra de contato.
- `ink`: detalhe desenhado/impresso, sem relevo automático.
- `contour`: linha ou contorno gráfico, sem tratamento de papel.
- `shadow`: sombra desenhada exportável; acompanha seu emissor e é recortada pelo receptor.
- `highlight`: área de luz/brilho desenhada, sem espessura nem sombra própria.

Use `follows` para detalhes/efeitos acompanharem a peça e `clipTo` para limitar a pintura ao suporte. Reconstrua contornos ocultos para o movimento pretendido. Use `assembly` para organizar objetos e um mesmo `cutout` nas peças físicas que compartilham uma borda externa única. Não rodeie cada olho ou mecha com borda branca como adesivos separados.

**Dê liberdade à sombra de cada peça.** O perfil é um ponto de partida. Ajuste `finish.shadow` por camada para distância aparente, intensidade, desfoque, cor e direção coerente com a luz. Papel encostado pode pedir contato curto; uma aba levantada pode pedir projeção mais distante e difusa. `elevation` é um atalho inicial opcional, não um nível obrigatório. Desligue sombras onde atrapalhem. Se o nariz usa `role: shadow`, evite duplicá-la com sombra automática excessiva.

Textura acompanha a peça com seed estável. Fibras vetoriais são opcionais e têm escala apropriada; cutout pode preferir superfícies limpas. Filtros de desfoque são rasterizados durante a exibição/renderização; a variante sem filtros usa projeções duras.

## Entrega e validação

```text
python <skill>/scripts/render_scene.py scene.json --out <destino> --profile cutout
```

`--profile` é opcional; a cena também pode escolher/incorporar um perfil. O renderer gera arte composta, flat, sem filtros, SVGs individuais, manifesto com funções/vínculos/acabamento resolvido, componente React por frame e prévia. Leia [animation.md](references/animation.md) para Remotion e limites de 2.5D.

Inspecione arte pronta, flat e separada, em miniatura e ampliação. Confira buracos, recortes, tangências, borda única, sombras por peça e vínculos em movimento. Verifique XML, IDs, referências, viewBox comum e ausência de raster. Detalhes presos à peça não se soltam ao separar a pilha; sombras acompanham emissor e receptor. O mesmo frame deve gerar a mesma pose fora de ordem.

Entregue uma nota breve sobre estilo, referências, reconstruções e validação. `garden.scene.json` e `style-lab.scene.json` exemplificam o contrato, não uma direção artística a copiar. Preserve artes anteriores e use pasta nova para experimentos. Cenas v1 conservam o comportamento antigo por compatibilidade; crie cenas v2 para o novo contrato.
