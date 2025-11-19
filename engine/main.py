import json
import pandas as pd

# ===============================
# FUNCIONES DE CARGA
# ===============================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_lista_precios(path="data_json/lista_precios.json"):
    df = pd.read_json(path)
    df.columns = [str(c).strip() for c in df.columns]
    return df

# ===============================
# BÚSQUEDA FLEXIBLE
# ===============================
def buscar_por_palabras(df, query):
    """Búsqueda general por marca + descripción + SKU."""
    query = query.lower().strip()
    if query == "":
        return df

    columnas = ["MARCA", "Descripción", "Codigo","PVP"]
    mask = False
    for col in columnas:
        mask |= df[col].astype(str).str.lower().str.contains(query)

    resultado = df[mask]
    return resultado


def buscar_por_sku(df, sku):
    sku = sku.lower().strip()
    return df[df["Codigo"].astype(str).str.lower() == sku]


def buscar_por_marca(df, marca):
    marca = marca.lower().strip()
    return df[df["MARCA"].astype(str).str.lower() == marca]


# ===============================
# MOSTRAR Y SELECCIONAR PRODUCTO
# ===============================
def mostrar_lista_y_seleccionar(df):
    df = df.reset_index(drop=True)

    print("\n--- Resultados encontrados ---")
    for i, row in df.iterrows():
        print(f"{i+1}) {row['MARCA']} | {row['Descripción']} | SKU: {row['Codigo']} | Precio: {row.get('Precio','-')} | PVP: {row.get('PVP','-')}")

    sel = input("\nSeleccione un producto (número): ").strip()
    if not sel.isdigit() or not (1 <= int(sel) <= len(df)):
        print("Selección inválida, tomando la primera opción.")
        sel = "1"

    return df.loc[int(sel)-1].to_dict()

# ===============================
# VALIDAR O PEDIR PVP MANUAL / USAR COSTO SI NO HAY PVP
# ===============================
def obtener_pvp(producto):
    pvp_valido = False
    pvp = producto.get("PVP", None)

    # Intentar convertir a float y validar que sea >0
    try:
        pvp = float(pvp)
        if pvp > 0:
            pvp_valido = True
    except:
        pvp_valido = False

    if not pvp_valido:
        print("\n⚠ El producto no tiene PVP válido.")
        # Pedir ingreso manual
        while True:
            entrada = input("Ingrese PVP manual (ENTER para usar el costo del producto): ").strip()
            if entrada == "":
                # Usar costo del producto, ejemplo campo "Precio" o "LP_Costo"
                costo = producto.get("Precio", None)
                if costo is not None:
                    try:
                        costo = float(costo)
                        print(f"Usando costo como PVP: {costo}")
                        return costo
                    except:
                        print("Costo inválido, ingrese un PVP manual válido.")
                        continue
                else:
                    print("No se encontró costo. Por favor ingrese un PVP manual válido.")
                    continue
            else:
                try:
                    pvp_manual = float(entrada)
                    if pvp_manual > 0:
                        return pvp_manual
                    else:
                        print("Ingrese un número mayor a 0.")
                except:
                    print("Entrada inválida, intente de nuevo.")
    else:
        return pvp

# ===============================
# INPUTS DEL USUARIO DESDE JSON CON COEFICIENTES
# ===============================
def mostrar_opciones_numeradas(titulo, opciones):
    print(f"\n--- {titulo} ---")
    for i, valor in enumerate(opciones, start=1):
        print(f"{i}) {valor}")
    seleccion = input("Seleccione el número: ").strip()
    if not seleccion.isdigit() or not (1 <= int(seleccion) <= len(opciones)):
        print("Opción inválida. Se selecciona la primera opción por defecto.")
        seleccion = "1"
    return opciones[int(seleccion)-1]


