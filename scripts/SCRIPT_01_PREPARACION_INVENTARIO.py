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
    Procesa el inventario de deslizamientos del SNGR (2010-2023):
    1. Lectura del archivo Excel original
    2. Validación y limpieza de coordenadas
    3. Reproyección a UTM 17S (EPSG:32717)
    4. Filtrado espacial dentro del AOI de Imbabura
    5. Análisis exploratorio
    6. Exportación a GeoPackage

Fuente de datos:
    - DESLIZAMIENTOS_SGNR.xlsx (SNGR, 2010-2023)

Referencias:
    - Guzzetti, F., et al. (2012). Landslide inventory maps: New tools for an
      old problem. Earth-Science Reviews, 112(1-2), 42-66.
    - Fell, R., et al. (2008). Guidelines for landslide susceptibility, hazard
      and risk zoning. Engineering Geology, 102(3-4), 85-98.

Normas: ISO 19157:2013, ISO 19115-1:2014
================================================================================
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import geopandas as gpd
    from shapely.geometry import Point
except ImportError:
    print("ERROR: geopandas no instalado. Ejecute: pip install geopandas")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURACIÓN - MODIFICAR SEGÚN TU SISTEMA
# ==============================================================================

BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Archivos de entrada
INVENTARIO_XLSX = BASE_PATH / "DESLIZAMIENTOS_SGNR.xlsx"
AOI_GPKG = Path(r"D:\DATA\AOI_IMBABURA_CANTON.gpkg")

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "01_PROCESSED"

# Sistemas de coordenadas
CRS_ORIGEN = "EPSG:4326"      # WGS84 (lat/lon)
CRS_DESTINO = "EPSG:32717"    # UTM zona 17S

# Período de análisis
ANIO_INICIO = 2010
ANIO_FIN = 2023


def imprimir_banner():
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
    """Carga el inventario desde Excel."""
    print(f"\n[INFO] Cargando inventario: {ruta.name}")

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")

    df = pd.read_excel(ruta, engine='openpyxl')

    print(f"       Registros cargados: {len(df):,}")
    print(f"       Columnas: {list(df.columns)}")

    return df


def identificar_columnas(df: pd.DataFrame) -> dict:
    """Identifica automáticamente las columnas clave."""
    print("\n[INFO] Identificando columnas...")

    columnas = {}
    cols_lower = {c.lower(): c for c in df.columns}

    # Latitud
    for c in ['latitud', 'lat', 'latitude', 'y']:
        if c in cols_lower:
            columnas['latitud'] = cols_lower[c]
            break

    # Longitud
    for c in ['longitud', 'lon', 'longitude', 'x', 'long']:
        if c in cols_lower:
            columnas['longitud'] = cols_lower[c]
            break

    # Fecha
    for c in ['fecha', 'date', 'fecha_evento', 'fecha del evento']:
        if c in cols_lower:
            columnas['fecha'] = cols_lower[c]
            break

    # Evento
    for c in ['evento', 'tipo_evento', 'event', 'tipo']:
        if c in cols_lower:
            columnas['evento'] = cols_lower[c]
            break

    # Cantón
    for c in ['canton', 'cantón', 'dpa_canton']:
        if c in cols_lower:
            columnas['canton'] = cols_lower[c]
            break

    # Año
    for c in ['anio', 'año', 'year']:
        if c in cols_lower:
            columnas['anio'] = cols_lower[c]
            break

    print("       Columnas identificadas:")
    for key, value in columnas.items():
        print(f"         {key}: {value}")

    return columnas


def validar_coordenadas(df: pd.DataFrame, col_lat: str, col_lon: str) -> tuple:
    """
    Valida coordenadas según criterios de calidad ISO 19157.

    Criterios:
        - Latitud: -5 a 2 (Ecuador)
        - Longitud: -82 a -75 (Ecuador)
        - Sin valores nulos
    """
    print("\n[INFO] Validando coordenadas (ISO 19157)...")

    stats = {
        'registros_iniciales': len(df),
        'nulos_latitud': int(df[col_lat].isna().sum()),
        'nulos_longitud': int(df[col_lon].isna().sum()),
        'fuera_rango': 0,
        'registros_validos': 0
    }

    # Eliminar nulos
    df_limpio = df.dropna(subset=[col_lat, col_lon])

    # Convertir a numérico
    df_limpio[col_lat] = pd.to_numeric(df_limpio[col_lat], errors='coerce')
    df_limpio[col_lon] = pd.to_numeric(df_limpio[col_lon], errors='coerce')
    df_limpio = df_limpio.dropna(subset=[col_lat, col_lon])

    # Validar rangos Ecuador
    mask_valido = (
        (df_limpio[col_lat] >= -5) & (df_limpio[col_lat] <= 2) &
        (df_limpio[col_lon] >= -82) & (df_limpio[col_lon] <= -75)
    )

    stats['fuera_rango'] = int((~mask_valido).sum())
    df_limpio = df_limpio[mask_valido]
    stats['registros_validos'] = len(df_limpio)

    print(f"       Registros iniciales: {stats['registros_iniciales']:,}")
    print(f"       Nulos latitud: {stats['nulos_latitud']}")
    print(f"       Nulos longitud: {stats['nulos_longitud']}")
    print(f"       Fuera de rango: {stats['fuera_rango']}")
    print(f"       Registros válidos: {stats['registros_validos']:,}")

    return df_limpio, stats


