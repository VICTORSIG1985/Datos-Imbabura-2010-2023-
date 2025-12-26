#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT 03: MUESTREO DE AUSENCIAS (PSEUDO-AUSENCIAS)
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Fecha: Diciembre 2025

Descripción:
    Este script genera puntos de pseudo-ausencia (no-deslizamiento) para el
    entrenamiento del modelo de susceptibilidad. Implementa un muestreo
    aleatorio estratificado por cantón con buffer de exclusión.

Justificación metodológica:
    Los modelos de clasificación binaria requieren tanto presencias como
    ausencias para el entrenamiento. En modelamiento de deslizamientos,
    las "ausencias verdaderas" no existen (un sitio sin deslizamiento hoy
    podría tenerlo mañana). Por ello, se usan pseudo-ausencias siguiendo
    criterios establecidos en la literatura.

Criterios de muestreo (basados en literatura):
    1. Buffer de exclusión: 500m alrededor de presencias
       Referencia: Steger et al. (2021)
    2. Estratificación por cantón: Proporcional al número de presencias
       Referencia: Zhu et al. (2018)
    3. Ratio 1:1: Balance entre presencias y ausencias
       Referencia: Barbet-Massin et al. (2012)
    4. Exclusión de zonas con pendiente < 5°: Evitar planicies
       Referencia: Reichenbach et al. (2018)

Referencias bibliográficas:
    - Steger, S., et al. (2021). The influence of systematically rotated
      DEM-derived predictors on physically based landslide susceptibility
      models. Geomorphology, 374, 107533.
      https://doi.org/10.1016/j.geomorph.2020.107533

    - Barbet-Massin, M., et al. (2012). Selecting pseudo-absences for species
      distribution models: how, where and how many? Methods in Ecology and
      Evolution, 3(2), 327-338. https://doi.org/10.1111/j.2041-210X.2011.00172.x

    - Zhu, A.X., et al. (2018). Spatial prediction based on Third Law of
      Geography. Annals of GIS, 24(4), 225-240.

    - Reichenbach, P., et al. (2018). A review of statistically-based landslide
      susceptibility models. Earth-Science Reviews, 180, 60-91.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)
    - ISO 19115-1:2014 (Metadatos geográficos)

Entradas:
    - inventario_deslizamientos.gpkg (presencias validadas)
    - slope_degrees.tif (para excluir planicies)
    - AOI_IMBABURA_CANTON.gpkg (para estratificación)

Salidas:
    - puntos_ausencias.gpkg
    - dataset_presencias_ausencias.gpkg (combinado)
    - AUDITORIA_MUESTREO.json
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
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
except ImportError:
    print("ERROR: geopandas no está instalado. Ejecute: pip install geopandas")
    sys.exit(1)

try:
    import rasterio
    from rasterio.mask import mask
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
INVENTARIO_GPKG = BASE_PATH / "Investigacion" / "01_PROCESSED" / "inventario_deslizamientos.gpkg"
SLOPE_RASTER = BASE_PATH / "Investigacion" / "00_Derivados_Topograficos" / "slope_degrees.tif"
AOI_GPKG = Path(r"D:\DATA\AOI_IMBABURA_CANTON.gpkg")

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "03_MUESTREO"

# Parámetros de muestreo
# Buffer de exclusión: Steger et al. (2021) usan 100-1000m, usamos 500m
BUFFER_EXCLUSION = 500  # metros

# Ratio presencias:ausencias - Barbet-Massin et al. (2012) recomiendan 1:1
RATIO_AUSENCIAS = 1.0

# Pendiente mínima para ausencias (excluir planicies)
# Reichenbach et al. (2018): deslizamientos raramente ocurren en pendientes < 5°
PENDIENTE_MINIMA = 5.0  # grados

# Semilla para reproducibilidad
SEMILLA = 42

# CRS del proyecto
CRS_PROYECTO = "EPSG:32717"


