"""Author editable technical slides from verified repository data."""
import json, math, sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(BASE/'build/deps'),'/home/samarth/.codex/skills/mck-ppt-design-skill']
from mck_ppt import MckEngine
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_MARK
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.oxml.xmlchemy import OxmlElement
import numpy as np

WEB=json.loads((BASE/'research/web-data.json').read_text()); D=WEB['data']; RUN=WEB['runs']['zero']
MAIN=json.loads((BASE/'research/main-data.json').read_text()); DER=json.loads((BASE/'research/derived.json').read_text())
NAVY='132D40'; TEAL='087E83'; AMBER='B87510'; PURPLE='77629B'; GRAY='526574'; LIGHT='E7ECEF'; WHITE='FFFFFF'; INK='172C3B'; RED='B14B49'
FONT='Carlito'; MATH='DejaVu Sans'
LEE='https://arxiv.org/pdf/2511.01005'
ZHU='https://doi.org/10.1021/acsphotonics.3c01694'
WEB_SRC='web/index.html: PhotonicSolver numerical core and embedded sparse matrix data'
MAIN_SRC='main.py: original solver, observed by presentation/build/collect_python.py'
ENG=MckEngine(total_slides=32); PRS=ENG.prs
META=[]

def rgb(c):return RGBColor.from_string(c)
def text(sl,x,y,w,h,s,size=20,color=INK,bold=False,align=PP_ALIGN.LEFT,font=FONT):
    sh=sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf=sh.text_frame;tf.clear();tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(.015);tf.margin_top=tf.margin_bottom=0
    for i,line in enumerate(str(s).split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.alignment=align
        p.font.name=font;p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=rgb(color)
        p.space_after=Pt(5);p.space_before=Pt(0)
    return sh

def shape(sl,x,y,w,h,label='',fill=WHITE,line=TEAL,size=19,kind=MSO_SHAPE.ROUNDED_RECTANGLE,color=INK,bold=False):
    sh=sl.shapes.add_shape(kind,Inches(x), Inches(y), Inches(w), Inches(h));sh.name='Flow: '+label[:45]
    sh.fill.solid();sh.fill.fore_color.rgb=rgb(fill);sh.line.color.rgb=rgb(line);sh.line.width=Pt(1.4)
    if kind==MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0]=.06
    tf=sh.text_frame;tf.clear();tf.word_wrap=True;tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    tf.margin_left=tf.margin_right=Inches(.09);tf.margin_top=tf.margin_bottom=Inches(.03)
    for i,l in enumerate(label.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=l;p.alignment=PP_ALIGN.CENTER
        p.font.name=FONT;p.font.size=Pt(size);p.font.color.rgb=rgb(color);p.font.bold=bold
        p.space_after=Pt(2)
    return sh

def line(sl,x1,y1,x2,y2,c=GRAY,width=1.6,arrow=True):
    # Editable strokes avoid endpoint-binding artifacts across office viewers.
    if abs(y2-y1)>.001 and abs(x2-x1)>.001:
        line(sl,x1,y1,x2,y1,c,width,False)
        return line(sl,x2,y1,x2,y2,c,width,arrow)
    thick=width/72
    sh=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(min(x1,x2)-(thick/2 if x1==x2 else 0)), Inches(min(y1,y2)-(thick/2 if y1==y2 else 0)), Inches(max(abs(x2-x1),thick)), Inches(max(abs(y2-y1),thick)))
    sh.fill.solid();sh.fill.fore_color.rgb=rgb(c);sh.line.fill.background()
    if arrow:
        tip=sl.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(x2-.045), Inches(y2-.045), Inches(.09), Inches(.09))
        tip.rotation=(90 if x2>x1 else 270) if y1==y2 else (180 if y2>y1 else 0)
        tip.fill.solid();tip.fill.fore_color.rgb=rgb(c);tip.line.fill.background()
    return sh

def path(sl,pts,c=GRAY):
    for i in range(len(pts)-1):line(sl,*pts[i],*pts[i+1],c,arrow=i==len(pts)-2)

def tag(sl,s,x=.6,y=1.22,w=11.9,c=GRAY):text(sl,x,y,w,.34,s,14,c)
def note(sl,s,x=.6,y=6.4,w=11.9,size=18,c=INK):text(sl,x,y,w,.78,s,size,c)

def mini(sl,active):
    labels=['Residual check','PCG correction','V-cycle','Optical product']
    for i,l in enumerate(labels):
        x=.6+i*3.05
        text(sl,x,1.22,2.8,.32,f'{i+1}  {l}',14,AMBER if i==active else GRAY,bold=i==active)
        if i<3:line(sl,x+2.57,1.37,x+2.92,1.37,LIGHT,1)

def new(title,source,notes='',stage=None,subtitle=None,layout='side_by_side',appendix=False):
    sl=ENG._ns();sl.background.fill.solid();sl.background.fill.fore_color.rgb=rgb(WHITE)
    n=len(PRS.slides)
    text(sl,.58,.35,12.1,.78,title,31,NAVY,True)
    line(sl,.6,1.08,12.7,1.08,LIGHT,1,False)
    if stage is not None:mini(sl,stage)
    elif subtitle:tag(sl,subtitle)
    text(sl,.6,7.26,11.5,.23,('Appendix  ·  ' if appendix else '')+source,10,GRAY)
    text(sl,12.1,7.22,.6,.26,str(n),12,GRAY,align=PP_ALIGN.RIGHT)
    sl.notes_slide.notes_text_frame.text=notes+'\n\nSources: '+source
    META.append(dict(idx=n,title=title,layout=layout,source=source,notes=notes,appendix=appendix))
    return sl

def table(sl,headers,rows,x=.6,y=1.85,w=12.05,h=4.2,widths=None,size=19):
    obj=sl.shapes.add_table(len(rows)+1,len(headers), Inches(x), Inches(y), Inches(w), Inches(h));tb=obj.table
    if widths:
        for col,frac in zip(tb.columns,widths):col.width=Inches(w*frac)
    for i,row in enumerate([headers]+rows):
        for j,v in enumerate(row):
            cell=tb.cell(i,j);cell.text=str(v);cell.margin_left=Inches(.12);cell.margin_right=Inches(.08)
            cell.margin_top=Inches(.07);cell.margin_bottom=Inches(.04);cell.vertical_anchor=MSO_ANCHOR.MIDDLE
            cell.fill.solid();cell.fill.fore_color.rgb=rgb(NAVY if i==0 else ('F3F6F7' if i%2 else WHITE))
            for p in cell.text_frame.paragraphs:
                p.font.name=FONT;p.font.size=Pt(size);p.font.bold=i==0;p.font.color.rgb=rgb(WHITE if i==0 else INK)
    return tb