def solicitar_inputs_con_coeficientes():
    forma_pago_json = load_json("data_json/coeficientes_Forma_Pago.json")
    cliente_json = load_json("data_json/coeficientes_cliente.json")
    embalaje_json = load_json("data_json/coeficientes_Embalajes.json")
    parametros_globales = load_json("data_json/coeficientes_Parámetros_Globales.json")

    resultado = {}

    # --- Forma de Pago ---
    opciones_forma_pago = [f"{f['nombre']} ({f['cuotas']} cuotas)" for f in forma_pago_json]
    seleccion_forma_pago = mostrar_opciones_numeradas("Forma de Pago", opciones_forma_pago)
    coef_forma_pago = next(f for f in forma_pago_json if f"{f['nombre']} ({f['cuotas']} cuotas)" == seleccion_forma_pago)
    resultado["forma_pago"] = seleccion_forma_pago
    resultado["coef_forma_pago"] = coef_forma_pago

    # --- Tipo de Cliente ---
    opciones_cliente = [c["nombre"] for c in cliente_json]
    seleccion_cliente = mostrar_opciones_numeradas("Tipo de Cliente", opciones_cliente)
    coef_cliente = next(c for c in cliente_json if c["nombre"] == seleccion_cliente)
    resultado["tipo_cliente"] = seleccion_cliente
    resultado["coef_cliente"] = coef_cliente

    # --- Tipo de Embalaje ---
    opciones_embalaje = [e["Embalaje"] for e in embalaje_json]
    seleccion_embalaje = mostrar_opciones_numeradas("Tipo de Embalaje", opciones_embalaje)
    coef_embalaje = next(e for e in embalaje_json if e["Embalaje"] == seleccion_embalaje)
    resultado["embalaje"] = seleccion_embalaje
    resultado["coef_embalaje"] = coef_embalaje

    # --- Inputs manuales ---
    while True:
        desc = input("Descuento (%) opcional: ").strip()
        try:
            resultado["descuento"] = float(desc)
            break
        except ValueError:
            print("Ingrese un número válido.")

    while True:
        margen = input("Margen manual (%) opcional (ENTER si no aplica): ").strip()
        if margen == "":
            resultado["margen"] = None
            break
        try:
            resultado["margen"] = float(margen)
            break
        except ValueError:
            print("Ingrese un número válido.")

    resultado["parametros_globales"] = parametros_globales
    return resultado

# ===============================
# GUARDAR SELECCIÓN
# ===============================
def guardar_seleccion_json(data, path="data_json/seleccion_usuario.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Selección guardada en {path}")

# ===============================
# MAIN
# ===============================
def main():
    df = load_lista_precios()

    while True:
        print("\n==============================")
        print("        SISTEMA DE PRECIOS")
        print("==============================")
        print("1) Buscar por palabras")
        print("2) Buscar por SKU exacto")
        print("3) Buscar por Marca")
        print("4) Salir")

        opcion = input("Seleccione: ").strip()

        if opcion == "1":
            query = input("Ingrese palabras relacionadas: ")
            df_filtrado = buscar_por_palabras(df, query)

        elif opcion == "2":
            sku = input("Ingrese SKU exacto: ")
            df_filtrado = buscar_por_sku(df, sku)
            if df_filtrado.empty:
                print("❌ No existe el SKU exacto.")
                continue

        elif opcion == "3":
            print("\nMarcas disponibles:")
            marcas = sorted(df["MARCA"].dropna().unique())
            for i, m in enumerate(marcas, start=1):
                print(f"{i}) {m}")

            sel = input("Seleccione marca por número: ").strip()
            if not sel.isdigit() or not (1 <= int(sel) <= len(marcas)):
                print("Opción inválida.")
                continue

            marca = marcas[int(sel)-1]
            df_filtrado = buscar_por_marca(df, marca)

        elif opcion == "4":
            print("Saliendo…")
            break

        else:
            print("Opción inválida.")
            continue

        # En caso de no encontrar productos
        if df_filtrado.empty:
            print("\n❌ No se encontraron productos.")
            continue

        # Selección final de producto
        producto = mostrar_lista_y_seleccionar(df_filtrado)

        # Validar o pedir PVP manual si no tiene o no es válido
        producto["PVP"] = obtener_pvp(producto)

        print(f"\nProducto seleccionado: {producto['Descripción']} | SKU: {producto['Codigo']} | PVP final usado: {producto['PVP']}")

        parametros = solicitar_inputs_con_coeficientes()

        data_final = {
            "producto": producto,
            "parametros": parametros
        }

        guardar_seleccion_json(data_final)

        print("\n⚠ Aquí se puede llamar a la función final de cálculo…")
        # calcular_precio_final(producto, parametros)

if __name__ == "__main__":
    main()
