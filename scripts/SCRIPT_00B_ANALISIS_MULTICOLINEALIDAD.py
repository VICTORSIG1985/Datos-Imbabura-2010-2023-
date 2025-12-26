#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT 00B: ANÁLISIS DE MULTICOLINEALIDAD
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Institución: Universidad de las Fuerzas Armadas ESPE
Fecha: Diciembre 2025

Descripción:
    Este script realiza el análisis de multicolinealidad entre todas las
    covariables candidatas ANTES del modelamiento. Identifica y elimina
    variables altamente correlacionadas para evitar:
    - Inflación de importancias en Random Forest
    - Inestabilidad en coeficientes
    - Redundancia de información

Metodología:
    1. Muestreo aleatorio estratificado de valores de rasters
    2. Cálculo de matriz de correlación de Pearson
    3. Identificación de pares con |r| > 0.80 (Dormann et al., 2013)
    4. Cálculo de VIF (Variance Inflation Factor)
    5. Eliminación iterativa basada en prioridad física (Varnes, 1978)

Referencias bibliográficas:
    - Dormann, C.F., et al. (2013). Collinearity: a review of methods to deal
      with it and a simulation study evaluating their performance.
      Ecography, 36(1), 27-46. https://doi.org/10.1111/j.1600-0587.2012.07348.x

    - O'Brien, R.M. (2007). A caution regarding rules of thumb for variance
      inflation factors. Quality & Quantity, 41(5), 673-690.
      https://doi.org/10.1007/s11135-006-9018-6

    - Varnes, D.J. (1978). Slope movement types and processes. In: Schuster,
      R.L., Krizek, R.J. (Eds.), Landslides: Analysis and Control. Special
      Report 176, Transportation Research Board, pp. 11-33.

    - Reichenbach, P., et al. (2018). A review of statistically-based landslide
      susceptibility models. Earth-Science Reviews, 180, 60-91.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)

Entradas:
    - Rasters de derivados topográficos (00_Derivados_Topograficos/)
    - Rasters de índices Landsat (02_COVARIABLES/LANDSAT/)
    - Raster de variables bioclimáticas WorldClim
    - Rasters de variables categóricas rasterizadas

Salidas:
    - Matriz de correlación (CSV y PNG)
    - Tabla de VIF (CSV)
    - Lista de variables seleccionadas (JSON)
    - Auditoría del proceso (JSON)
================================================================================
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import rasterio
    from rasterio.mask import mask
except ImportError:
    print("ERROR: rasterio no está instalado. Ejecute: pip install rasterio")
    sys.exit(1)

try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    STATSMODELS_DISPONIBLE = True
except ImportError:
    STATSMODELS_DISPONIBLE = False
    print("ADVERTENCIA: statsmodels no instalado. VIF se calculará manualmente.")

# Suprimir warnings de división
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Ruta base - MODIFICAR SEGÚN TU SISTEMA
BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Directorios de entrada
DIR_DERIVADOS_TOPO = BASE_PATH / "Investigacion" / "00_Derivados_Topograficos"
DIR_LANDSAT = BASE_PATH / "02_COVARIABLES" / "LANDSAT"
DIR_WORLDCLIM = BASE_PATH / "world_clim"
DIR_COVARIABLES = BASE_PATH / "Investigacion" / "02_COVARIABLES"

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "00_Analisis_Multicolinealidad"

# Parámetros de análisis
# Umbral de correlación: Dormann et al. (2013) recomienda 0.7-0.8
# Usamos 0.80 como umbral conservador
UMBRAL_CORRELACION = 0.80

# Umbral VIF: O'Brien (2007) sugiere VIF > 10 indica multicolinealidad severa
UMBRAL_VIF = 10.0

# Número de puntos de muestreo para extraer valores
N_MUESTRAS = 10000

# Semilla para reproducibilidad
SEMILLA = 42

