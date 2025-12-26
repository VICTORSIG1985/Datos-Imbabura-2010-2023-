#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT 01: PREPARACIÓN DEL INVENTARIO DE DESLIZAMIENTOS
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Fecha: Diciembre 2025

Descripción:
    Este script procesa el inventario de deslizamientos del SNGR (2010-2023),
    realizando las siguientes operaciones:
    1. Lectura del archivo Excel original
    2. Validación y limpieza de coordenadas
    3. Reproyección a UTM 17S (EPSG:32717)
    4. Filtrado espacial dentro del AOI de Imbabura
    5. Análisis exploratorio del inventario
    6. Exportación a GeoPackage validado

Fuente de datos:
    - Archivo: DESLIZAMIENTOS_SGNR.xlsx
    - Institución: Servicio Nacional de Gestión de Riesgos (SNGR)
    - Período: 2010-2023 (14 años)

Referencias metodológicas:
    - Guzzetti, F., et al. (2012). Landslide inventory maps: New tools for an
      old problem. Earth-Science Reviews, 112(1-2), 42-66.
      https://doi.org/10.1016/j.earscirev.2012.02.001

    - Van Westen, C.J., et al. (2008). From landslide inventories to landslide
      risk assessment; an attempt to support methodological development in India.
      Landslides and Engineered Slopes, 1445-1451.

    - Fell, R., et al. (2008). Guidelines for landslide susceptibility, hazard
      and risk zoning for land use planning. Engineering Geology, 102(3-4), 85-98.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)
    - ISO 19115-1:2014 (Metadatos geográficos)

Entradas:
    - DESLIZAMIENTOS_SGNR.xlsx (inventario original)
    - AOI_IMBABURA_CANTON.gpkg (límite provincial)

Salidas:
    - inventario_validado.gpkg (inventario georreferenciado)
    - estadisticas_inventario.csv (resumen estadístico)
    - AUDITORIA_INVENTARIO.json (trazabilidad)
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

try:
    import geopandas as gpd
    from shapely.geometry import Point
    from pyproj import CRS, Transformer
except ImportError:
    print("ERROR: geopandas no está instalado. Ejecute: pip install geopandas")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Ruta base - MODIFICAR SEGÚN TU SISTEMA
BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Archivos de entrada
INVENTARIO_XLSX = BASE_PATH / "DESLIZAMIENTOS_SGNR.xlsx"
AOI_GPKG = Path(r"D:\DATA\AOI_IMBABURA_CANTON.gpkg")

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "01_PROCESSED"

# Sistema de coordenadas
CRS_ORIGEN = "EPSG:4326"      # WGS84 geográfico (lat/lon)
CRS_DESTINO = "EPSG:32717"    # WGS 84 / UTM zona 17S

# Período de análisis
ANIO_INICIO = 2010
ANIO_FIN = 2023

# Nombres de columnas esperados en el Excel (ajustar si es necesario)
COL_LATITUD = "LATITUD"       # o "lat", "latitude", "Y"
COL_LONGITUD = "LONGITUD"     # o "lon", "longitude", "X"
COL_FECHA = "FECHA"           # o "fecha_evento", "date"
COL_EVENTO = "EVENTO"         # tipo de evento
COL_CANTON = "CANTON"         # cantón


def imprimir_banner():
    """Imprime el banner inicial del script."""
    print("=" * 70)
    print(" SCRIPT 01: PREPARACIÓN DEL INVENTARIO DE DESLIZAMIENTOS")
    print("=" * 70)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Fuente: {INVENTARIO_XLSX.name}")
    print(f" Período: {ANIO_INICIO}-{ANIO_FIN}")
    print(f" CRS destino: {CRS_DESTINO}")
    print(f" Output: {DIR_SALIDA}")
    print("=" * 70)


