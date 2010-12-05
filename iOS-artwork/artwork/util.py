#-------------------------------------------------------------------------------
#
# iOS .artwork file extractor
# (c)2008-2011 Dave Peck <code [at] davepeck [dot] org> All Rights Reserved
# 
# Released under the three-clause BSD license.
#
# http://github.com/davepeck/iphone-tidbits/
#
#-------------------------------------------------------------------------------

def flatten(thing):
    """Take arbitrarily nested lists or tuples and flatten them."""
    if (type(thing) == list) or (type(thing) == tuple):
        for item in thing:
            for flattened in flatten(item):
                yield flattened
    else:
        yield thing
        
        
class KnuthMorrisPratt(object):
    """Implement a search algorithm that works over lists."""
    @staticmethod
    def build_kmp_table(needle):
        m = len(needle)
        pi = [0] * m
        k = 0
        for q in range(1, m):
            while k > 0 and needle[k] != needle[q]:
                k = pi[k - 1]
            if needle[k] == needle[q]:
                k = k + 1
            pi[q] = k
        return pi

    @staticmethod
    def find(needle, haystack, starting_at = 0):
        n = len(haystack)
        m = len(needle)
        pi = KnuthMorrisPratt.build_kmp_table(needle)
        q = 0
        for i in range(starting_at, n):
            while q > 0 and needle[q] != haystack[i]:
                q = pi[q - 1]
            if needle[q] == haystack[i]:
                q = q + 1
            if q == m:
                return i - m + 1
        return -1    
