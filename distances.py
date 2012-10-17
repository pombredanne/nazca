# -*- coding : utf-8 -*-

def levenshtein(stra, strb):
    """ Compute the Levenshtein distance between stra and strb.

    The Levenshtein distance is defined as the minimal cost to transform stra
    into strb, where 3 operators are allowed :
        - Replace one character of stra into a character of strb
        - Add one character of strb into stra
        - Remove one character of strb
    """

    lena = len(stra)
    lenb = len(strb)
    onerowago = None
    thisrow = range(1, lenb + 1) + [0]
    for x in xrange(lena):
        onerowago, thisrow = thisrow, [0] * lenb + [x+1]
        for y in xrange(lenb):
            delcost = onerowago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = onerowago[y - 1] + (stra[x] != strb[y])
            thisrow[y] = min(delcost, addcost, subcost)
    return thisrow[lenb - 1]