def cargar_inventario_excel(ruta: Path) -> pd.DataFrame:
    """
    Carga el inventario de deslizamientos desde Excel.

    Args:
        ruta: Ruta al archivo Excel

    Returns:
        pd.DataFrame: Inventario cargado
    """
    print(f"\n[INFO] Cargando inventario: {ruta.name}")

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

    # Intentar leer el Excel
    try:
        df = pd.read_excel(ruta, engine='openpyxl')
    except Exception as e:
        print(f"  Intentando con xlrd...")
        df = pd.read_excel(ruta, engine='xlrd')

    print(f"       Registros cargados: {len(df):,}")
    print(f"       Columnas: {list(df.columns)}")

    return df


def identificar_columnas(df: pd.DataFrame) -> Dict[str, str]:
    """
    Identifica automáticamente las columnas de coordenadas y atributos.

    Args:
        df: DataFrame del inventario

    Returns:
        Dict: Mapeo de columnas identificadas
    """
    print("\n[INFO] Identificando columnas...")

    columnas = {}
    cols_lower = {c.lower(): c for c in df.columns}

    # Buscar columna de latitud
    for candidato in ['latitud', 'lat', 'latitude', 'y', 'coord_y']:
        if candidato in cols_lower:
            columnas['latitud'] = cols_lower[candidato]
            break

    # Buscar columna de longitud
    for candidato in ['longitud', 'lon', 'longitude', 'x', 'coord_x', 'long']:
        if candidato in cols_lower:
            columnas['longitud'] = cols_lower[candidato]
            break

    # Buscar columna de fecha
    for candidato in ['fecha', 'date', 'fecha_evento', 'fec_evento']:
        if candidato in cols_lower:
            columnas['fecha'] = cols_lower[candidato]
            break

    # Buscar columna de evento
    for candidato in ['evento', 'tipo_evento', 'event', 'tipo']:
        if candidato in cols_lower:
            columnas['evento'] = cols_lower[candidato]
            break

    # Buscar columna de cantón
    for candidato in ['canton', 'cantón', 'dpa_canton', 'nom_canton']:
        if candidato in cols_lower:
            columnas['canton'] = cols_lower[candidato]
            break

    # Buscar columna de año
    for candidato in ['anio', 'año', 'year', 'anio_evento']:
        if candidato in cols_lower:
            columnas['anio'] = cols_lower[candidato]
            break

    print("       Columnas identificadas:")
    for key, value in columnas.items():
        print(f"         {key}: {value}")

    return columnas


def validar_coordenadas(
    df: pd.DataFrame,
    col_lat: str,
    col_lon: str
) -> Tuple[pd.DataFrame, Dict]:
    """
    Valida y limpia las coordenadas del inventario.

    Criterios de validación:
        - Latitud: -5 a 2 (rango Ecuador)
        - Longitud: -82 a -75 (rango Ecuador)
        - No nulos
        - Valores numéricos

    Referencia:
        Guzzetti et al. (2012) - Requisitos de calidad para inventarios

    Args:
        df: DataFrame con coordenadas
        col_lat: Nombre columna latitud
        col_lon: Nombre columna longitud

    Returns:
        Tuple[pd.DataFrame, Dict]: (DataFrame limpio, estadísticas)
    """
    print("\n[INFO] Validando coordenadas...")

    stats = {
        'registros_iniciales': len(df),
        'nulos_latitud': 0,
        'nulos_longitud': 0,
        'fuera_rango': 0,
        'registros_validos': 0
    }

    # Contar nulos
    stats['nulos_latitud'] = df[col_lat].isna().sum()
    stats['nulos_longitud'] = df[col_lon].isna().sum()

    # Eliminar nulos
    df_limpio = df.dropna(subset=[col_lat, col_lon])

    # Convertir a numérico
    df_limpio[col_lat] = pd.to_numeric(df_limpio[col_lat], errors='coerce')
    df_limpio[col_lon] = pd.to_numeric(df_limpio[col_lon], errors='coerce')
    df_limpio = df_limpio.dropna(subset=[col_lat, col_lon])

    # Validar rangos para Ecuador
    # Latitud: -5 a 2
    # Longitud: -82 a -75
    mask_valido = (
        (df_limpio[col_lat] >= -5) & (df_limpio[col_lat] <= 2) &
        (df_limpio[col_lon] >= -82) & (df_limpio[col_lon] <= -75)
    )

    stats['fuera_rango'] = (~mask_valido).sum()
    df_limpio = df_limpio[mask_valido]

    stats['registros_validos'] = len(df_limpio)

    print(f"       Registros iniciales: {stats['registros_iniciales']:,}")
    print(f"       Nulos en latitud: {stats['nulos_latitud']}")
    print(f"       Nulos en longitud: {stats['nulos_longitud']}")
    print(f"       Fuera de rango Ecuador: {stats['fuera_rango']}")
    print(f"       Registros válidos: {stats['registros_validos']:,}")

    return df_limpio, stats


