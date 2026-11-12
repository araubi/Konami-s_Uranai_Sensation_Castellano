# Documentación técnica de Uranai Sensation (Konami, 1988, MSX2)

Notas reunidas durante la traducción al castellano (octubre de 2026). Sirven para entender el parche y para quien quiera desensamblar el juego: dónde está cada cosa en el disco, cómo se carga, cómo funciona el texto y qué trampas hay.

Todas las direcciones van en hexadecimal. «Disco» es el desplazamiento en bytes dentro de la imagen .dsk de 720 KB.

## 1. La imagen de partida

| Dato | Valor |
|---|---|
| Juego | Konami's Uranai Sensation (Fortune Teller), Konami 1988, MSX2, disco japonés |
| SHA1 del .dsk original | `f9499b9797c3bfe57623d5f82b578eb04787b364` |
| Variantes | existen dumps [a], [a2] y [a3]; las notas son del original de arriba |
| Máquina de pruebas | openMSX con Sony HB-F900 (MSX2) |

Todo lo que sigue se refiere a esa imagen. Con otro dump los desplazamientos pueden cambiar.

## 2. Estructura del disco y carga

- El disco no tiene un sistema de ficheros útil. Todo se lee por sectores sueltos.
- El sector de arranque lee 8 sectores desde el 234 (disco `1D400h`) a `8200h`. Ese bloque es el **residente**.
  - Para pasar de dirección del residente a disco: `disco = dirección + 1D400h - 8200h`.
- El resto se carga por sectores con BDOS 1Ah/2Fh, a través de la rutina `8908h` (con `8926h`).
- El disco está prácticamente lleno: en el original solo quedan 6 sectores libres.
- El juego usa 64 KB de RAM, no toca los puertos del mapper y casi no tiene RAM libre (`E600h-EAFFh` y poco más).

### Módulos de pantalla

Cada pantalla carga su código en `9200h`/`9800h`/`9C00h`. En la tabla, R es la constante que se suma a la dirección de RAM para obtener el desplazamiento en disco.

| Módulo | Carga en | Disco | R (disco = dir + R) |
|---|---|---|---|
| Residente | 8200h | 1D400h | 1D400h − 8200h |
| Lista de personas (64h) | 9800h | C400h | 2C00h |
| Registro de persona (6Fh) | 9C00h | DE00h | 4200h |
| VER DATOS / DISPLAY (7Dh) | 9C00h | FA00h | 5E00h |
| Afinidad / grupo sanguíneo (AAh) | 9800h | 15400h | 15400h − 9800h |
| Cuadro de consejos de afinidad | 9800h | 16000h | 16000h − 9800h |
| Horóscopo, ascendente (B8h) | 9800h | 17000h | 17000h − 9800h |
| Horóscopo, menú (BCh) | 9800h | 17800h | 17800h − 9800h |
| Quiromancia, pantalla de líneas | 9200h… | 1A000h… | 10E00h |
| Quiromancia, resultados | 9800h | 1A600h | 1A600h − 9800h |
| Quiromancia, preguntas | 9800h | — | 10200h (p. ej. 98ACh → 19AACh) |
| Omikuji | — | — | 8200h |

## 3. Rutinas del residente

| Dirección | Qué hace |
|---|---|
| 8221h | HL += A (índice en tablas) |
| 8275h / 827Bh | Mensaje suelto: `[x][y] texto FF` |
| 827Eh | Dibuja un carácter de texto; llama a 8BEAh y copia por VDP |
| 82AEh → 8DA0h | Sube glifos 1bpp a la VRAM |
| 82CCh → 8FC6h | Desempaqueta fuentes RLE. IX apunta a una lista de entradas de 5 bytes: `80, origen (2), código inicial, color`; un 0 termina la lista |
| 8ED2h | Rótulos hechos con glifos seguidos de la fuente: `[n][código inicial]` |
| 8B42h | Impresora de textos de interfaz (menús, letreros) |
| 8834h / 8841h | Lectura de la entrada |
| 8908h / 8926h | Lectura de sectores del disco |

## 4. Entrada

El byte de entrada tiene esta forma: bit 0 arriba, 1 abajo, 2 izquierda, 3 derecha, 4 espacio, 5 M, 6 RETURN, 7 ESC.

- `D1C9h` guarda las teclas pulsadas ahora.
- `D1C8h` guarda las teclas recién pulsadas en este cuadro.

## 5. Texto

### Fuente

- La fuente es de 8×8 y está en la página 1 de la VRAM (y = 256…319), con 256 huecos.
  - El código c está en x = (c & 1Fh) × 8, y = 256 + (c >> 5) × 8.
