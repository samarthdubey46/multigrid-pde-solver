"""Consistent, publication-style display equations for the PowerPoint deck."""
import hashlib,re
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import mathtext,rc_context
from matplotlib.font_manager import FontProperties
from PIL import Image
from pptx.util import Inches

ASSETS=Path(__file__).parent/'equations'
ASSETS.mkdir(exist_ok=True)
EXACT={
'Aℓ₊₁ = Rℓ Aℓ Pℓ        Rℓ = Pℓᵀ        ωℓ ≈ 1 / λmax(Aℓ)':r'A_{\ell+1}=R_\ell A_\ell P_\ell \qquad R_\ell=P_\ell^{\mathsf{T}} \qquad \omega_\ell\approx\frac{1}{\lambda_{\max}(A_\ell)}',
'−u″(t) = 1':r'-\frac{d^2u}{dt^2}=1',
'(2xᵢ − xᵢ₋₁ − xᵢ₊₁) / h² = 1':r'\frac{2x_i-x_{i-1}-x_{i+1}}{h^2}=1',
'A₀ = h⁻² tridiag(−1, 2, −1)':r'A_0=\frac{1}{h^2}\operatorname{tridiag}(-1,2,-1)',
'α = ρ / (pᵀq)':r'\alpha=\frac{\rho}{p^{\mathsf{T}}q}',
'β = ρnew / ρ':r'\beta=\frac{\rho_{\mathrm{new}}}{\rho}',
'ρnew = sᵀz':r'\rho_{\mathrm{new}}=s^{\mathsf{T}}z',
'Test ||s||₂ / ||r||₂ < 10⁻²':r'\frac{\Vert s\Vert_2}{\Vert r\Vert_2}<10^{-2}',
'η = ||r||₂ / ||b||₂':r'\eta=\frac{\Vert r\Vert_2}{\Vert b\Vert_2}',
'q = round(127 v / a) / 127':r'q=\frac{1}{127}\operatorname{round}\!\left(\frac{127v}{a}\right)',
'ỹ = 4a [ (Aq)/4 + ξ ],     ξᵢ ∼ N(0, 0.045²)':r'\widetilde{y}=4a\left[\frac{Aq}{4}+\xi\right],\quad \xi_i\sim\mathcal{N}(0,0.045^2)',
'ωℓ ≈ 1 / λmax(Aℓ)':r'\omega_\ell\approx\frac{1}{\lambda_{\max}(A_\ell)}',
'εnew = (I − ωA)ε':r'\varepsilon_{\mathrm{new}}=(I-\omega A)\varepsilon',
}
SUB=str.maketrans('₀₁₂₃₄₅₆₇₈₉ᵢⱼ₊₋','0123456789ij+-')
SUP=str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻','0123456789+-')

def formula(s):
    s=s.strip()
    if s in EXACT:return EXACT[s]
    for prefix in ['CPU update:','CPU:','Optics:','Then ','Find δ with ']:
        if s.startswith(prefix):
            rest=s[len(prefix):].strip()
            if prefix=='Find δ with ':return r'\mathrm{Find}\ \delta:\quad '+formula(rest)
            return (r'\mathrm{'+prefix.strip().replace(':','')+r'}:\quad ' if prefix not in ['Then '] else r'\mathrm{Then}\quad ')+formula(rest)
    s=re.sub(r'([A-Za-zω])ℓ([₊₋₀₁₂₃₄₅₆₇₈₉]*)',lambda m:m[1]+r'_{\ell '+m[2].translate(SUB)+'}',s)
    s=s.replace('xnew',r'x_{\mathrm{new}}').replace('rnew',r'r_{\mathrm{new}}').replace('ρnew',r'ρ_{\mathrm{new}}')
    s=s.replace('x*',r'x^{\star}').replace('ᵀ',r'^{\mathsf{T}}')
    s=re.sub('[₀₁₂₃₄₅₆₇₈₉ᵢⱼ₊₋]+',lambda m:'_{'+m[0].translate(SUB)+'}',s)
    s=re.sub('[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+',lambda m:'^{'+m[0].translate(SUP)+'}',s)
    s=s.replace('ℝ',r'\mathbb{R}').replace('ℓ',r'\ell ')
    for a,b in [('−','-'),('←',r'\leftarrow '),('→',r'\to '),('≈',r'\approx '),('∈',r'\in '),('⊗',r'\otimes '),('×',r'\times '),('…',r'\ldots '),('‖',r'\Vert '),('||',r'\Vert '),('∞',r'\infty '),('∼',r'\sim ')]:s=s.replace(a,b)
    s=s.replace('Vcycle',r'\operatorname{V}').replace('λmax',r'\lambda_{\max}').replace('Ac',r'A_c')
    s=s.replace(';',r';\quad ').replace('    ',r'\qquad ')
    return s

def is_formula(s):
    if s.startswith(('CPU update:','CPU:','Optics:','Test ||','Find δ with ','Then ')):return True
    if not any(c in s for c in ['=','←','≈','∈']):return False
    # Keep prose containing equations as readable body text.
    words=re.findall(r'[A-Za-z]{3,}',s)
    return all(w in ['new','newnew','max','tridiag','Vcycle','round','CPU','Optics','Test'] for w in words)

def equation(sl,x,y,w,h,s,size,color='172C3B',align='left'):
    tex=formula(s)
    key=hashlib.sha256((tex+str(size)+color).encode()).hexdigest()[:20]
    path=ASSETS/(key+'.png')
    if not path.exists():
        with rc_context({'mathtext.fontset':'stix','font.family':'STIXGeneral','savefig.transparent':True}):
            mathtext.math_to_image('$'+tex+'$',str(path),prop=FontProperties(size=size),dpi=400,color='#'+color)
    with Image.open(path) as im:iw,ih=im.size
    # Keep consistent physical point size unless a narrow box needs fitting.
    natural_w=iw/400;natural_h=ih/400
    scale=min(1,w/natural_w,h/natural_h)
    ww=natural_w*scale;hh=natural_h*scale
    xx=x+(w-ww)/2 if align=='center' else x
    pic=sl.shapes.add_picture(str(path),Inches(xx),Inches(y+(h-hh)/2),width=Inches(ww),height=Inches(hh))
    pic.name='Equation: '+s
    pic._element.nvPicPr.cNvPr.set('descr',s+' | LaTeX: '+tex)
    return pic