# Prioridad física de variables (mayor número = mayor prioridad de conservar)
# Basado en Varnes (1978) y Reichenbach et al. (2018)
PRIORIDAD_VARIABLES = {
    # === TOPOGRÁFICAS FUNDAMENTALES (Factores gravitacionales - Varnes, 1978) ===
    "dem": 10,              # Elevación - factor fundamental
    "slope_degrees": 9,     # Pendiente - factor gravitacional directo
    "curvatura": 8,         # Curvatura - concentración/dispersión de flujo
    "twi": 8,               # Índice de humedad topográfica
    "tri": 6,               # Rugosidad del terreno
    "tpi": 5,               # Posición topográfica
    "flow_accumulation": 6, # Acumulación de flujo
    "dist_drenajes": 7,     # Distancia a red de drenaje
    "aspect": 5,            # Orientación (menos crítico)

    # === ÍNDICES ESPECTRALES (Proxies de cobertura/humedad) ===
    "NDVI_media": 5,
    "NDVI_std": 4,
    "EVI_media": 4,
    "EVI_std": 3,
    "NDMI_media": 5,        # Humedad de vegetación - importante
    "NDMI_std": 4,
    "LST_media": 3,         # Temperatura superficial
    "LST_std": 2,
    "NDWI_media": 4,
    "NDWI_std": 3,
    "MNDWI_media": 3,
    "MNDWI_std": 2,
    "SAVI_media": 4,
    "SAVI_std": 3,
    "NBR_media": 4,
    "NBR_std": 3,

    # === BIOCLIMÁTICAS (Proxies climáticos) ===
    "bio1": 2,              # Temperatura media - PROXY del gradiente altitudinal
    "bio4": 3,              # Estacionalidad temperatura
    "bio12": 4,             # Precipitación anual - importante
    "bio13": 3,
    "bio14": 3,
    "bio15": 3,
    "bio16": 3,
    "bio17": 3,

    # === CATEGÓRICAS ===
    "geomorfologia": 8,     # Unidades geomorfológicas
    "cobertura": 6,         # Cobertura vegetal
    "deforestacion": 5,     # Cambio de cobertura
}


def imprimir_banner():
    """Imprime el banner inicial del script."""
    print("=" * 70)
    print(" SCRIPT 00B: ANÁLISIS DE MULTICOLINEALIDAD")
    print("=" * 70)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Umbral correlación: |r| > {UMBRAL_CORRELACION}")
    print(f" Umbral VIF: > {UMBRAL_VIF}")
    print(f" Muestras: {N_MUESTRAS:,}")
    print(f" Output: {DIR_SALIDA}")
    print("=" * 70)


def obtener_lista_rasters() -> Dict[str, Path]:
    """
    Obtiene la lista de todos los rasters disponibles para análisis.

    Returns:
        Dict[str, Path]: Diccionario {nombre_variable: ruta_archivo}
    """
    rasters = {}

    # 1. Derivados topográficos
    print("\n[INFO] Buscando derivados topográficos...")
    if DIR_DERIVADOS_TOPO.exists():
        for archivo in DIR_DERIVADOS_TOPO.glob("*.tif"):
            nombre = archivo.stem
            # Excluir hillshade (solo visualización)
            if nombre not in ['hillshade', 'flow_direction']:
                rasters[nombre] = archivo
                print(f"       + {nombre}")
    else:
        print(f"  ADVERTENCIA: No existe {DIR_DERIVADOS_TOPO}")

    # 2. Índices Landsat
    print("\n[INFO] Buscando índices Landsat...")
    if DIR_LANDSAT.exists():
        for archivo in DIR_LANDSAT.glob("*.tif"):
            nombre = archivo.stem
            # Limpiar nombre (quitar fechas)
            nombre_limpio = nombre.replace("_2010-2023", "").replace("-", "_")
            rasters[nombre_limpio] = archivo
            print(f"       + {nombre_limpio}")
    else:
        print(f"  ADVERTENCIA: No existe {DIR_LANDSAT}")

    # 3. WorldClim bioclimáticas (multibanda)
    print("\n[INFO] Buscando variables bioclimáticas...")
    worldclim_file = None
    if DIR_WORLDCLIM.exists():
        for archivo in DIR_WORLDCLIM.rglob("*.tif"):
            if "WorldClim" in archivo.name and "Imbabura" in archivo.name:
                worldclim_file = archivo
                break

    if worldclim_file and worldclim_file.exists():
        print(f"       Archivo WorldClim: {worldclim_file.name}")
        # Marcamos como multibanda para tratamiento especial
        rasters["_WORLDCLIM_MULTIBANDA_"] = worldclim_file

    # 4. Covariables categóricas rasterizadas
    print("\n[INFO] Buscando covariables categóricas rasterizadas...")
    if DIR_COVARIABLES.exists():
        for archivo in DIR_COVARIABLES.glob("*.tif"):
            nombre = archivo.stem
            rasters[nombre] = archivo
            print(f"       + {nombre}")

    return rasters


