# Animação e textura

Prefira um SVG inline com grupos e defs compartilhados: mesma escala, origens estáveis e recorte de sombra entre peças. Um `<img src="art.svg">` é uma imagem única para o host e não expõe grupos internos ao React.

O componente gerado recebe `frame` (número de frame) e `explode` entre 0 e 1. No Remotion:

```tsx
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {PaperScene} from './PaperScene';

export const Achievement = () => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{backgroundColor: '#f4eee5'}}>
    <PaperScene frame={frame} instanceId="achievement-a" />
  </AbsoluteFill>;
};
```

É um exemplo de integração, não um projeto Remotion completo. Para usar de fato, registre uma `Composition`, escolha dimensões, fps e duração no projeto existente e execute seus checks/render. A montagem de exemplo termina por volta do frame 100; adapte tempos conforme fps e narrativa.

Toda posição deve ser função do frame e dos dados estáticos. Não use CSS transitions/animations, relógio real, estado acumulado ou `Math.random()` por render para renderizar vídeo. O botão de reprodução do HTML é apenas uma inspeção interativa; o slider usa a mesma função de pose e permite verificar frames fora de ordem.

As camadas conservam IDs, funções e pivôs. O vínculo `follows` compartilha a transformação do alvo, inclusive em cadeia, para detalhes e sombras não se soltarem. O `clipTo` é atualizado a partir da pose atual do receptor. Sombras gráficas independentes continuam sem espessura, textura ou projeção própria. A sombra automática de cada papel usa os parâmetros resolvidos de sua própria `finish.shadow`, e pode ser desligada individualmente.

As peças conservam IDs e pivôs. A demonstração desloca, gira e escala cada peça em 2D, com ordem de pintura fixa. Para abrir uma asa inteira, componha a transformação do assembly com a transformação individual de cada pena; mova o receptor de sombra e o emissor no mesmo sistema de coordenadas. Referências `<use>` no componente atualizam os recortes a partir das poses atuais.

Não existe z-index geral em uma pilha SVG: ordem do DOM determina pintura. Deslocar em Z no HTML não recompõe por si só a oclusão dos caminhos. Para câmera atravessando a cena ou papel virando e mostrando verso/lateral, use planos 3D, geometria adicional ou cena 3D de fato. Um fold projetado em SVG serve para amplitude limitada; dois polígonos não são uma simulação de papel.

Textura: o padrão vetorial tem seed fixo e coordenadas locais e é recortado pela peça antes da transformação. Não sobreponha uma textura fixa de tela: isso faz o objeto escorregar por baixo do grão. Fibras vetoriais continuam nítidas no zoom, mas vídeo/PNG final sempre tem resolução definida. Sombras com blur são filtros rasterizados no tamanho de saída, mesmo quando o arquivo fonte é SVG. Para exportação estritamente geométrica, use `art.vector.svg`, que troca blur por sombra dura.

Referências oficiais consultadas em 2026-11-02:

- https://www.remotion.dev/docs/animating-properties — animação orientada por frame.
- https://www.remotion.dev/docs/use-current-frame — frame atual no componente/Sequence.
- https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDropShadow — sombra SVG.
- https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feTurbulence — ruído procedural (alternativa aos traços vetoriais).
