# Linguagem, construção e acabamento

Um perfil documenta três escolhas independentes. O renderer aplica construção/acabamento; o agente interpreta a linguagem do desenho ao criar a geometria. Nenhum preset muda automaticamente o formato de um rosto ou converte curvas existentes em origami.

## Escolha e precedência

1. Pedido explícito e referências do usuário definem o resultado. Uma exceção para uma arte pertence à cena; não modifica o padrão da coleção.
2. `--profile <nome-ou-caminho.json>` escolhe o perfil de partida; sem ele, use `style.profile` da cena.
3. Sem escolha na cena, cenas v2 usam `defaultProfile` de `<skill>/settings.json`, inicialmente `neutral`.
4. `style.drawing`, `style.construction` e `style.finish` da cena sobrescrevem recursivamente o perfil. Acabamento específico da camada sobrescreve o resultado da cena.

As quatro bases incluídas são `neutral`, `cutout`, `origami` e `layered-card`. Elas são alternativas de material/construção e não afirmam que o usuário aprovou uma linguagem de personagens. Defaults são conveniências substituíveis, não limites criativos.

A cena exportada inclui `resolvedStyle`. Ao reabri-la, ele é reutilizado; `--profile` permite começar por outro perfil. As opções explícitas de `style` ainda prevalecem. Cenas v1 sem escolha de perfil mantêm o acabamento anterior (`legacy-v1`) para não alterar os estudos silenciosamente.

## Registrar um estilo fixo

Crie um JSON em `assets/profiles/` ou no projeto. Parta de uma base e descreva concretamente as decisões aprovadas:

```json
{
  "id": "collection-style",
  "name": "Estilo da coleção",
  "drawing": {
    "references": ["referencias/personagens-aprovados.png"],
    "silhouettes": "Corpos compactos e mãos grandes; preservar vazios entre membros.",
    "faces": "Olhos simples, nariz por sombra e sobrancelhas recortadas.",
    "hair": "Massas amplas com poucas divisões internas.",
    "linework": "Sem contorno preto interno; borda externa branca.",
    "palette": "Escolhida por cena, mantendo contraste entre personagem e suporte."
  },
  "construction": {"kind": "cutout", "thickness": 0, "border": {"width": 6, "color": "#ffffff"}},
  "finish": {"texture": false, "surfaceShading": false, "shadow": {"enabled": false}}
}
```

O exemplo não constitui uma preferência atual do usuário. Referências são metadados para o agente ler: o renderer não abre imagens nem treina um modelo. Resolva os caminhos conforme o projeto/perfil e distribua as referências junto quando a portabilidade importar. Não invente que uma referência foi consultada.

Para fixar o padrão, salve `assets/profiles/<id>.json` e ajuste `settings.json` para `{"defaultProfile":"<id>"}` quando solicitado. Um perfil externo pode usar caminho absoluto no padrão local; para compartilhar, inclua-o na skill e use o slug. Isso muda o padrão sem bloquear instruções explícitas em um novo pedido.

Se o usuário pedir consistência estrita, mantenha as regras aprovadas e registre conflitos concretos antes de resolver uma exceção material. Anatomia e linguagem de traços não são switches de filtros.

## Sombra e autoria

Cada papel pode ter `finish.shadow` próprio. Use o perfil como condição inicial; ajuste distância, direção, desfoque, cor e opacidade pelo encaixe da peça e pela iluminação. Variações por camada não exigem criar outros perfis. Mantenha a direção da luz coerente, salvo múltiplas fontes intencionais.

Uma sombra gráfica desenhada pode ter qualquer contorno, cor e opacidade adequados ao estilo. Declare `role: shadow`, com `follows` e `clipTo`, em vez de forçar uma folha escura com textura e espessura. Essa sombra é exportada como camada separada. Sombras automáticas de contato continuam sendo efeitos das peças, não entradas extras no manifesto.