def chart(sl,series,x,y,w,h,xlabel='',ylabel='',log=False,kind='line'):
    # XY charts retain exact coordinates and all source data in editable workbooks.
    cd=XyChartData()
    for name,xs,ys,col in series:
        ser=cd.add_series(name)
        for a,b in zip(xs,ys):ser.add_data_point(float(a),float(b))
    ch=sl.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS,Inches(x),Inches(y),Inches(w),Inches(h),cd).chart
    ch.has_legend=True;ch.legend.position=XL_LEGEND_POSITION.BOTTOM;ch.legend.include_in_layout=False
    ch.legend.font.name=FONT;ch.legend.font.size=Pt(14)
    for s,(_,_,_,c) in zip(ch.series,series):s.format.line.color.rgb=rgb(c);s.format.line.width=Pt(2.4)
    for axis,label in [(ch.category_axis,xlabel),(ch.value_axis,ylabel)]:
        axis.tick_labels.font.name=FONT;axis.tick_labels.font.size=Pt(13)
        axis.format.line.color.rgb=rgb('B9C4CA');axis.major_tick_mark=XL_TICK_MARK.NONE
        axis.has_title=bool(label)
        if label:
            axis.axis_title.text_frame.text=label
            for p in axis.axis_title.text_frame.paragraphs:p.font.name=FONT;p.font.size=Pt(15)
    ch.value_axis.has_major_gridlines=True;ch.value_axis.major_gridlines.format.line.color.rgb=rgb(LIGHT)
    if log:
        scaling=ch.value_axis._element.find('{http://schemas.openxmlformats.org/drawingml/2006/chart}scaling')
        lb=OxmlElement('c:logBase');lb.set('val','10');scaling.insert(0,lb)
        ch.value_axis.maximum_scale=1;ch.value_axis.minimum_scale=1e-14;ch.value_axis.tick_labels.number_format='0E+0'
    return ch

def sparseplot(sl,o,x,y,w,h,c=TEAL,bins=None):
    nr,nc=o['rows'],o['cols'];shape(sl,x,y,w,h,fill='F6F8F9',line=LIGHT,kind=MSO_SHAPE.RECTANGLE)
    cells=set()
    for r in range(nr):
        for p in range(o['ptr'][r],o['ptr'][r+1]):
            if o['val'][p]==0:continue
            col=o['idx'][p]
            cells.add((int(r*min(nr,bins or nr)/nr),int(col*min(nc,bins or nc)/nc)))
    rr=min(nr,bins or nr);cc=min(nc,bins or nc)
    for r,col in cells:
        sh=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x+col*w/cc),Inches(y+r*h/rr),Inches(max(w/cc,.008)),Inches(max(h/rr,.008)))
        sh.fill.solid();sh.fill.fore_color.rgb=rgb(c);sh.line.fill.background()

def val(o,r,c):
    for k in range(o['ptr'][r],o['ptr'][r+1]):
        if o['idx'][k]==c:return o['val'][k]
    return 0.
def matrix_table(sl,o,rr,cc,x,y,w,h,fmt='.3f',size=14):
    rows=[[str(r+1)]+[format(val(o,r,c),fmt) for c in cc] for r in rr]
    return table(sl,['i / j']+[str(c+1) for c in cc],rows,x,y,w,h,size=size)
def sample(v,n=3):return '['+', '.join(f'{float(a):.4g}' for a in v[:n])+', …]ᵀ'

def hardware(sl,active=0,y=2.0):
    shape(sl,.65,y+.5,2.0,1.55,'CPU\nstate +\nupdates',fill='EAF5F4',line=TEAL,size=21)
    shape(sl,3.4,y+.15,1.65,1.0,'DAC +\nencoder',line=TEAL,size=19)
    shape(sl,10.45,y+.15,2.1,1.0,'Detector +\nADC',line=TEAL,size=19)
    shape(sl,3.4,y-0.5,1.65,.42,'Light source',line=AMBER,size=14)
    line(sl,4.22,y-.08,4.22,y+.15,AMBER)
    path(sl,[(2.65,y+.85),(3.05,y+.85),(3.05,y+.65),(3.4,y+.65)],TEAL)
    text(sl,2.6,y-.03,.75,.4,'eℓ',19,TEAL,True)
    for l,n in enumerate([64,22,8]):
        yy=y-.35+l*.84
        shape(sl,6.25,yy,2.3,.64,f'A{["₀","₁","₂"][l]}  {n} × {n}',fill='FFF4DD' if l==active else WHITE,line=AMBER if l==active else LIGHT,size=21,color=AMBER if l==active else GRAY)
    yy=y-.35+active*.84+.32
    path(sl,[(5.05,y+.65),(5.6,y+.65),(5.6,yy),(6.25,yy)],AMBER)
    path(sl,[(8.55,yy),(9.55,yy),(9.55,y+.65),(10.45,y+.65)],AMBER)
    path(sl,[(11.5,y+1.15),(11.5,y+2.65),(1.65,y+2.65),(1.65,y+2.05)],TEAL)
    text(sl,8.6,y+2.25,3.9,.36,'electrical yℓ = Aℓeℓ',19,TEAL)
    text(sl,6.1,y+2.03,2.8,.42,'Select one Aℓ',17,GRAY,align=PP_ALIGN.CENTER)

# 1
s=new('Photonic multigrid for Poisson problems', 'Project implementation inspired by Lee et al. (2025)',
      f'20-minute technical discussion. The contribution is a working numerical emulation and an inspectable architecture demonstrator. No experimental photonic processor or measured hardware speedup is claimed. Primary paper: {LEE}.',layout='cover')
text(s,.65,1.7,10.8,1.3,'A digital iterative solver with\nphotonic matrix–vector products',38,NAVY,True)
text(s,.65,3.3,10.9,.8,'Fixed matrices and changing correction vectors solve Ax = b',25,GRAY)
for i,(a,b,c) in enumerate([('Measure mismatch','r = b − Ax',TEAL),('Find correction','Aδ ≈ r',AMBER),('Update solution','x ← x + δ',TEAL)]):
    shape(s,.7+i*4.12,5.0,3.5,1.0,a+'\n'+b,line=c,size=22)
    if i<2:line(s,4.2+i*4.12,5.5,4.75+i*4.12,5.5)

# 2
s=new('The paper assigns smoothing products to optics', 'Lee et al., arXiv:2511.01005, pp. 3–6, 15–16',
      f'Lee combines multigrid preconditioning with digital Krylov iteration and residual correction. The demonstrated Poisson case uses two AMG levels. Its optical core stores weights and computes smoothing products. We adopt that computational partition. Source: {LEE}. The deck explains repository code rather than copying the paper figures.')
text(s,.65,1.72,6.5,.5,'Numerical structure adopted here',25,NAVY,True)
for i,t in enumerate(['Digital residual correction','Digital PCG + multigrid control','Photonic smoothing MVM']):
    shape(s,.8,2.5+i*1.1,5.9,.78,t,line=AMBER if i==2 else TEAL,fill='FFF4DD' if i==2 else WHITE,size=23)
    if i<2:line(s,3.75,3.28+i*1.1,3.75,3.58+i*1.1)
text(s,7.4,2.05,4.7,.5,'Current project',25,NAVY,True)
text(s,7.4,2.85,4.8,1.85,'Noisy 2D emulation\n+\nideal 1D demonstrator',24,INK)
text(s,7.4,4.8,4.8,1.25,'Hardware diagrams show\nfunctional assignments.',22,GRAY)
note(s,'Research question: can approximate smoothing reduce digital work while reliable residuals retain accuracy?',size=20)

# 3
s=new('Three implementations, different settings', 'Lee et al.; main.py; web/index.html; smoother.py',
      f'Keep every later result attached to its implementation. The browser is based more closely on the 1D smoother.py algorithm but uses N=64. smoother.py currently reaches its solve output then raises a ValueError in the final residual expression because A is a list. No results here are attributed to that failing report. Paper: {LEE}.')
