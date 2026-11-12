# Construye el disco de Uranai Sensation en castellano a partir del original intacto
import sys, os, re, glob, subprocess
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'tools'))
import rutas
import charset, rle, mkfont, bpe, chunks, recs
from wrap import wrap

ROOT=rutas.ROOT
HERE=os.path.join(ROOT,'src')                 # ensamblador y ficheros generados
TXT=os.path.join(ROOT,'trad')+os.sep
SJ=rutas.SJ
D=bytearray(rutas.orig())
ORIG=bytes(D)

def load(f):
    out={}
    for l in open(TXT+f,encoding='utf-8'):
        if l.startswith('#') or '|' not in l: continue
        o,t=l.rstrip('\n').split('|',1); out[int(o,16)]=t
    return out

def enc(s):
    out=bytearray(); i=0
    while i<len(s):
        for k,v in (('{N}',[0xFC]),('{o}',[0xF1]),('{a}',[0xF2]),
                    ('{←}',[0xFD,0xF3,0xFD]),('{→}',[0xFD,0xF2,0xFD]),('{↓}',[0xFD,0xF4,0xFD])):   # flechas: juego de glifos alterno (FD)
            if s.startswith(k,i): out+=bytes(v); i+=3; break
        else:
            ch=s[i]; i+=1
            out.append(0xFE if ch=='/' else charset.CODES[ch])
    return bytes(out)

# ---------------------------------------------------------------- textos
PARTMAX=240
parts=[]            # bytes sin terminador
chain=[]            # índice de la parte siguiente o None
def ids():
    n=0
    while True:
        if (n&255)!=255 and (n>>8)!=255: yield n
        n+=1
idgen=ids(); idlist=[]
def add_text(t,width,maxlines=None):
    lines=wrap(t,width) if t else ['']
    if maxlines: assert len(lines)<=maxlines,(t,lines)
    segs=[]; cur=b''
    for ln in lines:
        e=enc(ln)
        piece=(b'\xfe' if cur else b'')+e
        if cur and len(cur)+len(piece)>PARTMAX:
            segs.append(cur+b'\xfe'); cur=e
        else: cur+=piece
    segs.append(cur)
    first=len(parts)
    for k,s in enumerate(segs):
        parts.append(s); chain.append(len(parts) if k<len(segs)-1 else None)
    return first
def stub(pi): n=pid[pi]; return bytes([0xF0,n&255,n>>8])

texts={}
CLASSES=[('grupo_sanguineo.txt',15,None),('horoscopo.txt',29,None),('quiromancia_resultados.txt',13,None),
         ('omikuji.txt',18,3),('quiromancia_preguntas.txt',22,2)]
first={}
for f,w,ml in CLASSES:
    for o,t in load(f).items():
        first[o]=add_text(t,w,ml)
empty=add_text('',16)

# ---------------------------------------------------------------- textos de la impresora de UI (8B42h)
# ui.txt: OFFSET|texto  (OFFSET = disco, byte [x] del letrero; '/' = siguiente renglón; '@XX,YY:' fija la posición)
uiextra={}          # parte -> [(bytes crudos, texto)] tras el primer renglón
uinext={}           # parte -> (x,y) del renglón con que sigue la parte encadenada
uiplace=[]          # (offset, longitud original, parte, bytes en su sitio o None)
UIMAX=150           # bytes descomprimidos por parte (BUF2 llega hasta DCAFh)
uitxt=load('ui.txt') if os.path.exists(TXT+'ui.txt') else {}
uiraw={o:bytes.fromhex(t[1:].replace(' ','')) for o,t in uitxt.items() if t.startswith('=')}
for o in uiraw: del uitxt[o]
import grid
for o,t in grid.ui_lines().items(): uitxt.setdefault(o,t)
def ui_orig(o):
    # renglones del letrero original; se para en un FE que lleva a otra entrada de ui.txt
    segs=[]; i=o
    while True:
        x,y=ORIG[i],ORIG[i+1]; i+=2; j=i
        while ORIG[j] not in (0xFE,0xFF): j+=1
        segs.append((x,y,ORIG[i:j])); i=j+1
        if ORIG[j]==0xFF: return segs,i-o,None
        if i in uitxt: return segs,i-o,i
def ui_lines(o,t):
    segs,ln,nx=ui_orig(o); out=[]
    for k,l in enumerate(t.split('/')):
        m=re.match(r'@([0-9A-Fa-f]{2}),([0-9A-Fa-f]{2}):',l)
        if m: x,y=int(m.group(1),16),int(m.group(2),16); l=l[m.end():]
        elif k<len(segs): x,y=segs[k][0],segs[k][1]
        else: x,y=out[-1][0],out[-1][1]+12
        if l.startswith('♥'):
            # el ♥ es de 8 px y la letra siguiente (8 px con fondo) le comía 2: va suelto, 2 px a la izquierda
            # (salvo en la lista de la mano, donde la flecha está pegada), y el resto en su sitio
            r=l[1:]; n=len(r)-len(r.lstrip(' '))
            out.append((x-(0 if o==0x1AB1F else 2),y,enc('♥')))
            if r.strip(): out.append((x+6+6*n,y,enc(r.lstrip(' '))))
            continue
        out.append((x,y,enc(l)))
    return out,ln,nx
