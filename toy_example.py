#!/usr/bin/env python

import itertools as itr
import copct

# toy causal relation
def causes(v):
    if v == ('g','m','r'): return set(['p'])
    if v == ('p','p'): return set(['t'])
    if v == ('p','g'): return set(['x'])
    if v == ('r','p'): return set(['z'])
    return set()

# maximum effect sequence length (gmr case in causes)
M = 3

if __name__ == "__main__":
    # toy observed sequence
    w = tuple('gmrgmr')
    # compute explanations
    status, tlcovs, g = copct.explain(causes, w, M=M, verbose=True)
    # Prune by minimum cardinality
    tlcovs_ml, ml = copct.minCardinalityTLCovers(tlcovs)
    
    # Display results
    print('Observed w:')
    print(w)
    print('Singleton sub-covers:')
    for jk in itr.combinations(range(7),2):
        if len(g[jk])>0:
            print("sub-seq from %d to %d covered by: %s"%(jk[0], jk[1], g[jk]))
    print('Top-level covers:')
    print([u for (u,_,_,_,_) in tlcovs])
    print('MC top-level covers:')
    print([u for (u,_,_,_,_) in tlcovs_ml])