table(s,['','Lee Poisson experiment','main.py','Browser demonstrator'],[
 ['Role','Research foundation','Noisy numerical evidence','Explanatory model'],
 ['Problem','2D capacitor','64 × 64 = 4096 unknowns','1D, 64 unknowns'],
 ['AMG levels','2','4096 → 704 in this run','64 → 22 → 8 → 3'],
 ['Hybrid sweeps','4 pre / 0 post','4 pre / 0 post','3 pre / 3 post'],
 ['MVM behavior','Physical measurements','Input quantization + noise','Ideal floating point'],
 ],h=4.3,widths=[.16,.27,.28,.29],size=18)
note(s,'Main explanation: browser’s 1D model. Research evidence: main.py’s separate 2D run.',size=20)

# 4
s=new('The unknown vector stores sampled solution values', WEB_SRC,
      'The teaching problem is a 1D Poisson boundary-value problem, mathematically an ODE reduction of the PDE. Interior unknowns only are in x. Known boundaries enter b. h=1/65. The analytic quadratic is also the exact discrete solution for this stencil up to floating-point error. Its samples are a reference, never solver input.',subtitle='Ideal 1D teaching model')
text(s,.65,1.82,6.1,.8,'−u″(t) = 1\nu(0) = 100,   u(1) = 0',26,NAVY,font=MATH)
text(s,.65,3.05,6.1,1.0,'(2xᵢ − xᵢ₋₁ − xᵢ₊₁) / h² = 1\nh = 1 / 65,   x ∈ ℝ⁶⁴',23,INK,font=MATH)
text(s,.65,4.4,6.1,.75,'A₀ = h⁻² tridiag(−1, 2, −1)\nb = [422501, 1, …, 1]ᵀ',23,TEAL,font=MATH)
tt=[0]+[(i+1)/65 for i in range(64)]+[1];xx=[100]+D['exact']+[0]
chart(s,[('reference x*',tt,xx,NAVY)],7,1.8,5.55,4.35,'position t','u(t)')
note(s,'x = [u(t₁), …, u(t₆₄)]ᵀ. Iteration improves an equilibrium estimate; it is not physical time.',size=19)

# 5
s=new('The residual becomes the next correction problem', WEB_SRC+'; Lee Methods p. 16',
      'Let x* denote the exact discrete solution. Then A(x*−x)=b−Ax. We can measure r without knowing x*. PCG approximately solves for δ. Corrections change only interior values; boundary changes are zero. A small true residual certifies equations are closely satisfied, not by itself a universal solution-error bound.',stage=0)
text(s,.7,1.85,5.6,.7,'r = b − A₀x',34,TEAL,font=MATH)
text(s,.7,2.85,5.6,.8,'A₀(x* − x) = r',30,NAVY,font=MATH)
text(s,.7,4.0,5.6,1.3,'Find δ with A₀δ ≈ r\nThen xnew = x + δ',28,INK,font=MATH)
shape(s,7.15,1.95,5.05,.8,'Known: A₀, b, current x',line=TEAL,size=23)
shape(s,7.15,3.25,5.05,1.1,'Solve for a correction δ\nwhile current x stays in memory',line=TEAL,size=22)
shape(s,7.15,4.88,5.05,.9,'Recompute rnew\n= b − A₀(x + δ)',line=TEAL,size=22)
line(s,9.67,2.75,9.67,3.25,TEAL);line(s,9.67,4.35,9.67,4.88,TEAL)
note(s,'The exact solution x* is only a reference for evaluation. The algorithm uses the computable residual.',size=19)

# 6
s=new('One solver map connects all four routines', WEB_SRC,
      'This is a call hierarchy, not four physical chips. Each routine returns to its caller. Subsequent slides expand these same four blocks. Only the product inside the last block is assigned to optics. V-cycle is an action approximating A inverse, not an explicitly stored inverse or matrix M.',subtitle='Read downward for calls; read upward for returned values')
boxes=[(.7,1.85,'1  Outer correction','full solution x',TEAL),
       (3.25,2.95,'2  PCG correction','accumulated correction δ',TEAL),
       (5.8,4.05,'3  Multigrid V-cycle','z = Vcycle(s)',TEAL),
       (8.35,5.15,'4  Richardson smoothing','Optics: yℓ ≈ Aℓeℓ',AMBER)]
for x,y,a,b,c in boxes:shape(s,x,y,4.2,.87,a+'\n'+b,line=c,size=21)
for i in range(3):
    x,y,*_=boxes[i];xx,yy,*_=boxes[i+1]
    path(s,[(x+2.1,y+.87),(x+2.1,yy+.44),(xx,yy+.44)],TEAL)
text(s,.75,4.7,4.1,1.45,'Optics returns yℓ.\nCPU updates eℓ.\nCPU selects next request.',22,NAVY)
note(s,'Changing vectors: x → δ → s → eℓ. Fixed operators: Aℓ, Pℓ, Rℓ.',size=20)

# 7
s=new('The CPU closes every optical smoothing loop', WEB_SRC+'; web/README.md hardware mapping',
      'Functional hardware proposal for the browser. The CPU selects a level, retains e and g, and sends only e through shared DAC/modulator. Source illumination is not an extra numerical operation. Optical matrix weights act on the signed numerical representation; no specific signed encoding, sparse tiling, or physical switch is specified. Detector/ADC returns y, then CPU applies the Richardson update. CPU-only work does not require an extra trip through optics.',stage=3)
hardware(s,0,2.25)
text(s,.65,5.66,12.05,.65,'CPU update:  eℓ ← eℓ + ωℓ(gℓ − yℓ)',29,TEAL,font=MATH)
note(s,'Amber: optical product. Teal: electrical data and CPU work. The full solution x is not the encoded vector.',size=18)

# 8
s=new('A real smoothing request changes the local vector', WEB_SRC+'; zero-start event trace',
      'Numbers from the actual second pre-sweep on level zero in the first browser V-cycle, rounded for display. First sweep sends a zero vector and returns zero, giving e=ωg. The browser retains this zero-input MVM in its counters. x remains zero throughout the first correction solve; only local e changes here. All vector excerpts use indices1–3 of64.',stage=3)
f=RUN['flights'][1];enew=np.array(f['input'])+f['omega']*(np.array(f['g'])-np.array(f['output']))
table(s,['Stored or transferred quantity','Actual first three entries'],[
 ['g₀, retained on CPU',sample(f['g'])],['e₀, encoded input',sample(f['input'])],
 ['y₀ = A₀e₀, detected product',sample(f['output'])],['new e₀ = e₀ + ω₀(g₀ − y₀)',sample(enew)]
 ],h=3.8,widths=[.48,.52],size=23)
text(s,.65,5.95,11.8,.45,f'ω₀ = {f["omega"]:.8g}    ·    64 entries    ·    full x unchanged',20,TEAL)
note(s,'Next sweep encodes the updated e₀ through the same fixed matrix A₀.',size=20)

# 9
s=new('The multigrid V-cycle', WEB_SRC,
      'Actual browser schedule, 3 pre and3 post sweeps at each noncoarsest level. On entry initialize e_l=0. After pre-smoothing compute d_l=g_l−A_l e_l digitally, restrict g_next=R_l d_l, recurse. On return add P_l e_next to retained e_l and post-smooth. At the top return z=e0. AMG levels are algebraic spaces, not uniformly subsampled physical meshes. In main.py the hybrid schedule is a different two-level4/0 cycle.',stage=2)
