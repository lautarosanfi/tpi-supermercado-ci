import csv
import os
import tempfile

ARCHIVO_POR_DEFECTO = "COMPRAS_supermercado.csv"
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
CAMPOS_ORDEN = ("PRSUC", "PRCOD", "PRFEC", "PRPROV")
CAMPOS_REQUERIDOS = ("PRSUC", "PRCOD", "PRCANT", "PRPRE")


def moneda(x):
    return f"${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def resolver_path(nombre_archivo):
    nombre_archivo = nombre_archivo.strip()

    if not nombre_archivo:
        nombre_archivo = ARCHIVO_POR_DEFECTO

    if os.path.isabs(nombre_archivo):
        return nombre_archivo

    return os.path.join(DIRECTORIO_BASE, nombre_archivo)


def leer_csv(nombre_archivo):
    with open(nombre_archivo, newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        encabezado = next(lector)
        filas = [fila for fila in lector]

    return encabezado, filas


def clave_ordenacion(fila, indices):
    return tuple(fila[indice] for indice in indices)


def ordenar_burbuja(filas, indices):
    n = len(filas)

    for pasada in range(n - 1):
        hubo_cambio = False

        for i in range(n - 1 - pasada):
            if clave_ordenacion(filas[i], indices) > clave_ordenacion(filas[i + 1], indices):
                filas[i], filas[i + 1] = filas[i + 1], filas[i]
                hubo_cambio = True

        if not hubo_cambio:
            break

    return filas


def grabar_csv(nombre_archivo, encabezado, filas):
    with open(nombre_archivo, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f)
        escritor.writerow(encabezado)
        escritor.writerows(filas)


def generar_archivo_temporal_ordenado(nombre_archivo):
    encabezado, filas = leer_csv(nombre_archivo)
    indices = [encabezado.index(campo) for campo in CAMPOS_ORDEN]
    filas_ordenadas = ordenar_burbuja(filas, indices)

    archivo_temporal = tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        newline="",
        suffix=".csv",
        prefix="compras_ordenadas_",
        dir=os.path.dirname(nombre_archivo) or DIRECTORIO_BASE,
        encoding="utf-8-sig",
    )
    ruta_temporal = archivo_temporal.name
    archivo_temporal.close()

    grabar_csv(ruta_temporal, encabezado, filas_ordenadas)
    return ruta_temporal


def validar_fila(fila):
    """Valida una fila del CSV (como dict) y devuelve sus datos normalizados.

    Lanza ValueError si falta un campo requerido, si la cantidad o el precio
    no son numericos, o si tienen valores fuera de rango.
    """
    for campo in CAMPOS_REQUERIDOS:
        valor = fila.get(campo)

        if valor is None or str(valor).strip() == "":
            raise ValueError(f"Falta el campo requerido {campo}")

    try:
        cantidad = int(fila["PRCANT"])
    except (TypeError, ValueError):
        raise ValueError(f"PRCANT debe ser un numero entero: {fila['PRCANT']!r}")

    try:
        precio = float(fila["PRPRE"])
    except (TypeError, ValueError):
        raise ValueError(f"PRPRE debe ser un numero: {fila['PRPRE']!r}")

    if cantidad <= 0:
        raise ValueError(f"PRCANT debe ser mayor que cero: {cantidad}")

    if precio < 0:
        raise ValueError(f"PRPRE no puede ser negativo: {precio}")

    return {
        "sucursal": str(fila["PRSUC"]).strip(),
        "producto": str(fila["PRCOD"]).strip(),
        "cantidad": cantidad,
        "precio": precio,
        "importe": cantidad * precio,
    }


def calcular_totales(filas):
    """Acumula los totales del corte de control a partir de filas (dicts del CSV).

    Las filas invalidas se ignoran y se cuentan en 'filas_invalidas'.
    Devuelve un dict con:
      - por_producto: {(sucursal, producto): [unidades, importe]}
      - unidades_por_sucursal: {sucursal: unidades}
      - pesos_por_sucursal_producto: {sucursal: {producto: importe}}
      - total_general: importe total
      - filas_invalidas: cantidad de filas descartadas
    """
    por_producto = {}
    unidades_por_sucursal = {}
    pesos_por_sucursal_producto = {}
    total_general = 0
    filas_invalidas = 0

    for fila in filas:
        try:
            datos = validar_fila(fila)
        except ValueError:
            filas_invalidas += 1
            continue

        sucursal = datos["sucursal"]
        producto = datos["producto"]
        cantidad = datos["cantidad"]
        importe = datos["importe"]

        clave = (sucursal, producto)

        if clave not in por_producto:
            por_producto[clave] = [0, 0]

        por_producto[clave][0] += cantidad
        por_producto[clave][1] += importe

        if sucursal not in unidades_por_sucursal:
            unidades_por_sucursal[sucursal] = 0

        unidades_por_sucursal[sucursal] += cantidad

        if sucursal not in pesos_por_sucursal_producto:
            pesos_por_sucursal_producto[sucursal] = {}

        if producto not in pesos_por_sucursal_producto[sucursal]:
            pesos_por_sucursal_producto[sucursal][producto] = 0

        pesos_por_sucursal_producto[sucursal][producto] += importe

        total_general += importe

    return {
        "por_producto": por_producto,
        "unidades_por_sucursal": unidades_por_sucursal,
        "pesos_por_sucursal_producto": pesos_por_sucursal_producto,
        "total_general": total_general,
        "filas_invalidas": filas_invalidas,
    }


