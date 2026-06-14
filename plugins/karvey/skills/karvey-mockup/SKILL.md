---
name: karvey-mockup
description: Generate a navigable HTML mockup with 3 levels of depth from approved requirements. Iterate with user until approved, then advance to graphic design. Triggers include "karvey mockup", "generar mockup", "crear prototipo", "wireframe".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id> [--iteration N] [--shotgun | --variants N]
---

# Karvey Mockup — Prototipo Navegable HTML

## Propósito

Generar un archivo HTML navegable con 3 niveles de profundidad antes de definir el diseño gráfico. El ingeniero navega el mockup en el browser, da feedback, y se itera hasta aprobación. Solo después se avanza a diseño gráfico y arquitectura.

## Agnosticismo de target

El mockup **se adapta al target declarado** en `docs/spec/project.json` (campo `targets`) — ver `karvey/rules/targets.md`. **No asumir web por defecto:**

- **web** → HTML navegable (App Shell + vistas + overlays, como se describe abajo)
- **mobile (ios/android)** → flujo de pantallas (secuencia de pantallas con transiciones, no sidebar de escritorio)
- **cli** → transcript de comandos (entrada/salida de terminal de ejemplo)
- **api/backend** → ejemplos request/response (payloads de muestra por endpoint)

Los niveles, reglas y estructura HTML de las secciones siguientes aplican al target **web**. Para otros targets, generar el artefacto equivalente del target y guardar igualmente bajo `docs/spec/changes/{change-id}/` (ajustando la extensión cuando corresponda, ej. `mockup.md` para transcript CLI o ejemplos API). El resto del flujo (iteración, aprobación, sincronización de conocimiento) es idéntico.

## Modos de generación

- **Modo normal (default)**: una sola propuesta de mockup, que se itera con el usuario hasta aprobación (Pasos 1 a 6).
- **Modo shotgun (opt-in)**: generar **N variantes** del mockup de una vez (default **3**) con enfoques de diseño distintos, y ofrecer un **board comparativo** para que el usuario elija una o combine elementos de varias. Se activa con flag `--shotgun` (3 variantes) o `--variants N` (N variantes). Inspirado en `/design-shotgun`. Ver **Paso 3B**.

Si el usuario no pasa flag, usar siempre el modo normal.

## Niveles de navegación

- **Nivel 1 — App Shell**: Navegación principal (sidebar/topbar con secciones del producto)
- **Nivel 2 — Sección**: Vistas de cada sección (listados, formularios, dashboards)
- **Nivel 3 — Detalle**: Vistas de detalle (modales, paneles laterales, subvistas, wizards)

## Pasos de ejecución

### Paso 1 — Cargar contexto

Leer:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/proposal.md`

Verificar que `approvals.requirements.approved = true`. Si no, detener y pedir aprobar requirements primero.

**Verificar si aplica UI:** Leer `spec.json` → campo `layers`. Si solo incluye `[BD]` y/o `[Backend]` sin `[Frontend]`, preguntar al usuario: "Este cambio no parece tener interfaz de usuario. ¿Requiere mockup visual o pasamos directo a arquitectura?" Si no requiere, saltar a karvey-architecture.

Detectar iteración: si existe `docs/spec/changes/{change-id}/mockup.html`, incrementar el número de iteración.

### Paso 2 — Mapear pantallas desde requirements

Construir el mapa de pantallas leyendo los requirements:

```
Nivel 1 (Navegación):
  - {Sección A} → requirements {N.N, N.N}
  - {Sección B} → requirements {N.N, N.N}

Nivel 2 (Vistas por sección):
  Sección A:
    - Vista Lista: {qué muestra}
    - Vista Formulario: {qué captura}
  Sección B:
    - Vista Dashboard: {qué muestra}

Nivel 3 (Detalles):
  - Modal confirmación
  - Panel detalle
  - Wizard paso a paso
```

### Paso 3 — Generar mockup.html

Generar un único archivo HTML autocontenido:

**Estructura del HTML:**
```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>MOCKUP — {change-id} — Iteración {N}</title>
  <!-- Tailwind CDN — solo para prototipado, no implica su uso en el proyecto real -->
  <script src="https://cdn.tailwindcss.com"></script>
  <style>/* estilos adicionales */</style>
</head>
<body>
  <!-- Banner de mockup siempre visible -->
  <!-- App Shell con navegación Nivel 1 -->
  <!-- Contenedor de vistas Nivel 2 (cambia con navegación) -->
  <!-- Overlays de Nivel 3 (modales, paneles) -->
  <!-- JavaScript de navegación -->
