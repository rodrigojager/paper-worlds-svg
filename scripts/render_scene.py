#!/usr/bin/env python3
"""Render an authored paper scene using Python's standard library only."""
import argparse
import copy
import html
import json
import math
import random
import re
from pathlib import Path

SLUG = re.compile(r'^[a-z][a-z0-9-]*$')
COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')
GEOMETRY = {
    'path': {'d'}, 'circle': {'cx', 'cy', 'r'},
    'ellipse': {'cx', 'cy', 'rx', 'ry'},
    'rect': {'x', 'y', 'width', 'height', 'rx', 'ry'},
    'polygon': {'points'}, 'polyline': {'points'},
    'line': {'x1', 'y1', 'x2', 'y2'},
}
COMMON = {'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'fill-rule', 'opacity'}
SKILL_ROOT = Path(__file__).resolve().parents[1]
ROLES = {'paper', 'ink', 'contour', 'shadow', 'highlight'}
BASE_STYLE = {
    'id': 'neutral', 'drawing': {},
    'construction': {'kind': 'layered', 'thickness': .8, 'border': {'width': 0, 'color': '#ffffff'}},
    'finish': {'texture': False, 'surfaceShading': False, 'edgeColor': '#27232d', 'edgeOpacity': .3,
               'rim': {'width': 0, 'color': '#fff8e7', 'opacity': .36},
               'shadow': {'enabled': True, 'color': '#251f32', 'opacity': .18,
                          'hardOpacity': .14, 'dx': 1, 'dy': 2, 'blur': 1.2}}
}


def merge(base, overrides):
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else copy.deepcopy(value)
    return result


def load_profile(value):
    if isinstance(value, dict):
        return copy.deepcopy(value)
    path = Path(value)
    if not path.is_file():
        path = SKILL_ROOT/'assets'/'profiles'/(str(value)+'.json')
    if not path.is_file():
        raise ValueError('Unknown style profile: ' + str(value))
    profile = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(profile, dict):
        raise ValueError('Profile must be an object')
    return profile


def resolve_style(scene, profile=None):
    style = scene.get('style', {})
    if not isinstance(style, dict):
        raise ValueError('style must be an object')
    # v1 retains its original rendering unless a style is selected explicitly.
    legacy = scene.get('version') == 1 and not style and profile is None
    if legacy:
        result = merge(BASE_STYLE, {'id': 'legacy-v1', 'construction': {'thickness': 1},
                        'finish': {'texture': True, 'surfaceShading': True, 'edgeOpacity': .38,
                                   'rim': {'width': .65}, 'shadow': {'opacity': .26, 'hardOpacity': .18}}})
    elif 'resolvedStyle' in scene and profile is None:
        result = copy.deepcopy(scene['resolvedStyle'])
    else:
        setting = json.loads((SKILL_ROOT/'settings.json').read_text(encoding='utf-8'))
        choice = profile if profile is not None else style.get('profile', setting['defaultProfile'])
        result = merge(BASE_STYLE, load_profile(choice))
    result = merge(result, {k:v for k,v in style.items() if k != 'profile'})
    scene['resolvedStyle'] = result
    scene['_legacy'] = legacy
    return result


def finite(value, low, high, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('Invalid ' + name)


def validate_finish(finish):
    if set(finish)-set(BASE_STYLE['finish']): raise ValueError('Unknown finish parameter')
    if set(finish['rim'])-set(BASE_STYLE['finish']['rim']): raise ValueError('Unknown rim parameter')
    if set(finish['shadow'])-set(BASE_STYLE['finish']['shadow']): raise ValueError('Unknown shadow parameter')
    for key in ('texture','surfaceShading'):
        if not isinstance(finish[key], bool): raise ValueError(key + ' must be boolean')
    finite(finish['edgeOpacity'], 0, 1, 'edgeOpacity')
    rim, shadow = finish['rim'], finish['shadow']
    finite(rim['width'], 0, 100, 'rim width')
    finite(rim['opacity'], 0, 1, 'rim opacity')
    if not isinstance(shadow['enabled'], bool): raise ValueError('shadow.enabled must be boolean')
    for key in ('opacity','hardOpacity'):
        finite(shadow[key], 0, 1, 'shadow.'+key)
    for key in ('dx','dy'):
        finite(shadow[key], -1000, 1000, 'shadow.'+key)
    finite(shadow['blur'], 0, 100, 'shadow.blur')
    for color in (finish['edgeColor'],rim['color'],shadow['color']):
        if not isinstance(color, str) or not COLOR.fullmatch(color): raise ValueError('Finish colors must be #rrggbb')


def layer_finish(scene, layer):
    finish = copy.deepcopy(scene['resolvedStyle']['finish'])
    # elevation is a convenient seed for individual shadows, never a restriction.
    if scene.get('_legacy') or layer.get('elevation') is not None:
        e = layer.get('elevation', 2)
        finish['shadow'].update(dx=.5+e*.22, dy=1+e*.6, blur=.55+e*.34)
    for alias in ('texture','surfaceShading'):
        if alias in scene: finish[alias] = scene[alias]
        if alias in layer: finish[alias] = layer[alias]
    return merge(finish, layer.get('finish', {}))


def validate(scene, profile=None):
    if scene.get('version') not in (1, 2) or not SLUG.fullmatch(scene.get('id', '')):
        raise ValueError('Expected version 1 or 2 and a slug id')
    style = resolve_style(scene, profile)
    if style['construction']['kind'] not in ('layered','cutout','origami'):
        raise ValueError('Unknown construction kind')
    finite(style['construction']['thickness'], 0, 100, 'construction.thickness')
    border = style['construction']['border']
    finite(border['width'], 0, 100, 'border.width')
    if not COLOR.fullmatch(border['color']): raise ValueError('Invalid border color')
    validate_finish(style['finish'])
    box = scene.get('viewBox')
    if not isinstance(box, list) or len(box) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in box) or min(box[2:]) <= 0:
        raise ValueError('viewBox must be [x,y,positive width,positive height]')
    if not scene.get('layers'):
        raise ValueError('Scene needs layers')
    if scene.get('background') and not COLOR.fullmatch(scene['background']):
        raise ValueError('background must be a #rrggbb color')
    ids = set()
    for layer in scene['layers']:
        ident = layer.get('id', '')
        if not SLUG.fullmatch(ident) or ident in ids:
            raise ValueError('Invalid or duplicate layer id: ' + ident)
        ids.add(ident)
        layer.setdefault('label', ident)
        layer.setdefault('assembly', ident)
        layer.setdefault('role', 'paper')
        if layer['role'] not in ROLES: raise ValueError('Unknown role: ' + str(layer['role']))
        physical = layer['role'] == 'paper'
        layer.setdefault('castsShadow', physical)
        layer.setdefault('receivesShadow', physical)
        if not isinstance(layer['castsShadow'],bool) or not isinstance(layer['receivesShadow'],bool):
            raise ValueError('castsShadow/receivesShadow must be booleans')
        if not physical and (layer['castsShadow'] or layer['receivesShadow']):
            raise ValueError('Only paper casts/receives automatic contact shadows')
        layer.setdefault('opacity', 1)
        finite(layer['opacity'], 0, 1, 'layer opacity')
        layer.setdefault('pivot', [box[0] + box[2]/2, box[1] + box[3]/2])
        if len(layer['pivot']) != 2 or not all(isinstance(v, (int,float)) and math.isfinite(v) for v in layer['pivot']):
            raise ValueError('Invalid pivot: ' + ident)
        if scene['_legacy']: layer.setdefault('elevation', 2)
        layer.setdefault('thickness', style['construction']['thickness'] if physical else 0)
        for key in ('elevation', 'thickness'):
            if key not in layer: continue
            if not isinstance(layer[key], (int, float)) or not math.isfinite(layer[key]) or not 0 <= layer[key] <= 100:
                raise ValueError('Invalid ' + key + ': ' + ident)
        if not physical and (layer['thickness'] != 0 or layer.get('finish') or layer.get('texture') or layer.get('surfaceShading')):
            raise ValueError('Ink, contours, shadows and highlights do not receive physical finish: ' + ident)
        if physical: validate_finish(layer_finish(scene, layer))
        layer.setdefault('geometryStatus', 'authored')
        if layer['geometryStatus'] not in ('authored', 'visible-only', 'reconstructed'):
            raise ValueError('Unknown geometryStatus')
        if not layer.get('shapes'):
            raise ValueError('Empty piece: ' + ident)
        for shape in layer['shapes']:
            tag = shape.get('tag')
            if tag not in GEOMETRY or set(shape) - GEOMETRY[tag] - COMMON - {'tag'}:
                raise ValueError('Unsupported shape/attributes in ' + ident)
            for attr in ('fill', 'stroke'):
                if attr in shape and shape[attr] != 'none' and not COLOR.fullmatch(str(shape[attr])):
                    raise ValueError('Use #rrggbb colors or none')
            if not shape.keys() & GEOMETRY[tag]:
                raise ValueError('Missing shape geometry')
    by_id = {l['id']:l for l in scene['layers']}
    order = {l['id']:i for i,l in enumerate(scene['layers'])}
    for layer in scene['layers']:
        for key in ('follows','clipTo'):
            if key in layer and layer[key] not in by_id:
                raise ValueError('Missing '+key+' target: '+str(layer[key]))
        if 'clipTo' in layer and order[layer['clipTo']] >= order[layer['id']]:
            raise ValueError('clipTo must name an earlier receiver')
        if layer['role']=='shadow' and not all(layer.get(k) for k in ('follows','clipTo')):
            raise ValueError('An authored shadow needs follows and clipTo')
        seen=set()
        current=layer
        while 'follows' in current:
            if current['id'] in seen: raise ValueError('Cycle in follows relationships')
            seen.add(current['id']); current=by_id[current['follows']]
    return scene


def esc(v):
    return html.escape(str(v), quote=True)


def shapes(layer, silhouette=False, color='#27232d', border=0):
    result = []
    for shape in layer['shapes']:
        attrs = {k: v for k, v in shape.items() if k != 'tag'}
        if silhouette:
            # Preserve holes, alpha and strokes; recolor physical material.
            if attrs.get('fill', '#000000') != 'none':
                attrs['fill'] = color
            if attrs.get('stroke', 'none') != 'none':
                attrs['stroke'] = color
            if border:
                attrs.update(stroke=color, **{'stroke-width':border*2,'stroke-linejoin':'round','stroke-linecap':'round'})
                attrs.pop('opacity', None)
        result.append('<' + shape['tag'] + ' ' + ' '.join(f'{k}="{esc(v)}"' for k, v in attrs.items()) + '/>')
    return ''.join(result)


def texture(seed):
    rng = random.Random(seed)
    fibers = []
    for i in range(360):
        x, y = rng.uniform(1, 94), rng.uniform(1, 94)
        length, dy = rng.uniform(.4, 1.7), rng.uniform(-.5, .5)
        fibers.append(f'<path d="M{x:.2f} {y:.2f}q{length/2:.2f} {dy:.2f} {length:.2f} {dy/2:.2f}" stroke="{"#fffdf5" if i%3 else "#302530"}" stroke-width="{rng.uniform(.25,.55):.2f}" opacity="{rng.uniform(.05,.16):.2f}" fill="none"/>')
    return '<pattern id="paper-fibers" patternUnits="userSpaceOnUse" width="96" height="96">' + ''.join(fibers) + '</pattern>'


def tint(color, amount):
    values = [int(color[i:i+2],16) for i in (1,3,5)]
    target = 255 if amount > 0 else 0
    return '#' + ''.join(f'{round(v+(target-v)*abs(amount)):02x}' for v in values)


def shaded_shapes(layer):
    result = shapes(layer)
    return re.sub(r'fill="(#[0-9a-fA-F]{6})"', lambda m: f'fill="url(#material-{m.group(1)[1:].lower()})"', result)


def highlights(layer, rim):
    result = []
    for shape in layer['shapes']:
        if shape.get('fill', '#000000') == 'none':
            continue
        attrs = {k:v for k,v in shape.items() if k in GEOMETRY[shape['tag']]}
        attrs.update({'fill':'none','stroke':rim['color'],'stroke-width':rim['width'],'stroke-opacity':rim['opacity']})
        result.append('<' + shape['tag'] + ' ' + ' '.join(f'{k}="{esc(v)}"' for k,v in attrs.items()) + '/>')
    return ''.join(result)


def clip_shapes(layer, posed=False):
    # clipPath cannot rely on a use that indirectly references another use/group.
    # Emit actual basic geometry; update receivers alongside the posed piece.
    geometry = shapes(layer)
    geometry = geometry.replace('fill-rule=', 'clip-rule=')
    if posed:
        geometry = re.sub(r'<(path|circle|ellipse|rect|polygon|polyline|line) ',
                          lambda m: m.group(0) + f'data-follow="{layer["id"]}" ', geometry)
    return geometry


def make_svg(scene, mode='paper', only=None):
    if 'resolvedStyle' not in scene:
        scene = validate(copy.deepcopy(scene))
    box = scene['viewBox']
    x, y, w, h = box
    boxstr = ' '.join(map(str, box))
    layers = scene['layers'] if only is None else [scene['layers'][only]]
    needed = {l['id'] for l in layers} | {l['clipTo'] for l in layers if 'clipTo' in l}
    dependencies = [l for l in scene['layers'] if l['id'] in needed]
    construction = scene['resolvedStyle']['construction']
    border = construction['border']
    defs = [texture(scene.get('seed', 23))]
    colors = {s['fill'].lower() for l in dependencies for s in l['shapes'] if COLOR.fullmatch(s.get('fill',''))}
    for color in sorted(colors):
        defs.append(f'<linearGradient id="material-{color[1:]}" x1="0%" y1="0%" x2="70%" y2="100%"><stop offset="0" stop-color="{tint(color,.08)}"/><stop offset="0.55" stop-color="{color}"/><stop offset="1" stop-color="{tint(color,-.055)}"/></linearGradient>')
    body = []
    if scene.get('background') and only is None:
        body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{scene["background"]}"/>')
    # Every receiver is present in defs even for a standalone attached-detail export.
    for layer in dependencies:
        ident = layer['id']
        f = layer_finish(scene, layer)
        geom, outline = shapes(layer), shapes(layer, True, f['edgeColor'])
        defs.append(f'<g id="geometry-{ident}">{geom}</g><g id="outline-{ident}">{outline}</g>')
        defs.append(f'<g id="cast-{ident}">{shapes(layer, True, f["shadow"]["color"])}</g>')
        defs.append(f'<clipPath id="clip-{ident}" clipPathUnits="userSpaceOnUse">{clip_shapes(layer)}</clipPath>')
        defs.append(f'<clipPath id="receiver-{ident}" clipPathUnits="userSpaceOnUse">{clip_shapes(layer, True)}</clipPath>')
        detail = ''
        if mode != 'flat' and layer['role']=='paper' and f['texture']:
            detail = f'<g data-texture="true" clip-path="url(#clip-{ident})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#paper-fibers)"/></g>'
        shading = shaded_shapes(layer) if f['surfaceShading'] else ''
        if f['rim']['width']: shading += highlights(layer, f['rim'])
        shading = f'<g data-shading="true">{shading}</g>' if shading and mode!='flat' and layer['role']=='paper' else ''
        defs.append(f'<g id="surface-{ident}"><use href="#geometry-{ident}"/>{shading}{detail}</g>')
        defs.append(f'<g id="pose-{ident}" data-pose="{ident}"><use href="#geometry-{ident}"/></g>')
    border_groups = {}
    if border['width'] and mode!='flat':
        for layer in layers:
            if layer['role']=='paper':
                group = layer.get('cutout', layer['assembly'])
                border_groups.setdefault(group, []).append(layer)
        for group, members in border_groups.items():
            for member in members:
                defs.append(f'<g id="border-{member["id"]}">{shapes(member,True,border["color"],border["width"])}</g>')
    drawn_borders=set()
    previous=[]
    for layer in layers:
        ident=layer['id']; physical=layer['role']=='paper'
        f=layer_finish(scene,layer); s=f['shadow']
        group=layer.get('cutout',layer['assembly'])
        if group in border_groups and group not in drawn_borders:
            backing=''.join(f'<g data-follow="{m["id"]}"><use href="#border-{m["id"]}"/></g>' for m in border_groups[group])
            body.append(f'<g data-border="{esc(group)}">{backing}</g>')
            drawn_borders.add(group)
        shadow=''
        if mode!='flat' and previous and only is None and physical and layer['castsShadow'] and s['enabled']:
            defs.append(f'<clipPath id="below-{ident}" clipPathUnits="userSpaceOnUse">' + ''.join(clip_shapes(p, True) for p in previous) + '</clipPath>')
            dx,dy,blur=s['dx'],s['dy'],s['blur']
            margin=max(w,h)*.2+max(abs(dx),abs(dy))+blur*3
            if mode=='paper':
                defs.append(f'<filter id="shadow-{ident}" filterUnits="userSpaceOnUse" x="{x-margin}" y="{y-margin}" width="{w+margin*2}" height="{h+margin*2}" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceAlpha" stdDeviation="{blur}"/><feOffset dx="{dx}" dy="{dy}" result="offset"/><feFlood flood-color="{s["color"]}" flood-opacity="{s["opacity"]}"/><feComposite operator="in" in2="offset"/></filter>')
            soft = f'<g data-shadow="soft" clip-path="url(#below-{ident})"><use href="#pose-{ident}" filter="url(#shadow-{ident})"/></g>' if mode=='paper' else ''
            hard = f'<g data-shadow="hard" display="{"none" if mode == "paper" else "inline"}" clip-path="url(#below-{ident})" opacity="{s["hardOpacity"]}"><g transform="translate({dx} {dy})"><g data-follow="{ident}"><use href="#cast-{ident}"/></g></g></g>'
            shadow = soft + hard
        thick = layer['thickness']
        edge = f'<g data-edge="true" opacity="{f["edgeOpacity"]}" transform="translate(0 {thick})"><use href="#outline-{ident}"/></g>' if mode!='flat' and physical and thick else ''
        clip = f' clip-path="url(#receiver-{layer["clipTo"]})"' if 'clipTo' in layer else ''
        effect = ' data-effect="shadow"' if layer['role']=='shadow' else ''
        hidden = ' display="none"' if mode=='flat' and layer['role']=='shadow' else ''
        body.append(f'<g id="layer-{ident}" data-layer="{ident}" data-role="{layer["role"]}" data-label="{esc(layer["label"])}" opacity="{layer["opacity"]}"{clip}{effect}{hidden}>{shadow}<g data-follow="{ident}">{edge}<use href="#surface-{ident}"/></g></g>')
        if physical and layer['receivesShadow']: previous.append(layer)
    title = esc(scene.get('title', scene['id']))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" data-paper-mode="{mode}" viewBox="{boxstr}" role="img" aria-labelledby="scene-title"><title id="scene-title">{title}</title><defs>{"".join(defs)}</defs>{"".join(body)}</svg>'


POSE_JS = r'''
function pose(layer, index, frame, explode) {
  const u = Math.max(0, Math.min(1, (frame - index * 0.65) / 36));
  const remaining = Math.pow(1 - u, 3);
  const angle = index * 2.39996323;
  const spread = explode * (20 + index * 1.6);
  const dx = Math.cos(angle) * (remaining * 65 + spread);
  const dy = remaining * 85 + Math.sin(angle) * spread;
  const rotate = (remaining * 13 + explode * 7) * (index % 2 ? 1 : -1);
  const scale = 1 - remaining * 0.1;
  const [px, py] = layer.pivot;
  return `translate(${dx.toFixed(4)} ${dy.toFixed(4)}) translate(${px} ${py}) rotate(${rotate.toFixed(4)}) scale(${scale.toFixed(5)}) translate(${-px} ${-py})`;
}
function allPoses(layers, frame, explode) {
  const byId = new Map(layers.map((layer, i) => [layer.id, {layer, i}]));
  const poses = new Map();
  function resolve(id) {
    if (poses.has(id)) return poses.get(id);
    const entry = byId.get(id);
    const transform = entry.layer.follows ? resolve(entry.layer.follows) : pose(entry.layer, entry.i, frame, explode);
    poses.set(id, transform);
    return transform;
  }
  layers.forEach(layer => resolve(layer.id));
  return poses;
}
'''


def preview(scene, svg):
    data = json.dumps(scene, ensure_ascii=True).replace('</', '<\\/')
    template = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pequenos mundos · inspeção vetorial</title>
<style>*{box-sizing:border-box}body{margin:0;background:#e9e4da;color:#292b36;font:15px system-ui}header{padding:28px 5vw 18px;display:flex;justify-content:space-between;align-items:end;gap:24px}h1{font:500 32px Georgia;margin:4px 0}small{letter-spacing:.1em;text-transform:uppercase}p{line-height:1.6}main{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;margin:0 4vw 32px}.stage{background:#f8f4ec;border:1px solid #d7d1c7;border-radius:18px;overflow:hidden;min-height:540px;display:grid;place-items:center}.stage>svg{width:100%;max-height:78vh}.controls{padding:24px;background:#faf7f1;border-radius:18px}label{display:block;margin:18px 0 6px}input[type=range],select{width:100%}button,select{padding:9px;border:1px solid #ccc1b4;background:#fffaf2;border-radius:8px;color:#292b36}button{cursor:pointer}#list{font-size:12px;max-height:180px;overflow:auto}#list button{display:block;width:100%;text-align:left;padding:5px;border:0;background:none}.stage[data-mode=flat] [data-shadow],.stage[data-mode=flat] [data-edge],.stage[data-mode=flat] [data-texture],.stage[data-mode=flat] [data-shading]{display:none}.stage[data-mode=vector] [data-shadow=soft]{display:none}.stage[data-mode=vector] [data-shadow=hard]{display:block}.stage[data-texture=off] [data-texture]{display:none}@media(max-width:800px){main{grid-template-columns:1fr}header{display:block}.stage{min-height:0}.stage>svg{max-height:none}h1{font-size:26px}}</style>
<header><div><small>Estudo de construção · SVG editável</small><h1>__TITLE__</h1></div><span id="stats"></span></header>
<main><div id="stage" class="stage" data-mode="paper">__SVG__</div><aside class="controls"><small>Inspecione a montagem</small><p>Peças físicas, detalhes e efeitos têm funções distintas. O perfil orienta o acabamento; as formas vêm do desenho autoral.</p><label>Acabamento</label><select id="mode"><option value="paper">Perfil atual · sombras suaves</option><option value="flat">Flat · somente as cores</option><option value="vector">Vetor estrito · sombra dura</option></select><label><input id="texture" type="checkbox" checked> Fibras de papel</label><label>Separação das peças <output id="spreadValue">0%</output></label><input id="spread" type="range" min="0" max="1" step="0.01" value="0"><label>Frame da montagem <output id="frameValue">120</output></label><input id="frame" type="range" min="0" max="140" value="120"><button id="play">Reproduzir montagem</button><label>Fundo</label><select id="bg"><option value="#f8f4ec">Marfim</option><option value="#232b38">Escuro</option><option value="#ffffff">Branco</option></select><label>Peças · clique para isolar</label><div id="list"></div><button id="showAll">Mostrar todas</button><p style="font-size:12px">A separação é uma inspeção 2D. Ela não simula câmera 3D ou versos do papel.</p></aside></main>
<script>const scene=__DATA__;__POSE__
const stage=document.querySelector('#stage'), svg=stage.querySelector('svg');
const frame=document.querySelector('#frame'), spread=document.querySelector('#spread');
function update(){const poses=allPoses(scene.layers,+frame.value,+spread.value);scene.layers.forEach((layer,i)=>{const t=poses.get(layer.id);svg.querySelector('[data-pose="'+layer.id+'"]').setAttribute('transform',t);svg.querySelectorAll('[data-follow="'+layer.id+'"]').forEach(el=>el.setAttribute('transform',t));});document.querySelector('#frameValue').value=frame.value;document.querySelector('#spreadValue').value=Math.round(+spread.value*100)+'%';}
function finish(){const mode=stage.dataset.mode;const textured=document.querySelector('#texture').checked;svg.querySelectorAll('[data-shadow],[data-edge],[data-shading],[data-texture],[data-effect],[data-border]').forEach(el=>{const hide=mode==='flat'||(el.dataset.shadow==='soft'&&mode==='vector')||(el.dataset.shadow==='hard'&&mode!=='vector')||(el.hasAttribute('data-texture')&&!textured);el.setAttribute('display',hide?'none':'inline');});}
frame.oninput=spread.oninput=update;document.querySelector('#mode').onchange=e=>{stage.dataset.mode=e.target.value;finish()};document.querySelector('#texture').onchange=e=>{stage.dataset.texture=e.target.checked?'on':'off';finish()};document.querySelector('#bg').onchange=e=>stage.style.background=e.target.value;
document.querySelector('#stats').textContent=scene.layers.length+' camadas · nenhum bitmap';
scene.layers.forEach(l=>{const b=document.createElement('button');b.textContent=l.label;b.onclick=()=>{svg.querySelectorAll('[data-layer]').forEach(g=>g.style.display=g.dataset.layer===l.id?'':'none')};document.querySelector('#list').append(b)});
document.querySelector('#showAll').onclick=()=>svg.querySelectorAll('[data-layer]').forEach(g=>g.style.display='');
let running=false, tickId;document.querySelector('#play').onclick=()=>{running=!running;document.querySelector('#play').textContent=running?'Pausar':'Reproduzir montagem';if(!running){clearInterval(tickId);return;}frame.value=0;spread.value=0;update();tickId=setInterval(()=>{frame.value=+frame.value+1;update();if(+frame.value>=140){clearInterval(tickId);running=false;document.querySelector('#play').textContent='Reproduzir montagem';}},1000/30);};update();window.paperPreview={scene,pose,allPoses,update};</script></html>'''
    return template.replace('__TITLE__', esc(scene.get('title', scene['id']))).replace('__SVG__', svg).replace('__DATA__', data).replace('__POSE__', POSE_JS)


def react_component(scene, svg):
    # Renderer-owned markup only. Runtime values only enter escaped attributes.
    # SVG is inline so every pose can be addressed and animated independently.
    return '''import React from 'react';
type Layer = {id: string; pivot: number[]; follows?: string};
const layers: Layer[] = ''' + json.dumps([{k:l[k] for k in ('id','pivot','follows') if k in l} for l in scene['layers']]) + ''';
const source: string = ''' + json.dumps(svg, ensure_ascii=True) + ''';
''' + POSE_JS.replace('function pose(layer, index, frame, explode)', 'function pose(layer: Layer, index: number, frame: number, explode: number)').replace('function allPoses(layers, frame, explode)', 'function allPoses(layers: Layer[], frame: number, explode: number)').replace('const poses = new Map();', 'const poses = new Map<string, string>();').replace('function resolve(id)', 'function resolve(id: string): string').replace('return poses.get(id);', 'return poses.get(id)!;').replace('const entry = byId.get(id);', 'const entry = byId.get(id)!;') + '''
// Supply a unique stable instanceId when rendering multiple copies inline.
export function PaperScene({frame = 120, explode = 0, instanceId = 'paper-scene', style}: {frame?: number; explode?: number; instanceId?: string; style?: React.CSSProperties}) {
  const safeId = 'p-' + Array.from(instanceId).map(c => c.codePointAt(0)!.toString(16)).join('-');
  const poses = allPoses(layers, frame, Math.max(0, Math.min(1, explode)));
  let markup = source.replace(/data-(pose|follow)="([^"]+)"/g, (_all, kind, id) => `data-${kind}="${id}" transform="${poses.get(id)}"`);
  // One linear pass: repeated full-string replacement is costly for detailed scenes.
  markup = markup.replace(/\\bid="([^"]+)"|href="#([^"]+)"|url\\(#([^)]+)\\)|aria-labelledby="([^"]+)"/g,
    (_all, id, href, url, label) => id ? `id="${safeId}-${id}"` : href ? `href="#${safeId}-${href}"` : url ? `url(#${safeId}-${url})` : `aria-labelledby="${safeId}-${label}"`);
  return <div style={{width: '100%', height: '100%', display: 'grid', placeItems: 'center', ...style}} dangerouslySetInnerHTML={{__html: markup}} />;
}
'''


def render(scene, out, overwrite=False, profile=None):
    scene = validate(copy.deepcopy(scene), profile)
    out = Path(out)
    if out.exists() and any(out.iterdir()) and not overwrite:
        raise FileExistsError('Output directory is not empty; choose a new directory or --overwrite')
    out.mkdir(parents=True, exist_ok=True)
    (out/'layers').mkdir(exist_ok=True)
    for mode, filename in [('paper','art.svg'), ('flat','art.flat.svg'), ('vector','art.vector.svg')]:
        (out/filename).write_text(make_svg(scene, mode), encoding='utf-8')
    for i, layer in enumerate(scene['layers']):
        (out/'layers'/f'{layer["id"]}.svg').write_text(make_svg(scene, only=i), encoding='utf-8')
    manifest_layers=[]
    for i,l in enumerate(scene['layers']):
        entry={k:l[k] for k in ('id','label','assembly','cutout','role','pivot','elevation','thickness','opacity','geometryStatus','follows','clipTo','castsShadow','receivesShadow') if k in l}
        entry.update(z=i,file=f'layers/{l["id"]}.svg',resolvedFinish=layer_finish(scene,l) if l['role']=='paper' else None)
        manifest_layers.append(entry)
    manifest = {'version': 2, 'scene': scene['id'], 'style':scene['resolvedStyle'], 'viewBox': scene['viewBox'], 'order': 'back-to-front', 'shadowModel': 'Per-paper 2D projection over earlier receivers; authored shadows are independent non-physical layers', 'layers': manifest_layers}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    (out/'scene.json').write_text(json.dumps({k:v for k,v in scene.items() if not k.startswith('_')}, indent=2, ensure_ascii=False), encoding='utf-8')
    svg = make_svg(scene)
    (out/'preview.html').write_text(preview(scene, svg), encoding='utf-8')
    (out/'PaperScene.tsx').write_text(react_component(scene, svg), encoding='utf-8')
    return len(scene['layers'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scene', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--profile', help='Built-in profile name or JSON profile path')
    args = parser.parse_args()
    count = render(json.loads(args.scene.read_text(encoding='utf-8')), args.out, args.overwrite, args.profile)
    print(f'Rendered {count} pieces to {args.out.resolve()}')