for l,(n,y) in enumerate([(64,1.85),(22,3.1),(8,4.35)]):
    sub=['₀','₁','₂'][l];nxt=['₁','₂','₃'][l]
    shape(s,.65,y,3.85,.78,f'Level {l}: {n} values\n3 pre-sweeps',line=AMBER,size=21)
    shape(s,8.75,y,3.85,.78,f'Add P{sub}e{nxt}\n3 post-sweeps',line=AMBER,size=21)
    if l<2:
        line(s,2.57,y+.78,2.57,y+1.25,TEAL);text(s,2.83,y+.78,3.6,.4,f'g{nxt} = R{sub}(g{sub} − A{sub}e{sub})',16,TEAL)
        line(s,10.67,y+1.25,10.67,y+.78,TEAL)
    else:
        path(s,[(2.57,y+.78),(2.57,5.87),(5.0,5.87)],TEAL)
        text(s,.65,5.22,4.5,.35,'g₃ = R₂(g₂ − A₂e₂)',17,TEAL)
        path(s,[(8.3,5.87),(10.67,5.87),(10.67,y+.78)],TEAL)
shape(s,5.0,5.47,3.3,.8,'CPU direct solve\nA₃e₃ = g₃  (3 × 3)',line=TEAL,fill='EAF5F4',size=20)
text(s,4.75,2.2,3.75,2.2,'At every level:\nsave gℓ and eℓ\n\nOnly smoothing MVMs\nuse the optical route.',21,GRAY,align=PP_ALIGN.CENTER)
note(s,'Return z = e₀ to PCG. The V-cycle supplies an approximate correction, not the final PDE solution.',size=19)

# 10
s=new('Smoothing and coarse correction', WEB_SRC+'; derived.json controlled error experiment',
      'This is a controlled numerical teaching experiment using the stored browser operators, not a physical measurement. Choose an initial error sin(πt)+0.35sin(32πt), solve homogeneous error equation with three Richardson sweeps, apply the recursive coarse correction, then three post-sweeps. Display error profiles against zero. Norms are independently computed. The amplification relation follows directly from the Richardson update.',stage=2)
t=DER['t'];ep=DER['error_profiles'];norms=DER['error_norms']
chart(s,[('initial error',t,ep['initial'],GRAY),('3 smoothing sweeps',t,ep['after_smooth'],AMBER),('after coarse correction',t,ep['after_coarse'],TEAL)],.55,1.75,8.2,4.5,'position t','error')
text(s,9.0,2.0,3.65,1.4,'εnew = (I − ωA)ε\n\nMode j shrinks by\n1 − ωλⱼ',23,NAVY,font=MATH)
text(s,9.0,4.2,3.6,1.4,f'Error norm\n{norms["initial"]:.2f} → {norms["after_smooth"]:.2f} → {norms["after_coarse"]:.2f}',23,TEAL)
note(s,'Three post-sweeps reduce the norm further to '+f'{norms["after_post"]:.3f}'+'. The initial error is prescribed for this test.',size=18)

# 11
s=new('PCG turns a V-cycle correction into a search step', WEB_SRC+'; PCG recurrence',
      'The fixed RHS r is the outer residual for this PCG call. δ starts at zero. s is the residual of this correction problem. z is one V-cycle result. q=A0p is a high-precision CPU MVM, not the optical smoothing MVM. The ordering q before alpha is essential. The next slide completes the recurrence and stopping branches.',stage=1)
steps=[('Initialize','δ = 0;  s = r − A₀δ'),('Precondition','z = Vcycle(s);  p = z;  ρ = sᵀz'),('CPU MVM','q = A₀p'),('Step length','α = ρ / (pᵀq)'),('Update','δ ← δ + αp;  s ← s − αq')]
for i,(a,b) in enumerate(steps):
    yy=1.78+i*.86
    shape(s,.7,yy,7.6,.67,a+'    '+b,line=TEAL,size=21)
    if i<4:line(s,4.5,yy+.67,4.5,yy+.86,TEAL)
text(s,8.9,2.15,3.6,1.5,'p: direction\nα: step length\nδ: correction so far',23,NAVY)
text(s,8.9,4.1,3.6,1.5,'PCG arithmetic: CPU\nVcycle invokes\noptical products.',21,GRAY)
note(s,'The original full estimate x stays fixed until this correction solve returns δ.',size=20)

# 12
s=new('PCG stopping and direction updates', WEB_SRC+'; browser inner limit: 20 iterations',
      'Browser exact branch order: after δ and s updates compute ||s||/||r||. If below1e-2 returnδ. Otherwise compute another V-cycle, beta and direction update even on the final capped iteration, then the loop exits after20. The appendix records this detail. main.py instead calls SciPy CG with maxiter5 and rtol1e-12. Numerical breakdown is distinct from convergence.',stage=1)
shape(s,.8,1.9,4.3,.8,'Test ||s||₂ / ||r||₂ < 10⁻²',line=TEAL,size=23)
shape(s,8.0,1.9,4.3,.8,'Return δ to outer loop',line=TEAL,fill='EAF5F4',size=23)
line(s,5.1,2.3,8,2.3,TEAL);text(s,6.0,1.95,1.1,.3,'yes',17,TEAL)
line(s,2.95,2.7,2.95,3.35,TEAL);text(s,3.15,2.88,.8,.3,'no',17,GRAY)
shape(s,.8,3.35,5.45,.9,'z = Vcycle(s)\nρnew = sᵀz',line=TEAL,size=23)
shape(s,7.15,3.35,5.15,.9,'β = ρnew / ρ\np ← z + βp;  ρ ← ρnew',line=TEAL,size=23)
line(s,6.25,3.8,7.15,3.8,TEAL)
shape(s,7.15,5.05,5.15,.78,'Next iteration: q = A₀p',line=TEAL,size=23)
line(s,9.72,4.25,9.72,5.05,TEAL)
text(s,.85,4.9,5.6,1.28,'At the cap, return current δ.\nOuter true residual\nstill decides success.',21,GRAY)
note(s,'z = Vcycle(s) is an action approximating A₀⁻¹s. No inverse matrix is explicitly stored.',size=19)

# 13
s=new('Outer correction and true-residual checks', WEB_SRC+'; main.py solve_with_restarts',
      'Browser: outer loop at most10 corrections; tolerance1e-12; after the final correction it recomputes true residual and distinguishes converged/limit. main.py uses at most100 restarts, tolerance1e-10, and the run report recomputes final residual. Breakdown is a separate failure state. Fresh outer r is not a recycled inner residual. This is how correction quality is checked despite approximate inner products.',stage=0)
shape(s,.8,1.9,4.3,.75,'Start with current x',line=TEAL,size=24)
shape(s,.8,3.02,4.3,.9,'CPU: r = b − A₀x\nη = ||r||₂ / ||b||₂',line=TEAL,size=24)
shape(s,.8,4.4,4.3,.85,'η below outer tolerance?',line=TEAL,size=23)
line(s,2.95,2.65,2.95,3.02,TEAL);line(s,2.95,3.92,2.95,4.4,TEAL)
shape(s,8.0,4.4,4.3,.85,'Return converged x',line=TEAL,fill='EAF5F4',size=24)
line(s,5.1,4.82,8,4.82,TEAL);text(s,6.0,4.45,1,.3,'yes',18,TEAL)
shape(s,8.0,1.9,4.3,.85,'PCG correction solve\nA₀δ ≈ r',line=TEAL,size=23)
shape(s,8.0,3.12,4.3,.8,'CPU: x ← x + δ',line=TEAL,size=24)
line(s,10.15,2.75,10.15,3.12,TEAL);path(s,[(8,3.52),(6.6,3.52),(6.6,3.47),(5.1,3.47)],TEAL)
path(s,[(2.95,5.25),(2.95,5.9),(7.05,5.9),(7.05,2.32),(8,2.32)],TEAL)
text(s,3.25,5.48,3.4,.3,'no, and budget remains',17,GRAY)
note(s,'Limit or numerical error: return an unverified approximation with its status, never label it converged.',size=18)

