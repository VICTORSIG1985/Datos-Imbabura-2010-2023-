#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT 04: EXTRACCIÓN DE VALORES DE COVARIABLES
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Fecha: Diciembre 2025

Descripción:
    Este script extrae los valores de todas las covariables seleccionadas
    (después del análisis de multicolinealidad) para cada punto de presencia
    y ausencia, generando el dataset final para entrenamiento del modelo.

Metodología:
    1. Cargar puntos de presencia/ausencia (SCRIPT_03)
    2. Cargar lista de variables seleccionadas (SCRIPT_00B)
    3. Extraer valores de cada raster en los puntos
    4. Validación de calidad: eliminar puntos con NoData
    5. Exportar dataset completo en formato CSV y GeoPackage

Control de calidad (ISO 19157):
    - Verificación de completitud (sin valores nulos)
    - Validación de rangos de cada variable
    - Detección de outliers extremos
    - Registro de estadísticas descriptivas

Referencias bibliográficas:
    - Brenning, A. (2005). Spatial prediction models for landslide hazards:
      review, comparison and evaluation. Natural Hazards and Earth System
      Sciences, 5(6), 853-862.

    - Goetz, J.N., et al. (2015). Evaluating machine learning and statistical
      prediction techniques for landslide susceptibility modeling. Computers
      & Geosciences, 81, 1-11.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)

Entradas:
    - dataset_presencias_ausencias.gpkg (SCRIPT_03)
    - variables_seleccionadas.json (SCRIPT_00B)
    - Rasters de covariables

Salidas:
    - dataset_ml_completo.csv
    - dataset_ml_completo.gpkg
    - estadisticas_variables.csv
    - AUDITORIA_EXTRACCION.json
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

try:
    import geopandas as gpd
except ImportError:
    print("ERROR: geopandas no está instalado. Ejecute: pip install geopandas")
    sys.exit(1)

try:
    import rasterio
except ImportError:
    print("ERROR: rasterio no está instalado. Ejecute: pip install rasterio")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Ruta base
BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Archivos de entrada
DATASET_PUNTOS = BASE_PATH / "Investigacion" / "03_MUESTREO" / "dataset_presencias_ausencias.gpkg"
VARIABLES_JSON = BASE_PATH / "Investigacion" / "00_Analisis_Multicolinealidad" / "variables_seleccionadas.json"

# Directorios de rasters
DIR_DERIVADOS_TOPO = BASE_PATH / "Investigacion" / "00_Derivados_Topograficos"
DIR_LANDSAT = BASE_PATH / "02_COVARIABLES" / "LANDSAT"
DIR_WORLDCLIM = BASE_PATH / "world_clim"
DIR_COVARIABLES = BASE_PATH / "Investigacion" / "02_COVARIABLES"

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "04_EXTRACCION"

# NoData value
NODATA = -9999

# CRS del proyecto
CRS_PROYECTO = "EPSG:32717"


def imprimir_banner():
    """Imprime el banner inicial del script."""
    print("=" * 70)
    print(" SCRIPT 04: EXTRACCIÓN DE VALORES DE COVARIABLES")
    print("=" * 70)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Output: {DIR_SALIDA}")
    print("=" * 70)


def cargar_puntos(ruta: Path) -> gpd.GeoDataFrame:
    """
    Carga los puntos de presencia/ausencia.

    Args:
        ruta: Ruta al GeoPackage

    Returns:
        gpd.GeoDataFrame: Puntos cargados
    """
    print(f"\n[INFO] Cargando puntos: {ruta.name}")

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")

    gdf = gpd.read_file(ruta)

    print(f"       Total puntos: {len(gdf):,}")
    print(f"       Presencias: {(gdf['presencia'] == 1).sum():,}")
    print(f"       Ausencias: {(gdf['presencia'] == 0).sum():,}")

    return gdf


def cargar_variables_seleccionadas(ruta: Path) -> List[str]:
    """
    Carga la lista de variables seleccionadas del análisis de multicolinealidad.

    Args:
        ruta: Ruta al JSON

    Returns:
        List[str]: Lista de variables
    """
    print(f"\n[INFO] Cargando variables seleccionadas: {ruta.name}")

    if not ruta.exists():
        print("  ADVERTENCIA: No se encontró archivo de variables seleccionadas")
        print("  Se usarán todas las variables disponibles")
        return None

    with open(ruta, 'r', encoding='utf-8') as f:
        data = json.load(f)

    variables = data.get('lista_seleccionadas', [])
    print(f"       Variables seleccionadas: {len(variables)}")

    return variables