def muestrear_rasters(
    rasters: Dict[str, Path],
    n_muestras: int = 10000,
    semilla: int = 42
) -> pd.DataFrame:
    """
    Extrae valores de múltiples rasters en puntos aleatorios.

    Metodología:
        Se genera una muestra aleatoria estratificada de puntos dentro del
        extent del DEM. Para cada punto se extraen los valores de todas
        las covariables. Los puntos con NoData en cualquier variable se
        excluyen del análisis.

    Args:
        rasters: Diccionario de rutas a rasters
        n_muestras: Número de puntos a muestrear
        semilla: Semilla para reproducibilidad

    Returns:
        pd.DataFrame: DataFrame con valores extraídos
    """
    np.random.seed(semilla)

    print(f"\n[INFO] Iniciando muestreo de {n_muestras:,} puntos...")

    # Usar DEM como referencia para el extent
    dem_path = rasters.get('dem')
    if dem_path is None:
        raise FileNotFoundError("No se encontró el DEM en los rasters")

    with rasterio.open(dem_path) as src:
        bounds = src.bounds
        transform = src.transform
        height, width = src.height, src.width
        nodata = src.nodata

    # Generar puntos aleatorios dentro del extent
    # Generamos más puntos de los necesarios porque algunos caerán en NoData
    factor_extra = 3
    n_generar = n_muestras * factor_extra

    rows = np.random.randint(0, height, n_generar)
    cols = np.random.randint(0, width, n_generar)

    # Inicializar diccionario para almacenar valores
    valores = {nombre: [] for nombre in rasters.keys() if nombre != "_WORLDCLIM_MULTIBANDA_"}

    # Añadir columnas para WorldClim si existe
    if "_WORLDCLIM_MULTIBANDA_" in rasters:
        for bio in ['bio1', 'bio4', 'bio12', 'bio13', 'bio14', 'bio15', 'bio16', 'bio17']:
            valores[bio] = []

    # Almacenar posiciones válidas
    posiciones_validas = []

    print("[INFO] Extrayendo valores de rasters...")

    # Extraer valores de cada raster
    for nombre, ruta in rasters.items():
        if nombre == "_WORLDCLIM_MULTIBANDA_":
            continue  # Tratamiento especial después

        try:
            with rasterio.open(ruta) as src:
                data = src.read(1)
                nd = src.nodata if src.nodata is not None else -9999

                for i, (r, c) in enumerate(zip(rows, cols)):
                    if r < data.shape[0] and c < data.shape[1]:
                        val = data[r, c]
                        if val != nd and not np.isnan(val):
                            if len(valores[nombre]) <= i:
                                valores[nombre].append(val)
                            else:
                                valores[nombre][i] = val
                        else:
                            if len(valores[nombre]) <= i:
                                valores[nombre].append(np.nan)

        except Exception as e:
            print(f"  ERROR leyendo {nombre}: {e}")
            valores[nombre] = [np.nan] * n_generar

    # Extraer WorldClim (multibanda)
    if "_WORLDCLIM_MULTIBANDA_" in rasters:
        print("[INFO] Extrayendo variables bioclimáticas WorldClim...")
        try:
            with rasterio.open(rasters["_WORLDCLIM_MULTIBANDA_"]) as src:
                bandas_bio = ['bio1', 'bio4', 'bio12', 'bio13', 'bio14', 'bio15', 'bio16', 'bio17']
                for banda_idx, bio_nombre in enumerate(bandas_bio, start=1):
                    if banda_idx <= src.count:
                        data = src.read(banda_idx)
                        nd = src.nodata if src.nodata is not None else -9999

                        for i, (r, c) in enumerate(zip(rows, cols)):
                            # Ajustar índices si la resolución es diferente
                            r_adj = min(int(r * src.height / height), src.height - 1)
                            c_adj = min(int(c * src.width / width), src.width - 1)

                            val = data[r_adj, c_adj]
                            if val != nd and not np.isnan(val):
                                if len(valores[bio_nombre]) <= i:
                                    valores[bio_nombre].append(float(val))
                            else:
                                if len(valores[bio_nombre]) <= i:
                                    valores[bio_nombre].append(np.nan)

        except Exception as e:
            print(f"  ERROR leyendo WorldClim: {e}")

    # Crear DataFrame
    # Primero, igualar longitudes
    max_len = max(len(v) for v in valores.values())
    for nombre in valores:
        while len(valores[nombre]) < max_len:
            valores[nombre].append(np.nan)

    df = pd.DataFrame(valores)

    # Eliminar filas con cualquier NaN
    df_limpio = df.dropna()

    # Limitar a n_muestras
    if len(df_limpio) > n_muestras:
        df_limpio = df_limpio.sample(n=n_muestras, random_state=semilla)

    print(f"[INFO] Muestras válidas obtenidas: {len(df_limpio):,}")

    # Eliminar columna temporal de WorldClim si existe
    if "_WORLDCLIM_MULTIBANDA_" in df_limpio.columns:
        df_limpio = df_limpio.drop(columns=["_WORLDCLIM_MULTIBANDA_"])

    return df_limpio


