# Juego de caracteres de la traducción: carácter -> código de la fuente
import sys
ORDER=("abcdefghijklmnopqrstuvwxyz"            # 01-1A
       "ABCDEFGHIJKLMNOPQRSTUVWXYZ"            # 1B-34
       "á")                                    # 35
CODES={' ':0x00}
for i,ch in enumerate(ORDER): CODES[ch]=1+i
for i,ch in enumerate("0123456789"): CODES[ch]=0x36+i
# 43h y 44h se evitan: los intérpretes las tratan como marcas ゛゜
# Todo cabe en 01h-52h, que ninguna escena machaca (las escenas cargan sus glifos desde 53h)
for ch,c in zip("éíó",(0x40,0x41,0x42)): CODES[ch]=c
for ch,c in zip("úüñÁ¿¡.,:Ñ",range(0x45,0x4F)): CODES[ch]=c
CODES['♥']=0x4F
CODES['?']=0x51; CODES['!']=0x52
LAST=0x52
import os
def load_font(path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'font6.txt')):
    G={}; L=[l.rstrip('\n') for l in open(path,encoding='utf-8')][1:]
    i=0
    while i<len(L):
        if not L[i]: i+=1; continue
        ch=L[i]; rows=L[i+1:i+9]; i+=9
        G[ch]=bytes(int(r.replace('#','1').replace('.','0').ljust(8,'0'),2) for r in rows)
    return G
