"""
Implementation of rank-biased overlap, a similarity measure for indefinite rankings

Code copied and then modified from:
https://github.com/ragrawal/measures/blob/master/measures/rankedlist/RBO.py
https://github.com/maslinych/linis-scripts/blob/master/rbo_calc.py

RBO conceptualization and formulation described in:
http://www.williamwebber.com/research/papers/wmz10_tois.pdf
"""

import math

def score(l1, l2, p=0.0):
    """Calculates Ranked Biased Overlap (RBO) score.

    l1 -- Ranked List 1
    l2 -- Ranked List 2
    p  -- The probability that a user will continue to consider the
          next rank at any given depth d in a theoretically infinite
          list. The creators of RBO suggest that for a prefix of length
          k > 1, an appropriate value of p could be (1 - 1/k). This
          would give the first k ranks about 86% of the weight of the
          evaluation (with the other 14% going to the rest of the
          theoretically infinite ranks).
    """
    if l1 == None: l1 = []
    if l2 == None: l2 = []

    sl,ll = sorted([(len(l1), l1), (len(l2), l2)])
    s, S = sl
    l, L = ll
    if s == 0: return 0
    if not p:
        # letting p be 0 would screw up some calculations
        if l == 1: return 1 if S == L else 0
        p = 1 - 1/l

    # Calculate the overlaps at ranks 1 through l
    # (the longer of the two lists)
    ss = set([]) # contains elements from the smaller list to depth i
    ls = set([]) # contains elements from the longer list to depth i
    x_d = {0: 0}
    sum1 = 0.0
    for i in range(l):
        x = L[i]
        y = S[i] if i < s else None
        d = i + 1

        # if two elements are same then
        # we don't need to add to either of the set
        if x == y:
            x_d[d] = x_d[d-1] + 1.0
        # else add items to respective list
        # and calculate overlap
        else:
            ls.add(x)
            if y != None: ss.add(y)
            x_d[d] = x_d[d-1] + (1.0 if x in ss else 0.0) + (1.0 if y in ls else 0.0)
        #calculate average overlap
        sum1 += x_d[d]/d * pow(p, d)

    sum2 = sum(x_d[d] * (d-s) / (d*s) * pow(p,d) for d in range(s+1, l+1)) if s != l else 0

    sum3 = (((x_d[l]-x_d[s])/l if s != l else 0) + x_d[s]/s) * pow(p,l)

    # Equation 32
    rbo_ext = (1-p) / p * (sum1+sum2) + sum3
    return rbo_ext