import chunks
D=chunks.D
def allrecs(s):
    base=s*512; i=base; out=[]
    while i<base+1024:
        rest=D[i:base+1024]
        if not rest.strip(b'\x00'): break
        j=D.find(b'\xff',i)
        if j<0 or j>=base+1024: break
        out.append((i,D[i:j+1])); i=j+1
    return out,D[i:base+1024]
