# Rutas del proyecto y lectura del disco original del usuario
import os, sys, hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_SHA1='f9499b9797c3bfe57623d5f82b578eb04787b364'
ORIG=os.environ.get('URANAI_ORIG',os.path.join(ROOT,'orig.dsk'))
# volcado alternativo «(ja)»: igual salvo la lista de personas (sectores 59Eh-59Fh a E5h, sin datos)
ALT_SHA1='ed476ec5e77b39a2d9ba4df3b5eca50938131a48'
ALT=os.environ.get('URANAI_ALT',os.path.join(ROOT,'orig_alt.dsk'))
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
def alt():
    if not os.path.exists(ALT):
        sys.exit('Falta %s: copia ahí tu imagen del volcado alternativo (SHA-1 %s)'%(ALT,ALT_SHA1))
    d=open(ALT,'rb').read()
    if hashlib.sha1(d).hexdigest()!=ALT_SHA1:
        sys.exit('%s no es el disco esperado (SHA-1 %s)'%(ALT,ALT_SHA1))
    return d
