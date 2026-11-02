#!/usr/bin/env python3
"""Extract visible color components from a flat PNG. Requires Pillow.

This is a contour extractor, not hidden-geometry or depth reconstruction.
"""
import argparse
from collections import defaultdict, deque
import json
from pathlib import Path


def contours(pixels):
    edges = set()
    for x, y in pixels:
        if (x, y-1) not in pixels:
            edges.add(((x,y),(x+1,y)))
        if (x+1, y) not in pixels:
            edges.add(((x+1,y),(x+1,y+1)))
        if (x, y+1) not in pixels:
            edges.add(((x+1,y+1),(x,y+1)))
        if (x-1, y) not in pixels:
            edges.add(((x,y+1),(x,y)))
    outgoing = defaultdict(set)
    for a,b in edges:
        outgoing[a].add(b)
    paths = []
    while edges:
        start, nxt = min(edges)
        points = [start]
        prev, cur = start, nxt
        while True:
            edges.remove((prev,cur))
            outgoing[prev].remove(cur)
            if cur == start:
                break
            points.append(cur)
            dx, dy = cur[0]-prev[0], cur[1]-prev[1]
            priorities = [(cur[0]-dy,cur[1]+dx), (cur[0]+dx,cur[1]+dy), (cur[0]+dy,cur[1]-dx), prev]
            following = next((p for p in priorities if p in outgoing[cur]), None)
            if following is None:
                raise ValueError('Contour unexpectedly open')
            prev, cur = cur, following
        simple = []
        for i,p in enumerate(points):
            a,b = points[i-1], points[(i+1)%len(points)]
            if (p[0]-a[0])*(b[1]-p[1]) != (p[1]-a[1])*(b[0]-p[0]):
                simple.append(p)
        paths.append('M' + 'L'.join(f'{x} {y}' for x,y in simple) + 'Z')
    return ''.join(paths)


def extract(image_path, colors=10, min_area=12, alpha_threshold=128):
    from PIL import Image
    if not 1 <= colors <= 256 or min_area < 1 or not 1 <= alpha_threshold <= 255:
        raise ValueError('colors 1..256, min-area >=1, alpha-threshold 1..255')
    image = Image.open(image_path).convert('RGBA')
    w,h = image.size
    if w*h > 4_000_000:
        raise ValueError('Limit is 4 million pixels. Prepare a smaller flat reference explicitly.')
    rgba = list(image.getdata())
    opaque = [(i,p) for i,p in enumerate(rgba) if p[3] >= alpha_threshold]
    if not opaque:
        raise ValueError('No opaque pixels above alpha threshold')
    # Quantize only retained pixels: invisible RGB values must not consume palette slots.
    strip = Image.new('RGB', (len(opaque),1))
    strip.putdata([p[:3] for _,p in opaque])
    quant = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = quant.getpalette()
    palette_pixels = defaultdict(set)
    for (index,_), color_index in zip(opaque, quant.getdata()):
        palette_pixels[color_index].add((index%w,index//w))
    layers=[]
    discarded_pixels=discarded_regions=0
    for ci, pixels in sorted(palette_pixels.items()):
        color = '#'+''.join(f'{c:02x}' for c in palette[ci*3:ci*3+3])
        component_index=0
        while pixels:
            first=min(pixels)
            pixels.remove(first)
            component={first}
            queue=deque([first])
            while queue:
                x,y=queue.popleft()
                for neighbor in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                    if neighbor in pixels:
                        pixels.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
            if len(component)<min_area:
                discarded_pixels+=len(component)
                discarded_regions+=1
                continue
            component_index+=1
            ident=f'color-{ci:02d}-piece-{component_index:03d}'
            xs,ys=zip(*component)
            layers.append({'id':ident,'label':ident,'assembly':'unassigned','pivot':[(min(xs)+max(xs)+1)/2,(min(ys)+max(ys)+1)/2],'elevation':0,'thickness':0,'geometryStatus':'visible-only','shapes':[{'tag':'path','d':contours(component),'fill':color,'fill-rule':'evenodd'}]})
    if not layers:
        raise ValueError('No components survived min-area')
    return {'version':1,'id':'extracted-flat','title':'Extração visível — reconstrução pendente','viewBox':[0,0,w,h],'texture':False,'seed':23,'extraction':{'source':Path(image_path).name,'depthResolved':False,'hiddenGeometryReconstructed':False,'alphaThreshold':alpha_threshold,'quantizationColors':colors,'discardedRegions':discarded_regions,'discardedPixels':discarded_pixels,'warning':'Ordem arbitrária. Rever IDs, profundidade e contornos escondidos antes de animar.'},'layers':layers}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--colors',type=int,default=10)
    p.add_argument('--min-area',type=int,default=12)
    p.add_argument('--alpha-threshold',type=int,default=128)
    args=p.parse_args()
    if args.out.exists():
        raise FileExistsError('Choose a new output path')
    scene=extract(args.image,args.colors,args.min_area,args.alpha_threshold)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(scene,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pieces':len(scene['layers']),**scene['extraction']},ensure_ascii=True))
