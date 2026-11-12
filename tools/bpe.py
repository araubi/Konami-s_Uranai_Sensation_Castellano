# Compresión por pares de bytes (BPE): los códigos libres se usan como fichas que valen dos códigos
import collections
def train(recs, tokens):
    recs=[list(r) for r in recs]; table={}
    for t in tokens:
        c=collections.Counter()
        for r in recs:
            for i in range(len(r)-1): c[(r[i],r[i+1])]+=1
        if not c: break
        (a,b),n=c.most_common(1)[0]
        if n<3: break
        table[t]=(a,b)
        for k,r in enumerate(recs):
            o=[];i=0
            while i<len(r):
                if i+1<len(r) and r[i]==a and r[i+1]==b: o.append(t); i+=2
                else: o.append(r[i]); i+=1
            recs[k]=o
    return table,[bytes(r) for r in recs]
def expand(r,table):
    out=[]
    def ex(c):
        if c in table: ex(table[c][0]); ex(table[c][1])
        else: out.append(c)
    for c in r: ex(c)
    return bytes(out)