- Los glifos se copian con HMMM, de 8 px y con fondo.
  - **La x tiene que ser par**: el VDP ignora el bit bajo.
- Códigos comunes a todo el juego (00h-52h):

| Código | Contenido |
|---|---|
| 00 | espacio |
| 01-35 | hiragana |
| 36-3F | dígitos |
| 40-42 | A, B, O (grupos sanguíneos) |
| 43 / 44 | ゛ / ゜ |
| 45 / 46 | 、 / 。 |
| 48 / 49 | 「 / 」 |
| 4B | ー |
| 4F | ♥ |
| 50 | ↵ |
| 51 / 52 | ? / ! |

- Los códigos 53h-FAh son kanji y katakana propios de cada escena: cada pantalla carga los suyos.

### Códigos de control

| Código | Función |
|---|---|
| FF | fin de texto |
| FE | salto de línea |
| FD | alterna el modo «directo» (katakana: el código es el hueco de la fuente tal cual) |
| FC | nombre de la persona |
| FB | sin identificar |

Fuera del modo directo:

- BEh-D1h son kana con ゛ (tabla en `919Fh`). La marca ゛ se dibuja en la línea de arriba.
- D2h-D6h son kana con ゜.
- D7h-FAh son parejas tipo きゃ (tabla en `91B8h`).

### Las cuatro clases de texto

1. Textos largos, con el intérprete propio de cada módulo, que llama a `827Eh`.
2. Mensajes sueltos con `8275h`/`827Bh`, con el formato `[x][y] texto FF`.
3. Rótulos hechos con glifos consecutivos de la fuente (`8ED2h`). Por ejemplo, el menú 血液型相性占い / おみくじ / 西洋占星術 / 手相占い.
4. Gráficos puros: tablillas y pergaminos de la omikuji, botones del horóscopo, lámina de la mano, mapa de Japón, rejilla de entrada del nombre, fechas en era Showa…

### Dónde está cada bloque de texto (disco)

| Bloque | Disco | Notas |
|---|---|---|
| Omikuji | 76B00h-79FFFh | 422 frases en huecos fijos de 32 bytes, 2 líneas de unas 14 letras |
| Horóscopo (12 signos × 4 temas) | 2CF8Eh-2FBF6h | se carga a D300h en trozos de 2 sectores |
| Grupo sanguíneo | 3FC92h-4539Fh, y 1F800h-1FBFFh | compatibilidad, padres e hijos, trabajo, general |
| Quiromancia, preguntas | 1AFFFh-1B421h | hay otra copia en 15E00h |
| Quiromancia, resultados | 24000h-24FFFh | 4 trozos de 2 sectores a D300h. Cada registro: 3 bytes de cabecera + texto + FF. Fuente propia en el sector 333 |
| Mensajes de impresora | 1F000h | con copias en varios módulos (sectores 15, 17, 19, 76, 145, 172, 190, 214) |

## 6. Fichas de personas

- Están en RAM en `D700h + 48 × i` (5 fichas) y en disco a partir de `B3C00h` (sector 59Eh).
- Formato de cada ficha:

| Desplazamiento | Contenido |
|---|---|
| +00h | nombre |
| +16h | sexo: 0 hombre, 1 mujer |
| +1Ch | quiromancia: 19 bytes, la variante elegida para cada línea de la mano. FFh = sin marcar |
| +2Fh | sin identificar |

- El disco original trae una ficha de muestra en el hueco 1 (nombre ああああ), con ceros en los datos de la mano. Los huecos 2-5 vienen a FFh.

## 7. Quiromancia, pantalla de líneas

| Dirección | Uso |
|---|---|
| 9219h | línea actual |
| 921Bh-922Dh | variante elegida para cada línea, copiada de la ficha (+1Ch) por 9A71h/9A7Ah |
| 9231h | variante mostrada (FFh = ninguna) |
| 9232h | número de variantes de la línea actual |
| 9CA1h | puntero a la variante de la línea actual |

- La derecha (`9C72h`) suma 1 y da la vuelta a 0.
- La izquierda está en `9C88h`.
- El intérprete de la pantalla está en torno a `9340h-9410h`.

### Fallo del original

La izquierda hace `SUB 1` y solo da la vuelta si hay acarreo. Con la línea sin marcar (FFh) queda FEh. El juego entonces intenta escribir el texto de la variante FEh y llena la pantalla de basura.

- Pasa en el original japonés con cualquier persona registrada en los huecos 2-5.
- Para reproducirlo: entrar en la quiromancia con una persona nueva y pulsar ← en la pantalla de las líneas.
- Arreglo usado en la traducción, en disco `1AA88h` (`9C88h`):

