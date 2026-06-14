---
name: karvey-design-graphic
description: Define the graphic design specification for an approved mockup. Uses impeccable-inspired design laws to establish color system, typography, layout, and motion. Updates the mockup HTML with the visual system. Triggers include "karvey design-graphic", "diseño gráfico", "especificación visual", "sistema de diseño".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Design Graphic

## Propósito

Con el mockup aprobado como wireframe estructural, definir la especificación completa del diseño visual: color, tipografía, layout, motion y micro-interacciones. Actualizar el mockup HTML con el sistema visual definido.

## Pasos de ejecución

### Paso 1 — Cargar contexto

Leer:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/mockup.html`
- `docs/spec/changes/{change-id}/proposal.md`

Verificar `approvals.mockup.approved = true`. Si no, detener.

Buscar si existe `PRODUCT.md` o `DESIGN.md` en el proyecto para entender el brand existente.

### Paso 2 — Identificar el registro de diseño

Determinar el tipo de producto:

**Producto empresarial (B2B, herramienta interna):**
- Paleta contenida, funcionalidad sobre expresividad
- Tipografía de alta legibilidad
- Motion mínimo y no distractor
- Densidad de información alta

**Producto de consumo (B2C, experiencia de usuario):**
- Paleta más expresiva y de marca
- Tipografía con más personalidad
- Motion como parte de la experiencia
- Densidad de información moderada

Inferir del `proposal.md` y `spec.json.capability`.

**Agnosticismo de target (NO asumir web).** La guía de diseño depende del target declarado en `docs/spec/project.json` (ver `karvey/rules/targets.md`):

- **web** → **WCAG** (contraste, foco, semántica, navegación por teclado)
- **iOS** → **Apple Human Interface Guidelines (HIG)** (tipografía Dynamic Type, safe areas, gestos, controles nativos)
- **Android** → **Material Design** (elevación, componentes Material, touch targets, theming)
- **desktop** → convenciones de escritorio (densidad, menús, ventanas, atajos del SO)
- **cli/terminal** → convenciones de terminal (ancho de columnas, color ANSI, legibilidad monoespaciada, sin asumir GUI)

Las dimensiones de color, tipografía, layout y motion de los pasos siguientes se interpretan según la guía del target. Si el proyecto tiene varios targets, definir el sistema visual para cada uno respetando su guía. Ninguna fase asume "web" por defecto.

### Paso 3 — Definir sistema de color (OKLCH)

Elegir estrategia de paleta:

**Restrained (recomendado para B2B):**
- 1 color de acento, el resto neutros
- Acento: `oklch(55% 0.18 {hue})`
- Neutros: escala de grays `oklch(98% 0 0)` → `oklch(15% 0 0)`

**Committed:**
- 1 color primario + 1 de apoyo
- Primario: `oklch(50% 0.20 {hue})`
- Apoyo: `oklch(55% 0.15 {hue complementario})`

**Full palette:**
- Color primario, secundario, acento y semánticos
- Apropiado para productos con roles visuales diferenciados

Definir siempre:
- `--color-primary`: acción principal, CTA
- `--color-surface`: fondo de tarjetas/paneles
- `--color-background`: fondo de página
- `--color-border`: bordes sutiles
- `--color-text-primary`: texto principal
- `--color-text-secondary`: texto de apoyo
- `--color-semantic-success`: `oklch(62% 0.17 145)`
- `--color-semantic-error`: `oklch(55% 0.22 25)`
- `--color-semantic-warning`: `oklch(75% 0.18 80)`

### Paso 4 — Definir tipografía

Elegir 1-2 fuentes de Google Fonts (o system fonts para B2B):

**Para B2B empresarial:**
- Display/heading: Inter, DM Sans, o system-ui
- Body: misma familia, distintos pesos

**Para B2C:**
- Display: fuente con carácter (Fraunces, Instrument Serif, Plus Jakarta Sans)
- Body: fuente de alta legibilidad (Inter, DM Sans)

Escala tipográfica:
```
--text-xs:   0.75rem / 1rem
--text-sm:   0.875rem / 1.25rem
--text-base: 1rem / 1.5rem
--text-lg:   1.125rem / 1.75rem
--text-xl:   1.25rem / 1.75rem
--text-2xl:  1.5rem / 2rem
--text-3xl:  1.875rem / 2.25rem
```

### Paso 5 — Definir layout y spacing

Sistema de espaciado base 4px:
```
--space-1: 4px   --space-2: 8px   --space-3: 12px
--space-4: 16px  --space-6: 24px  --space-8: 32px
--space-12: 48px --space-16: 64px --space-24: 96px
```

Grid del producto:
- Sidebar: fijo 240px (o 64px colapsado)
- Content area: fluid con max-width según densidad
- Columnas de contenido: 12 columnas con gap de 24px

Border radius:
```
--radius-sm: 4px   --radius-md: 8px
--radius-lg: 12px  --radius-xl: 16px  --radius-full: 9999px
```

### Paso 6 — Definir motion

Para B2B: motion funcional, no decorativo
```css
--duration-fast: 100ms
--duration-base: 200ms
--duration-slow: 300ms
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1)
--ease-enter: cubic-bezier(0, 0, 0.2, 1)
--ease-exit: cubic-bezier(0.4, 0, 1, 1)
```

Regla: usar `--duration-fast` para feedback, `--duration-base` para transiciones, `--duration-slow` para overlays.

### Paso 7 — Verificar anti-patrones prohibidos

Antes de escribir el design-spec, confirmar que el sistema NO incluye:
- ❌ Side-stripe borders decorativos (borde de color solo en un lado de tarjetas)
- ❌ Gradient text (texto con gradiente de color)
- ❌ Glassmorphism decorativo (blur/transparencia sin función)
- ❌ Card grids con todas las tarjetas idénticas sin variación de énfasis
- ❌ Hero metrics (número grande en el centro de una pantalla como único contenido)
- ❌ Fondos con patrones de ruido o textura excesiva
- ❌ Animaciones de más de 500ms en interacciones frecuentes

### Paso 7B — Scoring de diseño 0-10 por dimensiones

Antes de cerrar el sistema visual, evaluar el design-spec/mockup con una **calificación 0-10 por cada dimensión de diseño relevante**. Las dimensiones se interpretan según la guía del target (Paso 2): WCAG para web, HIG para iOS, Material para Android, convenciones de escritorio/terminal según corresponda. No todas las dimensiones aplican a todos los targets (ej. "color/contraste" en una CLI se evalúa sobre color ANSI; "motion" puede no aplicar en terminal).

Dimensiones sugeridas (ajustar al target):

- **Jerarquía visual** — el ojo encuentra primero lo importante; énfasis claro entre primario/secundario/terciario
- **Tipografía** — escala coherente, pesos con propósito, legibilidad; en iOS respeta Dynamic Type, en CLI legibilidad monoespaciada
- **Color / contraste** — paleta intencional; contraste suficiente (WCAG AA/AAA en web; equivalente del target)
- **Espaciado / ritmo** — sistema base consistente, agrupación por proximidad, respiración visual
- **Consistencia** — tokens reutilizados, componentes uniformes, sin valores ad-hoc
- **Accesibilidad** — foco visible, navegación por teclado, targets táctiles, semántica; según checklist de la plataforma
- **Motion** — funcional y no distractor, duraciones razonables, respeta `prefers-reduced-motion` (o equivalente del target)

Para **cada dimensión**:

1. Asignar una **calificación 0-10**.
2. **Explicar explícitamente qué sería un 10** en esa dimensión para este diseño y target (la barra concreta de excelencia, no genérica).
3. Indicar **qué falta para llegar al 10** desde la calificación actual (gap accionable).

Tabla de scoring:

| Dimensión | Nota (0-10) | Qué sería un 10 | Qué falta para llegar |
|-----------|-------------|-----------------|-----------------------|
| Jerarquía visual | | | |
| Tipografía | | | |
| Color / contraste | | | |
| Espaciado / ritmo | | | |
| Consistencia | | | |
| Accesibilidad | | | |
| Motion | | | |

**Umbral aceptable:** promedio ≥ 8 y ninguna dimensión < 7. Si no se alcanza, **iterar el design-spec/mockup** (volver a los pasos 3-6 según la dimensión floja) y re-evaluar. Repetir hasta cumplir el umbral o hasta que el gap restante sea una decisión consciente de alcance documentada en el design-spec.

### Paso 8 — Escribir design-spec.md

```markdown
# Design Spec: {change-id}

