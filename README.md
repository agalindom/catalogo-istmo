# Catálogo web (Istmo / Lienzos / Trajes)

Catálogo estático que muestra productos (textiles) guardados en Airtable, para
compartir a clientes por link. Solo lectura. Se publica en GitHub Pages.

Ver `ESPECIFICACIONES.md` y `DECISIONES_PENDIENTES.md` para el contexto completo.

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
a las 3 bases. **Nunca** se sube al repositorio.

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

El build hace *full rebuild*: lee las 3 bases, descarga y optimiza las fotos a
WebP (~1200px), y renderiza el HTML. Los productos sin foto se descartan y se
registran en `build.log`.

## Publicar

Sube el contenido de `docs/` a un repo con GitHub Pages activado y comparte el
link. Para actualizar: re-correr `build.py` y volver a subir.

## Estructura del proyecto

```
build.py                 # script de build
requirements.txt
templates/index.html.j2  # template Jinja2
assets/style.css         # paleta clara/neutra
assets/app.js            # filtro + búsqueda (en el navegador)
docs/                  # salida generada (no versionar el contenido pesado)
```
