"""Observe original scripts without changing their solver paths or counters."""
import contextlib, hashlib, io, json, runpy, sys
from pathlib import Path
import numpy as np
import scipy, scipy.sparse.linalg as spla
import pyamg

root=Path(__file__).resolve().parents[2]
real_cg=spla.cg
cg_runs=[]
def observed_cg(A,b,*args,**kwargs):
    hist=[]
    prior=kwargs.get('callback')
    # Monitoring uses the sparse A stored by the source function, bypassing its counter.
    raw_A=A.matvec.__self__ if False else None
    def callback(x):
        # The gallery operator is exactly the main.py operator and is used only for diagnostics.
        matrix=pyamg.gallery.poisson((64,64),format='csr')
        hist.append(float(np.linalg.norm(b-matrix@x)/np.linalg.norm(b)))
        if prior: prior(x)
    kwargs['callback']=callback
    x,info=real_cg(A,b,*args,**kwargs)
    cg_runs.append(dict(rhs_norm=float(np.linalg.norm(b)),history=hist,info=int(info),maxiter=kwargs.get('maxiter'),x=x.tolist()))
    return x,info
spla.cg=observed_cg
# PyAMG's setup may use the legacy NumPy RNG separately from main.py's seeded generator.
np.random.seed(0)
stream=io.StringIO()
try:
    with contextlib.redirect_stdout(stream): ns=runpy.run_path(str(root/'main.py'))
finally: spla.cg=real_cg
(root/'presentation/research/main-run.txt').write_text(stream.getvalue())
def sparse_record(M):
    M=M.tocsr()
    return dict(rows=M.shape[0],cols=M.shape[1],nnz=M.nnz,ptr=M.indptr.tolist(),idx=M.indices.tolist(),val=M.data.tolist())
A,b=ns['A'],ns['b']
ref=spla.spsolve(A,b)
hybrid=np.sum([np.array(r['x']) for r in cg_runs[2:]],axis=0)
true_hist=[1.0]
x=np.zeros_like(b)
for r in cg_runs[2:]:
    x+=np.array(r['x']);true_hist.append(float(np.linalg.norm(b-A@x)/np.linalg.norm(b)))
record=dict(stdout=stream.getvalue(),versions=dict(numpy=np.__version__,scipy=scipy.__version__,pyamg=pyamg.__version__),
            seed_note='main.py rng=0; external np.random.seed(0) fixes PyAMG setup randomness for this observed run',
            sha256=hashlib.sha256((root/'main.py').read_bytes()).hexdigest(),
            counts=dict(plain=ns['plain'],digital=ns['digital'],hybrid=ns['hybrid'],analog=ns['count']['analog']),
            matrices={k:sparse_record(ns[k]) for k in ['A','P','R','A_coarse']},omega=float(ns['OMEGA']),
            b=b.tolist(),reference=ref.tolist(),hybrid_x=hybrid.tolist(),true_history=true_hist,
            solution_error=float(np.linalg.norm(hybrid-ref)/np.linalg.norm(ref)),cg_runs=cg_runs)
(root/'presentation/research/main-data.json').write_text(json.dumps(record))
print(stream.getvalue());print('Hierarchy:',[(k,(v['rows'],v['cols']),v['nnz']) for k,v in record['matrices'].items()]);print('True outer residuals:',true_hist)
