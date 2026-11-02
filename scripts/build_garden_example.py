#!/usr/bin/env python3
"""Author the bundled example with curves, not a raster generator."""
import json
import math
from pathlib import Path

NAVY='#293e50'; TEAL='#416b70'; SAGE='#78968a'; CREAM='#f7ead2'
PEACH='#e5b591'; GOLD='#ce9e52'; CORAL='#d97869'; ROSE='#b55f64'
layers=[]


def add(ident, shapes, pivot, assembly=None, elevation=2, thickness=1.2, label=None):
    layers.append({'id':ident,'label':label or ident.replace('-',' ').capitalize(),'assembly':assembly or ident,'pivot':pivot,'elevation':elevation,'thickness':thickness,'shapes':shapes})


def path(ident,d,color,pivot,**kwargs):
    add(ident,[{'tag':'path','d':d,'fill':color}],pivot,**kwargs)


def disk(ident,cx,cy,r,color,assembly=None):
    add(ident,[{'tag':'circle','cx':cx,'cy':cy,'r':r,'fill':color}],[cx,cy],assembly)


def leaf(ident,x,y,length,width,angle,color,fold,assembly='foliage'):
    a=math.radians(angle)
    def p(u,v):
        return f'{x+u*math.cos(a)-v*math.sin(a):.2f} {y+u*math.sin(a)+v*math.cos(a):.2f}'
    d=f'M{p(0,0)}C{p(length*.2,-width)} {p(length*.72,-width*.9)} {p(length,0)}C{p(length*.73,width*.8)} {p(length*.22,width*.7)} {p(0,0)}Z'
    path(ident,d,color,[x,y],assembly=assembly,elevation=3)
    d=f'M{p(0,0)}Q{p(length*.48,width*.08)} {p(length,0)}C{p(length*.73,width*.8)} {p(length*.22,width*.7)} {p(0,0)}Z'
    path(ident+'-fold',d,fold,[x,y],assembly=assembly,elevation=1,thickness=.5)


def flower(name,cx,cy,r,colors):
    for i in range(6):
        angle=-164+i*59
        length=r*(1+.09*math.sin(i*2))
        leaf(f'{name}-petal-{i+1}',cx,cy,length,r*.36,angle,colors[i%len(colors)],colors[(i+1)%len(colors)],name)
    disk(name+'-heart',cx,cy,r*.25,GOLD,name)
    for i in range(7):
        a=i*2.39996
        px=cx+math.cos(a)*r*.16;py=cy+math.sin(a)*r*.16
        disk(f'{name}-stamen-{i+1}',round(px,2),round(py,2),3,CREAM,name)