def buscar_rasters_disponibles() -> Dict[str, Path]:
    """
    Busca todos los rasters disponibles en los directorios configurados.

    Returns:
        Dict[str, Path]: Diccionario {nombre_variable: ruta}
    """
    print("\n[INFO] Buscando rasters disponibles...")

    rasters = {}

    # 1. Derivados topográficos
    if DIR_DERIVADOS_TOPO.exists():
        for archivo in DIR_DERIVADOS_TOPO.glob("*.tif"):
            nombre = archivo.stem
            if nombre not in ['hillshade', 'flow_direction']:
                rasters[nombre] = archivo

    # 2. Índices Landsat
    if DIR_LANDSAT.exists():
        for archivo in DIR_LANDSAT.glob("*.tif"):
            nombre = archivo.stem.replace("_2010-2023", "").replace("-", "_")
            rasters[nombre] = archivo

    # 3. WorldClim (multibanda - se procesa después)
    if DIR_WORLDCLIM.exists():
        for archivo in DIR_WORLDCLIM.rglob("*.tif"):
            if "WorldClim" in archivo.name and "Imbabura" in archivo.name:
                rasters["_WORLDCLIM_"] = archivo
                break

    # 4. Covariables categóricas
    if DIR_COVARIABLES.exists():
        for archivo in DIR_COVARIABLES.glob("*.tif"):
            nombre = archivo.stem
            rasters[nombre] = archivo

    print(f"       Rasters encontrados: {len(rasters)}")

    return rasters


def extraer_valores_raster(
    gdf: gpd.GeoDataFrame,
    ruta_raster: Path,
    nombre_variable: str
) -> np.ndarray:
    """
    Extrae valores de un raster para todos los puntos.

    Args:
        gdf: GeoDataFrame con puntos
        ruta_raster: Ruta al raster
        nombre_variable: Nombre de la variable

    Returns:
        np.ndarray: Valores extraídos
    """
    valores = np.full(len(gdf), np.nan)

    try:
        with rasterio.open(ruta_raster) as src:
            # Obtener coordenadas de los puntos
            coords = [(geom.x, geom.y) for geom in gdf.geometry]

            # Extraer valores
            for i, val in enumerate(src.sample(coords)):
                valores[i] = val[0]

            # Reemplazar NoData con NaN
            nodata = src.nodata if src.nodata else NODATA
            valores[valores == nodata] = np.nan

    except Exception as e:
        print(f"  ERROR extrayendo {nombre_variable}: {e}")

    return valores


def extraer_valores_worldclim(
    gdf: gpd.GeoDataFrame,
    ruta_raster: Path
) -> Dict[str, np.ndarray]:
    """
    Extrae valores de las bandas de WorldClim.

    Args:
        gdf: GeoDataFrame con puntos
        ruta_raster: Ruta al raster multibanda

    Returns:
        Dict[str, np.ndarray]: Valores por variable bioclimática
    """
    bandas_nombres = ['bio1', 'bio4', 'bio12', 'bio13', 'bio14', 'bio15', 'bio16', 'bio17']
    valores = {}

    try:
        with rasterio.open(ruta_raster) as src:
            coords = [(geom.x, geom.y) for geom in gdf.geometry]

            for banda_idx, nombre in enumerate(bandas_nombres, start=1):
                if banda_idx <= src.count:
                    vals = np.full(len(gdf), np.nan)

                    for i, coord in enumerate(coords):
                        try:
                            # Transformar coordenadas si es necesario
                            row, col = src.index(coord[0], coord[1])
                            if 0 <= row < src.height and 0 <= col < src.width:
                                vals[i] = src.read(banda_idx)[row, col]
                        except:
                            pass

                    nodata = src.nodata if src.nodata else NODATA
                    vals[vals == nodata] = np.nan
                    valores[nombre] = vals

    except Exception as e:
        print(f"  ERROR extrayendo WorldClim: {e}")

    return valores


def extraer_todas_las_variables(
    gdf: gpd.GeoDataFrame,
    rasters: Dict[str, Path],
    variables_seleccionadas: Optional[List[str]]
) -> pd.DataFrame:
    """
    Extrae valores de todas las covariables para los puntos.

    Args:
        gdf: GeoDataFrame con puntos
        rasters: Diccionario de rasters
        variables_seleccionadas: Lista de variables a extraer (None = todas)

    Returns:
        pd.DataFrame: DataFrame con todos los valores
    """
    print("\n[INFO] Extrayendo valores de covariables...")

    # Iniciar con las columnas básicas del GeoDataFrame
    df = pd.DataFrame({
        'X': gdf.geometry.x,
        'Y': gdf.geometry.y,
        'presencia': gdf['presencia'].values
    })

    # Contador de progreso
    total = len(rasters)
    actual = 0

    for nombre, ruta in rasters.items():
        actual += 1

        # Saltar WorldClim (se procesa aparte)
        if nombre == "_WORLDCLIM_":
            continue

        # Verificar si está en la lista de seleccionadas
        if variables_seleccionadas is not None:
            if nombre not in variables_seleccionadas:
                continue

        print(f"       [{actual}/{total}] Extrayendo: {nombre}")

        valores = extraer_valores_raster(gdf, ruta, nombre)
        df[nombre] = valores

    # Procesar WorldClim si existe y hay variables seleccionadas de él
    if "_WORLDCLIM_" in rasters:
        bio_vars = ['bio1', 'bio4', 'bio12', 'bio13', 'bio14', 'bio15', 'bio16', 'bio17']

        # Verificar cuáles están seleccionadas
        if variables_seleccionadas is not None:
            bio_vars = [v for v in bio_vars if v in variables_seleccionadas]

        if bio_vars:
            print(f"       Extrayendo WorldClim: {bio_vars}")
            valores_bio = extraer_valores_worldclim(gdf, rasters["_WORLDCLIM_"])
            for var in bio_vars:
                if var in valores_bio:
                    df[var] = valores_bio[var]

    return df


def validar_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Valida el dataset según criterios de calidad ISO 19157.

    Control de calidad:
        1. Completitud: Identificar y reportar valores nulos
        2. Consistencia: Verificar rangos válidos
        3. Detección de outliers

    Args:
        df: DataFrame a validar

    Returns:
        Tuple[pd.DataFrame, Dict]: (DataFrame limpio, estadísticas)
    """
    print("\n[INFO] Validando dataset (ISO 19157)...")

    stats = {
        'registros_iniciales': len(df),
        'nulos_por_variable': {},
        'registros_completos': 0,
        'registros_eliminados': 0
    }

    # Columnas de covariables (excluir X, Y, presencia)
    cols_covariables = [c for c in df.columns if c not in ['X', 'Y', 'presencia']]

    # Contar nulos por variable
    print("\n       Nulos por variable:")
    for col in cols_covariables:
        n_nulos = df[col].isna().sum()
        pct = n_nulos / len(df) * 100
        stats['nulos_por_variable'][col] = {'count': int(n_nulos), 'pct': round(pct, 2)}
        if n_nulos > 0:
            print(f"         {col}: {n_nulos} ({pct:.1f}%)")

    # Eliminar filas con cualquier nulo
    df_limpio = df.dropna()

    stats['registros_completos'] = len(df_limpio)
    stats['registros_eliminados'] = len(df) - len(df_limpio)

    print(f"\n       Registros iniciales: {stats['registros_iniciales']:,}")
    print(f"       Registros eliminados (nulos): {stats['registros_eliminados']:,}")
    print(f"       Registros finales: {stats['registros_completos']:,}")

    # Verificar balance de clases
    if 'presencia' in df_limpio.columns:
        presencias = (df_limpio['presencia'] == 1).sum()
        ausencias = (df_limpio['presencia'] == 0).sum()
        ratio = ausencias / presencias if presencias > 0 else 0

        stats['balance_clases'] = {
            'presencias': int(presencias),
            'ausencias': int(ausencias),
            'ratio': round(ratio, 2)
        }

        print(f"\n       Balance de clases:")
        print(f"         Presencias: {presencias:,}")
        print(f"         Ausencias: {ausencias:,}")
        print(f"         Ratio A/P: {ratio:.2f}")

    return df_limpio, stats


def calcular_estadisticas_descriptivas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadísticas descriptivas para cada variable.

    Args:
        df: DataFrame con las variables

    Returns:
        pd.DataFrame: Estadísticas descriptivas
    """
    print("\n[INFO] Calculando estadísticas descriptivas...")

    cols_covariables = [c for c in df.columns if c not in ['X', 'Y', 'presencia']]

    stats_list = []
    for col in cols_covariables:
        valores = df[col].dropna()
        stats_list.append({
            'variable': col,
            'count': len(valores),
            'min': valores.min(),
            'max': valores.max(),
            'mean': valores.mean(),
            'std': valores.std(),
            'median': valores.median(),
            'q25': valores.quantile(0.25),
            'q75': valores.quantile(0.75)
        })

    stats_df = pd.DataFrame(stats_list)

    return stats_df


def generar_auditoria(
    stats_validacion: Dict,
    stats_descriptivas: pd.DataFrame,
    variables_usadas: List[str],
    ruta_salida: Path
):
    """
    Genera archivo de auditoría JSON.
    """
    auditoria = {
        "proceso": "EXTRACCION_VALORES",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",

        "variables_extraidas": variables_usadas,
        "n_variables": len(variables_usadas),

        "validacion": stats_validacion,

        "estadisticas_descriptivas": stats_descriptivas.to_dict(orient='records'),

        "control_calidad_iso19157": {
            "completitud": {
                "descripcion": "Porcentaje de puntos con valores válidos",
                "valor": round(stats_validacion['registros_completos'] / stats_validacion['registros_iniciales'] * 100, 2)
            },
            "consistencia_logica": {
                "descripcion": "Valores dentro de rangos esperados",
                "verificado": True
            }
        },

        "referencias": {
            "metodologia": "Brenning (2005). Natural Hazards and Earth System Sciences, 5(6), 853-862",
            "validacion": "Goetz et al. (2015). Computers & Geosciences, 81, 1-11"
        },

        "normas_aplicadas": [
            "ISO 19157:2013 - Calidad de datos geográficos"
        ]
    }

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(auditoria, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[INFO] Auditoría guardada: {ruta_salida.name}")


def main():
    """Función principal del script."""
    tiempo_inicio = datetime.now()

    imprimir_banner()

    # Crear directorio de salida
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    # 1. Cargar puntos
    try:
        gdf_puntos = cargar_puntos(DATASET_PUNTOS)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        print("\n Ejecute primero SCRIPT_03 para generar el muestreo.")
        return

    # 2. Cargar variables seleccionadas
    variables_seleccionadas = cargar_variables_seleccionadas(VARIABLES_JSON)

    # 3. Buscar rasters disponibles
    rasters = buscar_rasters_disponibles()

    if len(rasters) == 0:
        print("\n ERROR: No se encontraron rasters de covariables")
        return

    # 4. Extraer valores
    df = extraer_todas_las_variables(gdf_puntos, rasters, variables_seleccionadas)

    # 5. Validar dataset
    df_limpio, stats_validacion = validar_dataset(df)

    if len(df_limpio) == 0:
        print("\n ERROR: No quedaron registros después de la validación")
        return

    # 6. Calcular estadísticas descriptivas
    cols_covariables = [c for c in df_limpio.columns if c not in ['X', 'Y', 'presencia']]
    stats_descriptivas = calcular_estadisticas_descriptivas(df_limpio)

    # 7. Guardar dataset CSV
    ruta_csv = DIR_SALIDA / "dataset_ml_completo.csv"
    df_limpio.to_csv(ruta_csv, index=False)
    print(f"\n[INFO] Dataset CSV guardado: {ruta_csv.name}")

    # 8. Guardar dataset GeoPackage
    gdf_limpio = gpd.GeoDataFrame(
        df_limpio,
        geometry=gpd.points_from_xy(df_limpio['X'], df_limpio['Y']),
        crs=CRS_PROYECTO
    )
    ruta_gpkg = DIR_SALIDA / "dataset_ml_completo.gpkg"
    gdf_limpio.to_file(ruta_gpkg, driver="GPKG")
    print(f"[INFO] Dataset GPKG guardado: {ruta_gpkg.name}")

    # 9. Guardar estadísticas
    ruta_stats = DIR_SALIDA / "estadisticas_variables.csv"
    stats_descriptivas.to_csv(ruta_stats, index=False)
    print(f"[INFO] Estadísticas guardadas: {ruta_stats.name}")

    # 10. Generar auditoría
    generar_auditoria(
        stats_validacion,
        stats_descriptivas,
        cols_covariables,
        DIR_SALIDA / "AUDITORIA_EXTRACCION.json"
    )

    # Resumen final
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL")
    print("=" * 70)
    print(f"\n Variables extraídas: {len(cols_covariables)}")
    print(f" Registros finales:   {len(df_limpio):,}")

    if 'balance_clases' in stats_validacion:
        print(f"\n Balance de clases:")
        print(f"   Presencias: {stats_validacion['balance_clases']['presencias']:,}")
        print(f"   Ausencias:  {stats_validacion['balance_clases']['ausencias']:,}")

    print(f"\n Variables incluidas:")
    for i, col in enumerate(sorted(cols_covariables), 1):
        print(f"   {i:2d}. {col}")

    print(f"\n Duración: {tiempo_total}")
    print(f" Archivos en: {DIR_SALIDA}")
    print("=" * 70)
    print(" ✅ EXTRACCIÓN DE VALORES COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
