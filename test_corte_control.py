from pathlib import Path

import pytest

import corte_control


def crear_csv(path, filas):
    contenido = "\n".join(
        [
            "PRSUC,PRCOD,PRFEC,PRPROV,PRCANT,PRPRE",
            *filas,
        ]
    )
    path.write_text(contenido + "\n", encoding="utf-8")


def fila_valida(**cambios):
    fila = {
        "PRSUC": "SUC01",
        "PRCOD": "P100",
        "PRFEC": "2025-01-01",
        "PRPROV": "PROV01",
        "PRCANT": "2",
        "PRPRE": "10",
    }
    fila.update(cambios)
    return fila


# ---------------------------------------------------------------------------
# Formato de moneda
# ---------------------------------------------------------------------------

def test_moneda_formatea_numero_con_pesos_y_decimales():
    assert corte_control.moneda(1234.5) == "$1.234,50"


# ---------------------------------------------------------------------------
# Validaciones (validar_fila)
# ---------------------------------------------------------------------------

def test_validar_fila_devuelve_datos_normalizados():
    resultado = corte_control.validar_fila(fila_valida())

    assert resultado == {
        "sucursal": "SUC01",
        "producto": "P100",
        "cantidad": 2,
        "precio": 10.0,
        "importe": 20.0,
    }


def test_validar_fila_rechaza_campo_faltante():
    fila = fila_valida()
    del fila["PRSUC"]

    with pytest.raises(ValueError, match="Falta el campo requerido PRSUC"):
        corte_control.validar_fila(fila)


def test_validar_fila_rechaza_campo_vacio():
    with pytest.raises(ValueError, match="Falta el campo requerido PRCOD"):
        corte_control.validar_fila(fila_valida(PRCOD="   "))


def test_validar_fila_rechaza_cantidad_no_numerica():
    with pytest.raises(ValueError, match="PRCANT debe ser un numero entero"):
        corte_control.validar_fila(fila_valida(PRCANT="abc"))


def test_validar_fila_rechaza_precio_no_numerico():
    with pytest.raises(ValueError, match="PRPRE debe ser un numero"):
        corte_control.validar_fila(fila_valida(PRPRE="caro"))


def test_validar_fila_rechaza_cantidad_negativa_o_cero():
    with pytest.raises(ValueError, match="PRCANT debe ser mayor que cero"):
        corte_control.validar_fila(fila_valida(PRCANT="0"))

    with pytest.raises(ValueError, match="PRCANT debe ser mayor que cero"):
        corte_control.validar_fila(fila_valida(PRCANT="-3"))


def test_validar_fila_rechaza_precio_negativo():
    with pytest.raises(ValueError, match="PRPRE no puede ser negativo"):
        corte_control.validar_fila(fila_valida(PRPRE="-1.5"))


# ---------------------------------------------------------------------------
# Calculo de totales (calcular_totales)
# ---------------------------------------------------------------------------

def test_calcular_totales_acumula_por_producto_sucursal_y_general():
    filas = [
        fila_valida(PRSUC="SUC01", PRCOD="P100", PRCANT="2", PRPRE="10"),
        fila_valida(PRSUC="SUC01", PRCOD="P100", PRCANT="3", PRPRE="10"),
        fila_valida(PRSUC="SUC01", PRCOD="P200", PRCANT="1", PRPRE="100"),
        fila_valida(PRSUC="SUC02", PRCOD="P100", PRCANT="4", PRPRE="5"),
    ]

    totales = corte_control.calcular_totales(filas)

    assert totales["por_producto"] == {
        ("SUC01", "P100"): [5, 50.0],
        ("SUC01", "P200"): [1, 100.0],
        ("SUC02", "P100"): [4, 20.0],
    }
    assert totales["unidades_por_sucursal"] == {"SUC01": 6, "SUC02": 4}
    assert totales["pesos_por_sucursal_producto"] == {
        "SUC01": {"P100": 50.0, "P200": 100.0},
        "SUC02": {"P100": 20.0},
    }
    assert totales["total_general"] == 170.0
    assert totales["filas_invalidas"] == 0


def test_calcular_totales_descarta_y_cuenta_filas_invalidas():
    filas = [
        fila_valida(PRCANT="2", PRPRE="10"),
        fila_valida(PRCANT="no-numerico"),
        fila_valida(PRPRE="-5"),
    ]

    totales = corte_control.calcular_totales(filas)

    assert totales["total_general"] == 20.0
    assert totales["filas_invalidas"] == 2


def test_calcular_totales_sin_filas_devuelve_estructuras_vacias():
    totales = corte_control.calcular_totales([])

    assert totales["por_producto"] == {}
    assert totales["total_general"] == 0
    assert totales["filas_invalidas"] == 0


# ---------------------------------------------------------------------------
# Producto mas vendido y extremos por importe
# ---------------------------------------------------------------------------

def test_producto_mas_vendido_suma_unidades_de_todas_las_sucursales():
    por_producto = {
        ("SUC01", "P100"): [5, 50.0],
        ("SUC02", "P100"): [4, 20.0],
        ("SUC01", "P200"): [8, 800.0],
    }

    assert corte_control.producto_mas_vendido(por_producto) == ("P100", 9)