## Registro de diseño
{B2B empresarial | B2C consumo} — {justificación}

## Sistema de color (OKLCH)
Estrategia: {Restrained | Committed | Full palette}

| Token | Valor OKLCH | Uso |
|-------|-------------|-----|
| --color-primary | oklch(...) | {uso} |
| --color-surface | oklch(...) | {uso} |
...

## Tipografía
| Token | Fuente | Peso | Uso |
|-------|--------|------|-----|
| Heading | {fuente} | 600-700 | Títulos de página y sección |
| Body | {fuente} | 400-500 | Texto de contenido |
| Caption | {fuente} | 400 | Metadatos, labels |

## Escala tipográfica
(tabla completa)

## Layout
- Sidebar: {fijo N px | colapsable | sin sidebar}
- Grid: {descripción}
- Max-width content: {N px}

## Spacing
(tabla base 4px)

## Border radius
(tabla)

## Motion
(tabla de variables)

## Componentes clave y su tratamiento visual
| Componente | Superficie | Borde | Shadow | Estado hover |
|------------|-----------|-------|--------|--------------|
| Botón primario | | | | |
| Botón secundario | | | | |
| Tarjeta de datos | | | | |
| Input de formulario | | | | |
| Row de tabla | | | | |
| Modal overlay | | | | |

