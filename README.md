# TPI - Supermercado CI

Trabajo Práctico Integrador: sistema de procesamiento de compras de un supermercado
con un flujo de trabajo basado en **Integración Continua** usando GitHub y GitHub Actions.

**Alumno:** Lautaro Sanfilippo

## Descripción del sistema

El sistema procesa un archivo CSV con las compras del supermercado
(`COMPRAS_supermercado.csv`, campos `PRSUC, PRCOD, PRFEC, PRPROV, PRCANT, PRPRE`)
y genera un reporte de corte de control con:

- **A) Por producto:** total de unidades e importe por cada par sucursal/producto.
- **B) Por sucursal:** total de unidades y productos de mayor/menor importe.
- **C) Total general:** cantidad de sucursales, producto más vendido e importe total.

Si el archivo de entrada no está ordenado, el programa lo ordena con
**ordenamiento burbuja** por las claves `PRSUC, PRCOD, PRFEC, PRPROV` generando un
archivo temporal. Las filas inválidas (campos faltantes, cantidades o precios no
numéricos o fuera de rango) se descartan y se informan.

Además, `algoritmos.py` implementa ordenamiento burbuja y búsqueda binaria sobre
listas de números.

## Estructura del proyecto

```text
├── .github/workflows/ci.yml   # Pipeline de CI (GitHub Actions)
├── corte_control.py            # Sistema de compras del supermercado
├── algoritmos.py               # Burbuja + búsqueda binaria
├── test_corte_control.py       # 33 tests (pytest + pytest-mock)
├── test_algoritmos.py          # 6 tests (unittest)
├── COMPRAS_supermercado.csv    # Dataset ordenado
├── COMPRAS_supermercado_desordenado_solo_sucursal.csv
└── requirements.txt            # Dependencias
```

## Cómo ejecutar el sistema

```bash
pip install -r requirements.txt
python corte_control.py
```

El programa pide el path del CSV (Enter usa el archivo por defecto) y si el
archivo ya está ordenado (`Y/N`).

## Cómo ejecutar los tests

```bash
python -m pytest -v
```

La suite tiene **39 tests** que cubren, entre otros:

- cálculo de totales (por producto, por sucursal y total general)
- producto más vendido
- validaciones de filas del CSV
- manejo de datos inválidos (no numéricos, negativos, campos vacíos/faltantes)
- ordenamiento burbuja y búsqueda binaria
- lectura/escritura de archivos y flujo principal (con mocks)

## Integración Continua

El pipeline ([.github/workflows/ci.yml](.github/workflows/ci.yml)) se ejecuta
automáticamente en cada **Pull Request** hacia `main` y en cada push a `main`:

1. Checkout del repositorio
2. Configuración de Python 3.12
3. Instalación de dependencias (`pip install -r requirements.txt`)
4. Ejecución automática de los tests (`pytest -v`)

## Protección de la rama principal

La rama `main` tiene reglas de protección configuradas:

- **Requiere Pull Request** antes de mergear (no se permite push directo,
  incluso para administradores).
- **Requiere que el check `test` de la pipeline pase** (si la pipeline falla,
  el merge queda bloqueado).
- La rama debe estar actualizada con `main` antes de mergear.
- No se permiten force-push ni borrado de la rama.

## Flujo de trabajo con Pull Requests

Cada modificación se realizó desde una rama secundaria, abriendo un PR y
esperando la ejecución automática de la pipeline:

| PR | Rama | Contenido |
|----|------|-----------|
| #1 | `feature/codigo-fuente` | Código fuente del sistema y datasets |
| #2 | `feature/unit-tests` | Pruebas unitarias y `requirements.txt` |
| #3 | `feature/pipeline-ci` | Pipeline de CI con GitHub Actions |
| #4 | `docs/readme` | Documentación completa (este README) |

### Simulación de errores

Para analizar el comportamiento de GitHub Actions ante fallos, se dejaron
**abiertos** dos PRs con modificaciones intencionales (el análisis de logs y
errores está en la descripción y comentarios de cada PR):

- **PR con tests que fallan:** un cambio en el código rompe los tests; la
  pipeline corre, `pytest` falla y GitHub bloquea el merge.
- **PR con pipeline rota:** una dependencia inexistente en `requirements.txt`
  hace fallar el paso de instalación; la pipeline ni siquiera llega a ejecutar
  los tests y el merge también queda bloqueado.

## Origen del código

El sistema y los tests fueron desarrollados originalmente en las branches
`licenciatura-lsanfilippo`, `licenciatura-lsanfilippo-paso2`,
`unit-testing-sanfilippo` y `lsanfilippo-ut-busquedas` del repositorio de la
cátedra, y adaptados para este trabajo (refactor a funciones puras testeables
y ampliación de la suite de tests).