# 14
s=new('The hierarchy is fixed while its vectors change', WEB_SRC+'; Galerkin and transpose identities verified',
      'Setup creates all A,P,R and omega values. A_next=R A P and R=P transpose are verified against the stored browser matrices. Optical copies of A0,A1,A2 serve smoothing; CPU copies compute reliable level residuals. A3 is a CPU direct solve. P,R are only digital. All ten browser operators appear in the appendix with values and sparsity. Coarsest omega is stored but unused.',subtitle='Browser operator inventory: 4 A matrices + 3 P matrices + 3 R matrices')
table(s,['Level','Operator and nonzeros','Prolongation Pℓ','Restriction Rℓ','Assignment'],[
 ['0','A₀: 64 × 64, 190','64 × 22','22 × 64','A: optics + CPU'],
 ['1','A₁: 22 × 22, 64','22 × 8','8 × 22','A: optics + CPU'],
 ['2','A₂: 8 × 8, 22','8 × 3','3 × 8','A: optics + CPU'],
 ['3','A₃: 3 × 3, 7','—','—','CPU direct solve'],
 ],h=3.7,widths=[.08,.28,.19,.19,.26],size=19)
text(s,.7,5.95,12,.5,'Aℓ₊₁ = Rℓ Aℓ Pℓ        Rℓ = Pℓᵀ        ωℓ ≈ 1 / λmax(Aℓ)',24,TEAL,font=MATH)
note(s,'The CPU retains separate local vectors at each level. Coarse vectors are coefficients in algebraic spaces.',size=18)

# 15
s=new('Convergence of the ideal browser model', WEB_SRC+'; fresh zero-start execution',
      'Reproduced the browser core without modifying it. Five outer corrections, ten top-level V-cycles,180 optical and111 digital calls, relative residual3.1704180357133085e-13. Plot left shows actual true residual history. Right shows final error against the analytic quadratic, not merely two visually overlapping solution curves. Counts include different matrix sizes and are not runtime weights.',subtitle='Ideal 1D model. Zero starting guess. Target 10⁻¹².')
hist=RUN['history'];xs=[a['step'] for a in hist];ys=[a['relative'] for a in hist]
chart(s,[('true residual',xs,ys,TEAL),('target',xs,[1e-12]*len(xs),GRAY)],.55,1.75,6.15,4.45,'outer correction count','relative residual',True)
err=(np.array(RUN['x'])-np.array(D['exact']))*1e9
chart(s,[('x − x*, ×10⁻⁹',DER['t'],err,NAVY)],6.85,1.75,5.85,4.45,'position t','solution error ×10⁻⁹')
note(s,'Final η = 3.17 × 10⁻¹³      180 optical calls      111 digital calls      10 V-cycles',size=22,c=TEAL)

# 16
s=new('The separate 2D noisy experiment', MAIN_SRC,
      'Actual64×64 positive discrete Laplacian with zero exterior values and signed source strips at rows21 and42, columns16through47. These are source terms, not prescribed-potential internal boundaries. Coordinates and amplitudes use the code unscaled stencil units. Displayed center-column profile is taken from the full computed2D field. Independent sparse direct solution is used only as evaluation reference. Main source SHA and versions are in research/main-data.json.',subtitle='main.py: 4096 unknowns, two AMG levels, input quantization and output noise')
text(s,.7,1.85,5.5,.9,'4xᵢⱼ − xᵢ₋₁,ⱼ − xᵢ₊₁,ⱼ\n− xᵢ,ⱼ₋₁ − xᵢ,ⱼ₊₁ = bᵢⱼ',25,NAVY,font=MATH)
shape(s,1.1,3.0,3.55,2.8,fill='F6F8F9',line=GRAY,kind=MSO_SHAPE.RECTANGLE)
shape(s,1.99,3.92,1.78,.09,fill=AMBER,line=AMBER,kind=MSO_SHAPE.RECTANGLE)
shape(s,1.99,4.84,1.78,.09,fill=TEAL,line=TEAL,kind=MSO_SHAPE.RECTANGLE)
text(s,4.9,3.72,1.2,.42,'+2',23,AMBER);text(s,4.9,4.64,1.2,.42,'−2',23,TEAL)
text(s,1.05,5.95,5.2,.42,'64 × 64 interior grid; exterior x = 0',18,GRAY)
field=np.array(MAIN['hybrid_x']).reshape(64,64);ref=np.array(MAIN['reference']).reshape(64,64)
chart(s,[('noisy hybrid',list(range(64)),field[:,32],AMBER),('direct reference',list(range(64)),ref[:,32],TEAL)],6.55,1.8,6.1,4.6,'row index, at column 32','potential (code units)')
note(s,'Verified relative residual: 3.96 × 10⁻¹¹. Relative solution error: '+f'{MAIN["solution_error"]:.2e}'+'.',size=20)

# 17
s=new('Counted digital products in the 2D run', MAIN_SRC+'; one controlled run, setup seed 0',
      'Plain148, digitalMG60, hybrid45 counted digital products; hybrid60 analog calls. Relative residuals independently observed: plain7.8e-11,digital6.1e-11,hybrid3.961e-11. Hybrid is69.6% fewer fine-grid digital products versusplain,25% versusdigitalMG. Excluded costs: setup,power iteration,P/R transfers,coarse spsolve, scalar/vector work, reporting residual,DAC/ADC,memory,calibration. Coarse matrix704×704 means excluded coarse cost can be material. No runtime or energy claim.',subtitle='Same 2D problem and final relative-residual target 10⁻¹⁰. Counter scope matters.')
table(s,['Method','Digital A calls','Analog A calls','True relative residual'],[
 ['Plain CG','148','0','7.8 × 10⁻¹¹'],['Digital MG–CG','60','0','6.1 × 10⁻¹¹'],['Noisy hybrid + restarts','45','60','4.0 × 10⁻¹¹']
 ],h=2.9,widths=[.36,.19,.19,.26],size=22)
text(s,.7,5.05,5.4,.75,'148 / 45 = 3.29',32,TEAL,True)
text(s,6.2,5.05,6.0,.9,'Ratio of counted digital products\nNo measured hardware speedup',21,NAVY)
note(s,'Transfers and repeated 704 × 704 coarse solves are excluded. Browser counts use a different convention.',size=18)

# 18
s=new('Implemented behavior and open questions', MAIN_SRC+'; web/README.md; Lee Methods',
      f'Paper-inspired structure is implemented, not an exact hardware reproduction. main.py quantizes the input and adds fresh Gaussian output noise. It has no matrix quantization, physical encoding, averaging or timing. Browser uses ideal MVMs and a functional shared-converter diagram. Classical PCG assumptions are not guaranteed under noisy variable asymmetric preconditioning. Zhu related work supports coherent signed multiplication with digital memory/reconfiguration, not a claimed replacement for the current multigrid code. References: {LEE}; {ZHU}.')