## Anti-patrones evitados
(lista de los que se verificaron)

## Scoring de diseño (0-10 por dimensión)
Target evaluado: {web (WCAG) | iOS (HIG) | Android (Material) | desktop | cli/terminal}

| Dimensión | Nota (0-10) | Qué sería un 10 | Qué falta para llegar |
|-----------|-------------|-----------------|-----------------------|
| Jerarquía visual | | | |
| Tipografía | | | |
| Color / contraste | | | |
| Espaciado / ritmo | | | |
| Consistencia | | | |
| Accesibilidad | | | |
| Motion | | | |

Promedio: {N}/10 — Umbral (≥8, ninguna <7): {cumple | no cumple}
Iteraciones realizadas: {N} — Gaps aceptados conscientemente: {descripción o "ninguno"}
```

Escribir a `docs/spec/changes/{change-id}/design-spec.md`.

### Paso 9 — Actualizar mockup.html con el sistema visual

Editar `mockup.html` para:
1. Agregar las CSS custom properties (`:root { --color-primary: ...; ... }`)
2. Reemplazar colores hardcodeados por las variables
3. Agregar la fuente vía `@import` de Google Fonts
4. Aplicar el sistema de motion a transiciones existentes
5. Actualizar el banner: `🎨 MOCKUP CON DISEÑO GRÁFICO — {change-id} — {fecha}`

### Paso 9B — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar `design-spec.md` y el `mockup.html` actualizado.
Si `docs/spec/graphify-out/` no existe, invocar `/graphify docs/spec/` sin `--update`.

### Paso 10 — Output

```
✅ Design spec generada

Archivos creados/actualizados:
  - docs/spec/changes/{change-id}/design-spec.md
  - docs/spec/changes/{change-id}/mockup.html (actualizado con sistema visual)

Sistema de diseño:
  - Registro: {B2B/B2C}
  - Estrategia de color: {nombre}
  - Tipografía: {fuente(s)}
  - Anti-patrones verificados: ✅
  - Scoring de diseño: {N}/10 promedio (umbral ≥8, ninguna <7) — {cumple | no cumple}

Actualizar spec.json: approvals.design_graphic = true

Siguiente paso:
/karvey-architecture {change-id}
```

Actualizar `spec.json`: `approvals.design_graphic.approved: true`, `phase: "design-graphic-approved"`.


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Arquitectura ahora?»
- Si confirma → ejecutá `/karvey-architecture {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
