import json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

base=Path(__file__).resolve().parents[1]
web=json.loads((base/'research/web-data.json').read_text())
d=web['data']
def mat(o): return csr_matrix((o['val'],o['idx'],o['ptr']),shape=(o['rows'],o['cols']))
A=[mat(l['A']) for l in d['levels']]
P=[mat(l['P']) for l in d['levels'][:-1]]
R=[mat(l['R']) for l in d['levels'][:-1]]
checks={}
for l in range(3):
    E=A[l+1]-R[l]@A[l]@P[l]
    checks[f'Galerkin_{l}']=float(np.linalg.norm(E.data)/np.linalg.norm(A[l+1].data))
    checks[f'transpose_{l}']=float(np.linalg.norm((R[l]-P[l].T).data))
def smooth(l,e,g):
    for _ in range(3): e=e+d['omega'][l]*(g-A[l]@e)
    return e
def cycle(l,g):
    if l==3:return spsolve(A[l],g)
    e=smooth(l,np.zeros_like(g),g)
    e+=P[l]@cycle(l+1,R[l]@(g-A[l]@e))
    return smooth(l,e,g)
# Controlled error-mode experiment on the stored browser operator.
t=np.arange(1,65)/65
initial=np.sin(np.pi*t)+0.35*np.sin(32*np.pi*t)
after_smooth=smooth(0,initial,np.zeros(64))
after_coarse=after_smooth+P[0]@cycle(1,R[0]@(-A[0]@after_smooth))
after_post=smooth(0,after_coarse,np.zeros(64))
out=dict(checks=checks,t=t.tolist(),error_profiles={k:v.tolist() for k,v in [('initial',initial),('after_smooth',after_smooth),('after_coarse',after_coarse),('after_post',after_post)]},
         error_norms={k:float(np.linalg.norm(v)) for k,v in [('initial',initial),('after_smooth',after_smooth),('after_coarse',after_coarse),('after_post',after_post)]})
(base/'research/derived.json').write_text(json.dumps(out,indent=2))
print(out['checks']);print(out['error_norms'])