def filtrar_deslizamientos(df: pd.DataFrame, col_evento: str) -> pd.DataFrame:
    """Filtra solo eventos de tipo DESLIZAMIENTO."""
    print("\n[INFO] Filtrando eventos de tipo DESLIZAMIENTO...")

    # Mostrar tipos encontrados
    tipos = df[col_evento].value_counts()
    print("       Tipos de evento encontrados:")
    for tipo, count in tipos.items():
        print(f"         {tipo}: {count:,}")

    # Filtrar deslizamientos
    keywords = ['DESLIZAMIENTO', 'DESLIZ', 'LANDSLIDE', 'DERRUMBE']
    mask = df[col_evento].str.upper().str.contains('|'.join(keywords), na=False)
    df_desl = df[mask].copy()

    print(f"\n       Deslizamientos encontrados: {len(df_desl):,}")

    return df_desl


def crear_geodataframe(df: pd.DataFrame, col_lat: str, col_lon: str) -> gpd.GeoDataFrame:
    """Convierte DataFrame a GeoDataFrame."""
    print(f"\n[INFO] Creando GeoDataFrame (CRS: {CRS_ORIGEN})...")

    geometry = [Point(xy) for xy in zip(df[col_lon], df[col_lat])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=CRS_ORIGEN)

    print(f"       Puntos creados: {len(gdf):,}")

    return gdf


