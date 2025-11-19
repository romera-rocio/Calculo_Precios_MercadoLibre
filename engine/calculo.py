import json
import pandas as pd
import traceback
import numpy as np  # Para usar np.nan

# 1. CARGAR JSON DE SELECCIÓN Y FORMULAS
with open("data_json\\seleccion_usuario.json", "r", encoding="utf-8") as f:
    SEL = json.load(f)

with open("data_json\\formulas.json", "r", encoding="utf-8") as f:
    FORMULAS = json.load(f)

# 2. ARMAR CONTEXTO BASE
ctx = {}

prod = SEL["producto"]
params = SEL["parametros"]

ctx["Descripcion"] = prod["Descripción"]
ctx["Codigo"] = prod["Codigo"]
ctx["SKU"] = prod["Codigo"]
ctx["Precio"] = prod["Precio"]
ctx["PVP"] = prod["PVP"]

coef_cliente = params["coef_cliente"]
ctx["coef_cliente"] = coef_cliente.get("coef_kira_dosificador", 1.0)

coef_pago = params["coef_forma_pago"]
ctx["coef_forma_pago"] = coef_pago.get("coef_kira_dosificador", 1.0)
ctx["coef_comision"] = coef_pago.get("comision", 0.0)
ctx["cuotas"] = coef_pago.get("cuotas", 1)

ctx["descuento_pct"] = params.get("descuento", 0.0)
ctx["Embalaje_Precio"] = params["coef_embalaje"]["Precio"]

ctx["EntregaGravada"] = params.get("EntregaGravada", 0.0)
ctx["EntregaNoGravada"] = params.get("EntregaNoGravada", 0.0)

for p in params["parametros_globales"]:
    nombre = p["Parámetro / nombre"].replace(" ", "_")
    ctx[nombre] = p["Valor / cuotas_texto"]

ctx["coef_iva"] = ctx.get("COEF_PARA_DEDUCIR_IVA", 0)
ctx["coef_iibb"] = ctx.get("INGRESOS_BRUTOS", 0)

ctx["coef_comision_vendedor"] = 0.0
ctx["Costo_Tipo"] = None

# 3. MINIMA LISTA DE PRECIOS PARA SOPORTAR BÚSQUEDAS
LP = pd.DataFrame([{
    "LP_Descripcion": ctx["Descripcion"],
    "LP_Precio": ctx["Precio"],
    "LP_PVP": ctx["PVP"]
}])

ctx["LP_Descripcion"] = LP["LP_Descripcion"]
ctx["LP_Precio"] = LP["LP_Precio"]
ctx["LP_PVP"] = LP["LP_PVP"]

# Función para buscar precio en LP por SKU
def buscar_precio_por_sku(LP, sku, columna):
    mask = LP["LP_Descripcion"].str.contains(str(sku), case=False, na=False)
    if mask.any():
        return LP.loc[mask, columna].iloc[0]
    else:
        return np.nan

# Valores manuales fallback (ajustalos según tus datos)
manual_values = {
    "Prod_CostoSKU": 17485,  # ejemplo costo manual
    "Prod_PVPProveedor": 0,  # ejemplo PVP manual
}

# Asignar valores base con fallback
ctx["Prod_CostoSKU"] = buscar_precio_por_sku(LP, ctx["SKU"], "LP_Precio")
if pd.isna(ctx["Prod_CostoSKU"]) or ctx["Prod_CostoSKU"] == 0:
    ctx["Prod_CostoSKU"] = manual_values["Prod_CostoSKU"]

ctx["Prod_PVPProveedor"] = buscar_precio_por_sku(LP, ctx["SKU"], "LP_PVP")
if pd.isna(ctx["Prod_PVPProveedor"]):
    ctx["Prod_PVPProveedor"] = manual_values["Prod_PVPProveedor"]

cache = {}

def safe_eval(expr, local_ctx):
    """
    Evalúa expresiones protegiendo divisiones por cero y otros errores comunes.
    Para division por cero, devuelve 0 en lugar de error.
    """
    try:
        # Para evitar ZeroDivisionError en divisiones, reemplazo con expresión condicional
        # Ejemplo: "(a/b)" --> "(a/b if b != 0 else 0)"
        # Aquí puedes hacer un reemplazo simple o usar una librería más avanzada si quieres
        # Por simplicidad, solo manejo el error con try-except

        return eval(expr, {}, local_ctx)
    except ZeroDivisionError:
        return 0
    except Exception as e:
        raise e

def resolver(nombre):
    if nombre in cache:
        return cache[nombre]

    if nombre in ctx and nombre not in FORMULAS:
        return ctx[nombre]

    info = FORMULAS[nombre]
    expr = info["formula_py"]

    # Resolver dependencias explícitas
    for v in info["variables"]:
        if v in FORMULAS:
            resolver(v)

    try:
        val = safe_eval(expr, ctx)
    except Exception:
        print(f"\n❌ ERROR en fórmula '{nombre}':\n{expr}")
        print("Detalle:", traceback.format_exc())
        val = np.nan
    cache[nombre] = val
    ctx[nombre] = val
    return val

# Resolver todas las fórmulas
for campo in FORMULAS:
    resolver(campo)

# Construir la fila final para Excel
fila = {
    "Descripción": ctx["Descripcion"],
    "SKU ( artículos del combo)": ctx["SKU"],
    "Precio  SKU COSTO": ctx.get("Prod_CostoSKU", np.nan),
    "PRECIO  PVP PROVEEDOR": ctx.get("Prod_PVPProveedor", np.nan),
    "Costos": ctx.get("Costo_Total", np.nan),
    "PVP": ctx.get("PVP_Redondeado", np.nan),
    "Cantidad de Pagos": ctx.get("Cantidad_Pagos", np.nan),
    "Precio de Venta ( R)": ctx.get("Precio_Venta_R", np.nan),
    "Precio de Venta": ctx.get("Precio_Venta_Final", np.nan),
    "Porcentaje de Descuento SOBRE PVP": ctx.get("Descuento_Porcentaje", np.nan),
    "Valor de cada cuota": ctx.get("Valor_Cuota", np.nan),
    "Entrega a Domicilio incluida": ctx.get("EntregaGravada", 0.0) + ctx.get("EntregaNoGravada", 0.0),
    "rentabilidad": ctx.get("Rentabilidad_Pesos", np.nan),
    "rentabilidad % arriba/abajo": ctx.get("Rentabilidad_A_B", np.nan),
    "rentabilidad % abajo/arriba": ctx.get("Rentabilidad_B_A", np.nan),
    "costo": ctx.get("Costo_Total", np.nan),
    "comision": ctx.get("Comision_Pago", np.nan),
    "Entrega a Domicilio gravada": ctx.get("Entrega_Gravada", 0.0),
    "Entrega a Domicilio no gravada": ctx.get("Entrega_NoGravada", 0.0),
    "IVA A PAGAR": ctx.get("IVA_Pagar", np.nan),
    "IIBB": ctx.get("IIBB", np.nan),
    "a cobrar con impuestos incluidos": ctx.get("A_Cobrar_Con_Impuestos", np.nan),
    "a cobrar sin impuestos": ctx.get("A_Cobrar_Sin_Impuestos", np.nan),
    "Comision Vendedor": ctx.get("Comision_Vendedor", np.nan),
}

df = pd.DataFrame([fila])
df.to_excel("resultado_precios.xlsx", index=False)

print("\n✅ Excel generado correctamente: resultado_precios.xlsx")
x