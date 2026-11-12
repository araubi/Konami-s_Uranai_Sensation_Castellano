# Paquetes de fuente RLE de Uranai Sensation (rutina 9014h)
def unpack(d, a):
    out=bytearray(); i=a
    while True:
        c=d[i]; i+=1
        if c==0: return bytes(out), i-a
        if c&0x80:
            n=c&0x7f; out+=d[i:i+n]; i+=n
        else:
            out+=bytes([d[i]])*c; i+=1
def pack(raw):
    out=bytearray(); i=0; n=len(raw); lit=bytearray()
    def flush():
        nonlocal lit
        while lit:
            ch=lit[:127]; out.append(0x80|len(ch)); out.extend(ch); lit=lit[127:]
    while i<n:
        j=i
        while j<n and raw[j]==raw[i] and j-i<127: j+=1
        if j-i>=3:
            flush(); out+=bytes([j-i,raw[i]]); i=j
        else:
            lit.append(raw[i]); i+=1
    flush(); out.append(0); return bytes(out)
