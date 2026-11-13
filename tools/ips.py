# Genera el parche IPS (orig.dsk -> uranai_es.dsk) y comprueba que da el mismo disco.
# Con --alt parte del volcado alternativo (orig_alt.dsk) y da el mismo uranai_es.dsk.
import os, sys, hashlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import rutas
A=rutas.ROOT
args=[x for x in sys.argv[1:] if x!='--alt']; ALT='--alt' in sys.argv
a=rutas.alt() if ALT else rutas.orig(); b=open(os.path.join(A,'uranai_es.dsk'),'rb').read()
assert len(a)==len(b)
dif=lambda k: a[k]!=b[k]
out=bytearray(b'PATCH'); i=0
while i<len(b):
    if not dif(i): i+=1; continue
    j=i
    while j<len(b) and j-i<0xffff and any(dif(k) for k in range(j,min(j+6,len(b)))): j+=1
    assert i!=0x454F46                      # «EOF» como desplazamiento (no pasa en 720 KB)
    out+=i.to_bytes(3,'big')+(j-i).to_bytes(2,'big')+b[i:j]; i=j
out+=b'EOF'
r=bytearray(a); k=5
while out[k:k+3]!=b'EOF':
    o=int.from_bytes(out[k:k+3],'big'); n=int.from_bytes(out[k+3:k+5],'big'); r[o:o+n]=out[k+5:k+5+n]; k+=5+n
assert bytes(r)==b
f=os.path.join(A,args[0] if args else ('UranaiSensation_ES_alt.ips' if ALT else 'UranaiSensation_ES.ips'))
open(f,'wb').write(out)
print('IPS',len(out),'bytes, SHA-1',hashlib.sha1(out).hexdigest(),'-> disco',hashlib.sha1(b).hexdigest())
