# Teclado de nombres en letras latinas: filas del letrero y tabla de códigos (AB4Bh del módulo 6Fh)
ROWS=["ABCDEFGHIJ","KLMNÑOPQRS","TUVWXYZÁ♥.","abcdefghij","klmnñopqrs","tuvwxyzáéí","óúü0123456","789!?,:"]
ROWOFF=[0xEC83+0x16*r for r in range(8)]
TABLE=0xED4B
def ui_lines():
    out={}
    for r,row in enumerate(ROWS):
        y=0x11+16*r; segs=[]          # +1: el cursor (cuadro rojo) tapaba la fila de arriba de la letra
        for c,ch in enumerate(row): segs.append('@%02X,%02X:%s'%(0x50+16*c,y,ch))
        if r==7: segs+=['@%02X,%02X:Sp'%(0x50+16*7,y),'@%02X,%02X:Fin'%(0x50+16*8,y)]
        out[ROWOFF[r]]='/'.join(segs)
    return out
def table(codes):
    t=bytearray()
    for row in ROWS:
        for ch in row: t+=bytes([0xFF,codes[ch]])
    t+=bytes([0xFF,0x00])          # Sp (índice 77)
    assert len(t)==78*2
    return bytes(t)