# título: letras propias de 8 px (códigos 01h-14h); una por renglón para que el avance de 6 px no las pise
TFONT={c:i+1 for i,c in enumerate('©KONAMI198PUSHCEY')}; TFONT.update({'L':0x12,'T':0x13,'R':0x14,'1':8,'9':9,'8':10})
TITLE={0xB1E4:(0x50,0x08,'©KONAMI 1988'),0xB1F3:(0x4C,0xC8,'PULSA ESPACIO'),0xB2E0:(0x64,0xC8,'INICIO')}
def title_lines(o):
    x,y,t=TITLE[o]; _,ln,nx=ui_orig(o)
    return [(x+8*i,y,bytes([TFONT[c]])) for i,c in enumerate(t) if c!=' '],ln,nx
for o in TITLE: uitxt.setdefault(o,'')
uifirst={}; uilast={}
for o,t in uitxt.items():
    L,ln,nx=title_lines(o) if o in TITLE else ui_lines(o,t)
    inplace=bytearray()
    for k,(x,y,e) in enumerate(L): inplace+=bytes([x,y])+e+(b'\xfe' if k<len(L)-1 else b'\xff')
    if nx is None and len(inplace)<=ln: uiplace.append((o,ln,None,bytes(inplace))); continue
    # partes de hasta UIMAX bytes, encadenadas
    groups=[[]]; size=0
    for k,(x,y,e) in enumerate(L):
        n=len(e)+(3 if k else 0)
        if groups[-1] and size+n>UIMAX: groups.append([]); size=0; n=len(e)
        groups[-1].append((x,y,e)); size+=n
    prev=None
    for g in groups:
        pi=len(parts); parts.append(g[0][2]); chain.append(None)
        uiextra[pi]=[(bytes([0xFE,0xF3,x,0xF3,y]),e) for x,y,e in g[1:]]
        if prev is None: uifirst[o]=pi
        else: chain[prev]=pi; uinext[prev]=(g[0][0],g[0][1])
        prev=pi
    uilast[o]=(prev,nx)
    uiplace.append((o,ln,uifirst[o],bytes([L[0][0],L[0][1]])))
# letreros nuevos en huecos libres (offset de disco, x, y, texto): [x][y] + stub de 5 bytes
UINEW=[(0x17C2A+5*i,0x23,0x3E,t) for i,t in enumerate(('Perfil','Amor','Salud','Dinero'))]   # cabecera del horóscopo
for o,x,y,t in UINEW:
    pi=len(parts); parts.append(enc(t)); chain.append(None)
    uiplace.append((o,5,pi,bytes([x,y])))
for o,(pi,nx) in uilast.items():
    if nx is not None:
        L,_,_=ui_lines(nx,uitxt[nx])
        chain[pi]=uifirst[nx]; uinext[pi]=(L[0][0],L[0][1])
# números de parte sin bytes FF
pid=[next(idgen) for _ in parts]

# ---------------------------------------------------------------- trozos virtuales
T=chunks.tables()
vchunks=[]          # (sector, datos, modo)
for s in sorted(T):
    rr,_=recs.allrecs(s)
    k=max(max(T[s]), max([i+1 for i,(o,_) in enumerate(rr) if o in first] or [0]))
    out=bytearray()
    for o,r in rr[:k]:
        assert 0xFF not in r[:3]
        out+=r[:3]+stub(first.get(o,empty))+b'\xff'
    vchunks.append((s,bytes(out),0))
omi=load('omikuji.txt')
for s in range(0x3B5,0x3CD,6):
    out=bytearray()
    for a in range(s*512,(s+6)*512,32): out+=stub(first[a])+b'\xff'
    vchunks.append((s,bytes(out),1))
for o,ln,pi,b in uiplace:
    if pi is None: D[o:o+ln]=b+bytes(ln-len(b))
    else:
        assert ln>=5,hex(o)
        D[o:o+ln]=(b+stub(pi)+b'\xff'+bytes(ln))[:ln]
for o,b in uiraw.items(): D[o:o+len(b)]=b
D[grid.TABLE:grid.TABLE+156]=grid.table(charset.CODES)
# preguntas de la quiromancia: dentro del módulo, se cambian en su sitio
for o,t in load('quiromancia_preguntas.txt').items():
    j=D.index(b'\xff',o)
    D[o:j+1]=stub(first[o])+b'\xff'+bytes(j+1-o-4)

# ---------------------------------------------------------------- compresión
TOKS=list(range(0x5E,0xF0))
term=[]
for i,p in enumerate(parts):
    term.append(b'\xff' if chain[i] is None else b'')
runs=list(parts); where={}
for i,ex in uiextra.items():
    for k,(r,t) in enumerate(ex): where[(i,k)]=len(runs); runs.append(t)
table,comp=bpe.train(runs,TOKS)
dic=bytearray(2*len(TOKS))
for t,(a,b) in table.items(): dic[2*(t-0x5E)]=a; dic[2*(t-0x5E)+1]=b
for i,p in enumerate(parts): assert bpe.expand(comp[i],table)==p
def packed(i):
    c=comp[i]
    for k,(r,t) in enumerate(uiextra.get(i,[])): c+=r+comp[where[(i,k)]]
    if chain[i] is None: return c+b'\xff'
    if i in uinext: x,y=uinext[i]; c+=bytes([0xFE,0xF3,x,0xF3,y])
    return c+stub(chain[i])

