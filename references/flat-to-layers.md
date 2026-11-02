# Referência flat e reconstrução

É possível usar duas etapas criativas sem tornar a geração de imagem uma dependência. Agentes sem ferramentas de imagem desenham a cena SVG diretamente. Agentes com ferramentas podem gerar um conceito flat e então reconstruí-lo. A skill não inclui um serviço nem um modelo gerador de PNG.

## Brief para gerar a referência opcional

Escolha primeiro o perfil de desenho e construção descrito em style-profiles.md. Use a ferramenta/skill de imagem disponível somente quando essa geração fizer parte do pedido. Adapte este texto:

> Crie [conceito] como projeto de recortes de cartolina. Composição [brief], silhueta [direção], [paleta por material]. Cores uniformes, contornos nítidos e fechados, sem gradiente, sombra, iluminação fotográfica, textura, perspectiva volumétrica contínua nem detalhes pintados que imitem relevo. Cada pena/pétala/face de dobra tem contorno próprio. Inclua riqueza de composição por recortes e sobreposições reais. Fundo transparente, sem texto. Esta imagem será reconstruída como peças vetoriais animáveis.

Essa imagem é uma **referência visual**, não uma especificação completa de fabricação. Para segmentação automática mais confiável, peça uma prancha adicional com peças inteiras, separadas por espaço e identificadas num arquivo externo, ou máscaras de IDs consistentes. Não pinte sombra na mesma máscara. Não confunda cores de identificação com paleta final.

## Extração disponível

```text
python <skill>/scripts/flat_to_scene.py reference.png --out extracted.scene.json --colors 10 --min-area 20
```

Depende de Pillow (`python -m pip install pillow` se necessário e apropriado ao ambiente). Quantiza as cores opacas, separa componentes conectados e extrai contornos de bordas de pixels, preservando buracos por `evenodd`. Não suaviza Bézier, não infere significado, não reconstitui partes escondidas e não descobre profundidade. Os contornos têm precisão da imagem de entrada e podem ficar serrilhados; depois de vetorizados, continuam sendo essa aproximação, não um ganho de detalhe. `--min-area` descarta regiões pequenas deliberadamente e é informado no relatório. Transparência parcial é limiarizada, sem preservar antialiasing. Imagens sem canal alfa mantêm o fundo como peça; remova/mascare conscientemente.

Cada peça começa com `geometryStatus: visible-only`. A ordem inicial é arbitrária (cor/componente); `elevation` inicial é zero. **Não renderize esse resultado como arte acabada sem revisão.**

## Reconstrução obrigatória para movimento

1. Migre para version 2 e classifique cada região como paper, ink, contour, shadow ou highlight. O extrator não infere essas funções. Defina follows/clipTo para detalhes e sombras. Identifique objetos e peças por significado, renomeie IDs e separe regiões que se tocam mas são papéis diferentes. Uma região da mesma cor pode conter vários objetos.
2. Defina o grafo de oclusão: qual peça passa atrás de qual. Ordene `layers`. Ciclos de entrelaçamento requerem dividir peças visuais, mantendo assembly/rig comum.
3. Reconstrua cada contorno oculto com geometria completa. Remova os recortes artificiais produzidos por objetos da frente. Marque `geometryStatus: reconstructed` somente quando isso tiver sido feito; `authored` indica desenho vetorial direto.
4. Simplifique a silhueta em curvas Bézier com poucos nós e controle visual. Preserve buracos, vazios, pontas e encaixes; não faça trace de sombras ou fibras.
5. Aplique a paleta final por material. A mesma cor pode aparecer em muitos níveis. Defina pivôs e eixos, depois adicione espessura, sombras e textura no renderer.
6. Abra a pilha e mova as peças pelo alcance pretendido. Partes sem verso ou lateral só suportam movimentos que não as exponham. Se não for possível reconstruir com confiança, registre a limitação e use amplitude menor.

Essa revisão é o ponto em que um trace automático se torna uma ilustração de papel organizada. Não prometa conversão perfeita de um PNG arbitrário por separação de cores.
