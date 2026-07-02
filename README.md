# Catálogo web (TANDA 1 ahora en bodega)

Catálogo estático que muestra productos (textiles) guardados en Airtable, para
compartir a clientes por link. Solo lectura. Se publica en GitHub Pages.

Cada producto muestra **foto, código y precio**; al tocar la foto se ven las
**medidas y la descripción**.

> **Nota:** el catálogo anterior de 3 bases (Istmo / Lienzos / Trajes) quedó
> **deprecado**. La fuente actual es una sola base y el código de build es el
> mismo, solo cambió la fuente de datos y las columnas mostradas. Ver
> `ESPECIFICACIONES.md`.

## Setup

```bash
# 1. Instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Exportar el token de Airtable (solo lectura)
export airtable_sari_token='patXXXXXXXX...'
```

El token requiere los scopes `schema.bases:read` y `data.records:read` y acceso
a la base `TANDA 1 ahora en bodega` (`appgUsPjhYfClzHSu`). **Nunca** se sube al
repositorio.

## Construir el catálogo

```bash
python3 build.py
```

Genera la carpeta `docs/` con:

```
docs/
  index.html
  assets/style.css
  assets/app.js
  img/*.webp
```

El build hace *full rebuild*: lee la base, descarga y optimiza las fotos a
WebP (~1200px), y renderiza el HTML. Se descartan (y se registran en `build.log`)
los productos **sin foto**, **marcados "vendido"** o con **precio $0**.

Opciones:

```bash
python3 build.py --limit 15    # mini-preview: 15 productos (para probar diseño)
python3 build.py --solo-render  # re-genera HTML reusando fotos ya descargadas
```

## Publicar

Sube el contenido de `docs/` a un repo con GitHub Pages activado y comparte el
link. Para actualizar: re-correr `build.py` y volver a subir.

## Estructura del proyecto

```
build.py                 # script de build (fuente: 1 base de Airtable)
requirements.txt
templates/index.html.j2  # template Jinja2
assets/style.css         # paleta clara/neutra
assets/app.js            # búsqueda por código + zoom (en el navegador)
docs/                    # salida generada
```