def filtrar_deslizamientos(df: pd.DataFrame, col_evento: str) -> pd.DataFrame:
    """
    Filtra solo los eventos de tipo DESLIZAMIENTO.

    Args:
        df: DataFrame del inventario
        col_evento: Nombre de la columna de tipo de evento

    Returns:
        pd.DataFrame: Solo deslizamientos
    """
    print("\n[INFO] Filtrando eventos de tipo DESLIZAMIENTO...")

    # Tipos de evento en el inventario
    tipos = df[col_evento].value_counts()
    print("       Tipos de evento encontrados:")
    for tipo, count in tipos.items():
        print(f"         {tipo}: {count:,}")

    # Filtrar deslizamientos (buscar variantes)
    keywords = ['DESLIZAMIENTO', 'DESLIZ', 'LANDSLIDE', 'DERRUMBE']

    mask = df[col_evento].str.upper().str.contains('|'.join(keywords), na=False)
    df_desl = df[mask].copy()

    print(f"\n       Deslizamientos encontrados: {len(df_desl):,}")

    return df_desl


def crear_geodataframe(
    df: pd.DataFrame,
    col_lat: str,
    col_lon: str,
    crs_origen: str = "EPSG:4326"
) -> gpd.GeoDataFrame:
    """
    Convierte DataFrame a GeoDataFrame.

    Args:
        df: DataFrame con coordenadas
        col_lat: Columna de latitud
        col_lon: Columna de longitud
        crs_origen: CRS de las coordenadas

    Returns:
        gpd.GeoDataFrame: GeoDataFrame georreferenciado
    """
    print(f"\n[INFO] Creando GeoDataFrame (CRS: {crs_origen})...")

    # Crear geometría
    geometry = [Point(xy) for xy in zip(df[col_lon], df[col_lat])]

    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs_origen)

    print(f"       Puntos creados: {len(gdf):,}")

    return gdf


def reproyectar(gdf: gpd.GeoDataFrame, crs_destino: str) -> gpd.GeoDataFrame:
    """
    Reproyecta el GeoDataFrame a un nuevo CRS.

    Args:
        gdf: GeoDataFrame origen
        crs_destino: CRS destino (ej: EPSG:32717)

    Returns:
        gpd.GeoDataFrame: GeoDataFrame reproyectado
    """
    print(f"\n[INFO] Reproyectando a {crs_destino}...")

    gdf_reproyectado = gdf.to_crs(crs_destino)

    # Añadir columnas de coordenadas UTM
    gdf_reproyectado['X_UTM'] = gdf_reproyectado.geometry.x
    gdf_reproyectado['Y_UTM'] = gdf_reproyectado.geometry.y

    print(f"       CRS resultante: {gdf_reproyectado.crs}")

    return gdf_reproyectado


def filtrar_por_aoi(gdf: gpd.GeoDataFrame, aoi_path: Path) -> gpd.GeoDataFrame:
    """
    Filtra puntos que caen dentro del área de interés (Imbabura).

    Args:
        gdf: GeoDataFrame de deslizamientos
        aoi_path: Ruta al GeoPackage del AOI

    Returns:
        gpd.GeoDataFrame: Puntos dentro del AOI
    """
    print(f"\n[INFO] Filtrando por AOI: {aoi_path.name}...")

    if not aoi_path.exists():
        print(f"  ADVERTENCIA: No se encontró AOI, se omite filtro espacial")
        return gdf

    # Cargar AOI
    aoi = gpd.read_file(aoi_path)

    # Asegurar mismo CRS
    if aoi.crs != gdf.crs:
        aoi = aoi.to_crs(gdf.crs)

    # Unir polígonos del AOI
    aoi_union = aoi.unary_union

    # Filtrar puntos dentro del AOI
    mask = gdf.geometry.within(aoi_union)
    gdf_filtrado = gdf[mask].copy()

    print(f"       Puntos antes del filtro: {len(gdf):,}")
    print(f"       Puntos dentro del AOI: {len(gdf_filtrado):,}")
    print(f"       Puntos fuera del AOI: {(~mask).sum()}")

    return gdf_filtrado