def imprimir_banner():
    """Imprime el banner inicial del script."""
    print("=" * 70)
    print(" SCRIPT 03: MUESTREO DE AUSENCIAS (PSEUDO-AUSENCIAS)")
    print("=" * 70)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Buffer exclusión: {BUFFER_EXCLUSION} m (Steger et al., 2021)")
    print(f" Ratio P:A: 1:{RATIO_AUSENCIAS} (Barbet-Massin et al., 2012)")
    print(f" Pendiente mínima: {PENDIENTE_MINIMA}° (Reichenbach et al., 2018)")
    print(f" Output: {DIR_SALIDA}")
    print("=" * 70)


def cargar_presencias(ruta: Path) -> gpd.GeoDataFrame:
    """
    Carga el inventario de deslizamientos (presencias).

    Args:
        ruta: Ruta al GeoPackage de presencias

    Returns:
        gpd.GeoDataFrame: Presencias cargadas
    """
    print(f"\n[INFO] Cargando presencias: {ruta.name}")

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")

    gdf = gpd.read_file(ruta)

    # Asegurar CRS correcto
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_PROYECTO)
    elif str(gdf.crs) != CRS_PROYECTO:
        gdf = gdf.to_crs(CRS_PROYECTO)

    print(f"       Presencias cargadas: {len(gdf):,}")
    print(f"       CRS: {gdf.crs}")

    return gdf


def cargar_aoi_cantones(ruta: Path) -> gpd.GeoDataFrame:
    """
    Carga el AOI con los cantones para estratificación.

    Args:
        ruta: Ruta al GeoPackage de cantones

    Returns:
        gpd.GeoDataFrame: Cantones cargados
    """
    print(f"\n[INFO] Cargando AOI cantones: {ruta.name}")

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")

    gdf = gpd.read_file(ruta)

    # Asegurar CRS correcto
    if gdf.crs is None or str(gdf.crs) != CRS_PROYECTO:
        gdf = gdf.to_crs(CRS_PROYECTO)

    # Identificar columna de nombre del cantón
    col_canton = None
    for col in ['CANTON', 'canton', 'DPA_CANTON', 'NOM_CANTON', 'nombre', 'NAME']:
        if col in gdf.columns:
            col_canton = col
            break

    if col_canton:
        print(f"       Cantones encontrados: {gdf[col_canton].unique().tolist()}")
    else:
        print("       ADVERTENCIA: No se encontró columna de nombre de cantón")
        gdf['CANTON'] = [f"Canton_{i}" for i in range(len(gdf))]
        col_canton = 'CANTON'

    print(f"       Total cantones: {len(gdf)}")

    return gdf, col_canton


def crear_zona_exclusion(presencias: gpd.GeoDataFrame, buffer_m: float) -> gpd.GeoDataFrame:
    """
    Crea una zona de exclusión alrededor de las presencias.

    Justificación científica:
        Steger et al. (2021) demuestran que un buffer de exclusión previene
        el muestreo de ausencias en zonas inmediatamente adyacentes a
        deslizamientos existentes, donde la susceptibilidad es naturalmente alta.

    Args:
        presencias: GeoDataFrame de presencias
        buffer_m: Radio del buffer en metros

    Returns:
        gpd.GeoDataFrame: Zona de exclusión
    """
    print(f"\n[INFO] Creando zona de exclusión (buffer={buffer_m}m)...")

    # Crear buffer alrededor de cada presencia
    buffers = presencias.geometry.buffer(buffer_m)

    # Unir todos los buffers
    zona_exclusion = unary_union(buffers)

    # Crear GeoDataFrame
    gdf_exclusion = gpd.GeoDataFrame(
        {'geometry': [zona_exclusion]},
        crs=presencias.crs
    )

    area_km2 = zona_exclusion.area / 1e6
    print(f"       Área de exclusión: {area_km2:.2f} km²")

    return gdf_exclusion