def calcular_matriz_correlacion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la matriz de correlación de Pearson.

    Referencia:
        Pearson, K. (1895). Notes on regression and inheritance in the
        case of two parents. Proceedings of the Royal Society of London.

    Args:
        df: DataFrame con las variables

    Returns:
        pd.DataFrame: Matriz de correlación
    """
    print("\n[INFO] Calculando matriz de correlación de Pearson...")

    # Solo columnas numéricas
    df_numerico = df.select_dtypes(include=[np.number])

    correlacion = df_numerico.corr(method='pearson')

    print(f"       Variables analizadas: {len(correlacion.columns)}")

    return correlacion


def identificar_pares_correlacionados(
    matriz_corr: pd.DataFrame,
    umbral: float = 0.80
) -> List[Tuple[str, str, float]]:
    """
    Identifica pares de variables con correlación superior al umbral.

    Referencia:
        Dormann, C.F., et al. (2013). Collinearity: a review of methods...
        Ecography, 36(1), 27-46.

    Args:
        matriz_corr: Matriz de correlación
        umbral: Umbral de correlación (default 0.80)

    Returns:
        List[Tuple]: Lista de (var1, var2, correlación)
    """
    print(f"\n[INFO] Identificando pares con |r| > {umbral}...")

    pares = []
    variables = matriz_corr.columns.tolist()

    for i, var1 in enumerate(variables):
        for var2 in variables[i+1:]:
            corr = matriz_corr.loc[var1, var2]
            if abs(corr) > umbral:
                pares.append((var1, var2, round(corr, 4)))

    # Ordenar por correlación absoluta descendente
    pares.sort(key=lambda x: abs(x[2]), reverse=True)

    print(f"       Pares encontrados: {len(pares)}")

    return pares


def calcular_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el Variance Inflation Factor (VIF) para cada variable.

    VIF = 1 / (1 - R²)

    Interpretación (O'Brien, 2007):
        - VIF = 1: No hay correlación
        - VIF < 5: Correlación moderada (aceptable)
        - VIF 5-10: Alta correlación (revisar)
        - VIF > 10: Multicolinealidad severa (eliminar)

    Referencia:
        O'Brien, R.M. (2007). A caution regarding rules of thumb for
        variance inflation factors. Quality & Quantity, 41(5), 673-690.

    Args:
        df: DataFrame con las variables

    Returns:
        pd.DataFrame: VIF por variable
    """
    print("\n[INFO] Calculando VIF (Variance Inflation Factor)...")

    df_numerico = df.select_dtypes(include=[np.number])

    # Eliminar columnas con varianza cero
    df_numerico = df_numerico.loc[:, df_numerico.std() > 0]

    vif_data = []

    if STATSMODELS_DISPONIBLE:
        # Usar statsmodels si está disponible
        from statsmodels.stats.outliers_influence import variance_inflation_factor

        # Añadir constante
        X = df_numerico.values

        for i, col in enumerate(df_numerico.columns):
            try:
                vif = variance_inflation_factor(X, i)
                vif_data.append({
                    'variable': col,
                    'VIF': round(vif, 2)
                })
            except:
                vif_data.append({
                    'variable': col,
                    'VIF': np.nan
                })
    else:
        # Cálculo manual usando R²
        from sklearn.linear_model import LinearRegression

        for col in df_numerico.columns:
            X = df_numerico.drop(columns=[col])
            y = df_numerico[col]

            try:
                modelo = LinearRegression()
                modelo.fit(X, y)
                r2 = modelo.score(X, y)
                vif = 1 / (1 - r2) if r2 < 1 else np.inf
                vif_data.append({
                    'variable': col,
                    'VIF': round(vif, 2)
                })
            except:
                vif_data.append({
                    'variable': col,
                    'VIF': np.nan
                })

    vif_df = pd.DataFrame(vif_data)
    vif_df = vif_df.sort_values('VIF', ascending=False)

    print(f"       Variables con VIF > {UMBRAL_VIF}: {len(vif_df[vif_df['VIF'] > UMBRAL_VIF])}")

    return vif_df


def seleccionar_variables(
    pares_correlacionados: List[Tuple[str, str, float]],
    vif_df: pd.DataFrame,
    variables_disponibles: List[str]
) -> Tuple[List[str], List[Dict]]:
    """
    Selecciona variables eliminando las redundantes basándose en prioridad física.

    Criterios de eliminación (en orden):
        1. Si |r| > 0.80 entre dos variables, eliminar la de menor prioridad
        2. Prioridad basada en relevancia física (Varnes, 1978):
           - DEM > slope > curvatura > TWI > índices espectrales > bioclimáticas
        3. En caso de empate, conservar la de menor VIF

    Justificación científica:
        - DEM es el factor gravitacional fundamental (Varnes, 1978)
        - bio1 (temperatura) es un proxy del gradiente altitudinal, por lo tanto
          si DEM y bio1 están correlacionados, se elimina bio1
        - Los índices espectrales son proxies de cobertura/humedad, menos
          fundamentales que los factores topográficos directos

    Args:
        pares_correlacionados: Lista de pares con alta correlación
        vif_df: DataFrame con VIF
        variables_disponibles: Lista de variables disponibles

    Returns:
        Tuple[List[str], List[Dict]]: (variables seleccionadas, log de decisiones)
    """
    print("\n[INFO] Seleccionando variables (eliminación por prioridad física)...")
    print("       Referencia: Varnes (1978), Reichenbach et al. (2018)")

    # Crear diccionario de VIF
    vif_dict = dict(zip(vif_df['variable'], vif_df['VIF']))

    # Variables a eliminar
    eliminadas = set()
    log_decisiones = []

    # Procesar cada par correlacionado
    for var1, var2, corr in pares_correlacionados:
        # Si alguna ya fue eliminada, saltar
        if var1 in eliminadas or var2 in eliminadas:
            continue

        # Obtener prioridades
        prio1 = PRIORIDAD_VARIABLES.get(var1, 1)
        prio2 = PRIORIDAD_VARIABLES.get(var2, 1)

        # Obtener VIF
        vif1 = vif_dict.get(var1, 0)
        vif2 = vif_dict.get(var2, 0)

        # Decidir cuál eliminar
        if prio1 > prio2:
            eliminar = var2
            conservar = var1
            razon = f"Menor prioridad física ({prio2} vs {prio1})"
        elif prio2 > prio1:
            eliminar = var1
            conservar = var2
            razon = f"Menor prioridad física ({prio1} vs {prio2})"
        else:
            # Empate: usar VIF
            if vif1 > vif2:
                eliminar = var1
                conservar = var2
                razon = f"Mayor VIF ({vif1:.1f} vs {vif2:.1f})"
            else:
                eliminar = var2
                conservar = var1
                razon = f"Mayor VIF ({vif2:.1f} vs {vif1:.1f})"

        eliminadas.add(eliminar)

        decision = {
            'par': f"{var1} vs {var2}",
            'correlacion': corr,
            'eliminada': eliminar,
            'conservada': conservar,
            'razon': razon,
            'prioridad_eliminada': PRIORIDAD_VARIABLES.get(eliminar, 1),
            'prioridad_conservada': PRIORIDAD_VARIABLES.get(conservar, 1),
            'vif_eliminada': vif_dict.get(eliminar, np.nan),
            'vif_conservada': vif_dict.get(conservar, np.nan)
        }
        log_decisiones.append(decision)

        print(f"       ELIMINAR: {eliminar} (r={corr:.3f} con {conservar})")
        print(f"                 Razón: {razon}")

    # Variables finales
    variables_seleccionadas = [v for v in variables_disponibles if v not in eliminadas]

    print(f"\n       Variables eliminadas: {len(eliminadas)}")
    print(f"       Variables seleccionadas: {len(variables_seleccionadas)}")

    return variables_seleccionadas, log_decisiones


