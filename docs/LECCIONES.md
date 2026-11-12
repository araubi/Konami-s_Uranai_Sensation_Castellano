# Lecciones de la traducción de Uranai Sensation

Lo aprendido al traducir este disco MSX2 japonés, útil para otros juegos. Los detalles del juego están en la [documentación técnica](DOCUMENTACION.md).

## Cómo montar una traducción
- **Construir siempre desde el original intacto.** El script (build.py) comprueba los bytes viejos antes de parchear con `pt(off, viejo, nuevo)`. Así cada versión es reproducible y un parche mal puesto falla al construir, no en el juego.
- **Textos fuera del código.** Usamos un fichero por tipo de texto, con líneas `OFFSET|texto` y `@x,y:` para recolocar renglones. Los cambios que pide el probador (acortar, mover) se hacen sin tocar ensamblador.
- **Disco lleno y RAM justa.** El castellano no cabía, así que lo comprimimos en pares de bytes en el mapper (128 KB). Es un requisito nuevo: avísalo en el LEEME.
- **Huecos.** Antes de meter una rutina en un hueco de un módulo, comprobar que ahí había texto que ya sustituimos. En la v2, una rutina pisó el descriptor de un menú y colgó el registro.

## Pantalla y fuente
- **HMMM ignora el bit bajo de la x.** Los glifos tienen que ir en x par, o salen desplazados.
- **Glifos con fondo.** Un glifo de 8 px con fondo, seguido de otro con avance de 6 px, pierde 2 px por la derecha (nos pasó con el ♥). Hay que pintarlo como segmento aparte 2 px a la izquierda. Las flechas de cursor se mueven lo mismo.
- **Margen dentro de los cuadros.** El criterio fue que el fondo negro del texto no toque el marco. Al acortar o mover un texto, ajustar también la tabla de cursores y la del resaltado (suele ser filas, ancho, y, x por opción).
- **Cuadros de tamaño fijo.** Es más fácil acortar el texto («Sacar omikuji» → «Omikuji») que agrandar el cuadro.
- **Cambiar un texto por otro más corto en el mismo sitio deja restos.** Rellenar con espacios («Mujer » tapa «Hombre»).
- **Nombres de persona.** Contarlos con su longitud máxima al partir renglones (wrap); si no, el renglón con nombre se sale.

## Pruebas y depuración en openMSX
- **Repetición .omr del probador.** Es lo más útil para reproducir sus fallos.
  - Graba con openMSX 21: el 20 no la abre.
  - El disco tiene que estar en el pool con el mismo SHA1. Pedir también su .dsk, que lleva sus datos guardados.
  - Cualquier tecla o loadstate nuestro corta la repetición: recargarla.
  - Las capturas justo después de `reverse goto` pueden salir viejas. Mejor dejarla correr y capturar.
- **Encontrar variables.** Volcar los 64 KB, pulsar una tecla, volver a volcar y comparar: las variables de la pantalla salen solas. Después, un `debug set_watchpoint write_mem` con `lappend` de `[reg pc]` da la rutina que las escribe.
- **Comparar siempre con el original japonés en el mismo estado.** Si se puede, crear ese estado con `poke` en las fichas de RAM. El fallo de la quiromancia (← con una línea sin marcar) resultó ser del original. Saberlo cambia el arreglo y cómo se explica.
- **Datos de muestra del disco.** Al vaciar una ficha de muestra no poner FF sin mirar qué valores espera el juego. El original traía ceros, y con FF salió el fallo latente.
- **Primera tecla tras loadstate.** Después de un loadstate la primera tecla suele perderse.

## Entregas
- Zip numerado (v2…v10) con LEEME y una sección «CAMBIOS DE LA VERSIÓN n», y un pantallazo de openMSX de lo arreglado.
- Si el probador manda su disco con datos, devolverle también su disco parcheado para que siga donde lo dejó.
- Un .md técnico (mapa de disco, módulos, rutinas, formatos, fallos del original) sirve para que otros desensamblen el juego sin pasar ficheros con copyright.