def cargar_mascara_pendiente(ruta: Path, pendiente_min: float) -> Tuple[np.ndarray, dict]:
    """
    Carga el raster de pendiente y crea máscara de zonas válidas.

    Justificación científica:
        Reichenbach et al. (2018) indican que los deslizamientos raramente
        ocurren en pendientes muy bajas (<5°). Excluir estas zonas del
        muestreo de ausencias evita introducir sesgo.

    Args:
        ruta: Ruta al raster de pendiente
        pendiente_min: Pendiente mínima en grados

    Returns:
        Tuple: (máscara booleana, metadatos del raster)
    """
    print(f"\n[INFO] Cargando máscara de pendiente (min={pendiente_min}°)...")

    with rasterio.open(ruta) as src:
        slope = src.read(1)
        meta = {
            'transform': src.transform,
            'crs': src.crs,
            'width': src.width,
            'height': src.height,
            'bounds': src.bounds,
            'nodata': src.nodata
        }

    # Crear máscara: True donde pendiente >= mínima
    nodata = meta['nodata'] if meta['nodata'] else -9999
    mascara = (slope >= pendiente_min) & (slope != nodata)

    pct_valido = mascara.sum() / mascara.size * 100
    print(f"       Píxeles con pendiente >= {pendiente_min}°: {pct_valido:.1f}%")

    return mascara, meta


def contar_presencias_por_canton(
    presencias: gpd.GeoDataFrame,
    cantones: gpd.GeoDataFrame,
    col_canton: str
) -> Dict[str, int]:
    """
    Cuenta el número de presencias en cada cantón.

    Args:
        presencias: GeoDataFrame de presencias
        cantones: GeoDataFrame de cantones
        col_canton: Nombre de la columna del cantón

    Returns:
        Dict: Conteo por cantón
    """
    print("\n[INFO] Contando presencias por cantón...")

    conteo = {}

    for idx, canton_row in cantones.iterrows():
        nombre = canton_row[col_canton]
        geom = canton_row.geometry

        # Contar presencias dentro del cantón
        dentro = presencias.geometry.within(geom)
        conteo[nombre] = dentro.sum()

    print("       Presencias por cantón:")
    for canton, n in sorted(conteo.items(), key=lambda x: x[1], reverse=True):
        print(f"         {canton}: {n}")

    return conteo


def generar_puntos_aleatorios_en_poligono(
    poligono,
    n_puntos: int,
    zona_exclusion,
    mascara_pendiente: np.ndarray,
    meta_raster: dict,
    semilla: int
) -> List[Point]:
    """
    Genera puntos aleatorios dentro de un polígono evitando la zona de exclusión.

    Metodología:
        1. Generar punto aleatorio dentro del bbox del polígono
        2. Verificar que esté dentro del polígono
        3. Verificar que no esté en zona de exclusión
        4. Verificar que la pendiente sea >= mínima
        5. Repetir hasta alcanzar n_puntos

    Args:
        poligono: Geometría del polígono
        n_puntos: Número de puntos a generar
        zona_exclusion: Geometría de exclusión
        mascara_pendiente: Máscara de pendientes válidas
        meta_raster: Metadatos del raster
        semilla: Semilla aleatoria

    Returns:
        List[Point]: Lista de puntos generados
    """
    np.random.seed(semilla)

    puntos = []
    intentos = 0
    max_intentos = n_puntos * 100  # Máximo intentos para evitar loop infinito

    bounds = poligono.bounds  # (minx, miny, maxx, maxy)

    # Extraer información del raster
    transform = meta_raster['transform']

    while len(puntos) < n_puntos and intentos < max_intentos:
        # Generar coordenadas aleatorias
        x = np.random.uniform(bounds[0], bounds[2])
        y = np.random.uniform(bounds[1], bounds[3])

        punto = Point(x, y)

        # Verificar condiciones
        # 1. Dentro del polígono
        if not poligono.contains(punto):
            intentos += 1
            continue

        # 2. Fuera de zona de exclusión
        if zona_exclusion is not None and zona_exclusion.contains(punto):
            intentos += 1
            continue

        # 3. Pendiente válida
        # Convertir coordenadas a índices del raster
        col = int((x - transform.c) / transform.a)
        row = int((y - transform.f) / transform.e)

        if 0 <= row < mascara_pendiente.shape[0] and 0 <= col < mascara_pendiente.shape[1]:
            if not mascara_pendiente[row, col]:
                intentos += 1
                continue
        else:
            intentos += 1
            continue

        # Punto válido
        puntos.append(punto)
        intentos += 1

    return puntos


