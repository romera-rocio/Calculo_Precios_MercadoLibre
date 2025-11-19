import os
import json
import pandas as pd


# ===================================================
# FUNCIONES PRINCIPALES
# ===================================================

def cargar_lista_precios(path_excel):
    """
    Lee el Excel de lista de precios y devuelve el DataFrame.
    """
    df = pd.read_excel(path_excel)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def cargar_coeficientes(path_excel):
    """
    Carga todas las hojas del Excel de coeficientes.
    Devuelve un dict:
    { "Hoja1": df, "Hoja2": df, ... }
    """
    hojas = pd.read_excel(path_excel, sheet_name=None)

    dataframes = {}
    for nombre_hoja, df in hojas.items():
        df.columns = [str(c).strip() for c in df.columns]
        dataframes[nombre_hoja] = df.fillna("")

    return dataframes


def guardar_json(data, path_json):
    """
    Guarda cualquier dict como JSON.
    """
    os.makedirs(os.path.dirname(path_json), exist_ok=True)

    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ===================================================
# GENERAR DICCIONARIO MAESTRO
# ===================================================

def generar_diccionario_maestro(lista_df, coef_dict, carpeta_salida="data_json"):
    """
    Crea un diccionario JSON con:
      - columnas de cada DF
      - ruta a cada JSON guardado
    """

    os.makedirs(carpeta_salida, exist_ok=True)

    diccionario = {
        "lista_precios": {},
        "coeficientes": {}
    }

    # -------- LISTA DE PRECIOS ----------
    # Guardar JSON
    lista_json_path = os.path.join(carpeta_salida, "lista_precios.json")

    guardar_json(lista_df.fillna("").to_dict(orient="records"), lista_json_path)

    diccionario["lista_precios"] = {
        "df_columns": list(lista_df.columns),
        "json_path": lista_json_path
    }

    # -------- COEFICIENTES (todas las hojas) ----------
    diccionario["coeficientes"] = {}

    for nombre_hoja, df in coef_dict.items():
        path_json = os.path.join(carpeta_salida, f"coeficientes_{nombre_hoja}.json")

        guardar_json(df.to_dict(orient="records"), path_json)

        diccionario["coeficientes"][nombre_hoja] = {
            "df_columns": list(df.columns),
            "json_path": path_json
        }

    # -------- Guardar diccionario maestro ----------
    diccionario_path = os.path.join(carpeta_salida, "diccionario.json")
    guardar_json(diccionario, diccionario_path)

    return diccionario, diccionario_path


# ===================================================
# MAIN DE EJEMPLO REAL
# ===================================================
if __name__ == "__main__":

    ruta_lista = r"data_0/Lista_precios.xlsx"
    ruta_coef = r"data_0/Coeficientes.xlsx"
    carpeta_salida = r"data_json"

    print("Cargando Lista de Precios...")
    lista_df = cargar_lista_precios(ruta_lista)
    print(lista_df.head())

    print("\nCargando Coeficientes...")
    coef_dict = cargar_coeficientes(ruta_coef)
    print(f"Hojas cargadas: {list(coef_dict.keys())}")

    print("\nGenerando diccionario maestro...")
    diccionario, path_diccionario = generar_diccionario_maestro(
        lista_df,
        coef_dict,
        carpeta_salida
    )

    print("\nDICCIONARIO MAESTRO GENERADO:")
    print(json.dumps(diccionario, indent=2, ensure_ascii=False))

    print(f"\nGuardado en: {path_diccionario}")
    print("\nOK — proceso finalizado.")