def generar_heatmap_correlacion(
    matriz_corr: pd.DataFrame,
    ruta_salida: Path,
    titulo: str = "Matriz de Correlación de Pearson"
):
    """
    Genera un heatmap de la matriz de correlación.

    Args:
        matriz_corr: Matriz de correlación
        ruta_salida: Ruta para guardar la imagen
        titulo: Título del gráfico
    """
    print(f"\n[INFO] Generando heatmap de correlación...")

    # Tamaño del gráfico según número de variables
    n_vars = len(matriz_corr.columns)
    fig_size = max(12, n_vars * 0.5)

    plt.figure(figsize=(fig_size, fig_size * 0.8))

    # Crear máscara para triángulo superior
    mask = np.triu(np.ones_like(matriz_corr, dtype=bool))

    # Heatmap
    sns.heatmap(
        matriz_corr,
        mask=mask,
        annot=True if n_vars <= 15 else False,
        fmt='.2f' if n_vars <= 15 else '',
        cmap='RdBu_r',
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={'shrink': 0.8, 'label': 'Correlación de Pearson'}
    )

    plt.title(titulo, fontsize=14, fontweight='bold')
    plt.tight_layout()

    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_salida.name}")


def generar_heatmap_variables_seleccionadas(
    matriz_corr: pd.DataFrame,
    variables_seleccionadas: List[str],
    ruta_salida: Path
):
    """
    Genera un heatmap solo con las variables seleccionadas.
    """
    # Filtrar matriz
    vars_en_matriz = [v for v in variables_seleccionadas if v in matriz_corr.columns]
    matriz_filtrada = matriz_corr.loc[vars_en_matriz, vars_en_matriz]

    generar_heatmap_correlacion(
        matriz_filtrada,
        ruta_salida,
        titulo="Matriz de Correlación - Variables Seleccionadas"
    )


def generar_auditoria(
    resultados: Dict,
    ruta_salida: Path
):
    """
    Genera archivo de auditoría JSON según ISO 19115.
    """
    auditoria = {
        "proceso": "ANALISIS_MULTICOLINEALIDAD",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",
        "institucion": "Universidad de las Fuerzas Armadas ESPE",

        "parametros": {
            "umbral_correlacion": UMBRAL_CORRELACION,
            "umbral_vif": UMBRAL_VIF,
            "n_muestras": N_MUESTRAS,
            "semilla": SEMILLA
        },

        "referencias_metodologicas": {
            "correlacion": "Dormann et al. (2013). Ecography, 36(1), 27-46",
            "vif": "O'Brien (2007). Quality & Quantity, 41(5), 673-690",
            "prioridad_fisica": "Varnes (1978). Landslides: Analysis and Control"
        },

        "resultados": resultados,

        "normas_aplicadas": [
            "ISO 19157:2013 - Calidad de datos geográficos"
        ]
    }

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(auditoria, f, indent=2, ensure_ascii=False, default=str)

    print(f"[INFO] Auditoría guardada: {ruta_salida.name}")


def main():
    """Función principal del script."""
    tiempo_inicio = datetime.now()

    imprimir_banner()

    # Crear directorio de salida
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    # 1. Obtener lista de rasters
    rasters = obtener_lista_rasters()

    if len(rasters) == 0:
        print("\n ERROR: No se encontraron rasters para analizar")
        return

    # 2. Muestrear valores
    try:
        df_muestras = muestrear_rasters(rasters, N_MUESTRAS, SEMILLA)
    except Exception as e:
        print(f"\nERROR en muestreo: {e}")
        import traceback
        traceback.print_exc()
        return

    if len(df_muestras) < 100:
        print(f"\nERROR: Muy pocas muestras válidas ({len(df_muestras)})")
        return

    # Guardar muestras
    df_muestras.to_csv(DIR_SALIDA / "muestras_valores.csv", index=False)
    print(f"\n[INFO] Muestras guardadas: muestras_valores.csv")

    # 3. Calcular matriz de correlación
    matriz_corr = calcular_matriz_correlacion(df_muestras)
    matriz_corr.to_csv(DIR_SALIDA / "matriz_correlacion.csv")

    # 4. Generar heatmap completo
    generar_heatmap_correlacion(
        matriz_corr,
        DIR_SALIDA / "heatmap_correlacion_completo.png"
    )

    # 5. Identificar pares correlacionados
    pares = identificar_pares_correlacionados(matriz_corr, UMBRAL_CORRELACION)

    # Guardar pares
    if pares:
        df_pares = pd.DataFrame(pares, columns=['Variable_1', 'Variable_2', 'Correlacion'])
        df_pares.to_csv(DIR_SALIDA / "pares_correlacionados.csv", index=False)

        print("\n" + "-" * 50)
        print(" PARES CON ALTA CORRELACIÓN (|r| > {:.2f})".format(UMBRAL_CORRELACION))
        print("-" * 50)
        for v1, v2, r in pares[:15]:  # Mostrar top 15
            print(f"   {v1:25s} <-> {v2:25s} : r = {r:+.4f}")
        if len(pares) > 15:
            print(f"   ... y {len(pares) - 15} pares más")

    # 6. Calcular VIF
    vif_df = calcular_vif(df_muestras)
    vif_df.to_csv(DIR_SALIDA / "vif_variables.csv", index=False)

    print("\n" + "-" * 50)
    print(" VARIABLES CON VIF > {:.0f}".format(UMBRAL_VIF))
    print("-" * 50)
    vif_alto = vif_df[vif_df['VIF'] > UMBRAL_VIF]
    if len(vif_alto) > 0:
        for _, row in vif_alto.iterrows():
            print(f"   {row['variable']:30s} : VIF = {row['VIF']:.1f}")
    else:
        print("   Ninguna variable con VIF > {:.0f}".format(UMBRAL_VIF))

    # 7. Seleccionar variables
    variables_disponibles = df_muestras.columns.tolist()
    vars_seleccionadas, log_decisiones = seleccionar_variables(
        pares, vif_df, variables_disponibles
    )

    # 8. Generar heatmap de variables seleccionadas
    generar_heatmap_variables_seleccionadas(
        matriz_corr,
        vars_seleccionadas,
        DIR_SALIDA / "heatmap_correlacion_seleccionadas.png"
    )

    # 9. Guardar lista de variables seleccionadas
    resultado_seleccion = {
        "variables_iniciales": len(variables_disponibles),
        "variables_eliminadas": len(variables_disponibles) - len(vars_seleccionadas),
        "variables_seleccionadas": len(vars_seleccionadas),
        "lista_seleccionadas": vars_seleccionadas,
        "lista_eliminadas": [v for v in variables_disponibles if v not in vars_seleccionadas],
        "decisiones": log_decisiones
    }

    with open(DIR_SALIDA / "variables_seleccionadas.json", 'w', encoding='utf-8') as f:
        json.dump(resultado_seleccion, f, indent=2, ensure_ascii=False)

    # 10. Generar auditoría
    resultados_auditoria = {
        "n_variables_analizadas": len(variables_disponibles),
        "n_muestras_utilizadas": len(df_muestras),
        "n_pares_correlacionados": len(pares),
        "n_variables_vif_alto": len(vif_alto),
        "n_variables_eliminadas": len(variables_disponibles) - len(vars_seleccionadas),
        "n_variables_seleccionadas": len(vars_seleccionadas),
        "variables_seleccionadas": vars_seleccionadas
    }

    generar_auditoria(resultados_auditoria, DIR_SALIDA / "AUDITORIA_MULTICOLINEALIDAD.json")

    # Resumen final
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL")
    print("=" * 70)
    print(f"\n Variables analizadas:    {len(variables_disponibles)}")
    print(f" Pares correlacionados:   {len(pares)} (|r| > {UMBRAL_CORRELACION})")
    print(f" Variables con VIF alto:  {len(vif_alto)} (VIF > {UMBRAL_VIF})")
    print(f" Variables ELIMINADAS:    {len(variables_disponibles) - len(vars_seleccionadas)}")
    print(f" Variables SELECCIONADAS: {len(vars_seleccionadas)}")

    print("\n VARIABLES SELECCIONADAS PARA MODELAMIENTO:")
    print(" " + "-" * 40)
    for i, var in enumerate(sorted(vars_seleccionadas), 1):
        prio = PRIORIDAD_VARIABLES.get(var, "?")
        print(f"   {i:2d}. {var:30s} (prioridad: {prio})")

    print(f"\n Duración: {tiempo_total}")
    print(f" Archivos en: {DIR_SALIDA}")
    print("=" * 70)
    print(" ✅ ANÁLISIS DE MULTICOLINEALIDAD COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