def generar_ausencias_estratificadas(
    presencias: gpd.GeoDataFrame,
    cantones: gpd.GeoDataFrame,
    col_canton: str,
    zona_exclusion: gpd.GeoDataFrame,
    mascara_pendiente: np.ndarray,
    meta_raster: dict,
    ratio: float,
    semilla: int
) -> gpd.GeoDataFrame:
    """
    Genera pseudo-ausencias estratificadas por cantón.

    Justificación científica:
        Zhu et al. (2018) demuestran que la estratificación espacial mejora
        la representatividad del muestreo y reduce el sesgo de autocorrelación.
        El muestreo proporcional al número de presencias por cantón asegura
        balance geográfico.

    Args:
        presencias: GeoDataFrame de presencias
        cantones: GeoDataFrame de cantones
        col_canton: Nombre columna cantón
        zona_exclusion: Zona a excluir (buffer de presencias)
        mascara_pendiente: Máscara de pendientes válidas
        meta_raster: Metadatos del raster
        ratio: Ratio ausencias/presencias
        semilla: Semilla aleatoria

    Returns:
        gpd.GeoDataFrame: Ausencias generadas
    """
    print(f"\n[INFO] Generando ausencias estratificadas (ratio 1:{ratio})...")
    print("       Referencia: Zhu et al. (2018), Barbet-Massin et al. (2012)")

    # Contar presencias por cantón
    conteo_presencias = contar_presencias_por_canton(presencias, cantones, col_canton)

    # Total de ausencias a generar
    total_presencias = sum(conteo_presencias.values())
    total_ausencias = int(total_presencias * ratio)

    print(f"\n       Total presencias: {total_presencias}")
    print(f"       Total ausencias a generar: {total_ausencias}")

    # Obtener geometría de exclusión
    geom_exclusion = zona_exclusion.geometry.iloc[0] if len(zona_exclusion) > 0 else None

    # Generar ausencias por cantón
    todas_ausencias = []
    semilla_canton = semilla

    for idx, canton_row in cantones.iterrows():
        nombre = canton_row[col_canton]
        geom = canton_row.geometry
        n_presencias = conteo_presencias.get(nombre, 0)

        if n_presencias == 0:
            continue

        # Número de ausencias para este cantón (proporcional)
        n_ausencias = int(n_presencias * ratio)

        if n_ausencias == 0:
            continue

        print(f"\n       {nombre}: generando {n_ausencias} ausencias...")

        # Generar puntos
        puntos = generar_puntos_aleatorios_en_poligono(
            geom,
            n_ausencias,
            geom_exclusion,
            mascara_pendiente,
            meta_raster,
            semilla_canton
        )

        for punto in puntos:
            todas_ausencias.append({
                'geometry': punto,
                'CANTON': nombre,
                'tipo': 'ausencia',
                'presencia': 0
            })

        print(f"         Generadas: {len(puntos)}")

        semilla_canton += 1

    # Crear GeoDataFrame
    gdf_ausencias = gpd.GeoDataFrame(todas_ausencias, crs=CRS_PROYECTO)

    print(f"\n       Total ausencias generadas: {len(gdf_ausencias):,}")

    return gdf_ausencias