</body>
</html>
```

**Reglas de construcción:**

1. **Banner persistente** en top: `🔧 MOCKUP — {change-id} — Iteración {N} — {fecha}`
2. **Navegación Nivel 1**: sidebar o topbar con íconos de placeholder (círculos grises) y nombres de sección
3. **Vistas Nivel 2**: representar cada pantalla como una vista con:
   - Título de la pantalla
   - Tabla/lista con columnas reales (labels reales, datos de ejemplo coherentes con el dominio)
   - Botones con labels reales ("Transferir llamada", "Confirmar", no "Button 1")
   - Formularios con campos reales y tipos correctos
   - Estados de carga representados con skeletons grises
4. **Nivel 3**: modales y paneles implementados como overlays que se muestran/ocultan con JS puro
5. **Navegación JS**: `showView(viewId)`, `showModal(modalId)`, `closeModal(modalId)` — sin dependencias externas
6. **Paleta neutral**: grays únicamente. El color y el design system del proyecto real vendrán en karvey-design-graphic.
7. **Responsive básico**: funcionar en 1280px+ de ancho mínimo
8. **Datos de ejemplo**: usar datos ficticios pero coherentes con el dominio (nombres de tenant, tipos de llamada reales, etc.)

**Elementos prohibidos en el mockup:**
- Lorem ipsum (usar texto real del dominio)
- "Button 1", "Section A" (usar labels reales)
- Imágenes externas (usar divs con bg-gray-300)
- Frameworks JS pesados (solo Tailwind CDN y JS nativo)

### Paso 3B — Modo shotgun (solo si `--shotgun` o `--variants N`)

Reemplaza al Paso 3/4 cuando el modo shotgun está activo. En vez de un solo mockup, generar **N variantes** (default 3) que exploren enfoques de diseño distintos sobre el **mismo** mapa de pantallas del Paso 2 (mismas pantallas, datos y labels reales — varía el enfoque, no el alcance). Ejemplos de ejes de variación: densidad de información (compacto vs. espacioso), patrón de navegación (sidebar vs. topbar vs. tabs), jerarquía visual, flujo de la tarea principal.

1. **Cargar preferencias de taste** (si existen): leer `docs/spec/changes/{change-id}/taste.md` y/o `docs/spec/taste.md`. Aplicar esas preferencias a todas las variantes para no repetir enfoques ya descartados.
2. **Generar N variantes**, cada una autocontenida y siguiendo todas las "Reglas de construcción" del Paso 3 (paleta neutral, datos reales, JS nativo, banner, etc.):
   ```
   docs/spec/changes/{change-id}/mockup-variant-1.html
   docs/spec/changes/{change-id}/mockup-variant-2.html
   docs/spec/changes/{change-id}/mockup-variant-N.html
   ```
   El banner de cada variante incluye su enfoque: `🔧 MOCKUP — {change-id} — Variante {k}/{N}: {enfoque} — {fecha}`.
3. **Generar board comparativo** `docs/spec/changes/{change-id}/mockup-board.html`: una página autocontenida que muestra las N variantes lado a lado en `<iframe>` (o tarjetas con captura/enlace a cada archivo), cada una con su nombre de enfoque y un resumen de 1 línea de en qué se diferencia. El board permite abrir cada variante en grande.
4. Actualizar `spec.json` (ver Paso 4) con `approvals.mockup.variants: N` además de los campos normales.

**Elección y taste:** ofrecer al usuario abrir el board (`open docs/spec/changes/{change-id}/mockup-board.html`) y pedirle que elija una variante o indique qué combinar ("la navegación de la 1 con las tablas de la 3"). Al recibir la elección:
- Consolidar la variante elegida (o el combinado) como `mockup.html`, que pasa a ser el mockup de trabajo para el ciclo de iteración normal (Paso 6).
- **Recordar el taste**: anexar a `docs/spec/changes/{change-id}/taste.md` qué enfoque/elementos prefirió y cuáles descartó, en bullets cortos, para guiar futuras iteraciones y futuros shotgun de este change.

### Paso 4 — Escribir archivo

```
docs/spec/changes/{change-id}/mockup.html
```

Actualizar `spec.json`:
- `phase: "mockup-generated"`
- `approvals.mockup.generated: true`
- `updated_at: {timestamp}`

### Paso 4B — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar el `mockup.html` creado o modificado.
Si `docs/spec/graphify-out/` no existe, invocar `/graphify docs/spec/` sin `--update`.

### Paso 5 — Presentar al usuario

**Modo shotgun:** presentar el board comparativo en vez de un único archivo (`open docs/spec/changes/{change-id}/mockup-board.html`), listar las N variantes con su enfoque, y pedir al usuario que elija una o indique qué combinar. Tras la elección, continuar con el ciclo de iteración normal (Paso 6) sobre el `mockup.html` consolidado.

**Modo normal:**

```
🖥️ Mockup generado — Iteración {N}

Archivo: docs/spec/changes/{change-id}/mockup.html
Abrir con: open docs/spec/changes/{change-id}/mockup.html

Pantallas incluidas ({N} total):
  Nivel 1 — Navegación:
    - {sección 1}
    - {sección 2}
  Nivel 2 — Vistas:
    - {sección 1}: {vista A}, {vista B}
    - {sección 2}: {vista C}
  Nivel 3 — Detalles:
    - {modal/panel 1}
    - {modal/panel 2}

¿Qué feedback tenés? Describí los cambios y genero la Iteración {N+1}.
O escribí "aprobado" para avanzar a diseño gráfico.
```

### Paso 6 — Ciclo de iteración

Si el usuario da feedback:
1. Leer el feedback detalladamente
2. Identificar qué pantallas/componentes cambiar
3. Editar `mockup.html` aplicando los cambios
4. Incrementar el número de iteración en el banner
5. Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`)
6. Volver al Paso 5

Si el usuario aprueba:
- Actualizar `spec.json`: `approvals.mockup.approved: true`
- Output:
```
✅ Mockup aprobado — Iteración {N}

Siguiente paso:
/karvey-design-graphic {change-id}
```

## Safety

- Verificar que requirements estén aprobados antes de generar
- Si el mockup tiene >20 pantallas, preguntar si dividir en módulos
- En modo shotgun, si `--variants N` pide más de 5 variantes, preguntar antes (costo/ruido); cada variante y el board deben abrir sin errores en browser moderno
- El archivo HTML debe abrir sin errores en browser moderno (Chrome/Safari/Firefox)
- No usar `document.write` ni `eval` en el JS generado


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Diseño gráfico ahora?»
- Si confirma → ejecutá `/karvey-design-graphic {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
