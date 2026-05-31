#!/usr/bin/env python3
"""
Build del catálogo web estático (Istmo / Lienzos / Trajes).

Lee 3 bases de Airtable (solo lectura), descarga y optimiza las fotos a WebP,
y genera un sitio estático en /salida listo para publicar en GitHub Pages.

Decisiones (ver ESPECIFICACIONES.md §13):
  - Orden: por código ascendente. Filtro por origen en el navegador.
  - Cada tarjeta muestra su origen.
  - Producto sin foto (o descarga fallida): se descarta y se registra en log.
  - Producto con varias fotos: se usa solo la primera.

Requisitos de entorno:
  - Variable de entorno `airtable_sari_token` (token solo-lectura de Airtable).
  - pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image, ImageOps
from pyairtable import Api

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).parent
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
# Carpeta de salida = "docs" porque GitHub Pages publica desde / o /docs.
OUT_DIR = ROOT / "docs"
OUT_IMG_DIR = OUT_DIR / "img"
OUT_ASSETS_DIR = OUT_DIR / "assets"

TOKEN_ENV = "airtable_sari_token"

# Las 3 bases. `codigo`/`foto` son los nombres de campo reales en cada base.
CAMPO_PRECIO = "Precio contado en efectivo"

BASES = [
    {
        "origen": "Istmo",
        "base_id": "appaNMwGX5X7kGL4F",
        "table_id": "tblZcEO4pd4PFzzwJ",
        "campo_codigo": "Codigo",
        "campo_foto": "Foto",
        "campo_precio": CAMPO_PRECIO,
    },
    {
        "origen": "Lienzos",
        "base_id": "appkxN7OtOT0X0GxJ",
        "table_id": "tblUkmiGsPJ2V7fEs",
        "campo_codigo": "Name",
        "campo_foto": "Attachments",
        "campo_precio": CAMPO_PRECIO,
    },
    {
        "origen": "Trajes",
        "base_id": "appvIxMVAhGKHamzo",
        "table_id": "tblMBfQeqmQ4LWZgz",
        "campo_codigo": "Name",
        "campo_foto": "Attachments",
        "campo_precio": CAMPO_PRECIO,
    },
]

# Optimización de imagen
MAX_SIDE = 1200           # lado mayor en px (suficiente para zoom/lightbox)
WEBP_QUALITY = 80         # calidad WebP
REQUEST_TIMEOUT = 30      # seg por descarga

# Ritmo de lectura de Airtable (~5 req/seg). pyairtable pagina solo;
# la pausa entre páginas la maneja la librería, pero limitamos descargas.
DOWNLOAD_PAUSE = 0.0      # las fotos van al CDN de Airtable, no a la API

TITULO = "Catálogo"

# Mostrar precios en el catálogo. Por ahora False (decisión de negocio).
# Ponlo en True para que los precios aparezcan en las tarjetas y el zoom.
# Cuando es False, los precios NO se escriben en el HTML publicado.
VER_PRECIOS = False

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "build.log", mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger("build")


# --------------------------------------------------------------------------- #
# Modelo normalizado
# --------------------------------------------------------------------------- #

@dataclass
class Producto:
    codigo: str
    origen: str
    imagen: str          # ruta relativa, ej. "img/istmo-573.webp"
    precio: int | None = None  # pesos; None si la base no tiene precio

    @property
    def codigo_orden(self):
        """Clave de orden: numérica si el código es número, si no alfabética."""
        m = re.match(r"^\s*(\d+)", self.codigo)
        return (0, int(m.group(1))) if m else (1, self.codigo.lower())

    @property
    def precio_fmt(self) -> str:
        """Precio formateado, ej. '$1,200'. Cadena vacía si no hay precio."""
        return f"${self.precio:,.0f}" if self.precio is not None else ""


def slugify(value: str) -> str:
    """Normaliza a minúsculas sin acentos ni espacios, seguro para nombre de archivo."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


# --------------------------------------------------------------------------- #
# Airtable
# --------------------------------------------------------------------------- #

def get_token() -> str:
    token = os.environ.get(TOKEN_ENV)
    if not token:
        log.error("Falta la variable de entorno %r con el token de Airtable.", TOKEN_ENV)
        log.error("  export %s='patXXXX...'", TOKEN_ENV)
        sys.exit(1)
    return token


def leer_registros(api: Api, base: dict, limit: int | None = None) -> list[dict]:
    """Lee los registros de una base (paginado por pyairtable).

    Si `limit` es un entero, lee como máximo esa cantidad (para mini-previews).
    """
    table = api.table(base["base_id"], base["table_id"])
    if limit:
        registros = table.all(max_records=limit)
    else:
        registros = table.all()  # pagina automáticamente respetando el rate limit
    log.info("  %-8s : %d registros leídos", base["origen"], len(registros))
    return registros


def extraer_foto_url(fields: dict, campo_foto: str) -> str | None:
    """Devuelve la URL de la PRIMERA foto, o None si no hay."""
    attachments = fields.get(campo_foto)
    if not attachments:
        return None
    if isinstance(attachments, list) and attachments:
        return attachments[0].get("url")
    return None


