# Corte de líneas por palabras para cajas de ancho fijo
def wrap(s, width, name_len=5):   # nombres de hasta 5 letras (NMAX en build.py)
    lines=[]; cur=''
    for w in s.split(' '):
        ln=lambda t: len(t.replace('{N}','N'*name_len).replace('{o}','o').replace('{a}','a'))
        if not cur: cur=w
        elif ln(cur)+1+ln(w)<=width: cur+=' '+w
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines
