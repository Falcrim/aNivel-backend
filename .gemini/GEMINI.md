# aNivel Backend — Guía de Arquitectura, Dominio y Estándares de Ingeniería

Este documento es la referencia técnica oficial del backend de **aNivel** (Django 6 + Django REST Framework + PostgreSQL). Define la estructura, reglas de negocio, endpoints y convenciones para optimizar el desarrollo y futuras auditorías.

---

## 1. Stack Tecnológico & Convenciones Generales

- **Framework:** Python 3.14+, Django 6.x, Django REST Framework (DRF).
- **Base de Datos:** PostgreSQL (con nombres de tabla explícitos en `Meta.db_table`).
- **Idioma del Código:**
  - Código, variables, métodos, clases y rutas: **Inglés**.
  - Textos de cara al usuario (`verbose_name`, `help_text`, mensajes de validación y errores): **Español**.
- **Auditoría:** Todos los modelos heredan de `TimeStampedModel` (`created_at`, `updated_at`).

---

## 2. Estructura y Capas de la Aplicación

```
aNivel-backend/
├── anivel_back/             # Configuración global (settings.py, urls.py raíz, wsgi.py)
├── core/                    # Módulo central y entidades maestras
│   ├── models/              # Project, Category, Subcategory, UnitOfMeasure, PurchaseUnit
│   ├── serializers/         # Serializers de lectura y escritura
│   ├── api/                 # ViewSets y URLs (/api/core/)
│   └── tests/               # Pruebas unitarias de modelos y endpoints core
└── materials/               # Módulo de materiales y presupuestos de obra
    ├── models/              # MaterialCatalogItem, MaterialBudgetItem (Snapshot)
    ├── serializers/         # Separación ReadSerializer / WriteSerializer / Action DTOs
    ├── api/                 # ViewSets, filtros y acciones personalizadas (/api/materials/)
    └── tests/               # Pruebas de snapshots, fórmulas matemáticas y endpoints
```

### Regla de Capas en cada App:
1. `models/`: Definición de entidad, constraints, índices (`db_index=True`, `indexes=[models.Index(...)]`) y validaciones en `clean()`.
2. `serializers/`:
   - `ReadSerializer`: Anida detalles de relaciones (`project_detail`, `subcategory_detail`, `unit_measure_detail`, `unit_purchase_detail`).
   - `WriteSerializer`: Plano y eficiente para operaciones CRUD.
3. `api/viewsets`: Controladores delgados (*thin controllers*), optimización con `.select_related()` para evitar problemas **N+1**, y selección dinámica de serializer con `get_serializer_class()`.

---

## 3. Dominio del Negocio y Reglas de Presupuesto

### 3.1. Estructura Jerárquica (`core`)
- **`Project`:** Obra o proyecto de construcción.
- **`Category`:** Categoría mayor de costos (*Materiales*, *Mano de Obra*, *Gastos Generales*).
- **`Subcategory`:** Agrupación de segundo nivel (*Fierros*, *Cementos*, *Pinturas* dentro de Materiales).
- **`UnitOfMeasure`:** Unidad técnica de medida en obra (*ml*, *m2*, *m3*, *kg*, *pza*).
- **`PurchaseUnit`:** Unidad comercial de compra (*barra*, *bolsa*, *tubo*, *rollo*, *balde*, *Gbl*).

### 3.2. Catálogo Maestro vs. Presupuesto por Obra (`materials`)
- **`MaterialCatalogItem` (Inventario Global):** Plantilla maestra reutilizable con factor de conversión, merma sugerida y precio referencial.
- **`MaterialBudgetItem` (Snapshot de Obra):**
  - **Patrón Snapshot:** Al incorporar un material a una obra, se congelan todos sus valores en un registro independiente.
  - Los cambios en la obra no modifican el catálogo maestro; las modificaciones posteriores en el catálogo maestro no alteran presupuestos ya creados.

### 3.3. Fórmulas Matemáticas del Backend:
1. **Ítem Normal (`is_global=False`):**
   - Cantidad Neta: $\text{cantidad\_neta} = \text{quantity\_obra} \times (1 + \text{waste\_pct})$
   - **Compra Requerida (Redondeo hacia arriba obligatorio):**
     $$\text{quantity\_purchase} = \left\lceil \frac{\text{cantidad\_neta}}{\text{conversion\_factor}} \right\rceil \quad (\text{math.ceil})$$
2. **Ítem Global (`is_global=True`):** Compras en paquete directo por `quantity_purchase` y `price_per_purchase_unit` (`quantity_obra = None`, `waste_pct = 0`).
3. **Ítem Personalizado (`catalog_item = None`):** Creado directamente dentro de la obra sin existencia previa en catálogo.

---

## 4. Cheat Sheet de Endpoints (Rutas API)

### Core (`/api/core/`)
- `GET / POST` `/api/core/projects/` $\to$ Listar / Crear Obras
- `GET / PUT / DELETE` `/api/core/projects/{id}/` $\to$ Detalle / Modificar / Eliminar Obra
- `GET / POST` `/api/core/categories/` $\to$ Listar / Crear Categorías
- `GET / POST` `/api/core/subcategories/?category={id}` $\to$ Listar / Crear Subcategorías
- `GET / POST` `/api/core/units-of-measure/` $\to$ Unidades de Medida
- `GET / POST` `/api/core/purchase-units/` $\to$ Unidades de Compra

### Materials (`/api/materials/`)
- `GET / POST` `/api/materials/catalog/` $\to$ Catálogo Maestro de Materiales
- `GET` `/api/materials/catalog/grouped-by-subcategory/` $\to$ Catálogo agrupado para vistas rápidas
- `GET` `/api/materials/budget/by-project/?project_id={id}` $\to$ Presupuesto de obra agrupado con subtotales
- `GET` `/api/materials/budget/summary/?project_id={id}` $\to$ Métricas y totales consolidados (costo, peso kg)
- `POST` `/api/materials/budget/from-catalog/` $\to$ Vincular ítem de catálogo con cómputo de obra
- `POST` `/api/materials/budget/from-catalog-global/` $\to$ Vincular ítem global en paquete cerrado
- `POST` `/api/materials/budget/custom/` $\to$ Crear ítem personalizado ad-hoc

---

## 5. Comandos de Verificación Rápida

```bash
# Ejecutar suite de pruebas de Django
python manage.py test

# Verificar migraciones pendientes o inconsistencias
python manage.py check

# Iniciar servidor de desarrollo
python manage.py runserver
```
