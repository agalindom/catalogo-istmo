# Especificaciones — Catálogo web de productos (TANDA 1 ahora en bodega)

> Documento de especificaciones. Define **qué** se va a construir y **cómo**.
> Fecha original: 2026-05-30 · Actualizado: 2026-07-01

> **Cambio de fuente (2026-07-01):** el catálogo original de **3 bases**
> (Istmo / Lienzos / Trajes) quedó **deprecado**. Ahora la fuente es **una sola
> base** (`TANDA 1 ahora en bodega`) y el catálogo **sí muestra precio y medidas**.
> El código de build es el mismo; solo cambió la fuente de datos y las columnas.

---

## 1. Objetivo

Generar un **catálogo web estático** que exponga los productos almacenados en Airtable, para compartir a clientes mediante un **link**. Los clientes **solo ven** (no editan, no inician sesión, no envían nada). La fuente de datos sigue siendo Airtable; el catálogo se reconstruye cuando hay cambios.

## 2. Alcance

### Dentro del alcance
- Leer productos de **1 base** de Airtable (solo lectura).
- Mostrar por producto: **Código**, **Foto** y **Precio**. Al tocar la foto se amplía (zoom).
- Catálogo **único** con buscador por código.
- Descargar y **optimizar** las fotos (resolver la expiración de URLs de Airtable).
- Generar sitio **estático** (HTML + imágenes) y publicarlo en **GitHub Pages**.

### Fuera del alcance (por ahora)
- Edición de datos / escritura a Airtable.
- Login de clientes, carrito, pedidos o pagos.
- Filtro por origen / categoría (una sola fuente).
- Actualización en tiempo real (el catálogo se actualiza al re-construir).

## 3. Restricciones técnicas que guían el diseño

1. **Las URLs de imagen de Airtable expiran** (caducan a las pocas horas) → **no** se pueden enviar al cliente; hay que **descargar las fotos y servirlas nosotros**.
2. **El token de Airtable es secreto** → solo se usa en la máquina al construir; **nunca** se sube al repositorio (repo público).
3. **Permiso del token: solo lectura** → el script jamás escribe en Airtable.
4. **Límite de API de Airtable**: ~5 peticiones/seg → el script respeta el ritmo (paginación + pausa).

## 4. Stack tecnológico

- **Lenguaje:** Python 3.
- **Librerías:**
  - `pyairtable` (o `requests`) → leer registros de Airtable.
  - `requests` → descargar las fotos.
  - `Pillow` → redimensionar/comprimir a WebP.
  - `Jinja2` → generar el HTML.
- **Hosting:** GitHub Pages (estático, gratis, CDN).
- **Sin** servidor en vivo, sin base de datos, sin framework web (FastAPI/Flask no son necesarios para un catálogo solo-lectura).

## 5. Fuente de datos (Airtable)

Base única **TANDA 1 ahora en bodega** (`appgUsPjhYfClzHSu`), tabla `tblZcEO4pd4PFzzwJ`:

| Campo (Airtable) | Uso en el catálogo |
|------------------|--------------------|
| `Codigo` | código del producto |
| `Foto` | foto (se usa la primera del attachment) |
| `Precio especial EFECTIVO contado` | precio mostrado (fórmula = `REMATE` × 1.10) |
| `DE VENTA EN` | si contiene "vendido", el producto se descarta |

- Volumen: 188 registros → **~185 productos** publicados (se descartan vendidos y precio $0).

## 6. Modelo de datos normalizado

```
Producto:
  codigo:   str        # ej. "573"
  imagen:   str        # ruta local relativa, ej. "img/tanda-1-573.webp"
  precio:   int        # pesos (siempre presente; precio 0 se descarta)
```

- Nombre de archivo de imagen: `tanda-1-{codigo}.webp` (minúsculas, sin espacios).

## 7. Flujo del build (script de Python)