def main():
    # Long complete cut silhouettes underpin the pop-up scenery.
    path('book-cover','M88 695Q266 661 492 754Q710 636 910 683L924 846Q716 810 502 936Q278 846 77 857Z',NAVY,[500,815],assembly='book',elevation=0)
    path('book-cover-left','M88 695Q275 667 492 754L502 922Q278 829 91 844Z',TEAL,[492,754],assembly='book')
    path('book-cover-right','M492 754Q710 636 910 683L911 831Q705 803 502 922Z',GOLD,[492,754],assembly='book')
    for i in range(4):
        dy=-i*8
        path(f'page-left-{i}',f'M103 {683+dy}Q294 {668+dy} 492 {754+dy}L501 {901+dy}Q282 {810+dy} 99 {828+dy}Z',CREAM if i%2 else PEACH,[492,754],assembly='book',elevation=1)
        path(f'page-right-{i}',f'M492 {754+dy}Q694 {639+dy} 896 {669+dy}L906 {805+dy}Q700 {782+dy} 501 {901+dy}Z',CREAM if i%2 else '#d5c9a9',[492,754],assembly='book',elevation=1)
    path('page-fold-left','M492 730Q288 625 113 659Q290 693 492 867Z','#fff3dc',[492,730],assembly='book',elevation=4)
    path('page-fold-right','M492 730Q707 605 890 646Q699 662 492 867Z','#ead7b3',[492,730],assembly='book',elevation=4)
    # Islands of layered scenery rise from the paper pages.
    path('hill-back','M181 665Q282 508 409 583Q559 472 713 561Q790 586 834 660Q645 633 493 757Q318 674 181 665Z',SAGE,[495,698],assembly='landscape',elevation=3)
    path('hill-mid','M182 665Q307 548 429 647Q602 519 831 659Q635 645 493 757Q313 680 182 665Z',TEAL,[495,698],assembly='landscape',elevation=3)
    path('hill-front','M191 674Q351 602 492 727Q625 628 822 669Q635 684 493 778Q330 695 191 674Z',NAVY,[495,718],assembly='landscape',elevation=3)
    # A winding path is a separate strip, not a painted shadow.
    path('winding-path','M493 779Q445 716 535 691Q598 672 547 646Q504 623 514 579L545 580Q535 614 575 635Q654 682 567 711Q501 733 529 758Z',GOLD,[517,713],assembly='landscape',elevation=2)
    path('path-highlight','M493 779Q445 716 535 691Q598 672 547 646Q504 623 514 579L525 579Q513 621 561 643Q616 676 545 700Q477 725 506 772Z',CREAM,[517,713],assembly='landscape',elevation=1,thickness=.5)
    # Complete stems are retained behind the portal and flowers.
    stems=[('stem-left','M434 651C366 501 350 369 294 273L302 269C365 373 377 511 444 649Z',TEAL),('stem-right','M583 646C642 514 667 377 741 260L748 265C678 391 653 525 592 648Z',TEAL),('stem-upper','M521 631C512 449 531 325 572 199L580 202C543 339 526 459 531 632Z',SAGE)]
    for ident,d,col in stems:path(ident,d,col,[520,630],assembly='stems')
    for i,(x,y,l,w,a,c,f) in enumerate([
        (379,484,161,39,-155,NAVY,TEAL), (360,418,139,34,-117,TEAL,SAGE),
        (335,355,125,30,-157,SAGE,TEAL), (411,564,135,33,-179,TEAL,NAVY),
        (644,482,155,39,-34,TEAL,SAGE), (676,399,148,34,-65,NAVY,TEAL),
        (706,334,115,29,-8,SAGE,TEAL), (610,554,157,39,-9,NAVY,TEAL),
        (542,326,123,31,-130,TEAL,SAGE), (554,273,101,26,-24,SAGE,TEAL),
    ]):leaf(f'leaf-{i+1}',x,y,l,w,a,c,f)
    # Framed paper doorway, including separate returns and opening.
    path('portal-back','M410 617L410 430C410 289 602 289 602 430L602 617Z',NAVY,[506,617],assembly='portal',elevation=5)
    path('portal-outer','M424 610L424 429C424 308 588 308 588 429L588 610Z',GOLD,[506,610],assembly='portal',elevation=2)
    path('portal-return','M439 609L439 431C439 330 574 330 574 431L574 609Z',CREAM,[506,609],assembly='portal',elevation=2)
    path('portal-opening','M455 606L455 433C455 355 560 355 560 433L560 606Z',TEAL,[508,606],assembly='portal',elevation=1)
    path('door-left-fold','M455 434L495 458L495 587L455 606Z',CORAL,[455,520],assembly='portal',elevation=3)
    path('door-left-inner','M464 452L484 465L484 573L464 586Z',PEACH,[455,520],assembly='portal',elevation=1)
    disk('door-handle',487,525,3.4,CREAM,'portal')
    disk('portal-sun',527,425,22,PEACH,'portal')
    path('portal-horizon','M496 545Q529 496 560 538L560 606L496 606Z',SAGE,[528,570],assembly='portal',elevation=1)
    path('portal-threshold','M443 608L574 608L590 624L430 624Z',CREAM,[508,608],assembly='portal',elevation=2)
    # Two hero blossoms and a smaller bud; asymmetry keeps the silhouette alive.
    flower('coral-flower',315,303,103,[CORAL,PEACH,ROSE])
    flower('ivory-flower',727,312,84,[CREAM,'#e4d3ad',PEACH])
    leaf('top-bud',574,225,81,27,-85,GOLD,PEACH,'bud')
    # Small foreground paper fans provide a different scale of detail.
    for i,(x,y,a,l) in enumerate([(279,679,-147,83),(290,686,-101,91),(303,691,-54,76),(718,677,-135,75),(729,674,-84,88),(741,671,-30,76)]):
        leaf(f'foreground-{i+1}',x,y,l,20,a,CORAL if i<3 else SAGE,PEACH if i<3 else TEAL,'foreground')
    # Folded messenger bird in flight: all wing/tail pieces have their own pivots.
    path('bird-tail','M650 180L614 178L640 161L663 164Z',GOLD,[657,169],assembly='bird',elevation=4)
    path('bird-wing-back','M664 172Q638 116 664 83Q686 123 682 163Z',TEAL,[671,168],assembly='bird',elevation=5)
    path('bird-wing-front','M662 171Q693 117 743 123Q720 164 680 183Z',CREAM,[671,168],assembly='bird',elevation=4)
    path('bird-wing-fold','M662 171Q708 145 743 123Q720 164 680 183Z',PEACH,[671,168],assembly='bird',elevation=1)
    path('bird-body','M641 178Q674 151 690 177Q705 190 720 171L732 179Q709 213 679 200Q658 193 641 178Z',CORAL,[685,183],assembly='bird',elevation=3)
    path('bird-beak','M721 172L747 177L730 183Z',GOLD,[724,177],assembly='bird',elevation=1)
    disk('bird-eye',724,175,2.3,NAVY,'bird')
    scene={'version':1,'id':'garden-of-encounters','title':'Jardim dos encontros','viewBox':[0,0,1000,1000],'seed':46,'texture':True,'layers':layers}
    target=Path(__file__).resolve().parents[1]/'assets'/'garden.scene.json'
    target.write_text(json.dumps(scene,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Authored {len(layers)} pieces: {target}')


if __name__=='__main__':main()