def analisis_exploratorio(gdf: gpd.GeoDataFrame, col_mapping: Dict, dir_salida: Path):
    """
    Realiza análisis exploratorio del inventario.

    Args:
        gdf: GeoDataFrame del inventario
        col_mapping: Mapeo de columnas
        dir_salida: Directorio para guardar gráficos
    """
    print("\n[INFO] Realizando análisis exploratorio...")

    estadisticas = {}

    # Estadísticas generales
    estadisticas['total_registros'] = len(gdf)
    estadisticas['bbox'] = {
        'minx': float(gdf.total_bounds[0]),
        'miny': float(gdf.total_bounds[1]),
        'maxx': float(gdf.total_bounds[2]),
        'maxy': float(gdf.total_bounds[3])
    }

    # Por año (si existe columna)
    col_anio = col_mapping.get('anio')
    if col_anio and col_anio in gdf.columns:
        por_anio = gdf[col_anio].value_counts().sort_index()
        estadisticas['por_anio'] = por_anio.to_dict()

        print("\n       Deslizamientos por año:")
        for anio, count in por_anio.items():
            print(f"         {int(anio)}: {count}")

        # Gráfico temporal
        fig, ax = plt.subplots(figsize=(12, 5))
        por_anio.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black')
        ax.set_xlabel('Año')
        ax.set_ylabel('Número de deslizamientos')
        ax.set_title('Distribución Temporal de Deslizamientos - Imbabura (2010-2023)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(dir_salida / 'distribucion_temporal_deslizamientos.png', dpi=150)
        plt.close()

    # Por cantón (si existe columna)
    col_canton = col_mapping.get('canton')
    if col_canton and col_canton in gdf.columns:
        por_canton = gdf[col_canton].value_counts()
        estadisticas['por_canton'] = por_canton.to_dict()

        print("\n       Deslizamientos por cantón:")
        for canton, count in por_canton.items():
            print(f"         {canton}: {count}")

        # Gráfico por cantón
        fig, ax = plt.subplots(figsize=(10, 6))
        por_canton.plot(kind='barh', ax=ax, color='coral', edgecolor='black')
        ax.set_xlabel('Número de deslizamientos')
        ax.set_ylabel('Cantón')
        ax.set_title('Distribución de Deslizamientos por Cantón')
        plt.tight_layout()
        plt.savefig(dir_salida / 'distribucion_cantonal_deslizamientos.png', dpi=150)
        plt.close()

    # Guardar estadísticas
    with open(dir_salida / 'estadisticas_inventario.json', 'w', encoding='utf-8') as f:
        json.dump(estadisticas, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n       Gráficos guardados en: {dir_salida}")

    return estadisticas


def generar_auditoria(
    stats_validacion: Dict,
    stats_exploratorio: Dict,
    ruta_entrada: Path,
    ruta_salida: Path,
    dir_auditoria: Path
):
    """
    Genera archivo de auditoría del proceso.
    """
    auditoria = {
        "proceso": "PREPARACION_INVENTARIO",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",

        "entradas": {
            "archivo": str(ruta_entrada),
            "fuente": "Servicio Nacional de Gestión de Riesgos (SNGR)",
            "periodo": f"{ANIO_INICIO}-{ANIO_FIN}"
        },

        "salidas": {
            "archivo": str(ruta_salida),
            "formato": "GeoPackage",
            "crs": CRS_DESTINO
        },

        "validacion": stats_validacion,
        "estadisticas": stats_exploratorio,

        "referencias_metodologicas": {
            "inventarios": "Guzzetti et al. (2012). Earth-Science Reviews, 112(1-2), 42-66",
            "calidad": "Fell et al. (2008). Engineering Geology, 102(3-4), 85-98"
        },

        "normas_aplicadas": [
            "ISO 19157:2013 - Calidad de datos geográficos",
            "ISO 19115-1:2014 - Metadatos geográficos"
        ]
    }

    ruta_auditoria = dir_auditoria / "AUDITORIA_INVENTARIO.json"
    with open(ruta_auditoria, 'w', encoding='utf-8') as f:
        json.dump(auditoria, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[INFO] Auditoría guardada: {ruta_auditoria.name}")


def main():
    """Función principal del script."""
    tiempo_inicio = datetime.now()

    imprimir_banner()

    # Crear directorio de salida
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    # 1. Cargar inventario
    try:
        df = cargar_inventario_excel(INVENTARIO_XLSX)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        print("\n Por favor, verifica la ruta del archivo Excel en la configuración.")
        return
    except Exception as e:
        print(f"\n ERROR al cargar Excel: {e}")
        return

    # 2. Identificar columnas
    col_mapping = identificar_columnas(df)

    if 'latitud' not in col_mapping or 'longitud' not in col_mapping:
        print("\n ERROR: No se encontraron columnas de coordenadas")
        print("       Columnas disponibles:", list(df.columns))
        return

    # 3. Validar coordenadas
    df_valido, stats_validacion = validar_coordenadas(
        df,
        col_mapping['latitud'],
        col_mapping['longitud']
    )

    if len(df_valido) == 0:
        print("\n ERROR: No quedaron registros válidos después de la validación")
        return

    # 4. Filtrar solo deslizamientos
    if 'evento' in col_mapping:
        df_desl = filtrar_deslizamientos(df_valido, col_mapping['evento'])
    else:
        print("\n[INFO] No se encontró columna de tipo de evento, se usan todos los registros")
        df_desl = df_valido

    if len(df_desl) == 0:
        print("\n ERROR: No se encontraron eventos de tipo DESLIZAMIENTO")
        return

    # 5. Crear GeoDataFrame
    gdf = crear_geodataframe(
        df_desl,
        col_mapping['latitud'],
        col_mapping['longitud'],
        CRS_ORIGEN
    )

    # 6. Reproyectar a UTM 17S
    gdf_utm = reproyectar(gdf, CRS_DESTINO)

    # 7. Filtrar por AOI (si existe)
    gdf_final = filtrar_por_aoi(gdf_utm, AOI_GPKG)

    # 8. Análisis exploratorio
    stats_exploratorio = analisis_exploratorio(gdf_final, col_mapping, DIR_SALIDA)

    # 9. Guardar GeoPackage
    ruta_salida = DIR_SALIDA / "inventario_deslizamientos.gpkg"
    gdf_final.to_file(ruta_salida, driver="GPKG")
    print(f"\n[INFO] Inventario guardado: {ruta_salida.name}")

    # 10. Generar auditoría
    generar_auditoria(
        stats_validacion,
        stats_exploratorio,
        INVENTARIO_XLSX,
        ruta_salida,
        DIR_SALIDA
    )

    # Resumen final
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL")
    print("=" * 70)
    print(f"\n Registros originales:    {stats_validacion['registros_iniciales']:,}")
    print(f" Registros válidos:       {stats_validacion['registros_validos']:,}")
    print(f" Deslizamientos finales:  {len(gdf_final):,}")
    print(f"\n CRS:                     {CRS_DESTINO}")
    print(f" Extent X:                [{gdf_final.total_bounds[0]:.2f}, {gdf_final.total_bounds[2]:.2f}]")
    print(f" Extent Y:                [{gdf_final.total_bounds[1]:.2f}, {gdf_final.total_bounds[3]:.2f}]")

    print(f"\n Duración: {tiempo_total}")
    print(f" Archivos en: {DIR_SALIDA}")
    print("=" * 70)
    print(" ✅ INVENTARIO PREPARADO EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    main()