```
1. Leer las 3 bases de Airtable (paginado, respetando 5 req/seg).
2. Por cada producto:
   a. Tomar código + URL temporal de la foto.
   b. Descargar la foto original (temporal).
   c. Redimensionar (lado mayor ~800px) y comprimir → WebP.
   d. Guardar SOLO la versión optimizada en /salida/img/.
   e. Descartar la original (no se acumulan archivos pesados).
3. Renderizar index.html (Jinja2) con todas las tarjetas (código + foto).
4. Copiar CSS/JS al directorio de salida.
=> Resultado: carpeta /salida lista para publicar.
```

- **Estrategia de build:** *full rebuild* (reconstruye todo cada vez). Simple y robusto. Tiempo estimado: ~2-3 min.
- Mejora futura opcional: build incremental (solo descarga fotos nuevas).

## 8. Salida / estructura del sitio

```
/salida
  index.html          # catálogo (grid de tarjetas)
  /assets
    style.css
    app.js            # filtros + buscador + lazy load
  /img
    istmo-573.webp
    lienzos-168.webp
    trajes-447.webp
    ...
```

## 9. Frontend (lo que ve el cliente)

- **Grid de tarjetas**: cada tarjeta = foto + código + precio.
- **Buscador** por código.
- **Zoom / lightbox**: al tocar una foto se amplía y muestra código y precio.
- **Lazy load** de imágenes (`loading="lazy"`): el navegador descarga solo lo visible → catálogo rápido y liviano.
- **Responsive**: se ve bien en celular (los clientes lo abrirán por WhatsApp).
- Sin backend: toda la búsqueda ocurre en el navegador sobre datos ya incluidos.

## 10. Dimensionamiento / recursos

| Concepto | Estimación |
|----------|-----------|
| Fotos originales (celular) | ~2–5 MB c/u (NO se conservan) |
| Foto optimizada (WebP ~800px) | ~80–150 KB c/u |
| **Catálogo completo (~735 fotos)** | **~70–110 MB** |
| Pico de disco durante build | fotos optimizadas + 1 original temporal |
| Límites GitHub Pages (repo <1GB, archivo <100MB, ~100GB/mes) | Holgadamente dentro |

## 11. Seguridad

- El token de Airtable vive en **variable de entorno** (`airtable_sari_token`) en la máquina; **no** se escribe en el código ni en el repo.
- `.gitignore` excluye cualquier archivo con secretos y las fotos originales temporales.
- El sitio publicado **no contiene** el token (solo HTML + imágenes ya descargadas).
- El catálogo funciona aunque Airtable esté caído (es independiente una vez construido).

## 12. Publicación y actualización

1. Construir con el script → carpeta `/salida`.
2. Subir el contenido a un repo de GitHub con Pages activado (rama/carpeta de publicación).
3. Compartir el link de GitHub Pages a los clientes.
4. **Para actualizar** (nuevos productos): re-correr el script y volver a subir.
   - Automatización futura opcional: GitHub Action programada que reconstruye y publica sola.

## 13. Decisiones tomadas y pendientes

### Tomadas (2026-05-30)
- [x] **Orden:** por código ascendente. El filtro superior (Todos / Istmo / Lienzos / Trajes) permite ver cada categoría.
- [x] **Etiqueta de origen:** sí, cada tarjeta muestra su origen (Istmo/Lienzos/Trajes) además del código.
- [x] **Productos sin foto:** se descartan (no aparecen en el catálogo); se registran en un log del build.
- [x] **Productos con varias fotos:** se usa solo la primera del attachment.

### Pendientes
- [ ] Nombre del repo y URL final de GitHub Pages.
- [ ] ¿Dominio propio en el futuro? (opcional).
- [ ] Diseño visual (colores, logo, título del catálogo).

## 14. Criterios de aceptación

- El catálogo abre por link y muestra ~735 productos (código + foto).
- Las imágenes cargan siempre (no dependen de URLs de Airtable que expiran).
- Filtro por origen y búsqueda por código funcionan en el navegador.
- Se ve bien en celular.
- El token de Airtable no aparece en ningún archivo publicado.
- Reconstruir tras agregar productos en Airtable refleja los cambios.