# ---------------------------------------------------------------- imagen del mapper
SEGSZ=0x3FA0   # 7FA0h-7FFFh: rutina sexo (sexo.asm) en cada segmento
segs={4:bytearray(dic)}
for s in (5,6,7): segs[s]=bytearray(dic)
pidx_len=3*(max(pid)+1)
seg4=segs[4]; seg4+=bytes(0x200-len(seg4))          # hasta 4200h
pidx=bytearray(pidx_len); seg4+=pidx
ctab_at=len(seg4)
seg4+=bytes(8*len(vchunks)+2)
cent=[]
for s,data,mode in vchunks:
    cent.append((s,4,0x4000+len(seg4),len(data) if mode==0 else len(data)//4,mode)); seg4+=data
ct=bytearray()
for s,sg,a,n,m in cent: ct+=bytes([s&255,s>>8,sg,a&255,a>>8,n&255,n>>8,m])
ct+=b'\xff\xff'
seg4[ctab_at:ctab_at+len(ct)]=ct
seg4[0x1FE:0x200]=bytes([(0x4000+ctab_at)&255,(0x4000+ctab_at)>>8])
cur=4
for i in range(len(parts)):
    b=packed(i)
    if len(segs[cur])+len(b)>SEGSZ: cur+=1; assert cur<=7,'no cabe en el mapper'
    a=0x4000+len(segs[cur]); segs[cur]+=b
    n=pid[i]; seg4[0x200+3*n:0x200+3*n+3]=bytes([cur,a&255,a>>8])
used=[s for s in segs if len(segs[s])>len(dic)]
r=subprocess.run([SJ,'--nologo','sexo.asm'],cwd=HERE,capture_output=True,text=True)
if r.returncode: print(r.stdout,r.stderr); raise SystemExit(1)
sexo_bin=open(HERE+'/sexo.bin','rb').read()
print('partes',len(parts),'bruto',sum(map(len,parts)),'comprimido',sum(len(packed(i)) for i in range(len(parts))))
print('mapper:',{s:hex(len(segs[s])) for s in used})
for s_ in used: segs[s_]+=bytes(SEGSZ-len(segs[s_]))+sexo_bin

# ---------------------------------------------------------------- sectores libres
free=[]
for s,data,mode in vchunks:
    n=6 if mode else 2
    free+=range(s,s+n)
free=sorted(set(free))
def runs_of(lst):
    out=[]; st=lst[0]; pv=lst[0]
    for x in lst[1:]:
        if x!=pv+1: out.append((st,pv-st+1)); st=x
        pv=x
    out.append((st,pv-st+1)); return out
fr=runs_of(free)
print('sectores libres',len(free),fr)
alloc_ptr=[list(r) for r in fr]
def alloc(n):
    for r in alloc_ptr:
        if r[1]>=n: s=r[0]; r[0]+=n; r[1]-=n; return s
    raise Exception('disco lleno')

# ---------------------------------------------------------------- ensamblado
patch_sites=[]
thunks=[]
for k,m in enumerate(re.finditer(rb'\xed\x5b..\x2a(..)\x7e\x23\xcd',ORIG,re.S)):
    var=m.group(1)
    site=m.start()+4
    if any(abs(site-p)<0x200 for p,_ in patch_sites): continue
    thunks.append('th%d:\tld hl,(0%04Xh)\n\tjp chk\n'%(k,var[0]|var[1]<<8))
    patch_sites.append((site,'th%d'%k))
thunks.append('tho:\tcall chk\n\tjp 0A793h\n')
patch_sites.append((0x128B8,'tho'))
open(HERE+'/thunks.inc','w').write(''.join(thunks))

def asm(initsec,initlen,runs):
    open(HERE+'/gen.inc','w').write(
        'INITSEC equ %d\nINITLEN equ %d\nSEXVAR equ 0D24Bh\nSEXMASK equ 1\nSEXMALE equ 0\n'%(initsec,initlen))
    open(HERE+'/runs.inc','w').write(''.join('\tdw %d\n\tdb %d,%d\n\tdw %d\n'%r for r in runs))
    open(HERE+'/horo_a.inc','w').write('\tdb '+','.join('%d'%c for c in enc(': ascendente '))+',255\n')
    open(HERE+'/horo_b.inc','w').write(''.join('\tdb '+','.join('%d'%c for c in enc(s))+',255\n' for s in
        'Aries Tauro Géminis Cáncer Leo Virgo Libra Escorpio Sagitario Capricornio Acuario Piscis'.split()))
    r=subprocess.run([SJ,'--nologo','--sym=eng.sym','eng.asm'],cwd=HERE,capture_output=True,text=True)
    if r.returncode: print(r.stdout,r.stderr); raise SystemExit(1)
    sym={}
    for l in open(HERE+'/eng.sym'):
        p=l.split(':')
        if len(p)>=2 and 'EQU' in l:
            sym[p[0].strip()]=int(l.split('0x')[1].split()[0],16)
    return sym

# bloques del mapper a disco (como mucho 8 sectores por bloque)
blocks=[]
for s in used:
    img=bytes(segs[s]); img+=bytes(-len(img)%512)
    ks=[k for k in range(len(img)//512) if any(img[k*512:k*512+512])]   # sin los sectores vacíos (hueco antes de sexo)
    while ks:
        n=1
        while n<8 and n<len(ks) and ks[n]==ks[0]+n: n+=1
        off=ks[0]*512; blocks.append((s,0x4000+off,img[off:off+n*512],n)); ks=ks[n:]
initlen=2
initsec=alloc(initlen)
runs=[]
for s,a,part,n in blocks:
    sec=alloc(n)
    D[sec*512:sec*512+len(part)]=part
    runs.append((sec,n,s,a))
sym=asm(initsec,initlen,runs)
init=open(HERE+'/init.bin','rb').read()
assert len(init)<=initlen*512, len(init)
D[initsec*512:initsec*512+len(init)]=init
boot=open(HERE+'/boot.bin','rb').read()
D[0x60:0x60+len(boot)]=boot
assert ORIG[0x4A:0x4D]==bytes.fromhex('c30082')
D[0x4A:0x4D]=bytes([0xC3,0x60,0xC0])

# ---------------------------------------------------------------- parches del juego
RES=0x1D400-0x8200          # residente: disco = dirección + RES
def res(a): return a+RES
assert ORIG[res(0x8908):res(0x8908)+4]==bytes.fromhex('3e2f181c')
v=sym['vload']; D[res(0x8908):res(0x8908)+3]=bytes([0xC3,v&255,v>>8])
# impresora de UI: [x][y] y luego posible texto comprimido; avance de 6 px
assert ORIG[res(0x8B4E):res(0x8B4E)+4]==bytes.fromhex('56235e23')
a=sym['uixy']; D[res(0x8B4E):res(0x8B4E)+4]=bytes([0xCD,a&255,a>>8,0x00])
assert ORIG[res(0x8B76)]==8; D[res(0x8B76)]=6
for site,lab in patch_sites:
    a=sym[lab]
    assert ORIG[site] in (0x2a,0xcd)
    D[site:site+3]=bytes([0xCD,a&255,a>>8])

# fuente latina (como en la prueba de concepto)
G=mkfont.glyph
p1=rle.pack(b''.join(G(c) for c in range(0x01,0x4F)))
p2=rle.pack(b''.join(G(c) for c in range(0x4F,0x51)))
p3=rle.pack(b"".join(G(c) for c in range(0x51,charset.LAST+1)))
base=0xB210; a1=base; a2=a1+len(p1); a3=a2+len(p2); end=a3+len(p3)
assert end<=0xB5A4, hex(end)
D[0x89200:0x89210]=bytes([0x80,a1&255,a1>>8,0x01,0x0E, 0x80,a2&255,a2>>8,0x4F,0x08, 0x80,a3&255,a3>>8,0x51,0x0E, 0])
blob=p1+p2+p3; D[0x89210:0x89210+len(blob)]=blob
for m in re.finditer(re.escape(bytes.fromhex('3affd1b720')),ORIG): D[m.start()+4]=0x18
for m in re.finditer(re.escape(bytes.fromhex('cd7e823e0132f5dccda882')),ORIG): D[m.start()+9:m.start()+11]=bytes([0x9f,0x91])
D[0x1E39F:0x1E3A4]=bytes.fromhex('7ac60657c9')    # 919Fh: avance de 6 píxeles

# nombres de hasta 8 letras latinas (un byte por letra, sin marcas ゛゜)
def pt(o,old,new):
    assert ORIG[o:o+len(old)]==old,(hex(o),ORIG[o:o+len(old)].hex())
    D[o:o+len(new)]=new
def cw(a): return bytes([0xCD,a&255,a>>8])
R64=0x2C00                                  # módulo de la lista (64h, en 9800h)
# menú principal: resaltado rosa (filas, ancho, y, x) a la medida de Afinidad, Horóscopo, Quiromancia, Omikuji y Lista
pt(0xA953+R64,bytes.fromhex('0a3a79580a2a89580a2289a00c2277a0101a73d0'),bytes.fromhex('0a3479560a3a89560a4689940a2e79940a2279c8'))
# registro: cursores de los menús Indicar/No lo sé/Salir (tabla compartida en EEEDh), 6 px a la izquierda como los textos
pt(0xEEED,bytes.fromhex('6a38006a78006ab800'),bytes.fromhex('6a32006a72006ab200'))
# lista: nombres 1 píxel a la derecha para que no los pise el cuadro rojo (sprites de 32 px en x=20h, 58h...)
tb=bytearray(ORIG[0xA9EE+R64:0xA9EE+R64+80])
for i in range(20): tb[4*i+3]+=2      # nombres 2 px a la derecha: 5 letras (29 px) caben justas en el cuadro rojo (30 px por dentro)
pt(0xA9EE+R64,ORIG[0xA9EE+R64:0xA9EE+R64+80],bytes(tb))
# mano: resaltado naranja de Dcha./Izda. (18 px, pensado para 右/左) -> 32 px desde x=CEh
pt(0x98AC+0x10200,bytes.fromhex('2171cf110a12'),bytes.fromhex('2171c8110a1c'))
# mano, pantalla de líneas: ← con la línea sin marcar (FFh, persona nueva) dejaba FEh y el texto de
# la variante FEh se salía de madre (fallo también del original). Ahora FFh y 0 dan la vuelta a la última.
pt(0x1AA88,bytes.fromhex('ed5ba19c1ad60130043a32923d1218e8'),bytes.fromhex('ed5ba19c1a3dfefe38043a32923d18e7'))
# mano: Der./Izq. 6 px a la izquierda (textos en ui.txt) y su cursor 4 px
pt(0x19B4B,bytes.fromhex('72c00082c000'),bytes.fromhex('72bc0082bc00'))
R6=0x4200                                   # módulo de registro (6Fh, en 9C00h)
NMAX=5                                      # letras del nombre: más no caben en el cuadro rojo de la lista (32 px)
pt(0x18FA+7,b'\xfe\x04',bytes([0xfe,NMAX]))       # 9301h: tope de posiciones
pt(0xA796+R6,b'\x3e\x03',bytes([0x3e,NMAX-1]))
pt(0xA6A2+R6,b'\xfe\x03',bytes([0xfe,NMAX-1]))
pt(0xA6A9+R6,b'\xfe\x03',bytes([0xfe,NMAX-1]))
pt(0xA6C2+R6,b'\x3e\x03',bytes([0x3e,NMAX-1]))
pt(0xA5CB+R6,b'\xfe\x04',bytes([0xfe,NMAX]))
pt(0xA725+R6,bytes.fromhex('87cd2182798787878257'),bytes.fromhex('00cd2182798781878257'))
pt(0xA6D0+R6,bytes.fromhex('3eff772377'),bytes.fromhex('3eff770000'))
pt(0xA6D6+R6,bytes.fromhex('7e23cddfa67ec37e82'),bytes.fromhex('7ec37e8200000000c9'))
pt(0xA771+R6,bytes.fromhex('3a2cd277233a2dd277'),bytes.fromhex('3a2dd2770000000000'))
pt(0xA56F+R6,bytes.fromhex('213010111830'),bytes.fromhex('213008111840'))   # cuadro del nombre más ancho
pt(0xA5DE+R6,bytes.fromhex('113a18'),bytes.fromhex('113a10'))
# mapa del lugar de nacimiento: «Mar» y «Ext» (fuera de Japón) en lugar de うみ y その他
pt(0xAEF7+R6,bytes.fromhex('e52336cd2336eae1'),cw(sym['mar'])+bytes.fromhex('1803000000'))
pt(0xAEEB+R6,bytes.fromhex('e536d92336e32336dae1'),bytes([0xE5,0x36,(0x1F-0x36)&255,0x23,0x36,(0x18-0x36)&255,0x23,0x36,(0x14-0x36)&255,0xE1]))
for f,a in (('m6f_a.bin',0xAC1A),('m6f_b.bin',0xAC97),('m6f_c.bin',0xAC66)):
    b=open(HERE+'/'+f,'rb').read(); D[a+R6:a+R6+len(b)]=b
# salida TV/impresora de la sangre: flechas de las opciones más juntas (fuente de 6 px)
for o in (0x156D4,0x15705):
    pt(o-5,bytes([0x38,0,ORIG[o-3],0x70]),bytes([0x28,0,ORIG[o-3],0x68]))
# salida TV/impresora de la sangre: resaltado de «TV» e «Impresora» a su medida (HL = x,y; B = ancho)
R_AA=0x15400-0x9800
pt(0x9BBA+R_AA,bytes.fromhex('010e1a'),bytes.fromhex('010e0e'))
pt(0x9BC3+R_AA,bytes.fromhex('010e2a'),bytes.fromhex('010e38'))
pt(0x9BAD+R_AA,bytes.fromhex('211d40'),bytes.fromhex('211d30'))
pt(0x9BB7+R_AA,bytes.fromhex('216d40'),bytes.fromhex('216d30'))
# horóscopo (módulo B8h en 9800h = disco 17000h): frase del ascendente y cuadro más ancho
R_B8=0x17000-0x9800
for f,a in (('mb8_a.bin',0x985E),('mb8_b.bin',0x9894)):
    b=open(HERE+'/'+f,'rb').read(); D[a+R_B8:a+R_B8+len(b)]=b
pt(0x987D+R_B8,bytes.fromhex('0118a0'),bytes.fromhex('0118d0'))
pt(0x988E+R_B8,bytes.fromhex('1118a0'),bytes.fromhex('1118d0'))
pt(0xA2F9+R_B8,bytes.fromhex('0118a0'),bytes.fromhex('0118d0'))   # al quitar el cuadro
# horóscopo, menú (módulo BCh en 9800h = disco 17800h): cabecera con la palabra en lugar de dos kanji
R_BC=0x17800-0x9800
pt(0x9C81+R_BC,bytes.fromhex('214b9c3a17d2cd6c82e5113e237dcd7e82cda882e17ccd7e82'),
   bytes.fromhex('3a17d26f878785c62a6f269ccd7582').ljust(25,b'\x00'))
pt(0x9CA0+R_BC,bytes.fromhex('210a14'),bytes.fromhex('210a26'))
# mano: el menú de resultados (2 filas de 4 columnas verticales) pasa a una lista de 7 renglones con flecha →
o=0x9D85+0x10E00
pt(o+6,bytes.fromhex('0204'),bytes.fromhex('0700'))      # 7 filas, sin columnas
pt(o+8,bytes.fromhex('0e10050e20050e30050e4005361005362005363005363005'),
   b''.join(bytes([0x0C+11*min(i,6),0x11,0]) for i in range(8)))
# barra amarilla que marca el apartado elegido (era vertical, detrás de la columna): marca pequeña a la izquierda
pt(0x9E70+0x10E00,bytes.fromhex('17101720173017400000'+'3f203f30'),
   b''.join(b'\x00\x00' if i==4 else bytes([0x0C+11*i,0x0B]) for i in range(7)))
pt(0x9E54+0x10E00,bytes.fromhex('011c0a'),bytes.fromhex('010804'))
# calendario del registro: la baldosa de 月 detrás del número del mes pasa a ser fondo (queda solo el número)
D[0x85AE0:0x85B00]=ORIG[0x853A0:0x853C0]
# mano: tabla resumen de respuestas (columnas verticales 1-4 / 5-7 y «OK» a la izquierda) -> lista de 8 renglones
# «n Nombre» con la casilla de la respuesta a la derecha; el índice del menú pasa a ser el renglón (OK el último)
R=0x1A600-0x9800
pt(0x9CFF+R+6,bytes.fromhex('0204'),bytes.fromhex('0800'))
pt(0x9D07+R,bytes.fromhex('1f28021f38021f48021f58025f18025f38025f48025f5802'),
   b''.join(bytes([0x1F+0x10*i if i<7 else 0x9F,0x16,2]) for i in range(8)))
# las 12 casillas pequeñas de «Otros» (antes en dos columnas verticales a la izquierda): 4x3 a la derecha del renglón 7
# (tabla de 12 entradas desde 9966h; la entrada e es la respuesta 12-e, contando desde 0)
pt(0x9966+R,bytes.fromhex('a028982890288828802878 28a030983090308830803078 30'.replace(' ','')),
   b''.join(bytes([0x7A+8*((12-e)//4),0x44+8*((12-e)%4)]) for e in range(1,13)))
pt(0x9B3C+R,bytes.fromhex('0302010000060504'),bytes.fromhex('0001020304050600'))   # índice -> línea
pt(0x9ADF+R,bytes.fromhex('3e04'),bytes.fromhex('3e07'))          # el cursor empieza en OK
pt(0x93AB-0x600,bytes.fromhex('fe04'),bytes.fromhex('fe07'))      # OK es el índice 7 (código de 9200h, sector 70)
pt(0x9AF2+R,bytes.fromhex('115058'),bytes.fromhex('111c58'))      # casillas de las líneas 1-4
pt(0x9AFD+R,bytes.fromhex('119058'),bytes.fromhex('115c58'))      # y 5-6, una debajo de otra
pt(0x9B19+R,bytes.fromhex('7ad61057'),bytes.fromhex('7bc6105f'))
# omikuji: frase de la sacerdotisa 『ようおまいりやした』 (dos copias; detrás hay ceros de relleno)
for o in (0x7CAC3,0x7D4C3):
    assert ORIG[o:o+13]==bytes.fromhex('492603000 51f0228240c104aff'.replace(' ','')) and not any(ORIG[o+13:o+24])
    t=enc('¡Muchas gracias!')+b'\xff'; D[o:o+len(t)]=t
# omikuji: otras frases entre 『』 de las escenas (detrás también hay ceros)
for o,n,t in ((0x7A2C3,11,'¡Je, je, je!'),          # 『へっへっへっへっ』 (el sacerdote se ríe)
              (0x7C0C3,10,'¡Para {N}!'),            # 『〈nombre〉のおみくじ!』
              (0x7DEC3,11,'........'),              # 『、、、、、、、、』
              (0x7ACC3,9,'¡Tómalo!'),           # 『おみくじです』
              (0x7B6C3,12,'¡Para ti!')):        # 『おみくじを どうぞ』
    assert ORIG[o]==0x49 and ORIG[o+n-1]==0xFF and not any(ORIG[o+n:o+n+8])
    t=enc(t)+b'\xff'; assert len(t)<=n+8; D[o:o+len(t)]=t
# sangre: nombres de hasta 8 letras y la pregunta en un segundo renglón (cuadro más alto)
R_AA=0x15400-0x9800
b=open(HERE+'/maa.bin','rb').read(); assert len(b)<=0x3C; D[0x9872+R_AA:0x9872+R_AA+len(b)]=b
pt(0x992A+R_AA,bytes.fromhex('18807040'),bytes.fromhex('24906a38'))
# afinidad: resaltado de las opciones de los menús de los globos (filas, ancho, y, x por opción; tabla 9B5Bh)
def hlt(items): return b''.join(bytes([0x0A,len(t)*6+2,y,x]) for t,x,y in items)
pt(0x9B5B+R_AA,ORIG[0x9B5B+R_AA:0x9B5B+R_AA+20],hlt([(t,0x5E,0x5F+16*i) for i,t in enumerate(('No caer mal','Al declararse','Como cónyuge','Afinidad','Volver'))]))
pt(0x9B6F+R_AA,ORIG[0x9B6F+R_AA:0x9B6F+R_AA+16],hlt([(t,0x4E,0x11+16*i) for i,t in enumerate(('Educar al hijo','Cómo motivarle','Padres e hijos','Volver'))]))
pt(0x9B7F+R_AA,ORIG[0x9B7F+R_AA:0x9B7F+R_AA+24],hlt([('Ganar respeto',0x2E,0x87),('Reñir novatos',0x96,0x87),('Tras un error',0x2E,0x97),
    ('Venderte bien',0x96,0x97),('Guiar novatos',0x2E,0xA7),('Volver',0x96,0xA7)]))
pt(0x99E9+R_AA,bytes.fromhex('a8a000'),bytes.fromhex('a88800'))   # cursor de «Volver» en la segunda columna
# flechas de los menús con ♥: 2 px a la izquierda, como el ♥ (tablas de cursor: y, x, 0)
for a,n in ((0x993E+R_AA,5),(0x998F+R_AA,4),(0x99DA+R_AA,6),(0xAA23,2),(0xAC72,2),(0x10FBA,2)):
    for i in range(n): D[a+3*i+1]-=2
# afinidad, cuadro de consejos (módulo en 9800h, disco 16000h): texto 2 px a la derecha (x par: el VDP copia de 2 en 2)
pt(0x16038,bytes.fromhex('117050'),bytes.fromhex('117052'))
pt(0x1663D,bytes.fromhex('3a879c6f2600cd529e'),bytes.fromhex('2e5a00000000000000'))   # el ↵ en x=ACh, tras 15 letras (antes 16), sin pisar el marco
c=sym['anio']; pt(0xA96B+R6,bytes.fromhex('cd77a9'),cw(c))   # año 19xx
# sexo: «Hombre»/«Mujer» en lugar de 男性/女性 (textos en el hueco tras el stub de EEC4h)
SH,SM=0xACCA,0xACCA+9
D[SH+R6:SH+R6+18]=bytes([0x44,0x38])+enc('Hombre')+b'\xff'+bytes([0x44,0x38])+enc('Mujer ')+b'\xff'   # mismo sitio y un espacio: tapa del todo «Hombre»
pt(0xA900+R6,bytes.fromhex('111820'),bytes.fromhex('111830'))
pt(0xA906+R6,ORIG[0xA906+R6:0xA923+R6],(cw(0xA5DB)+bytes.fromhex('111600197eb7')+bytes([0x21,SH&255,SH>>8,0x28,0x03,0x21,SM&255,SM>>8,0xC3,0x75,0x82])).ljust(0x1D,b'\x00'))
for m in re.finditer(re.escape(bytes.fromhex('0042004000414041')),ORIG):   # grupos O, A, B, AB
    D[m.start():m.start()+8]=bytes([0,0x29,0,0x1B,0,0x1C,0x1B,0x1C])
o=0x59E*512                          # lista vacía (el original traía «ああああ» de prueba)
assert ORIG[o:o+4]==b'\x01'*4; D[o:o+0x30]=b'\xff'*0x30
pt(0xA642+R6,b'\xe5',b'\xc9')            # sin pasar el nombre a parejas al editar
c=sym['curtab']; pt(0xA708+R6,bytes.fromhex('213bab'),bytes([0x21,c&255,c>>8]))
n=sym['nlen']
for m in re.finditer(rb'\x3e\x04\x32(..)\x22(..)\x21\x18\xd2\x22(..)\xc9',ORIG,re.S):
    D[m.start():m.start()+15]=b'\x22'+m.group(2)+cw(n)+b'\x32'+m.group(1)+b'\x22'+m.group(3)+b'\xc9\x00\x00'
for m in re.finditer(rb'\x06\x04\x21\x18\xd2\xc5\x7e\x23',ORIG):
    D[m.start():m.start()+5]=cw(n)+b'\x47\x00'
pt(0x129A2,bytes.fromhex('e506042118d2'),b'\xe5'+cw(n)+b'\x47\x00')   # omikuji (A7A2h)
pt(0x129D5,b'\xc6\x08',b'\xc6\x06')
a6=sym['adv6']
for m in re.finditer(rb'\xfe\x44\x28\x0b\xcd(..)\xcd\xa8\x82',ORIG,re.S): D[m.start()+7:m.start()+10]=cw(a6)

# VER DATOS (módulo 7Dh en 9C00h): rótulos en letras, año 19xx, fecha con puntos, hora con «:» y «h»
R7=0x5E00
tab=enc('Fecha 19')+b'\xfe\xfe'+enc('Hora')+b'\xfe\xfe'+enc('Grupo')+b'\xfe\xfe'+enc('Sexo')+b'\xfe\xfe\xfe'+enc('Espacio')+b'\xff'
SH7=0xA232+len(tab); SM7=SH7+7
tab+=enc('Hombre')+b'\xff'+enc('Mujer')+b'\xff'
assert len(tab)==0x33,len(tab)
pt(0xA232+R7,ORIG[0xA232+R7:0xA265+R7],tab)
pt(0x9C36+R7,bytes.fromhex('112038'),bytes.fromhex('113034'))   # rótulos 4 px más a la derecha (lejos de los agujeros)
pt(0x9E1D+R7,b'\x3e\x5e',bytes([0x3e,charset.CODES['.']]))
pt(0x9E2E+R7,b'\x3e\x5f',bytes([0x3e,charset.CODES['.']]))
pt(0x9E3F+R7,b'\x3e\x55',b'\x3e\x00')
# VER DATOS: todo lo demás también 4 px a la derecha (LD DE,yx / LD HL,xy con la x en el byte alto)
for a in (0x9D1F,0x9D25,0x9DEA,0x9DFB,0x9E08,0x9E1F,0x9E30,0x9E41,0x9E4E,0x9E54,0x9E5A,0x9E82,0x9E94,0x9E9D,
          0x9D2B,0x9D34,0x9DDF,0x9DF0,0x9E14,0x9E25,0x9E36,0x9E77):
    assert D[a+R7] in (0x11,0x21); D[a+R7+2]+=4
pt(0x9E51+R7,bytes.fromhex('cd5d9e'),cw(sym['yr2']))
pt(0x9DE8+R7,b'\x3e\x5a',bytes([0x3e,charset.CODES[':']]))
pt(0x9DF9+R7,b'\x3e\x58',bytes([0x3e,charset.CODES['h']]))
pt(0x9E80+R7,b'\x3e\x63',b'\x3e\x00')
pt(0xA265+R7,bytes.fromhex('4200400041004041'),bytes([0x29,0,0x1B,0,0x1C,0,0x1B,0x1C]))
sx=bytes.fromhex('dd7e16b7')+bytes([0x21,SH7&255,SH7>>8,0x28,0x03,0x21,SM7&255,SM7>>8])+bytes.fromhex('11605ac3ee9c')
pt(0x9EB6+R7,ORIG[0x9EB6+R7:0x9ECE+R7],sx.ljust(0x18,b'\x00'))

# omikuji: la caja original (112 x 40) con 3 líneas de 18 letras, avance de 6 px y salto de línea de 12 px
OM=0x8200                                   # disco = dirección + OM en el módulo de la omikuji
def pk(a,old,new):
    assert ORIG[a+OM:a+OM+len(old)]==old,(hex(a),ORIG[a+OM:a+OM+len(old)].hex())
    D[a+OM:a+OM+len(new)]=new
pk(0xA6BC,b'\x90\x90',b'\x8a\x8a')   # E = y, D = x
n=sym['omisalto']; pk(0xA764,bytes.fromhex('11a090'),bytes([0xCD,n&255,n>>8]))
pk(0xA6F7,b'\x08',b'\x06')
pk(0xA47E,bytes.fromhex('012010'),bytes.fromhex('012410'))   # la copia a pantalla (16 x 32) no llegaba a la 3.ª línea: 16 x 36

# gráficos redibujados (gfx/*.json: 'offset:nibble' -> color; nibble 1 = el de la izquierda)
import glob,json
for f in sorted(glob.glob(ROOT+'/gfx/*.json')):
    for k,c in json.load(open(f)).items():
        o,h=k.split(':'); o=int(o,16)
        D[o]=(D[o]&0x0F)|(c<<4) if h=='1' else (D[o]&0xF0)|c

# pergaminos de la omikuji rehechos (gfx_scrolls.json: sector -> mapa de baldosas + baldosas)
SCR=[917,911,905,899,893,887,881,875]
for s,h in json.load(open(ROOT+'/gfx/datos/gfx_scrolls.json')).items():
    x=bytes.fromhex(h); assert len(x)<=6*512; D[int(s)*512:int(s)*512+len(x)]=x
    i=SCR.index(int(s)); n=max(c for c in x[:x.index(0xFF)] if c!=0xFE)
    assert ORIG[0xA408+0x8200+i]==max(c for c in ORIG[int(s)*512:ORIG.index(0xFF,int(s)*512)] if c!=0xFE)
    D[0xA408+0x8200+i]=n                      # baldosas que se suben a la VRAM (tabla A408h del módulo)

# datos gráficos enteros (gfx_raw_*.json: offset -> datos): lámina de la quiromancia (mapa nuevo del módulo C7h y
# baldosas de los letreros) y cabeceras del panel de preguntas
for f in sorted(glob.glob(ROOT+'/gfx/datos/gfx_raw_*.json')):
  for o,h in json.load(open(f)).items():
    x=bytes.fromhex(h); D[int(o,16):int(o,16)+len(x)]=x

def savesum(X):                             # suma de comprobación de la lista (9A9Dh)
    o=0x59E*512; X[o+0x3FF]=sum(X[o:o+0x3FF])&255
savesum(D)
out=sys.argv[1] if len(sys.argv)>1 else ROOT+'/uranai_es.dsk'
open(out,'wb').write(D)
# disco de pruebas con dos personas ya apuntadas
def person(name,y,m,d,h,mi,place,blood,sex):
    r=bytearray(b'\xff'*0x30)
    e=enc(name); r[0:len(e)]=e
    r[8:10]=b'\x62\x84'; r[0xF:0x18]=bytes([y,m,d,h,mi,place,blood,sex,0])
    r[0x1C:0x2F]=bytes(0x13); r[0x2F]=len(name)
    return bytes(r)
T=bytearray(D); o=0x59E*512
T[o:o+0x30]=person('Rubén',0x50,0x06,0x15,0x12,0x00,0x0D,1,0)
T[o+0x30:o+0x60]=person('María',0x55,0x03,0x08,0x09,0x30,0x01,2,1)
savesum(T); open(out.replace('.dsk','_prueba.dsk'),'wb').write(T)
print('init en sector',initsec,'residente %04X-%04X'%(sym['res'],sym['resend']),'->',out)