def test_producto_mas_vendido_sin_datos_lanza_error():
    with pytest.raises(ValueError, match="No hay datos"):
        corte_control.producto_mas_vendido({})


def test_productos_extremos_devuelve_mayor_y_menor_importe():
    pesos = {"P100": 50.0, "P200": 100.0, "P300": 10.0}

    mayor, menor = corte_control.productos_extremos(pesos)

    assert mayor == ("P200", 100.0)
    assert menor == ("P300", 10.0)


def test_productos_extremos_sin_datos_lanza_error():
    with pytest.raises(ValueError, match="No hay productos"):
        corte_control.productos_extremos({})


# ---------------------------------------------------------------------------
# Manejo de archivos
# ---------------------------------------------------------------------------

def test_resolver_path_usa_archivo_por_defecto_si_no_recibe_nombre(tmp_path, mocker):
    mocker.patch.object(corte_control, "DIRECTORIO_BASE", str(tmp_path))

    resultado = corte_control.resolver_path("   ")

    assert resultado == str(tmp_path / corte_control.ARCHIVO_POR_DEFECTO)


def test_resolver_path_devuelve_absoluto_sin_modificar(tmp_path):
    archivo = tmp_path / "compras.csv"

    resultado = corte_control.resolver_path(str(archivo))

    assert resultado == str(archivo)


def test_resolver_path_convierte_relativo_en_path_del_directorio_base(tmp_path, mocker):
    mocker.patch.object(corte_control, "DIRECTORIO_BASE", str(tmp_path))

    resultado = corte_control.resolver_path("datos.csv")

    assert resultado == str(tmp_path / "datos.csv")


def test_leer_csv_devuelve_encabezado_y_filas(tmp_path):
    archivo = tmp_path / "datos.csv"
    crear_csv(archivo, ["SUC02,P200,2025-01-01,PROV01,3,10.5"])

    encabezado, filas = corte_control.leer_csv(str(archivo))

    assert encabezado == ["PRSUC", "PRCOD", "PRFEC", "PRPROV", "PRCANT", "PRPRE"]
    assert filas == [["SUC02", "P200", "2025-01-01", "PROV01", "3", "10.5"]]


def test_grabar_csv_crea_archivo_con_encabezado_y_filas(tmp_path):
    archivo = tmp_path / "salida.csv"
    encabezado = ["PRSUC", "PRCOD"]
    filas = [["SUC01", "P100"], ["SUC02", "P200"]]

    corte_control.grabar_csv(str(archivo), encabezado, filas)

    assert archivo.exists()
    assert corte_control.leer_csv(str(archivo)) == (encabezado, filas)


# ---------------------------------------------------------------------------
# Ordenamiento
# ---------------------------------------------------------------------------

def test_clave_ordenacion_devuelve_los_campos_pedidos():
    fila = ["SUC02", "P200", "2025-01-01", "PROV01", "3", "10.5"]

    resultado = corte_control.clave_ordenacion(fila, [0, 1, 3])

    assert resultado == ("SUC02", "P200", "PROV01")


def test_ordenar_burbuja_ordena_por_multiples_columnas():
    filas = [
        ["SUC02", "P100", "2025-01-03", "PROV01"],
        ["SUC01", "P200", "2025-01-02", "PROV01"],
        ["SUC01", "P100", "2025-01-01", "PROV02"],
    ]

    resultado = corte_control.ordenar_burbuja(filas, [0, 1, 2, 3])

    assert resultado == [
        ["SUC01", "P100", "2025-01-01", "PROV02"],
        ["SUC01", "P200", "2025-01-02", "PROV01"],
        ["SUC02", "P100", "2025-01-03", "PROV01"],
    ]


def test_generar_archivo_temporal_ordenado_crea_csv_ordenado(tmp_path):
    archivo = tmp_path / "entrada.csv"
    crear_csv(
        archivo,
        [
            "SUC02,P100,2025-01-03,PROV01,1,10",
            "SUC01,P200,2025-01-02,PROV01,1,10",
            "SUC01,P100,2025-01-01,PROV02,1,10",
        ],
    )

    temporal = corte_control.generar_archivo_temporal_ordenado(str(archivo))

    try:
        encabezado, filas = corte_control.leer_csv(temporal)
        assert Path(temporal).exists()
        assert encabezado == ["PRSUC", "PRCOD", "PRFEC", "PRPROV", "PRCANT", "PRPRE"]
        assert filas[0][:4] == ["SUC01", "P100", "2025-01-01", "PROV02"]
        assert filas[1][:4] == ["SUC01", "P200", "2025-01-02", "PROV01"]
        assert filas[2][:4] == ["SUC02", "P100", "2025-01-03", "PROV01"]
    finally:
        Path(temporal).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Interaccion con el usuario
# ---------------------------------------------------------------------------