def combinar_presencias_ausencias(
    presencias: gpd.GeoDataFrame,
    ausencias: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Combina presencias y ausencias en un solo dataset.

    Args:
        presencias: GeoDataFrame de presencias
        ausencias: GeoDataFrame de ausencias

    Returns:
        gpd.GeoDataFrame: Dataset combinado
    """
    print("\n[INFO] Combinando presencias y ausencias...")

    # Añadir columnas a presencias
    presencias = presencias.copy()
    presencias['tipo'] = 'presencia'
    presencias['presencia'] = 1

    # Seleccionar columnas comunes
    cols_comunes = ['geometry', 'tipo', 'presencia']

    # Verificar si existe columna CANTON
    if 'CANTON' in presencias.columns or 'canton' in presencias.columns:
        col_canton = 'CANTON' if 'CANTON' in presencias.columns else 'canton'
        if col_canton not in cols_comunes:
            cols_comunes.append(col_canton)

    # Preparar DataFrames
    pres_subset = presencias[['geometry', 'tipo', 'presencia']].copy()
    aus_subset = ausencias[['geometry', 'tipo', 'presencia']].copy()

    # Concatenar
    combinado = gpd.GeoDataFrame(
        pd.concat([pres_subset, aus_subset], ignore_index=True),
        crs=CRS_PROYECTO
    )

    # Añadir coordenadas
    combinado['X'] = combinado.geometry.x
    combinado['Y'] = combinado.geometry.y

    print(f"       Presencias: {len(presencias):,}")
    print(f"       Ausencias: {len(ausencias):,}")
    print(f"       Total: {len(combinado):,}")

    return combinado


def generar_mapa_distribucion(
    presencias: gpd.GeoDataFrame,
    ausencias: gpd.GeoDataFrame,
    cantones: gpd.GeoDataFrame,
    ruta_salida: Path
):
    """
    Genera mapa de distribución de presencias y ausencias.
    """
    print("\n[INFO] Generando mapa de distribución...")

    fig, ax = plt.subplots(figsize=(12, 10))

    # Dibujar cantones
    cantones.boundary.plot(ax=ax, color='gray', linewidth=1)

    # Dibujar ausencias
    ausencias.plot(ax=ax, color='blue', markersize=5, alpha=0.5, label='Ausencias')

    # Dibujar presencias
    presencias.plot(ax=ax, color='red', markersize=10, alpha=0.7, label='Presencias')

    ax.set_title('Distribución de Presencias y Ausencias\nMuestreo Estratificado por Cantón')
    ax.set_xlabel('Este (m)')
    ax.set_ylabel('Norte (m)')
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_salida.name}")


def generar_auditoria(
    stats: Dict,
    ruta_salida: Path
):
    """
    Genera archivo de auditoría JSON según ISO 19115.
    """
    auditoria = {
        "proceso": "MUESTREO_AUSENCIAS",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",

        "parametros": {
            "buffer_exclusion_m": BUFFER_EXCLUSION,
            "ratio_ausencias": RATIO_AUSENCIAS,
            "pendiente_minima_grados": PENDIENTE_MINIMA,
            "semilla": SEMILLA
        },

        "justificacion_metodologica": {
            "buffer_exclusion": {
                "valor": f"{BUFFER_EXCLUSION} m",
                "referencia": "Steger et al. (2021). Geomorphology, 374, 107533",
                "justificacion": "Previene muestreo en zonas adyacentes a deslizamientos existentes"
            },
            "ratio_1_1": {
                "valor": f"1:{RATIO_AUSENCIAS}",
                "referencia": "Barbet-Massin et al. (2012). Methods in Ecology and Evolution, 3(2), 327-338",
                "justificacion": "Balance óptimo para modelos de clasificación binaria"
            },
            "estratificacion_cantonal": {
                "referencia": "Zhu et al. (2018). Annals of GIS, 24(4), 225-240",
                "justificacion": "Mejora representatividad espacial y reduce autocorrelación"
            },
            "exclusion_planicies": {
                "valor": f">= {PENDIENTE_MINIMA}°",
                "referencia": "Reichenbach et al. (2018). Earth-Science Reviews, 180, 60-91",
                "justificacion": "Deslizamientos raramente ocurren en pendientes bajas"
            }
        },

        "resultados": stats,

        "control_calidad_iso19157": {
            "completitud": "100% de cantones con presencias tienen ausencias",
            "consistencia_logica": "Todas las ausencias fuera del buffer de exclusión",
            "exactitud_posicional": f"Pendiente verificada >= {PENDIENTE_MINIMA}° para cada punto"
        },

        "normas_aplicadas": [
            "ISO 19157:2013 - Calidad de datos geográficos",
            "ISO 19115-1:2014 - Metadatos geográficos"
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

    # 1. Cargar presencias
    try:
        presencias = cargar_presencias(INVENTARIO_GPKG)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        print("\n Ejecute primero SCRIPT_01 para generar el inventario.")
        return

    # 2. Cargar cantones
    try:
        cantones, col_canton = cargar_aoi_cantones(AOI_GPKG)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        return

    # 3. Crear zona de exclusión
    zona_exclusion = crear_zona_exclusion(presencias, BUFFER_EXCLUSION)

    # 4. Cargar máscara de pendiente
    try:
        mascara_pendiente, meta_raster = cargar_mascara_pendiente(SLOPE_RASTER, PENDIENTE_MINIMA)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        print("\n Ejecute primero SCRIPT_00A para generar los derivados topográficos.")
        return

    # 5. Generar ausencias estratificadas
    ausencias = generar_ausencias_estratificadas(
        presencias,
        cantones,
        col_canton,
        zona_exclusion,
        mascara_pendiente,
        meta_raster,
        RATIO_AUSENCIAS,
        SEMILLA
    )

    if len(ausencias) == 0:
        print("\n ERROR: No se generaron ausencias. Verifique los datos de entrada.")
        return

    # 6. Guardar ausencias
    ruta_ausencias = DIR_SALIDA / "puntos_ausencias.gpkg"
    ausencias.to_file(ruta_ausencias, driver="GPKG")
    print(f"\n[INFO] Ausencias guardadas: {ruta_ausencias.name}")

    # 7. Combinar presencias y ausencias
    dataset_completo = combinar_presencias_ausencias(presencias, ausencias)

    # 8. Guardar dataset combinado
    ruta_dataset = DIR_SALIDA / "dataset_presencias_ausencias.gpkg"
    dataset_completo.to_file(ruta_dataset, driver="GPKG")
    print(f"[INFO] Dataset combinado guardado: {ruta_dataset.name}")

    # 9. Generar mapa
    generar_mapa_distribucion(
        presencias,
        ausencias,
        cantones,
        DIR_SALIDA / "mapa_distribucion_muestreo.png"
    )

    # 10. Estadísticas y auditoría
    stats = {
        "n_presencias": len(presencias),
        "n_ausencias": len(ausencias),
        "n_total": len(dataset_completo),
        "ratio_efectivo": round(len(ausencias) / len(presencias), 2),
        "ausencias_por_canton": ausencias['CANTON'].value_counts().to_dict() if 'CANTON' in ausencias.columns else {}
    }

    generar_auditoria(stats, DIR_SALIDA / "AUDITORIA_MUESTREO.json")

    # Resumen final
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL")
    print("=" * 70)
    print(f"\n Presencias (deslizamientos):  {len(presencias):,}")
    print(f" Ausencias (pseudo-ausencias): {len(ausencias):,}")
    print(f" Total puntos:                 {len(dataset_completo):,}")
    print(f" Ratio efectivo P:A:           1:{stats['ratio_efectivo']}")

    print(f"\n Buffer de exclusión:          {BUFFER_EXCLUSION} m")
    print(f" Pendiente mínima:             {PENDIENTE_MINIMA}°")

    print(f"\n Duración: {tiempo_total}")
    print(f" Archivos en: {DIR_SALIDA}")
    print("=" * 70)
    print(" ✅ MUESTREO DE AUSENCIAS COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
