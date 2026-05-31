# Decisiones pendientes — Catálogo web (Istmo / Lienzos / Trajes)

> **Para retomar en otra máquina.** Este documento contiene el contexto completo del proyecto
> y las decisiones que faltan tomar antes de escribir código. Léelo junto con `ESPECIFICACIONES.md`.
> Fecha: 2026-05-30

---

## A. Contexto rápido (para retomar desde cero)

**Qué se está construyendo:** un catálogo web **estático** que muestra productos (textiles)
guardados en Airtable, para compartir a clientes por **link**. Los clientes **solo ven** (no editan,
no hay login, no envían nada). Se publica en **GitHub Pages**. Todo el build se hace con **Python**.

**Por qué estático y no un servidor (FastAPI/Flask):**
- Las **URLs de imagen de Airtable expiran** a las pocas horas → hay que descargar las fotos y servirlas nosotros.
- El **token de Airtable es secreto** y el repo de GitHub Pages es público → el token solo se usa al construir, nunca se publica.
- Un sitio estático es **gratis, rápido, no se cae y es liviano** (las prioridades del proyecto). Un servidor en vivo cuesta, se puede caer y es innecesario para datos que casi no cambian.

**Las 3 bases de Airtable (datos reales ya verificados):**

| Base | baseId | tableId | Campo código | Campo foto | # productos |
|------|--------|---------|--------------|------------|-------------|
| Istmo | `appaNMwGX5X7kGL4F` | `tblZcEO4pd4PFzzwJ` | `Codigo` | `Foto` | ~294 |
| Lienzos y enaguas | `appkxN7OtOT0X0GxJ` | `tblUkmiGsPJ2V7fEs` | `Name` | `Attachments` | ~307 |
| Trajes | `appvIxMVAhGKHamzo` | `tblMBfQeqmQ4LWZgz` | `Name` | `Attachments` | ~134 |

**En el catálogo solo se muestra:** código + foto. Nada de precios, medidas ni técnica.

**Setup necesario en la otra máquina (antes de construir):**
- Python 3 + librerías: `pyairtable` (o `requests`), `requests`, `Pillow`, `Jinja2`.
- El token de Airtable (solo lectura) en la variable de entorno **`airtable_sari_token`** (sin guion final).
  - El token requiere los scopes `schema.bases:read` y `data.records:read`, y acceso a las 3 bases.
- (Opcional) El MCP de Airtable en Claude Code, agregado con:
  `claude mcp add airtable --env AIRTABLE_API_KEY="$airtable_sari_token" -- npx -y airtable-mcp-server`

---

## B. Decisiones pendientes (qué falta y por qué importa)

### 1. Orden de los productos en el catálogo — ✅ DECIDIDO (2026-05-30)
**Decisión:** ordenar por **código ascendente**. El filtro superior (Todos / Istmo / Lienzos / Trajes)
permite ver cada categoría por separado.

---

### 2. ¿La etiqueta de origen se muestra en la tarjeta? — ✅ DECIDIDO (2026-05-30)
**Decisión:** **sí**, cada tarjeta muestra su origen (Istmo / Lienzos / Trajes) además del código.

---

### 2b. Manejo de fotos — ✅ DECIDIDO (2026-05-30)
- **Producto sin foto** (o cuya descarga falla): se **descarta** (no aparece en el catálogo); se registra en un log del build.
- **Producto con varias fotos** (Attachments con más de una): se usa **solo la primera**.

---

### 3. Identidad visual del catálogo (título, colores, logo)
**Qué definir:** nombre/título que aparece arriba del catálogo · colores principales · si hay logo (y el archivo).

**Por qué importa:** es lo que ve el cliente y representa la marca. No es solo estético: el título y el logo
dan confianza y profesionalismo al link que vas a compartir por WhatsApp. Necesito el texto del título y,
si hay logo, el archivo de imagen para incluirlo en el sitio.

---

### 4. Nombre del repositorio en GitHub
**Qué definir:** nombre del repo (define también la URL pública de GitHub Pages, del tipo
`https://<usuario>.github.io/<repo>/`) · cuenta de GitHub a usar.

**Por qué importa:** es la URL que compartirás a los clientes. Conviene un nombre limpio y memorable.
También determina dónde se publica y cómo se actualiza después.

---

### 5. (Futuro / opcional) Dominio propio
**Qué definir:** si más adelante quieres un dominio propio (ej. `catalogo.tudominio.com`) en vez de la URL de github.io.

**Por qué importa:** no bloquea el arranque (se puede empezar con la URL gratis de GitHub Pages y migrar después),
pero si ya tienes dominio, conviene planearlo desde el inicio para no cambiar el link compartido más tarde.

---

### 6. (Decisión técnica ya tomada, anotada para referencia) Estrategia de actualización
**Decidido:** empezar con **full rebuild** (el script reconstruye todo cada vez, ~2-3 min). Simple y robusto.
**Pendiente futuro:** si actualizas seguido, agregar **build incremental** (solo descarga fotos nuevas) y/o
una **GitHub Action programada** que reconstruya y publique sola.

---

## C. Siguiente paso al retomar

1. Confirmar setup de la sección A (Python, librerías, token en `airtable_sari_token`).
2. Responder las decisiones 1–4 (la 5 y 6 pueden quedar para después).
3. Con eso, escribir el script de build de Python y el template HTML.
4. Probar localmente, luego publicar en GitHub Pages.
