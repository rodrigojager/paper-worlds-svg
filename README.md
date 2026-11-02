# Pequenos mundos em SVG

Skill para agentes de IA criarem ilustrações vetoriais em camadas, com aparência de papel recortado, cartolinas empilhadas ou origami. Funciona por código, sem exigir um gerador de imagens.

A linguagem do desenho, a construção em papel e o acabamento são decisões independentes. Personagens, proporções e contornos seguem o brief e as referências escolhidas, enquanto a skill organiza geometrias, vínculos, materiais e sombras para edição e animação.

## Recursos

- Perfis opcionais `neutral`, `cutout`, `origami` e `layered-card`, além de perfis próprios com referências e regras de desenho.
- Borda externa branca por conjunto de peças para cutout.
- Camadas com funções distintas: `paper`, `ink`, `contour`, `shadow` e `highlight`.
- Sombras automáticas configuráveis por peça: deslocamento, desfoque, cor e opacidade.
- Sombras desenhadas exportáveis, com vínculo ao emissor e recorte pelo receptor.
- Textura de fibras vetoriais, espessura e acabamento opcionais.
- SVG composto, flat, sem filtros e SVGs individuais com alinhamento comum.
- Fonte JSON, manifesto, componente React controlado por frame e prévia HTML interativa.
- Extrator opcional de contornos de PNG flat, com preservação de buracos.

## Instalação no Codex

Clone na pasta de skills do seu Codex. No PowerShell, usando a localização padrão:

```powershell
git clone https://github.com/rodrigojager/paper-worlds-svg.git "$HOME/.codex/skills/paper-worlds-svg"
```

Se a pasta já existir, preserve as alterações locais antes de atualizar. Caso use `CODEX_HOME`, utilize sua pasta `skills` correspondente.

A entrada da skill é [SKILL.md](SKILL.md). Os scripts de renderização usam Python 3 e biblioteca padrão. Apenas a extração de PNG precisa de Pillow:

```powershell
python -m pip install pillow
```

## Uso com um agente

> Use $paper-worlds-svg para criar uma conquista que represente acolher pessoas novas. Escolha a linguagem do desenho conforme minhas referências e use cartolinas em camadas. Ajuste a distância e a intensidade das sombras por peça. Entregue a cena, os SVGs e uma prévia interativa.

## Renderização por linha de comando

Execute a partir da pasta deste repositório:

```powershell
python scripts/render_scene.py assets/style-lab.scene.json --out outputs/laboratorio --profile cutout
```

Abra `outputs/laboratorio/preview.html` para inspecionar as peças, trocar acabamento, isolar camadas, percorrer frames e reproduzir a montagem.

Outro exemplo incluído:

```powershell
python scripts/render_scene.py assets/garden.scene.json --out outputs/jardim
```

O jardim usa o contrato v1, preservado por compatibilidade. Novas cenas devem usar v2, como o laboratório.

## Sombras por peça

Cada papel pode sobrescrever o padrão do perfil:

```json
{
  "finish": {
    "shadow": {
      "enabled": true,
      "dx": 5,
      "dy": 9,
      "blur": 5,
      "opacity": 0.28,
      "hardOpacity": 0.22,
      "color": "#453752"
    }
  }
}
```

Use contato curto para peças próximas e projeções mais distantes/difusas para abas levantadas. A direção da luz deve permanecer coerente. `castsShadow: false` desliga a projeção de uma peça sem alterar as demais.

Detalhes impressos e efeitos gráficos não ganham textura, espessura ou sombra própria. Uma sombra autoral, como a de um nariz, usa `role: shadow`, `follows` e `clipTo` para acompanhar a peça e permanecer no receptor.

## Perfis e referências

`settings.json` define o perfil padrão, inicialmente `neutral`. Um perfil pode documentar formas de rosto, cabelo, proporções, paleta, tratamento de contornos e referências aprovadas. A cena pode escolher outro perfil ou sobrescrever suas opções.

Os perfis orientam o agente a desenhar a geometria. Selecionar `origami` em um SVG existente não cria automaticamente faces ou vincos. Os exemplos deste repositório demonstram o contrato técnico e não impõem uma linguagem de personagens.

## Documentação

- [Instruções da skill](SKILL.md).
- [Formato de cena e funções das camadas](references/scene-format.md).
- [Perfis de desenho, construção e acabamento](references/style-profiles.md).
- [Animação e integração com Remotion](references/animation.md).
- [Extração de referências flat e reconstrução](references/flat-to-layers.md).

## Limites

A composição e as sombras são aproximações 2D. Versos, laterais, câmeras atravessando a cena e dobras físicas exigem geometria ou rig adicionais. O componente React é preparado para receber frames de um host como Remotion, mas não inclui um projeto de vídeo completo.

SVGs com sombras suaves usam filtros rasterizados durante a exibição/renderização. `art.vector.svg` dispensa filtros e utiliza projeções duras. A extração de PNG recupera contornos visíveis; profundidade, significado das regiões e partes ocultas precisam de revisão pelo agente.