# --------------------------------------------------------------------------- #
# Imágenes
# --------------------------------------------------------------------------- #

def descargar_y_optimizar(url: str, destino: Path) -> bool:
    """Descarga una foto, la redimensiona y guarda como WebP. True si tuvo éxito."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))

        # Aplica la orientación EXIF (las cámaras guardan la foto en horizontal
        # con una etiqueta de rotación; sin esto, algunas saldrían giradas).
        img = ImageOps.exif_transpose(img)

        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        img.save(destino, "WEBP", quality=WEBP_QUALITY, method=6)
        return True
    except Exception as exc:  # noqa: BLE001 - registramos y descartamos
        log.warning("    fallo descarga/optimización (%s): %s", destino.name, exc)
        return False


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #

def preparar_salida(solo_render: bool = False) -> None:
    if solo_render:
        # Conserva las fotos ya descargadas; solo re-genera HTML y assets.
        if not OUT_IMG_DIR.exists():
            log.error("--solo-render requiere fotos ya descargadas en %s", OUT_IMG_DIR)
            log.error("Corre primero un build normal (sin --solo-render).")
            sys.exit(1)
        OUT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")
        return
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_IMG_DIR.mkdir(parents=True)
    OUT_ASSETS_DIR.mkdir(parents=True)
    # .nojekyll: evita que GitHub Pages procese el sitio con Jekyll.
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")


def copiar_assets() -> None:
    for nombre in ("style.css", "app.js"):
        src = ASSETS_DIR / nombre
        if src.exists():
            shutil.copy(src, OUT_ASSETS_DIR / nombre)
        else:
            log.warning("  asset faltante: %s", src)


def renderizar(productos: list[Producto]) -> None:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html.j2")
    origenes = sorted({p.origen for p in productos})
    html = template.render(
        titulo=TITULO, productos=productos, origenes=origenes, ver_precios=VER_PRECIOS
    )
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    log.info("  index.html generado (%d productos, precios=%s)", len(productos), VER_PRECIOS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build del catálogo estático.")
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Mini-preview: descarga como máximo N productos por base.",
    )
    parser.add_argument(
        "--solo-render", action="store_true",
        help="Re-genera el HTML reusando las fotos ya descargadas (no descarga nada).",
    )
    args = parser.parse_args()

    inicio = time.time()
    if args.solo_render:
        log.info("=== Re-render del catálogo (sin descargar fotos) ===")
    elif args.limit:
        log.info("=== Build del catálogo (PREVIEW: %d por base) ===", args.limit)
    else:
        log.info("=== Build del catálogo ===")

    token = get_token()
    api = Api(token)

    preparar_salida(solo_render=args.solo_render)

    productos: list[Producto] = []
    descartados = 0
    nombres_usados: set[str] = set()

    for base in BASES:
        log.info("Leyendo base %s ...", base["origen"])
        registros = leer_registros(api, base, limit=args.limit)

        for rec in registros:
            fields = rec.get("fields", {})
            codigo = str(fields.get(base["campo_codigo"], "")).strip()
            if not codigo:
                descartados += 1
                log.info("    descartado (sin código): rec %s", rec.get("id"))
                continue

            url = extraer_foto_url(fields, base["campo_foto"])
            if not url:
                descartados += 1
                log.info("    descartado (sin foto): %s/%s", base["origen"], codigo)
                continue

            precio_raw = fields.get(base["campo_precio"])
            try:
                precio = int(round(float(precio_raw))) if precio_raw not in (None, "") else None
            except (TypeError, ValueError):
                precio = None

            # Nombre de archivo único; si colisiona, sufijo incremental.
            nombre = f"{slugify(base['origen'])}-{slugify(codigo)}"
            nombre_final = nombre
            n = 2
            while nombre_final in nombres_usados:
                nombre_final = f"{nombre}-{n}"
                n += 1
            nombres_usados.add(nombre_final)

            destino = OUT_IMG_DIR / f"{nombre_final}.webp"
            if args.solo_render:
                # Reusar la foto ya descargada; si no existe, se omite.
                if not destino.exists():
                    descartados += 1
                    continue
            elif not descargar_y_optimizar(url, destino):
                descartados += 1
                continue

            productos.append(
                Producto(
                    codigo=codigo,
                    origen=base["origen"],
                    imagen=f"img/{nombre_final}.webp",
                    precio=precio,
                )
            )
            if DOWNLOAD_PAUSE:
                time.sleep(DOWNLOAD_PAUSE)

    # Orden global: por código ascendente (numérico cuando aplica).
    productos.sort(key=lambda p: p.codigo_orden)

    copiar_assets()
    renderizar(productos)

    dur = time.time() - inicio
    log.info("=== Listo en %.1fs ===", dur)
    log.info("  productos publicados: %d", len(productos))
    log.info("  descartados (sin código/foto o descarga fallida): %d", descartados)
    log.info("  carpeta de salida: %s", OUT_DIR)


if __name__ == "__main__":
    main()
