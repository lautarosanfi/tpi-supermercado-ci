def cargar_numeros():
    Numeros = []

    while True:
        num = int(input("Ingrese un numero: "))

        if num == 0:
            break

        if num < 1 or num > 100000:
            print("Error: el numero debe estar entre 1 y 100000")
        else:
            Numeros.append(num)

    return Numeros


def ordenar_burbuja(Numeros):
    n = len(Numeros)

    for i in range(n):
        for j in range(0, n - i - 1):
            if Numeros[j] > Numeros[j + 1]:
                aux = Numeros[j]
                Numeros[j] = Numeros[j + 1]
                Numeros[j + 1] = aux

    return Numeros


def busqueda_binaria(Numeros, buscado):
    inicio = 0
    fin = len(Numeros) - 1

    while inicio <= fin:
        medio = (inicio + fin) // 2

        if Numeros[medio] == buscado:
            return True
        elif buscado < Numeros[medio]:
            fin = medio - 1
        else:
            inicio = medio + 1

    return False


if __name__ == "__main__":
    Numeros = cargar_numeros()

    Numeros = ordenar_burbuja(Numeros)

    print("Arreglo ordenado:", Numeros)

    buscado = int(input("Ingrese el numero a buscar: "))

    encontrado = busqueda_binaria(Numeros, buscado)

    if encontrado:
        print("Numero encontrado")
    else:
        print("Numero no encontrado")