def reproyectar(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Reproyecta a UTM 17S."""
    print(f"\n[INFO] Reproyectando a {CRS_DESTINO}...")

    gdf_utm = gdf.to_crs(CRS_DESTINO)
    gdf_utm['X_UTM'] = gdf_utm.geometry.x
    gdf_utm['Y_UTM'] = gdf_utm.geometry.y

    print(f"       CRS resultante: {gdf_utm.crs}")

    return gdf_utm


def filtrar_por_aoi(gdf: gpd.GeoDataFrame, aoi_path: Path) -> gpd.GeoDataFrame:
    """Filtra puntos dentro del AOI de Imbabura."""
    print(f"\n[INFO] Filtrando por AOI: {aoi_path.name}...")

    if not aoi_path.exists():
        print("  ADVERTENCIA: No se encontró AOI, se omite filtro")
        return gdf

    aoi = gpd.read_file(aoi_path)
    if aoi.crs != gdf.crs:
        aoi = aoi.to_crs(gdf.crs)

    aoi_union = aoi.unary_union
    mask = gdf.geometry.within(aoi_union)
    gdf_filtrado = gdf[mask].copy()

    print(f"       Puntos antes: {len(gdf):,}")
    print(f"       Puntos dentro AOI: {len(gdf_filtrado):,}")
    print(f"       Puntos fuera AOI: {(~mask).sum()}")

    return gdf_filtrado


def analisis_exploratorio(gdf: gpd.GeoDataFrame, col_mapping: dict, dir_salida: Path) -> dict:
    """Análisis exploratorio con gráficos."""
    print("\n[INFO] Realizando análisis exploratorio...")

    estadisticas = {
        'total_registros': len(gdf),
        'bbox': {
            'minx': float(gdf.total_bounds[0]),
            'miny': float(gdf.total_bounds[1]),
            'maxx': float(gdf.total_bounds[2]),
            'maxy': float(gdf.total_bounds[3])
        }
    }

    # Por año
    col_anio = col_mapping.get('anio')
    if col_anio and col_anio in gdf.columns:
        por_anio = gdf[col_anio].value_counts().sort_index()
        estadisticas['por_anio'] = {int(k): int(v) for k, v in por_anio.items()}

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
        plt.savefig(dir_salida / 'fig_temporal_deslizamientos.png', dpi=150)
        plt.close()

    # Por cantón
    col_canton = col_mapping.get('canton')
    if col_canton and col_canton in gdf.columns:
        por_canton = gdf[col_canton].value_counts()
        estadisticas['por_canton'] = {str(k): int(v) for k, v in por_canton.items()}

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
        plt.savefig(dir_salida / 'fig_cantonal_deslizamientos.png', dpi=150)
        plt.close()

    # Guardar estadísticas
    with open(dir_salida / 'estadisticas_inventario.json', 'w', encoding='utf-8') as f:
        json.dump(estadisticas, f, indent=2, ensure_ascii=False)

    print(f"\n       Gráficos guardados en: {dir_salida}")

    return estadisticas


def generar_auditoria(stats_val: dict, stats_exp: dict, dir_salida: Path):
    """Genera auditoría ISO 19115."""
    auditoria = {
        "proceso": "PREPARACION_INVENTARIO",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",

        "entradas": {
            "archivo": str(INVENTARIO_XLSX),
            "fuente": "Servicio Nacional de Gestión de Riesgos (SNGR)",
            "periodo": f"{ANIO_INICIO}-{ANIO_FIN}"
        },

        "validacion_iso19157": {
            "completitud": round(stats_val['registros_validos'] / stats_val['registros_iniciales'] * 100, 2),
            "registros_iniciales": stats_val['registros_iniciales'],
            "registros_validos": stats_val['registros_validos'],
            "nulos_eliminados": stats_val['nulos_latitud'] + stats_val['nulos_longitud'],
            "fuera_rango_eliminados": stats_val['fuera_rango']
        },

        "estadisticas": stats_exp,

        "referencias": [
            "Guzzetti et al. (2012). Earth-Science Reviews, 112(1-2), 42-66",
            "Fell et al. (2008). Engineering Geology, 102(3-4), 85-98"
        ],

        "normas": ["ISO 19157:2013", "ISO 19115-1:2014"]
    }

    with open(dir_salida / "AUDITORIA_INVENTARIO.json", 'w', encoding='utf-8') as f:
        json.dump(auditoria, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[INFO] Auditoría guardada: AUDITORIA_INVENTARIO.json")


def main():
    tiempo_inicio = datetime.now()

    imprimir_banner()

    # Crear directorio de salida
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    # 1. Cargar inventario
    try:
        df = cargar_inventario_excel(INVENTARIO_XLSX)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        return

    # 2. Identificar columnas
    col_mapping = identificar_columnas(df)

    if 'latitud' not in col_mapping or 'longitud' not in col_mapping:
        print("\n ERROR: No se encontraron columnas de coordenadas")
        return

    # 3. Validar coordenadas
    df_valido, stats_val = validar_coordenadas(
        df, col_mapping['latitud'], col_mapping['longitud']
    )

    if len(df_valido) == 0:
        print("\n ERROR: No quedaron registros válidos")
        return

    # 4. Filtrar deslizamientos
    if 'evento' in col_mapping:
        df_desl = filtrar_deslizamientos(df_valido, col_mapping['evento'])
    else:
        df_desl = df_valido

    if len(df_desl) == 0:
        print("\n ERROR: No se encontraron deslizamientos")
        return

    # 5. Crear GeoDataFrame
    gdf = crear_geodataframe(df_desl, col_mapping['latitud'], col_mapping['longitud'])

    # 6. Reproyectar
    gdf_utm = reproyectar(gdf)

    # 7. Filtrar por AOI
    gdf_final = filtrar_por_aoi(gdf_utm, AOI_GPKG)

    # 8. Análisis exploratorio
    stats_exp = analisis_exploratorio(gdf_final, col_mapping, DIR_SALIDA)

    # 9. Guardar GeoPackage
    ruta_salida = DIR_SALIDA / "inventario_deslizamientos.gpkg"
    gdf_final.to_file(ruta_salida, driver="GPKG")
    print(f"\n[INFO] Inventario guardado: {ruta_salida.name}")

    # 10. Auditoría
    generar_auditoria(stats_val, stats_exp, DIR_SALIDA)

    # Resumen
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL")
    print("=" * 70)
    print(f"\n Registros originales:    {stats_val['registros_iniciales']:,}")
    print(f" Registros válidos:       {stats_val['registros_validos']:,}")
    print(f" Deslizamientos finales:  {len(gdf_final):,}")
    print(f"\n CRS: {CRS_DESTINO}")
    print(f" Extent X: [{gdf_final.total_bounds[0]:.2f}, {gdf_final.total_bounds[2]:.2f}]")
    print(f" Extent Y: [{gdf_final.total_bounds[1]:.2f}, {gdf_final.total_bounds[3]:.2f}]")
    print(f"\n Duración: {tiempo_total}")
    print(f" Archivos en: {DIR_SALIDA}")
    print("=" * 70)
    print(" ✅ INVENTARIO PREPARADO EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    main()
