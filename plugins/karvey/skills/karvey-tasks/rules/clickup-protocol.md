# ClickUp Protocol — Método Karvey

## Credenciales — `.connections.json`

Las credenciales se guardan en `.connections.json` en la raíz del proyecto. **Este archivo NUNCA se sube al repositorio.**

### Setup inicial (si no existe)

Si `.connections.json` no existe en el proyecto, crearlo con esta estructura y agregar al `.gitignore`:

```bash
# Agregar a .gitignore
echo ".connections.json" >> .gitignore
```

```json
{
  "clickup": {
    "api_key": "YOUR_CLICKUP_API_KEY",
    "user_id": "YOUR_CLICKUP_USER_ID",
    "workspace_id": "YOUR_WORKSPACE_ID"
  }
}
```

> Indicar al usuario que complete los valores reales en `.connections.json` localmente antes de continuar.

### Leer credenciales en bash

```bash
API_KEY=$(python3 -c "import json; print(json.load(open('.connections.json'))['clickup']['api_key'])")
USER_ID=$(python3 -c "import json; print(json.load(open('.connections.json'))['clickup']['user_id'])")
WORKSPACE_ID=$(python3 -c "import json; print(json.load(open('.connections.json'))['clickup']['workspace_id'])")
```

## Estructura WBS: Epic > Feature > Task

```
E{n} Nombre del Epic
├── E{n}.F{n} Nombre del Feature
│   ├── E{n}.F{n}.T{n} [BD] Descripción
│   ├── E{n}.F{n}.T{n} [Backend] Descripción
│   └── E{n}.F{n}.T{n} [Frontend] Descripción
```

### Capas válidas
| Etiqueta | Agente |
|---|---|
| `[BD]` | Base de datos (SPs, migraciones, queries) |
| `[Backend]` | Lógica de servidor (API, servicios, funciones) |
| `[Frontend]` | Vue/React/UI |
| `[Infra]` | Docker, pipelines, infra |
| `[Test]` | Testing y QA |

## Operaciones MCP

### Crear Epic
```
clickup_create_task
  name: "E{n} {Nombre del Epic}"
  list_id: "{BACKLOG_LIST_ID}"
  task_type: "Epic"
  description: (ver template epic)
  tags: ["{cliente}"]
  priority: "normal"
```

### Crear Feature
```
clickup_create_task
  name: "E{n}.F{n} {Nombre del Feature}"
  list_id: "{BACKLOG_LIST_ID}"
  task_type: "Feature"
  description: (ver template feature)
  tags: ["{cliente}"]
```

### Crear Task
```
clickup_create_task
  name: "E{n}.F{n}.T{n} [Capa] {Descripción}"
  list_id: "{BACKLOG_LIST_ID}"
  description: (ver template task)
  tags: ["{cliente}"]
  priority: "normal"
  start_date: "YYYY-MM-DD"
  due_date: "YYYY-MM-DD"
```
> NOTA: `time_estimate` NO funciona en MCP. Siempre actualizar via REST API después de crear.

## Operaciones REST API

### Crear dependencia (task A espera a task B)
```bash
curl -s -X POST "https://api.clickup.com/api/v2/task/{A}/dependency" \
  -H "Authorization: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"depends_on":"{B}"}'
```

### Agregar task al Sprint activo
```bash
curl -s -X POST "https://api.clickup.com/api/v2/list/{SPRINT_LIST_ID}/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" \
  -H "Content-Type: application/json"
```

### Actualizar time_estimate (OBLIGATORIO, MCP no lo guarda)
```bash
curl -s -X PUT "https://api.clickup.com/api/v2/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"time_estimate": {MS}}'
```

### Conversión horas → ms
| Tiempo | Ms |
|---|---|
| 10min | 600,000 |
| 15min | 900,000 |
| 20min | 1,200,000 |
| 30min | 1,800,000 |
| 1h | 3,600,000 |
| 2h | 7,200,000 |

## Flujo de estados
```
to do → in progress → listo! para pap → complete
```

### Al iniciar task
```
clickup_update_task(task_id, status="in progress")
clickup_start_time_tracking(task_id)
```

### Al completar task
```
clickup_stop_time_tracking()
clickup_create_task_comment(task_id, "RESUMEN:\n- qué se hizo\n- archivos modificados\n- resultado: OK")
clickup_update_task(task_id, status="listo! para pap")
```

### Cascada de estados
- Cuando TODAS las tasks de un Feature → Feature a "listo! para pap"
- Cuando TODOS los Features de un Epic → Epic a "listo! para pap"
- Un Feature solo cambia cuando TODAS las capas (BD+Backend+Frontend) están listas

## Backlogs por proyecto

Los List IDs son específicos de cada workspace. Obtenerlos con:
```
clickup_get_workspace_hierarchy
  max_depth: 3
```
Buscar el folder del proyecto y copiar el `list_id` del backlog correspondiente.

| Proyecto | List ID |
|---|---|
| {Proyecto 1} | `YOUR_BACKLOG_LIST_ID` |
| {Proyecto 2} | `YOUR_BACKLOG_LIST_ID` |

## Sprint activo

Verificar antes de cada registro:
```
clickup_get_list
  list_name: "Sprint XX"
```
Buscar en el folder de sprints del workspace (ej. "Dev Sprints").
