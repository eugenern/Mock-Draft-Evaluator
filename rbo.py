"""
Implementation of rank-biased overlap, a similarity measure for indefinite rankings

Code copied and then modified from:
https://github.com/ragrawal/measures/blob/master/measures/rankedlist/RBO.py
https://github.com/maslinych/linis-scripts/blob/master/rbo_calc.py

RBO conceptualization and formulation described in:
http://www.williamwebber.com/research/papers/wmz10_tois.pdf
"""

def score(list_1, list_2, p=0.0):
    """Calculates Ranked Biased Overlap (RBO) score.

    list_1 -- Ranked List 1
    list_2 -- Ranked List 2
    p  -- The probability that a user will continue to consider the
          next rank at any given depth d in a theoretically infinite
          list. The creators of RBO suggest that for a prefix of length
          k > 1, an appropriate value of p could be (1 - 1/k). This
          would give the first k ranks about 86% of the weight of the
          evaluation (with the other 14% going to the rest of the
          theoretically infinite ranks).
    """
    if list_1 is None:
        list_1 = []
    if list_2 is None:
        list_2 = []

    (short_len, short_list), (long_len, long_list) = sorted(
        [(len(list_1), list_1), (len(list_2), list_2)]
        )
    if short_len == 0:
        return 0
    if not p:
        # letting p be 0 would screw up some calculations
        if long_len == 1:
            return 1 if short_list == long_list else 0
        p = 1 - 1/long_len

    # Calculate the overlaps at ranks 1 through long_len
    # (the longer of the two lists)
    short_set = set([]) # contains elements from the smaller list to depth i
    long_set = set([]) # contains elements from the longer list to depth i
    x_d = {0: 0}
    sum1 = 0.0
    for i in range(long_len):
        long_elem = long_list[i]
        short_elem = short_list[i] if i < short_len else None
        d = i + 1

        # if two elements are same then
        # we don't need to add to either of the set
        if long_elem == short_elem:
            x_d[d] = x_d[d-1] + 1.0
        # else add items to respective list
        # and calculate overlap
        else:
            long_set.add(long_elem)
            if short_elem != None:
                short_set.add(short_elem)
            x_d[d] = (x_d[d-1]
                      + (1.0 if long_elem in short_set else 0.0)
                      + (1.0 if short_elem in long_set else 0.0))
        #calculate average overlap
        sum1 += x_d[d]/d * pow(p, d)

    if short_len != long_len:
        sum2 = sum(x_d[d] * (d-short_len) / (d*short_len) * pow(p, d)
                   for d in range(short_len+1, long_len+1)
                  )
        sum3 = (((x_d[long_len]-x_d[short_len])/long_len
                 + x_d[short_len]/short_len)
                * pow(p, long_len))
    else:
        sum2 = 0
        sum3 = x_d[long_len]/long_len * pow(p, long_len)

    # Equation 32
    rbo_ext = (1-p) / p * (sum1+sum2) + sum3
    return rbo_ext