```
original: ED 5B A1 9C  1A  D6 01  30 04  3A 32 92  3D  12  18 E8
arreglo : ED 5B A1 9C  1A  3D  FE FE  38 04  3A 32 92  3D  18 E7
          LD DE,(9CA1h) / LD A,(DE) / DEC A / CP FEh / JR C,+4 /
          LD A,(9232h) / DEC A / JR 9C7Fh   (9C7Fh = LD (DE),A de la rutina de la derecha)
```

## 8. Otras tablas útiles (en RAM, del módulo cargado)

| Dirección | Qué es |
|---|---|
| A953h | Menú principal: resaltado rosa. Entradas de 4 bytes: filas, ancho, y, x |
| D517h | Menú principal: cursores |
| A9EEh | Lista: posiciones de los nombres |
| EEEDh | Registro: tabla de cursores compartida por los menús. Entradas `y, x, 0` |
| 9936h / 9987h / 99D2h | Afinidad: estructuras de los menús de los globos: puntero de cursores, puntero de texto, D234h, filas, columnas |
| 9B5Bh | Afinidad: resaltado por opción (filas, ancho, y, x) |
| A47Eh | Omikuji: copia de la caja de texto a la pantalla (16×32 en el original) |
| A408h | Omikuji: tabla de baldosas que se suben a la VRAM |

## 9. Cómo está hecha la traducción

`build.py` parte siempre del disco original intacto y aplica los cambios con `pt(desplazamiento, viejo, nuevo)`, que comprueba los bytes originales antes de escribir. Si el disco no es el esperado, falla al construir.

- **Fuente latina** (`tools/font6.txt`, 6×8): ocupa los códigos 01h-52h, que ninguna escena machaca (las escenas cargan sus glifos desde 53h): a-z, A-Z, á, dígitos, é í ó, ú ü ñ Á ¿ ¡ . , : Ñ, ♥, ↵, ? y !. La tabla está en `tools/charset.py`. El avance de la impresora de interfaz (8B42h) pasa a 6 px.
- **Textos** (`trad/`): líneas `DESPLAZAMIENTO|texto`. `/` corta renglón, `@XX,YY:` coloca un renglón, `{N}` es el nombre de la persona y `{o}`/`{a}` dan la terminación según su sexo.
- **Compresión y mapper**: el castellano no cabe en el disco ni en los 64 KB del original. Los textos largos se comprimen por pares de bytes (`tools/bpe.py`, fichas 5Eh-EFh) y van a los segmentos 4-6 del mapper. Un cargador nuevo (`src/eng.asm`, en el sector 251) copia el residente nuevo a 8003h-81FFh y el texto a la RAM extra. Las lecturas de los trozos de texto japoneses se cambian por «trozos virtuales» que se descomprimen en DB00h. Por eso **hace falta un MSX2 con 128 KB**.
- **Sexo** (`src/sexo.asm`, en 7FA0h de cada segmento de texto): busca el nombre de la frase en las fichas (D700h + 48·i, sexo en +16h) y elige «o» o «a».
- **Gráficos** (`gfx/`): retoques por píxel (`desplazamiento:nibble → color`) y, en `gfx/datos/`, los pergaminos de la omikuji, la lámina de la quiromancia y las cabeceras de sus preguntas rehechos enteros.
- **Huecos**: antes de poner una rutina en un hueco de un módulo hay que comprobar que allí había texto ya sustituido. Una rutina que pisó el descriptor de un menú colgaba el registro.

## 10. Cómo se probó

- **openMSX controlado por socket**: arrancamos con control y mandamos órdenes Tcl desde Python. Así pulsamos teclas (`keymatrixdown/up`), tomamos capturas con `screenshot -raw` y guardamos o cargamos estados.
- **Trucos útiles de Tcl**:
  - Ver quién escribe una variable: `debug set_watchpoint write_mem {921Bh 922Dh} {} {lappend ::wl [format %04x [reg pc]]}`.
  - Volcar los 64 KB y comparar antes y después de pulsar una tecla: así salen solas las variables de cada pantalla.
  - Registrar las lecturas de sectores enganchando 8908h: así sale el mapa de qué carga cada pantalla.
- **Repeticiones .omr**: los fallos se reprodujeron con las grabaciones del probador y su disco con datos. Las grabadas con openMSX 21 no se abren con el 20. Si metes una tecla tuya durante la repetición, esta se corta y hay que volver a cargarla.
- **Primera tecla tras loadstate**: después de un `loadstate`, la primera tecla suele perderse.

## 11. Créditos

- Juego: © Konami 1988.
- Traducción al castellano: dirección y pruebas, araubi. Ingeniería inversa, traducción y código: desarrollado con Claude (Anthropic).

Documentación bajo CC BY-NC-SA 4.0 (ver LICENSE-CC).