table(s,['Implemented and checked','Still to establish'],[
 ['Nested residual / CG / multigrid computation','Variable-preconditioner convergence across trials'],
 ['Input quantization and additive noise in main.py','Calibration against measured optical errors'],
 ['Fixed matrix blocks and CPU feedback in demonstrator','Signed encoding, sparse tiling, and physical routing'],
 ['True residuals and algorithmic counters','End-to-end latency and energy, including transfers'],
 ],h=4.25,widths=[.49,.51],size=21)
note(s,'Related work: Zhu et al. (2024) provides a coherent signed-MVM architecture with digital memory and control.',size=18)

# 19
s=new('Next validation: full computational cost', MAIN_SRC+'; web/README.md',
      'Close on the scientific contribution and next validation. The method works for the reported cases. A next experiment should retain identical matrices and compare calibrated noisy MVM/preconditioner variants over repeated seeds, use independently recomputed residuals, and include coarse factorization, transfers, memory/conversion overhead in time/energy accounting. Do not promise an outcome. Main talk ends here; the following slides are technical backup.',layout='key_takeaway')
text(s,.75,1.85,11.7,1.35,'Optics computes matrix–vector products.\nThe CPU builds and verifies the solution.',31,NAVY,True)
for i,(a,b,c) in enumerate([('Residual check','What remains unsatisfied?',TEAL),('Approximate correction','Which inexpensive products help?',AMBER),('True-residual verification','Did the equations improve?',TEAL)]):
    shape(s,.7+i*4.12,3.65,3.5,1.3,a+'\n'+b,line=c,size=21)
    if i<2:line(s,4.2+i*4.12,4.3,4.75+i*4.12,4.3)
note(s,'Next: calibrated noise + repeated trials + full cost accounting, with the same sparse operators.',size=22)

# 20
s=new('Complete recurrence and termination conditions', WEB_SRC, 'Exact algebraic recurrence of the browser core. Index k counts completed PCG iterations. rho_new overwrites rho after beta. At the capped final iteration, the source still computes its next V-cycle and direction before returning. Breakdown checks nonfinite alpha and positive pTq. Outer loop distinguishes convergence and limit.',subtitle='Technical appendix: browser configuration',appendix=True)
table(s,['Routine','Ordered operations'],[
 ['Outer initialization','Choose x. Load Aℓ, Pℓ, Rℓ, ωℓ, b.'],
 ['Outer check','r = b − A₀x; test ||r|| / ||b|| < 10⁻¹².'],
 ['PCG initialization','δ = 0; s = r − A₀δ; z = V(s); p = z; ρ = sᵀz.'],
 ['PCG step','q = A₀p; α = ρ/(pᵀq); δ += αp; s −= αq.'],
 ['PCG check','Return δ if ||s|| / ||r|| < 10⁻².'],
 ['New direction','z = V(s); ρnew = sᵀz; β = ρnew/ρ; p = z + βp; ρ = ρnew.'],
 ['Caps / return','PCG: 20 steps. Outer: 10 corrections, then final true-residual check.'],
 ['Outer update','x += δ; return to fresh outer residual.'],
 ],h=4.65,widths=[.23,.77],size=17)

# 21
s=new('Recursive V-cycle and smoothing pseudocode', WEB_SRC, 'V(l,g) returns a local correction. R_l=P_l transpose. The coarse solve uses elimination, not an explicit inverse. CPU computes d and all transfer products. e starts at zero only on V-cycle entry; post-smoothing starts from the corrected value. Main2D cycle differs and is shown later.',appendix=True,subtitle='Every operation belongs to a CPU or optical assignment')
text(s,.65,1.85,7.5,4.8,'V(l, g):\n  if l = 3: return solve(A₃, g)\n  e = 0\n  repeat 3 times: e = Smooth(l, e, g)\n  d = g − Aℓe                 [CPU]\n  gc = Rℓd                    [CPU]\n  ec = V(l + 1, gc)\n  e = e + Pℓec                [CPU]\n  repeat 3 times: e = Smooth(l, e, g)\n  return e',21,NAVY,font='DejaVu Sans Mono')
text(s,8.3,1.85,4.25,3.2,'Smooth(l, e, g):\n\nencode e\ny = Aℓe      [optical]\ndetect y\ne = e + ωℓ(g − y)\n                 [CPU]\nreturn e',22,TEAL)
note(s,'At level 0, g₀ = s and V(0, s) returns z. The outer solution x is separate.',size=19)

# 22
s=new('Fine operators A₀ and A₁', WEB_SRC, 'Actual stored matrices. Sparsity panels show every nonzero; tables are labeled excerpts, not complete matrices. A0=h^-2 tridiag(−1,2,−1), h=1/65. All entries are retained in embedded browser CSR data.',appendix=True,subtitle='A₀: 64 × 64, 190 nonzeros. A₁: 22 × 22, 64 nonzeros.')
for j,l in enumerate([0,1]):
    o=D['levels'][l]['A'];x=.7+j*6.15
    sparseplot(s,o,x,1.85,2.0,2.0,AMBER)
    text(s,x+2.25,2.0,3.5,1.6,f'A{["₀","₁"][l]} fixed\nCPU residuals\nOptical smoothing',22,NAVY)
    matrix_table(s,o,range(4),range(4),x,4.25,5.65,1.8,size=14)
    text(s,x,6.15,5.6,.35,'Upper-left 4 × 4 excerpt; rounded to 3 decimals',14,GRAY)

# 23
s=new('Coarse operators A₂ and A₃', WEB_SRC, 'Complete numerical matrices, rounded to3decimals. A2 has22 nonzeros, A3 has7. Original sparse matrices remain full precision. A3 direct solve is CPU-only. No inverse is formed.',appendix=True,subtitle='Full matrices shown. Entries rounded to 3 decimals.')
matrix_table(s,D['levels'][2]['A'],range(8),range(8),.6,1.9,8.0,3.9,size=11)
text(s,.7,6.05,7.8,.5,'A₂  (8 × 8): optical smoothing + digital residuals',20,NAVY)
matrix_table(s,D['levels'][3]['A'],range(3),range(3),9.0,2.3,3.65,2.2,size=14)
text(s,9.0,4.8,3.65,1.0,'A₃  (3 × 3)\nCPU direct solve',22,TEAL)

# 24,25
for l,sub,n,nc in [(0,'₀',64,22),(1,'₁',22,8)]:
    po=D['levels'][l]['P'];ro=D['levels'][l]['R']
    s=new(f'Transfer operators P{sub} and R{sub}',WEB_SRC,'Every nonzero is shown in the sparsity views. Selected numerical entries below are excerpts. R=P transpose exactly in stored data. These operators do not change during the solve, and both matrix-vector operations are digital.',appendix=True,subtitle=f'P{sub}: {n} × {nc}. R{sub}: {nc} × {n}. Fixed algebraic transfer operators.')
    sparseplot(s,po,.8,1.9,3.3,2.1,PURPLE);sparseplot(s,ro,7.0,1.9,4.7,1.6,PURPLE)
    text(s,4.35,2.0,2.2,1.2,'coarse\ncorrection\nto fine',20,PURPLE)
    text(s,7.0,3.7,5.1,.4,'fine residual to coarse: gnext = R d',18,PURPLE)
    matrix_table(s,po,range(5),range(4),.7,4.45,5.65,1.8,size=13)
    matrix_table(s,ro,range(4),range(5),6.85,4.45,5.65,1.8,size=13)
    note(s,'Numerical excerpts: first rows / columns. Full patterns above; zeros outside these excerpts are not implied.',size=16)

