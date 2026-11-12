# Trozos de texto que el juego carga por sectores (se sustituyen por trozos virtuales en el mapper)
import rutas
D=rutas.orig()
def tables():
    import re
    out={}
    for r,base in [(0x160B5,0x16000),(0x18593,0x18400),(0x1C8FD,0x1C800)]:
        ra=r-base+0x9800
        for m in re.finditer(re.escape(bytes([ra&255,ra>>8])),D[base:base+0x3000]):
            a=base+m.start()
            if D[a-1] in (0xc3,0xcd) and D[a-4]==0x21:
                to=(D[a-3]|D[a-2]<<8)-0x9800+base; i=to
                while True:
                    s=D[i]|D[i+1]<<8; k=D[i+2]
                    if not (0x100<s<0x5A0 or s==0xFB) or k==0 or k>40: break
                    out.setdefault(s,set()).add(k); i+=3
    return out
def records(sec,n):
    """registros terminados en FF desde el principio del trozo de 2 sectores"""
    base=sec*512; i=base; recs=[]
    for k in range(n):
        j=D.index(b'\xff',i)
        recs.append((i,D[i:j+1])); i=j+1
    assert i<=base+1024
    return recs
if __name__=='__main__':
    T=tables()
    for s in sorted(T):
        r=records(s,max(T[s]))
        print('%04X n=%d maxidx=%d'%(s,len(T[s]),max(T[s])),' '.join('%05X'%o for o,_ in r))