def test_solicitar_path_csv_reintenta_hasta_encontrar_archivo(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["no_existe.csv", "ok.csv"])
    mocker.patch.object(corte_control, "resolver_path", side_effect=["/tmp/no", "/tmp/ok"])
    mocker.patch.object(corte_control.os.path, "isfile", side_effect=[False, True])

    resultado = corte_control.solicitar_path_csv()

    assert resultado == "/tmp/ok"
    assert "No se encontro el archivo indicado" in capsys.readouterr().out


def test_solicitar_si_esta_ordenado_retorna_true_con_y(mocker):
    mocker.patch("builtins.input", return_value="y")

    resultado = corte_control.solicitar_si_esta_ordenado()

    assert resultado is True


def test_solicitar_si_esta_ordenado_reintenta_si_respuesta_es_invalida(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["tal vez", "N"])

    resultado = corte_control.solicitar_si_esta_ordenado()

    assert resultado is False
    assert "Ingrese Y para si o N para no" in capsys.readouterr().out


def test_preparar_archivo_devuelve_original_si_ya_esta_ordenado(mocker):
    generar_temporal = mocker.patch.object(corte_control, "generar_archivo_temporal_ordenado")

    resultado = corte_control.preparar_archivo("entrada.csv", True)

    assert resultado == ("entrada.csv", None)
    generar_temporal.assert_not_called()


def test_preparar_archivo_genera_temporal_si_no_esta_ordenado(mocker, capsys):
    mocker.patch.object(
        corte_control,
        "generar_archivo_temporal_ordenado",
        return_value="temporal.csv",
    )

    resultado = corte_control.preparar_archivo("entrada.csv", False)

    assert resultado == ("temporal.csv", "temporal.csv")
    assert "Se genero un archivo temporal ordenado" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Reporte completo (corte_control)
# ---------------------------------------------------------------------------

def test_corte_control_imprime_totales_por_producto_sucursal_y_total(tmp_path, capsys):
    archivo = tmp_path / "compras.csv"
    crear_csv(
        archivo,
        [
            "SUC01,P100,2025-01-01,PROV01,2,10",
            "SUC01,P100,2025-01-02,PROV01,3,10",
            "SUC01,P200,2025-01-03,PROV01,1,100",
            "SUC02,P100,2025-01-04,PROV01,4,5",
        ],
    )

    corte_control.corte_control(str(archivo))

    salida = capsys.readouterr().out
    assert "A) POR PRODUCTO" in salida
    assert "B) POR SUCURSAL" in salida
    assert "C) TOTAL GENERAL" in salida
    assert "SUC01" in salida
    assert "P100" in salida
    assert "P200" in salida
    assert "Cantidad sucursales: 2" in salida
    assert "Producto mas vendido: P100 (9 unidades)" in salida
    assert "Importe total:       $170,00" in salida


def test_corte_control_informa_si_archivo_no_tiene_registros(tmp_path, capsys):
    archivo = tmp_path / "vacio.csv"
    archivo.write_text("PRSUC,PRCOD,PRFEC,PRPROV,PRCANT,PRPRE\n", encoding="utf-8")

    corte_control.corte_control(str(archivo))

    assert "El archivo no contiene registros para procesar" in capsys.readouterr().out


def test_corte_control_avisa_cuantas_filas_invalidas_descarto(tmp_path, capsys):
    archivo = tmp_path / "compras.csv"
    crear_csv(
        archivo,
        [
            "SUC01,P100,2025-01-01,PROV01,2,10",
            "SUC01,P200,2025-01-02,PROV01,error,10",
        ],
    )

    corte_control.corte_control(str(archivo))

    salida = capsys.readouterr().out
    assert "se descartaron 1 filas invalidas" in salida
    assert "Importe total:       $20,00" in salida


# ---------------------------------------------------------------------------
# Flujo principal (main)
# ---------------------------------------------------------------------------

def test_main_prepara_y_procesa_archivo(mocker):
    mocker.patch.object(corte_control, "solicitar_path_csv", return_value="entrada.csv")
    mocker.patch.object(corte_control, "solicitar_si_esta_ordenado", return_value=True)
    mocker.patch.object(
        corte_control,
        "preparar_archivo",
        return_value=("entrada.csv", None),
    )
    procesar = mocker.patch.object(corte_control, "corte_control")
    eliminar = mocker.patch.object(corte_control.os, "remove")

    corte_control.main()

    procesar.assert_called_once_with("entrada.csv")
    eliminar.assert_not_called()


def test_main_elimina_temporal_si_fue_generado(mocker):
    mocker.patch.object(corte_control, "solicitar_path_csv", return_value="entrada.csv")
    mocker.patch.object(corte_control, "solicitar_si_esta_ordenado", return_value=False)
    mocker.patch.object(
        corte_control,
        "preparar_archivo",
        return_value=("temporal.csv", "temporal.csv"),
    )
    mocker.patch.object(corte_control, "corte_control")
    mocker.patch.object(corte_control.os.path, "exists", return_value=True)
    eliminar = mocker.patch.object(corte_control.os, "remove")

    corte_control.main()

    eliminar.assert_called_once_with("temporal.csv")
