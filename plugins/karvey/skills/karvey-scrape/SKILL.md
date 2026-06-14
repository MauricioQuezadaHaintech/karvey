---
name: karvey-scrape
description: Web data extractor for the Karvey method. Pulls data from a web page; first call prototypes the extraction, then codifies it into a reusable, tested script/skill for fast re-runs. Triggers include "karvey scrape", "scraping", "extraer datos web", "scrapear", "codificar skill", "skillify".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [url] [--codify]
---

# karvey-scrape

**Skill transversal del Método Karvey™.** Es una **capa de apoyo, NO una fase**. No cambia `spec.json:phase` ni hace avanzar el flujo del método. Se puede invocar desde cualquier fase cuando necesitas extraer datos de una página web y, opcionalmente, dejar esa extracción codificada como un artefacto reutilizable.

Inspirada en `/scrape` + `/skillify` de gstack: combina un **extractor web** (prototipo rápido) con un **codificador de skills** (script + test + fixture reutilizable).

## Propósito

- **Prototipar**: en la primera llamada, extraer los datos pedidos de la página objetivo. Cuando el contenido sea dinámico o requiera interacción (JS, login, paginación, scroll), usar el runtime de browse disponible; para HTML estático basta con `curl`/`fetch` + parseo.
- **Codificar (`--codify` / skillify)**: sintetizar a partir del prototipo un **script reutilizable + test + fixture**, correr el test, y **pedir confirmación antes de commitear**.
- **Resultado**: extracciones repetibles y rápidas para intents que se repiten, sin tener que re-descubrir selectores ni lógica cada vez.

## Pasos

### 1. Prototipar (primera llamada)

1. Recibir la `[url]` y la descripción de los datos a extraer.
2. Determinar la naturaleza de la página:
   - **Estática** → descargar HTML y parsear (selectores CSS/XPath, regex acotado, JSON embebido).
   - **Dinámica / con interacción** → usar el runtime de browse (navegar, esperar selectores, scroll, paginación, login si corresponde).
3. Extraer los datos solicitados y presentarlos al usuario en un formato estructurado (JSON/tabla).
4. Registrar los detalles relevantes de la extracción: URL, selectores/queries, pasos de navegación, formato de salida. Esto es la base para la codificación.

### 2. Codificar (`--codify` / skillify)

Cuando se pasa `--codify` (o el usuario pide "codificar skill" / "skillify"):

1. **Sintetizar el script reutilizable** a partir del prototipo: parametrizar URL/inputs, encapsular selectores y pasos de navegación, definir el contrato de salida.
2. **Generar un test** que valide la extracción contra un **fixture** (snapshot del HTML/respuesta capturado en el prototipo), de modo que el test sea determinista y no dependa de la red.
3. **Correr el test** y ajustar hasta que pase.
4. **Pedir confirmación explícita antes de commitear** el script + test + fixture.

## Reglas

- **Respetar términos de uso y `robots.txt`** de los sitios. No usar esta skill para scraping abusivo, evasión de protecciones, ni recolección masiva no autorizada.
- **No avanza la fase.** Es capa de apoyo; nunca modificar `spec.json:phase` desde aquí.
- Mantener los fixtures acotados y los tests deterministas (sin llamadas de red en el test).
- No commitear nada sin confirmación del usuario.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
