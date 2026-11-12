# Rutas del proyecto y lectura del disco original del usuario
import os, sys, hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_SHA1='f9499b9797c3bfe57623d5f82b578eb04787b364'
ORIG=os.environ.get('URANAI_ORIG',os.path.join(ROOT,'orig.dsk'))
SJ=os.environ.get('SJASMPLUS','sjasmplus')
_orig=None
def orig():
    global _orig
    if _orig is None:
        if not os.path.exists(ORIG):
            sys.exit('Falta %s: copia ahí tu imagen del disco original (SHA-1 %s)'%(ORIG,ORIG_SHA1))
        d=open(ORIG,'rb').read()
        if hashlib.sha1(d).hexdigest()!=ORIG_SHA1:
            sys.exit('%s no es el disco esperado (SHA-1 %s)'%(ORIG,ORIG_SHA1))
        _orig=d
    return _orig