# 26
s=new('Transfer operators P₂ and R₂', WEB_SRC, 'Complete final transfer pair rounded to4decimals. This is an algebraically constructed interpolation matrix, not simple averaging or selection of every nth physical sample.',appendix=True,subtitle='Full final transfer pair. R₂ = P₂ᵀ. Both operations run on the CPU.')
matrix_table(s,D['levels'][2]['P'],range(8),range(3),.75,1.9,4.4,4.1,fmt='.4f',size=17)
matrix_table(s,D['levels'][2]['R'],range(3),range(8),5.75,2.65,6.85,2.2,fmt='.4f',size=12)
text(s,6.0,5.3,6.3,.75,'P₂e₃ has 8 entries.\nR₂d₂ has 3 entries.',24,PURPLE)

# 27
s=new('The 2D experiment uses four fixed sparse matrices', MAIN_SRC, 'All four stored matrices of main.py: A,P,R,Ac. Matrix A has4096rows,20224nnz. P4096x704 with10116nnz, R transpose, Ac704square6096nnz. A=I64 kronT64 +T64 kronI64 with T tridiag−1,2,−1. The occupancy views bin sparse indices into64x64 cells for legibility; a colored bin indicates at least one nonzero, not a literal matrix entry. Identity is notation, not a separately allocated solver matrix.',appendix=True,subtitle='main.py hierarchy from the measured run; distinct from the browser matrices')
items=[('A','A',4096,4096),('P','P',4096,704),('R','R',704,4096),('Ac','A_coarse',704,704)]
for i,(lab,key,n,m) in enumerate(items):
    x=.65+i*3.13;o=MAIN['matrices'][key]
    text(s,x,1.85,2.8,.8,f'{lab}: {n} × {m}\n{o["nnz"]:,} nonzeros',19,NAVY,True)
    sparseplot(s,o,x,2.95,2.7,2.6,AMBER if key=='A' else PURPLE,bins=64)
text(s,.7,5.93,12,.5,'A = I₆₄ ⊗ T₆₄ + T₆₄ ⊗ I₆₄      Ac = RAP      R = Pᵀ',24,NAVY,font=MATH)
note(s,'T₆₄ = tridiag(−1, 2, −1). Patterns use 64 × 64 occupancy bins. Coarse solve: CPU.',size=18)

# 28
s=new('The noisy smoother has a specific software model', MAIN_SRC, 'Exact noisy_mvm implementation: scale ismaxabs(v), zero input returnszeros; q=round(127v/scale)/127; y=4scale[(Aq)/4+Gaussian(0,.045²)]. No separate matrix quantization or256-repeat averaging. Main smooth initializes e=omega*rhs, algebraically skippingA@0, so4pre sweeps callanalogMVM3times. Each hybrid V-cycle computes residualdigitally, restricts, does spsolve, prolongs, and returns withoutpostsmoothing.',appendix=True,subtitle='main.py: input quantization + independent Gaussian output noise')
text(s,.75,1.85,11.7,2.4,'a = ||v||∞\nq = round(127 v / a) / 127\nỹ = 4a [ (Aq)/4 + ξ ],     ξᵢ ∼ N(0, 0.045²)',28,NAVY,font=MATH)
text(s,.75,4.35,11.8,1.5,'If a = 0, return zero.\nFour pre-sweeps begin with e = ωg, then use three analog MVMs.\nNo post-smoothing in the hybrid configuration.',23,TEAL)
note(s,'Not modeled: matrix quantization, optical averaging, device drift, saturation, conversion timing, or energy.',size=18)

# 29
s=new('Settings and counter definitions', 'main.py; web/index.html; source-level review', 'main.py uses SciPy CG with inner rtol1e-12 and maximum5steps in each outer restart, tolerance1e-10 maximum100restarts. Browser inner rtol1e-2maximum20,outer1e-12maximum10. main counter includes fineA exact/noisy wrappers only; excludes setup/diagnostics/transfers/coarsesolve. Browser countsdigital A,R,P, plus opticalA and convertercalls. Neither is a complete hardware cost model. main.py ignores info codes; reported convergence independently checked.',appendix=True)
table(s,['Setting','main.py hybrid','Browser'],[
 ['Outer target / cap','10⁻¹⁰ / 100 restarts','10⁻¹² / 10 corrections'],
 ['Inner CG target / cap','10⁻¹² / 5 steps','10⁻² / 20 steps'],
 ['Smoothing','4 pre / 0 post','3 pre / 3 post'],
 ['Digital counter','Fine A wrapper calls','Aℓ, Pℓ and Rℓ calls'],
 ['Zero-input smoothing','First product skipped','Explicitly counted'],
 ['Coarse solve','704 × 704 sparse solve','3 × 3 direct solve'],
 ['Convergence evidence','Independent true residual','True residual + terminal status'],
 ],h=4.6,widths=[.3,.35,.35],size=18)

# 30
s=new('Convergence theory and observed results', 'SciPy CG documentation; main.py; web/index.html',
      'SciPy CG requires Hermitian positive definiteA and a Hermitian positive definite preconditioner. The standard fixed linear SPD-preconditioner argument doesnot transfer automatically to this noisy, quantized, asymmetric action. This run converges empirically. A nextcomparison should include flexibleKrylov formulations and multiple noise realizations. https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.cg.html . Residual-error relation is exact for invertibleA; conditioning and discretization remain distinct.',appendix=True)
text(s,.7,1.9,11.8,1.05,'Classical PCG assumes a fixed, linear, SPD preconditioner.\nNoise and quantization make this V-cycle variable.',26,NAVY)
text(s,.7,3.45,11.8,1.2,'A(x* − x) = r\nx* − x = A⁻¹r',30,TEAL,font=MATH)
text(s,.7,5.0,11.7,1.15,'A small residual measures satisfaction of the discrete equations.\nSolution error also depends on conditioning. PDE error also depends on discretization.',23,INK)

# 31
s=new('Related work: Zhu’s coherent processor', 'Zhu et al., ACS Photonics 11, 1189–1196 (2024)',
      f'Relatedwork only. Verified publisherabstract describes coherent analogue cores that perform signed multiplication, digital electronics for memory/reconfigurability, and error management for finite-difference PDEs. The supplementary-information listing explicitly covers fixed-point Richardson and Jacobi with residuecorrection. We do not claim a reproduction of that hardware, exact PDE geometry, bitdepth, or iteration schedule. Source:{ZHU}. Fullpaywalledarticle wasnotused for detailednumericalclaims.',appendix=True)
table(s,['Aspect','Lee-inspired project','Zhu related work'],[
 ['Numerical emphasis','Multigrid inside Krylov + residual correction','Fixed-point iteration with error management'],
 ['Optical assignment','Smoothing matrix–vector products','Coherent signed products'],
 ['Electronics','Residuals, vectors, transfers, control','Memory, reconfiguration, control'],
 ['Project status','Numerical emulation and ideal demonstrator','Architecture reference; not reproduced'],
 ],h=4.2,widths=[.22,.4,.38],size=21)