def producto_mas_vendido(por_producto):
    """Devuelve (producto, unidades) del producto con mas unidades vendidas.

    Suma las unidades de todas las sucursales. Lanza ValueError si no hay datos.
    """
    if not por_producto:
        raise ValueError("No hay datos para calcular el producto mas vendido")

    unidades_por_producto = {}

    for (_, producto), (unidades, _) in por_producto.items():
        if producto not in unidades_por_producto:
            unidades_por_producto[producto] = 0

        unidades_por_producto[producto] += unidades

    mas_vendido = None
    max_unidades = None

    for producto in sorted(unidades_por_producto):
        unidades = unidades_por_producto[producto]

        if max_unidades is None or unidades > max_unidades:
            max_unidades = unidades
            mas_vendido = producto

    return mas_vendido, max_unidades


def productos_extremos(pesos_por_producto):
    """Devuelve ((producto_mayor, importe_mayor), (producto_menor, importe_menor))
    segun el importe acumulado de cada producto en una sucursal.
    Lanza ValueError si no hay datos.
    """
    if not pesos_por_producto:
        raise ValueError("No hay productos para comparar")

    mayor_producto = None
    mayor_importe = None
    menor_producto = None
    menor_importe = None

    for producto in pesos_por_producto:
        importe = pesos_por_producto[producto]

        if mayor_importe is None or importe > mayor_importe:
            mayor_importe = importe
            mayor_producto = producto

        if menor_importe is None or importe < menor_importe:
            menor_importe = importe
            menor_producto = producto

    return (mayor_producto, mayor_importe), (menor_producto, menor_importe)


def solicitar_path_csv():
    while True:
        nombre_archivo = input(f"Indique el path del csv [{ARCHIVO_POR_DEFECTO}]: ")
        ruta = resolver_path(nombre_archivo)

        if os.path.isfile(ruta):
            return ruta

        print("No se encontro el archivo indicado. Intente nuevamente.")


def solicitar_si_esta_ordenado():
    while True:
        respuesta = input("El archivo esta ordenado (Y/N): ").strip().upper()

        if respuesta in {"Y", "N"}:
            return respuesta == "Y"

        print("Ingrese Y para si o N para no.")


def preparar_archivo(nombre_archivo, esta_ordenado):
    if esta_ordenado:
        return nombre_archivo, None

    ruta_temporal = generar_archivo_temporal_ordenado(nombre_archivo)
    print()
    print(f"Se genero un archivo temporal ordenado: {ruta_temporal}")
    print()
    return ruta_temporal, ruta_temporal


def corte_control(nombre_archivo):
    with open(nombre_archivo, newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        totales = calcular_totales(lector)

    por_producto = totales["por_producto"]
    unidades_por_sucursal = totales["unidades_por_sucursal"]
    pesos_por_sucursal_producto = totales["pesos_por_sucursal_producto"]

    if not por_producto:
        print()
        print("El archivo no contiene registros para procesar.")
        print()
        return

    if totales["filas_invalidas"]:
        print()
        print(f"Atencion: se descartaron {totales['filas_invalidas']} filas invalidas.")

    ancho_sucursal = max(len("Sucursal"), max(len(str(s)) for s in unidades_por_sucursal))
    ancho_producto = max(len("Producto"), max(len(str(clave[1])) for clave in por_producto))

    print()
    print("=" * 90)
    print("A) POR PRODUCTO".center(90))
    print("=" * 90)
    print(
        f'{"Sucursal":<{ancho_sucursal}}   '
        f'{"Producto":<{ancho_producto}}   '
        f'{"TOTUNI":>10}   '
        f'{"TOTPES":>16}'
    )
    print("-" * 90)

    for clave in sorted(por_producto):
        sucursal, producto = clave
        totuni = por_producto[clave][0]
        totpes = por_producto[clave][1]

        print(
            f'{sucursal:<{ancho_sucursal}}   '
            f'{producto:<{ancho_producto}}   '
            f'{totuni:>10}   '
            f'{moneda(totpes):>16}'
        )

    print()
    print("=" * 90)
    print("B) POR SUCURSAL".center(90))
    print("=" * 90)

    for sucursal in sorted(unidades_por_sucursal):
        productos = pesos_por_sucursal_producto[sucursal]
        (mayor_producto, mayor_importe), (menor_producto, menor_importe) = productos_extremos(productos)

        print("-" * 90)
        print(f"Sucursal:           {sucursal}")
        print(f"Total unidades:     {unidades_por_sucursal[sucursal]}")
        print(f"Producto mayor:     {mayor_producto}")
        print(f"Importe mayor:      {moneda(mayor_importe)}")
        print(f"Producto menor:     {menor_producto}")
        print(f"Importe menor:      {moneda(menor_importe)}")

    mas_vendido, unidades_mas_vendido = producto_mas_vendido(por_producto)

    print()
    print("=" * 90)
    print("C) TOTAL GENERAL".center(90))
    print("=" * 90)
    print(f"Cantidad sucursales: {len(unidades_por_sucursal)}")
    print(f"Producto mas vendido: {mas_vendido} ({unidades_mas_vendido} unidades)")
    print(f"Importe total:       {moneda(totales['total_general'])}")
    print("=" * 90)
    print()


def main():
    nombre_archivo = solicitar_path_csv()
    esta_ordenado = solicitar_si_esta_ordenado()
    archivo_a_procesar, archivo_temporal = preparar_archivo(nombre_archivo, esta_ordenado)

    try:
        corte_control(archivo_a_procesar)
    finally:
        if archivo_temporal and os.path.exists(archivo_temporal):
            os.remove(archivo_temporal)
            print(f"Se elimino el archivo temporal: {archivo_temporal}")


if __name__ == "__main__":
    main()
