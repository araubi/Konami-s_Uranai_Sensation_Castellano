# Genera la imagen de muestra y el paquete RLE de la fuente latina (códigos 01h..LAST)
import os, charset, rle, rutas
G=charset.load_font()
d=rutas.orig()
orig,_=rle.unpack(d,0x89210)           # 01-4E originales
orig4f,_=rle.unpack(d,0x89463)         # 4F-52
inv={c:ch for ch,c in charset.CODES.items()}
def glyph(c):
    if c in inv and inv[c] in G: return G[inv[c]]
    if c==0x4F: return orig4f[0:8]
    if c==0x50: return orig4f[8:16]
    return bytes(8)
raw=b''.join(glyph(c) for c in range(1,charset.LAST+1))
pk=rle.pack(raw)
if __name__=='__main__':
    print('glifos',len(raw)//8,'bruto',len(raw),'rle',len(pk))
    from PIL import Image
    im=Image.new('L',(16*8*4,6*8*4),0)
    for c in range(0,0x60):
        g=glyph(c) if c else bytes(8)
        for y in range(8):
            for x in range(8):
                if g[y]>>(7-x)&1:
                    for a in range(4):
                        for b in range(4): im.putpixel(((c%16)*32+x*4+a,(c//16)*32+y*4+b),255)
    im.save(os.path.join(rutas.ROOT,'font6.png'))