note(s,'Common principle: approximate optical linear operations cooperate with digital state and correction.',size=19)

# Additional technical evidence before the source list.
s=new('The actual two-level cycle in main.py', MAIN_SRC,
      'Exact main.py V-cycle. smooth(g,mvm,pre) starts e=omega*g, then applies pre-1 updates. The residual d=g−A e is digital. RestrictionR, coarse spsolveAc, and prolongationP are digital. For digital2/2, post smoothing is applied as a correction to the existing e: e+=smooth(g−A e,exact_mvm,2). This equals two Richardson post-updates in exact arithmetic. Hybrid4/0returnswithoutpost. PlainCG anddigitalMGCGsolveAx=bdirectly; onlyhybridusesouterrestartscorrectionloop.',appendix=True,subtitle='4096 → 704. Hybrid: four pre-sweeps, no post-smoothing.')
for i,(label,col) in enumerate([
    ('e = Smooth(g, 4 sweeps)     [3 analog calls]',AMBER),
    ('d = g − Ae     [digital residual]',TEAL),
    ('gc = Rd;  solve Ac ec = gc     [CPU]',TEAL),
    ('e ← e + Pec     [digital prolongation]',TEAL),
    ('Hybrid: return e     [no post-smoothing]',TEAL)]):
    yy=1.85+i*.85
    shape(s,.7,yy,8.0,.67,label,line=col,size=21)
    if i<4:line(s,4.7,yy+.67,4.7,yy+.85,TEAL)
text(s,9.0,1.95,3.5,3.5,'Digital baseline:\n2 pre + 2 post\n\nPlain / digital CG:\nsolve Ax = b\n\nHybrid only:\nshort correction solves\nwith outer restarts',20,NAVY)
note(s,'The coarse solver runs on a 704 × 704 matrix each cycle. Its cost is absent from the MVM counters.',size=18)

s=new('Setup constructs operators before iteration starts', WEB_SRC+'; main.py PyAMG setup',
      'Hierarchy is constructed before reported solver counters. PyAMG smoothed aggregation formsP,R and Galerkincoarseoperators. Browser ships these matrices asCSRarrays; allsetupiscompletebeforevisualized solve. Source smoother.py computesweightsbyeigsh. main.py estimatesfineoperator spectralradiusby30poweriterationsusing itsseededgenerator. Stored browsercoarsestomega isunusedbecauselevel3directsolve. Setup isnot countedinthe reportedMVMs.',appendix=True)
for i,label in enumerate(['Discretize: A, b','Build AMG: P, R, RAP','Choose ω; load fixed weights']):
    shape(s,.7+i*4.12,1.85,3.5,.95,label,line=TEAL,size=21)
    if i<2:line(s,4.2+i*4.12,2.325,4.75+i*4.12,2.325,TEAL)
table(s,['Browser level','Stored relaxation weight','Use'],[
 [str(l),f'{D["omega"][l]:.9g}',('Richardson smoothing' if l<3 else 'Unused: direct solve')]
 for l in range(4)],x=.7,y=3.35,w=7.8,h=2.75,widths=[.2,.38,.42],size=19)
text(s,9.0,3.45,3.6,2.25,'main.py\n30 power iterations\n\nω = '+f'{MAIN["omega"]:.8f}',22,NAVY)
note(s,'During the solve: A, P, R, and ω stay fixed. Only solution, residual, and correction vectors change.',size=18)

s=new('True residuals contract across noisy restarts', MAIN_SRC+'; independently recomputed residual history',
      'The histogram is not reconstructed from CG recursive residuals. At each accumulatedoutercorrection,weindependentlycompute||b−Ax||/||b||withthesparseA. FourcorrectioncallswithfiveCGstepseachproduce20Vcycles and60analogcalls. Theouterloopthenchecksconvergence. Monitoring MVMs areanalysisdiagnostics andnotinsertedintotheoriginalcounter. Plot usesa truelogarithmicverticalaxis.',appendix=True,subtitle='main.py noisy hybrid. Each correction solve has at most five CG steps.')
hs=MAIN['true_history'];ix=list(range(len(hs)))
chart(s,[('true residual',ix,hs,TEAL),('target 10⁻¹⁰',ix,[1e-10]*len(ix),GRAY)],.6,1.8,8.5,4.55,'completed outer corrections','relative residual',True)
text(s,9.3,2.2,3.1,2.1,'Four corrections\n\n20 V-cycles\n\n60 analog calls',24,NAVY)
note(s,'Observed convergence for this seeded run; robustness across noise realizations remains to be measured.',size=18)

# Sources
s=new('Sources and reproducibility', 'Primary papers, current source code, and recorded numerical runs',
      'Primarymethodsource Leehttps://arxiv.org/pdf/2511.01005. Zhuhttps://doi.org/10.1021/acsphotonics.3c01694. BackgroundShewchukhttps://www.cs.cmu.edu/~quake-papers/painless-conjugate-gradient.pdf. Presentationdesignreferenceshttps://writing.engr.psu.edu/AE_Student_Classroom_Notes.pdf andhttps://catalyst.harvard.edu/writing-communication-center/visualize-science/slides/. Compared publicmultigridtutorialhttps://sites.cs.ucsb.edu/~gilbert/cs219/cs219Spr2018/Slides/cs219-12-mgtut_part2.pdf. No publishedslideartworkcopied. All numericalcharts use recordedsourcevalues.',appendix=True)
text(s,.7,1.75,12,2.2,'Lee et al. (2025), Integrated photonic multigrid solver for partial differential equations\narXiv:2511.01005\n\nZhu et al. (2024), Coherent General-Purpose Photonic Matrix Processor\nACS Photonics 11, 1189–1196. DOI: 10.1021/acsphotonics.3c01694',21,NAVY)
text(s,.7,4.1,12,1.3,'Repository evidence: main.py and web/index.html\nBrowser: all three initial guesses reproduced.\n2D: original noise generator seed 0; PyAMG setup fixed with NumPy seed 0.',20,TEAL)
v=MAIN['versions']
text(s,.7,5.6,12,.8,'Run environment: '+', '.join(k+' '+v for k,v in v.items())+'\nSource SHA-256: '+MAIN['sha256'][:24]+'…',17,GRAY)

# Persist machine-readable content and speaker notes before rendering.
for i,m in enumerate(META):
    sl=PRS.slides[i]
    m['text']=[sh.text for sh in sl.shapes if getattr(sh,'has_text_frame',False)]
    m['tables']=[[[cell.text for cell in row.cells] for row in sh.table.rows] for sh in sl.shapes if sh.has_table]
(BASE/'content.json').write_text(json.dumps({'brief':{'audience':'Professor new to this project','duration_minutes':20,'main_slides':19},'slides':META},indent=2))
(BASE/'outline.json').write_text(json.dumps({'slides':[{k:m[k] for k in ['idx','title','layout','appendix']} for m in META]},indent=2))
(BASE/'build/speaker-notes.md').write_text('\n\n'.join(f'## {m["idx"]}. {m["title"]}\n\n{m["notes"]}\n\nSources: {m["source"]}' for m in META))
ENG.save(str(BASE/'build/photonic-pde-draft.pptx'))
print(f'Created {len(PRS.slides)} slides: 19 main + {len(PRS.slides)-19} appendix.')
