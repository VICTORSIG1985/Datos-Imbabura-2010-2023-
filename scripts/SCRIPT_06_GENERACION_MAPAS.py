#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT 06: GENERACIÓN DE MAPAS DE SUSCEPTIBILIDAD
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Fecha: Diciembre 2025

Descripción:
    Este script aplica los modelos entrenados (Random Forest y Gradient Boosting)
    a toda el área de estudio para generar mapas de susceptibilidad a deslizamientos.
    Los mapas de probabilidad se clasifican en cinco niveles de susceptibilidad
    según criterios establecidos en la literatura científica.

Clasificación de susceptibilidad:
    - Muy Baja:  0.00 - 0.20 (áreas con mínima probabilidad)
    - Baja:      0.20 - 0.40 (áreas con baja probabilidad)
    - Media:     0.40 - 0.60 (áreas con probabilidad moderada)
    - Alta:      0.60 - 0.80 (áreas con alta probabilidad)
    - Muy Alta:  0.80 - 1.00 (áreas con probabilidad máxima)

Referencias bibliográficas:
    - Fell, R., et al. (2008). Guidelines for landslide susceptibility, hazard
      and risk zoning for land use planning. Engineering Geology, 102(3-4), 85-98.
      https://doi.org/10.1016/j.enggeo.2008.03.022

    - Reichenbach, P., et al. (2018). A review of statistically-based landslide
      susceptibility models. Earth-Science Reviews, 180, 60-91.
      https://doi.org/10.1016/j.earscirev.2018.03.001

    - Guzzetti, F., et al. (1999). Landslide hazard evaluation: a review of
      current techniques. Geomorphology, 31(1-4), 181-216.

    - van Westen, C.J., et al. (2008). Spatial data for landslide susceptibility,
      hazard, and vulnerability assessment. Engineering Geology, 102(3-4), 112-131.

    - Varnes, D.J. (1984). Landslide hazard zonation: a review of principles and
      practice. UNESCO, Paris, 63 pp.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)
    - ISO 19115:2014 (Metadatos geográficos)

Entradas:
    - modelo_random_forest.joblib (SCRIPT_05)
    - modelo_gradient_boosting.joblib (SCRIPT_05)
    - importancia_variables.csv (SCRIPT_05)
    - Rasters de covariables seleccionadas

Salidas:
    - susceptibilidad_rf.tif (probabilidad Random Forest)
    - susceptibilidad_gb.tif (probabilidad Gradient Boosting)
    - susceptibilidad_ensamble.tif (promedio de probabilidades)
    - susceptibilidad_clases.tif (clasificación 1-5)
    - mapa_susceptibilidad.png (visualización para artículo)
    - AUDITORIA_MAPAS.json
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
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
import matplotlib.patches as mpatches

try:
    import rasterio
    from rasterio.windows import Window
    from rasterio.transform import from_bounds
except ImportError:
    print("ERROR: rasterio no está instalado. Ejecute: pip install rasterio")
    sys.exit(1)

try:
    import geopandas as gpd
except ImportError:
    print("ERROR: geopandas no está instalado. Ejecute: pip install geopandas")
    sys.exit(1)

try:
    import joblib
except ImportError:
    print("ERROR: joblib no está instalado. Ejecute: pip install joblib")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Ruta base
BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Directorios de entrada
DIR_MODELOS = BASE_PATH / "Investigacion" / "05_MODELOS"
DIR_VARIABLES_SELEC = BASE_PATH / "Investigacion" / "00_VARIABLES_SELECCIONADAS"

# Archivo de AOI
AOI_GPKG = Path(r"D:\DATA\AOI_IMBABURA_CANTON.gpkg")

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "06_MAPAS"

# Configuración espacial
CRS_DESTINO = "EPSG:32717"
NODATA = -9999
RESOLUCION = 30  # metros

# Clasificación de susceptibilidad (Fell et al., 2008; Reichenbach et al., 2018)
# Intervalos iguales basados en probabilidad
CLASES_SUSCEPTIBILIDAD = {
    1: {"nombre": "Muy Baja", "rango": (0.00, 0.20), "color": "#2166AC"},
    2: {"nombre": "Baja", "rango": (0.20, 0.40), "color": "#92C5DE"},
    3: {"nombre": "Media", "rango": (0.40, 0.60), "color": "#F7F7F7"},
    4: {"nombre": "Alta", "rango": (0.60, 0.80), "color": "#F4A582"},
    5: {"nombre": "Muy Alta", "rango": (0.80, 1.00), "color": "#B2182B"}
}

# Tamaño de bloques para procesamiento (evita problemas de memoria)
BLOCK_SIZE = 1024


def imprimir_banner():
    """Imprime el banner inicial del script."""
    print("=" * 70)
    print(" SCRIPT 06: GENERACIÓN DE MAPAS DE SUSCEPTIBILIDAD")
    print("=" * 70)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" CRS: {CRS_DESTINO}")
    print(f" Resolución: {RESOLUCION}m")
    print(f" Output: {DIR_SALIDA}")
    print("=" * 70)


def cargar_modelos(dir_modelos: Path) -> Tuple:
    """
    Carga los modelos entrenados.

    Args:
        dir_modelos: Directorio con los modelos

    Returns:
        Tuple: (modelo_rf, modelo_gb, importancia)
    """
    print("\n[INFO] Cargando modelos entrenados...")

    ruta_rf = dir_modelos / "modelo_random_forest.joblib"
    ruta_gb = dir_modelos / "modelo_gradient_boosting.joblib"
    ruta_imp = dir_modelos / "importancia_variables.csv"

    if not ruta_rf.exists():
        raise FileNotFoundError(f"No se encontró: {ruta_rf}")
    if not ruta_gb.exists():
        raise FileNotFoundError(f"No se encontró: {ruta_gb}")
    if not ruta_imp.exists():
        raise FileNotFoundError(f"No se encontró: {ruta_imp}")

    modelo_rf = joblib.load(ruta_rf)
    modelo_gb = joblib.load(ruta_gb)
    importancia = pd.read_csv(ruta_imp)

    print(f"       Random Forest: cargado")
    print(f"       Gradient Boosting: cargado")
    print(f"       Variables: {len(importancia)}")

    return modelo_rf, modelo_gb, importancia


def obtener_rutas_covariables(
    importancia: pd.DataFrame,
    dir_variables: Path
) -> Dict[str, Path]:
    """
    Obtiene las rutas de los rasters de covariables seleccionadas.

    Args:
        importancia: DataFrame con variables seleccionadas
        dir_variables: Directorio con las variables

    Returns:
        Dict: {nombre_variable: ruta_raster}
    """
    print("\n[INFO] Localizando rasters de covariables...")

    rutas = {}
    no_encontradas = []

    for var in importancia['variable']:
        # Buscar raster en el directorio de variables seleccionadas
        ruta = dir_variables / f"{var}.tif"

        if ruta.exists():
            rutas[var] = ruta
        else:
            # Buscar con diferentes extensiones
            for ext in ['.TIF', '.tiff', '.TIFF']:
                ruta_alt = dir_variables / f"{var}{ext}"
                if ruta_alt.exists():
                    rutas[var] = ruta_alt
                    break
            else:
                no_encontradas.append(var)

    print(f"       Variables encontradas: {len(rutas)}")
    if no_encontradas:
        print(f"       ⚠️  No encontradas: {', '.join(no_encontradas)}")

    return rutas


def obtener_extension_comun(rutas: Dict[str, Path]) -> Dict:
    """
    Obtiene la extensión común de todos los rasters.

    Args:
        rutas: Diccionario con rutas de rasters

    Returns:
        Dict: Información de extensión (bounds, shape, transform, crs)
    """
    print("\n[INFO] Determinando extensión común...")

    bounds_list = []
    shapes = []
    transforms = []
    crs = None

    for nombre, ruta in rutas.items():
        with rasterio.open(ruta) as src:
            bounds_list.append(src.bounds)
            shapes.append((src.height, src.width))
            transforms.append(src.transform)
            if crs is None:
                crs = src.crs

    # Usar la extensión del primer raster como referencia
    # (asumimos que todos tienen la misma extensión)
    primer_ruta = list(rutas.values())[0]
    with rasterio.open(primer_ruta) as src:
        extension = {
            'bounds': src.bounds,
            'height': src.height,
            'width': src.width,
            'transform': src.transform,
            'crs': src.crs
        }

    print(f"       Dimensiones: {extension['width']} x {extension['height']} píxeles")
    print(f"       CRS: {extension['crs']}")

    return extension


def generar_mapa_susceptibilidad(
    modelo_rf,
    modelo_gb,
    rutas_covariables: Dict[str, Path],
    variables_orden: List[str],
    extension: Dict,
    dir_salida: Path
) -> Dict:
    """
    Genera los mapas de susceptibilidad por bloques.

    Referencia metodológica:
        van Westen, C.J., et al. (2008). Spatial data for landslide susceptibility.
        Engineering Geology, 102(3-4), 112-131.

    Args:
        modelo_rf: Modelo Random Forest
        modelo_gb: Modelo Gradient Boosting
        rutas_covariables: Rutas a los rasters
        variables_orden: Orden de variables según el modelo
        extension: Extensión espacial
        dir_salida: Directorio de salida

    Returns:
        Dict: Estadísticas de los mapas generados
    """
    print("\n[INFO] Generando mapas de susceptibilidad...")
    print(f"       Procesando por bloques de {BLOCK_SIZE}x{BLOCK_SIZE} píxeles")

    # Crear rasters de salida
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'width': extension['width'],
        'height': extension['height'],
        'count': 1,
        'crs': extension['crs'],
        'transform': extension['transform'],
        'nodata': NODATA,
        'compress': 'lzw'
    }

    # Abrir archivos de salida
    ruta_rf = dir_salida / "susceptibilidad_rf.tif"
    ruta_gb = dir_salida / "susceptibilidad_gb.tif"
    ruta_ens = dir_salida / "susceptibilidad_ensamble.tif"

    dst_rf = rasterio.open(ruta_rf, 'w', **profile)
    dst_gb = rasterio.open(ruta_gb, 'w', **profile)
    dst_ens = rasterio.open(ruta_ens, 'w', **profile)

    # Abrir todos los rasters de covariables
    src_covars = {}
    for var, ruta in rutas_covariables.items():
        src_covars[var] = rasterio.open(ruta)

    # Estadísticas
    total_pixels = 0
    valid_pixels = 0
    prob_sum = 0

    # Procesar por bloques
    height = extension['height']
    width = extension['width']

    n_bloques_y = (height + BLOCK_SIZE - 1) // BLOCK_SIZE
    n_bloques_x = (width + BLOCK_SIZE - 1) // BLOCK_SIZE
    total_bloques = n_bloques_y * n_bloques_x

    bloque_actual = 0

    for row_off in range(0, height, BLOCK_SIZE):
        for col_off in range(0, width, BLOCK_SIZE):
            bloque_actual += 1

            # Calcular tamaño del bloque
            win_height = min(BLOCK_SIZE, height - row_off)
            win_width = min(BLOCK_SIZE, width - col_off)

            window = Window(col_off, row_off, win_width, win_height)

            # Leer covariables para este bloque
            X_block = np.zeros((win_height * win_width, len(variables_orden)), dtype=np.float32)
            mask_valid = np.ones(win_height * win_width, dtype=bool)

            for i, var in enumerate(variables_orden):
                if var in src_covars:
                    data = src_covars[var].read(1, window=window)
                    X_block[:, i] = data.ravel()
                    mask_valid &= (data.ravel() != NODATA) & ~np.isnan(data.ravel())
                else:
                    # Variable no encontrada - marcar como inválido
                    mask_valid[:] = False

            # Predecir solo píxeles válidos
            prob_rf = np.full(win_height * win_width, NODATA, dtype=np.float32)
            prob_gb = np.full(win_height * win_width, NODATA, dtype=np.float32)
            prob_ens = np.full(win_height * win_width, NODATA, dtype=np.float32)

            if np.any(mask_valid):
                X_valid = X_block[mask_valid]

                # Predicción
                pred_rf = modelo_rf.predict_proba(X_valid)[:, 1]
                pred_gb = modelo_gb.predict_proba(X_valid)[:, 1]
                pred_ens = (pred_rf + pred_gb) / 2

                prob_rf[mask_valid] = pred_rf
                prob_gb[mask_valid] = pred_gb
                prob_ens[mask_valid] = pred_ens

                # Estadísticas
                valid_pixels += np.sum(mask_valid)
                prob_sum += np.sum(pred_ens)

            total_pixels += win_height * win_width

            # Escribir bloques
            dst_rf.write(prob_rf.reshape(win_height, win_width), 1, window=window)
            dst_gb.write(prob_gb.reshape(win_height, win_width), 1, window=window)
            dst_ens.write(prob_ens.reshape(win_height, win_width), 1, window=window)

            # Progreso
            if bloque_actual % 10 == 0 or bloque_actual == total_bloques:
                pct = (bloque_actual / total_bloques) * 100
                print(f"       Progreso: {pct:.1f}% ({bloque_actual}/{total_bloques} bloques)")

    # Cerrar archivos
    for src in src_covars.values():
        src.close()
    dst_rf.close()
    dst_gb.close()
    dst_ens.close()

    print(f"\n       Mapas generados:")
    print(f"         - {ruta_rf.name}")
    print(f"         - {ruta_gb.name}")
    print(f"         - {ruta_ens.name}")

    estadisticas = {
        'total_pixels': total_pixels,
        'valid_pixels': valid_pixels,
        'porcentaje_valido': round(valid_pixels / total_pixels * 100, 2),
        'probabilidad_media': round(prob_sum / valid_pixels, 4) if valid_pixels > 0 else 0
    }

    return estadisticas


def clasificar_susceptibilidad(
    dir_salida: Path,
    clases: Dict = CLASES_SUSCEPTIBILIDAD
) -> Dict:
    """
    Clasifica el mapa de susceptibilidad en niveles.

    Referencia:
        Fell, R., et al. (2008). Guidelines for landslide susceptibility.
        Engineering Geology, 102(3-4), 85-98.

    Args:
        dir_salida: Directorio con mapas de probabilidad
        clases: Diccionario con definición de clases

    Returns:
        Dict: Estadísticas de clasificación
    """
    print("\n[INFO] Clasificando susceptibilidad en niveles...")

    ruta_prob = dir_salida / "susceptibilidad_ensamble.tif"
    ruta_clases = dir_salida / "susceptibilidad_clases.tif"

    with rasterio.open(ruta_prob) as src:
        prob = src.read(1)
        profile = src.profile.copy()

    # Clasificar
    profile['dtype'] = 'uint8'
    clases_arr = np.zeros_like(prob, dtype=np.uint8)

    # Aplicar clasificación
    for clase, info in clases.items():
        min_val, max_val = info['rango']
        mask = (prob >= min_val) & (prob < max_val)
        clases_arr[mask] = clase

    # Clase 5 incluye el límite superior
    clases_arr[(prob >= 0.80) & (prob <= 1.0)] = 5

    # NoData
    clases_arr[prob == NODATA] = 0

    # Guardar
    with rasterio.open(ruta_clases, 'w', **profile) as dst:
        dst.write(clases_arr, 1)

    print(f"       Guardado: {ruta_clases.name}")

    # Estadísticas por clase
    estadisticas = {}
    total_valido = np.sum(clases_arr > 0)

    print("\n       Distribución de clases:")
    for clase, info in clases.items():
        n_pixels = np.sum(clases_arr == clase)
        pct = (n_pixels / total_valido * 100) if total_valido > 0 else 0
        estadisticas[info['nombre']] = {
            'clase': clase,
            'n_pixels': int(n_pixels),
            'porcentaje': round(pct, 2)
        }
        print(f"         Clase {clase} ({info['nombre']}): {pct:.1f}%")

    return estadisticas


def generar_visualizacion(
    dir_salida: Path,
    aoi_gpkg: Path,
    clases: Dict = CLASES_SUSCEPTIBILIDAD
):
    """
    Genera visualización del mapa para el artículo científico.

    Args:
        dir_salida: Directorio con mapas
        aoi_gpkg: Ruta al AOI
        clases: Diccionario de clases
    """
    print("\n[INFO] Generando visualización para artículo...")

    # Cargar datos
    ruta_prob = dir_salida / "susceptibilidad_ensamble.tif"
    ruta_clases = dir_salida / "susceptibilidad_clases.tif"

    with rasterio.open(ruta_prob) as src:
        prob = src.read(1)
        extent = [src.bounds.left, src.bounds.right,
                  src.bounds.bottom, src.bounds.top]

    with rasterio.open(ruta_clases) as src:
        clases_arr = src.read(1)

    # Cargar AOI si existe
    try:
        gdf_aoi = gpd.read_file(aoi_gpkg)
        gdf_aoi = gdf_aoi.to_crs(CRS_DESTINO)
    except Exception:
        gdf_aoi = None

    # Crear figura con dos subplots
    fig, axes = plt.subplots(1, 2, figsize=(16, 10))

    # =========================================================================
    # Subplot 1: Mapa de probabilidad continua
    # =========================================================================
    ax1 = axes[0]

    # Enmascarar NoData
    prob_masked = np.ma.masked_where(prob == NODATA, prob)

    im1 = ax1.imshow(prob_masked, extent=extent, cmap='RdYlGn_r',
                     vmin=0, vmax=1, origin='upper')

    if gdf_aoi is not None:
        gdf_aoi.boundary.plot(ax=ax1, color='black', linewidth=0.5)

    ax1.set_title('Probabilidad de Susceptibilidad\n(Modelo Ensamble)', fontsize=12)
    ax1.set_xlabel('Este (m)', fontsize=10)
    ax1.set_ylabel('Norte (m)', fontsize=10)

    cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8, pad=0.02)
    cbar1.set_label('Probabilidad', fontsize=10)

    # =========================================================================
    # Subplot 2: Mapa clasificado
    # =========================================================================
    ax2 = axes[1]

    # Crear colormap discreto
    colors = [clases[i]['color'] for i in range(1, 6)]
    cmap_disc = ListedColormap(colors)
    bounds = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = BoundaryNorm(bounds, cmap_disc.N)

    # Enmascarar NoData
    clases_masked = np.ma.masked_where(clases_arr == 0, clases_arr)

    im2 = ax2.imshow(clases_masked, extent=extent, cmap=cmap_disc,
                     norm=norm, origin='upper')

    if gdf_aoi is not None:
        gdf_aoi.boundary.plot(ax=ax2, color='black', linewidth=0.5)

    ax2.set_title('Clasificación de Susceptibilidad\n(5 Niveles)', fontsize=12)
    ax2.set_xlabel('Este (m)', fontsize=10)
    ax2.set_ylabel('Norte (m)', fontsize=10)

    # Leyenda
    legend_patches = [
        Patch(facecolor=clases[i]['color'], edgecolor='black',
              label=f"{clases[i]['nombre']} ({clases[i]['rango'][0]:.2f}-{clases[i]['rango'][1]:.2f})")
        for i in range(1, 6)
    ]
    ax2.legend(handles=legend_patches, loc='lower left', fontsize=9,
               title='Susceptibilidad')

    plt.tight_layout()

    # Guardar
    ruta_fig = dir_salida / "mapa_susceptibilidad.png"
    plt.savefig(ruta_fig, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"       Guardado: {ruta_fig.name}")

    # =========================================================================
    # Figura adicional: Histograma de probabilidades
    # =========================================================================
    fig2, ax = plt.subplots(figsize=(10, 6))

    prob_valid = prob[prob != NODATA]
    ax.hist(prob_valid, bins=50, color='steelblue', edgecolor='white', alpha=0.7)

    # Líneas de división de clases
    for clase, info in clases.items():
        ax.axvline(x=info['rango'][0], color='red', linestyle='--', alpha=0.5)

    ax.set_xlabel('Probabilidad de Susceptibilidad', fontsize=12)
    ax.set_ylabel('Frecuencia (píxeles)', fontsize=12)
    ax.set_title('Distribución de Probabilidades de Susceptibilidad', fontsize=14)
    ax.set_xlim(0, 1)

    plt.tight_layout()

    ruta_hist = dir_salida / "histograma_susceptibilidad.png"
    plt.savefig(ruta_hist, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_hist.name}")


def calcular_estadisticas_por_canton(
    dir_salida: Path,
    aoi_gpkg: Path
) -> Optional[pd.DataFrame]:
    """
    Calcula estadísticas de susceptibilidad por cantón.

    Args:
        dir_salida: Directorio con mapas
        aoi_gpkg: Ruta al AOI con cantones

    Returns:
        DataFrame con estadísticas por cantón
    """
    print("\n[INFO] Calculando estadísticas por cantón...")

    try:
        gdf = gpd.read_file(aoi_gpkg)
        gdf = gdf.to_crs(CRS_DESTINO)
    except Exception as e:
        print(f"       ⚠️  No se pudo cargar AOI: {e}")
        return None

    # Verificar columna de nombre
    col_nombre = None
    for col in ['DPA_DESCAN', 'CANTON', 'canton', 'NOMBRE', 'nombre']:
        if col in gdf.columns:
            col_nombre = col
            break

    if col_nombre is None:
        print("       ⚠️  No se encontró columna de nombre de cantón")
        return None

    ruta_clases = dir_salida / "susceptibilidad_clases.tif"

    with rasterio.open(ruta_clases) as src:
        stats_cantones = []

        for idx, row in gdf.iterrows():
            try:
                # Extraer valores dentro del polígono
                from rasterio.mask import mask
                out_image, out_transform = mask(src, [row.geometry], crop=True)
                data = out_image[0]

                # Calcular estadísticas
                valid = data[data > 0]
                if len(valid) > 0:
                    stats = {
                        'canton': row[col_nombre],
                        'n_pixels': len(valid),
                        'muy_baja_pct': round(np.sum(valid == 1) / len(valid) * 100, 2),
                        'baja_pct': round(np.sum(valid == 2) / len(valid) * 100, 2),
                        'media_pct': round(np.sum(valid == 3) / len(valid) * 100, 2),
                        'alta_pct': round(np.sum(valid == 4) / len(valid) * 100, 2),
                        'muy_alta_pct': round(np.sum(valid == 5) / len(valid) * 100, 2),
                        'susceptibilidad_alta_total': round(
                            (np.sum(valid == 4) + np.sum(valid == 5)) / len(valid) * 100, 2
                        )
                    }
                    stats_cantones.append(stats)
            except Exception as e:
                print(f"       Error en {row[col_nombre]}: {e}")

    df_stats = pd.DataFrame(stats_cantones)

    # Ordenar por susceptibilidad alta
    df_stats = df_stats.sort_values('susceptibilidad_alta_total', ascending=False)

    # Guardar
    ruta_csv = dir_salida / "estadisticas_por_canton.csv"
    df_stats.to_csv(ruta_csv, index=False)

    print(f"       Guardado: {ruta_csv.name}")
    print("\n       Cantones con mayor susceptibilidad alta+muy alta:")
    for i, row in df_stats.head(5).iterrows():
        print(f"         {row['canton']}: {row['susceptibilidad_alta_total']:.1f}%")

    return df_stats


def generar_auditoria(
    stats_mapas: Dict,
    stats_clases: Dict,
    variables_usadas: List[str],
    ruta_salida: Path
):
    """
    Genera archivo de auditoría JSON.
    """
    auditoria = {
        "proceso": "GENERACION_MAPAS_SUSCEPTIBILIDAD",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",

        "configuracion": {
            "crs": CRS_DESTINO,
            "resolucion": RESOLUCION,
            "nodata": NODATA,
            "block_size": BLOCK_SIZE
        },

        "modelos_aplicados": [
            "Random Forest (Breiman, 2001)",
            "Gradient Boosting (Friedman, 2001)",
            "Ensamble (promedio aritmético)"
        ],

        "clasificacion_susceptibilidad": {
            clase: {
                "nombre": info["nombre"],
                "rango_probabilidad": f"{info['rango'][0]:.2f} - {info['rango'][1]:.2f}"
            }
            for clase, info in CLASES_SUSCEPTIBILIDAD.items()
        },

        "estadisticas_mapas": stats_mapas,
        "distribucion_clases": stats_clases,
        "variables_usadas": variables_usadas,

        "referencias_bibliograficas": [
            "Fell, R., et al. (2008). Guidelines for landslide susceptibility. Engineering Geology, 102(3-4), 85-98",
            "Reichenbach, P., et al. (2018). Earth-Science Reviews, 180, 60-91",
            "Guzzetti, F., et al. (1999). Geomorphology, 31(1-4), 181-216",
            "van Westen, C.J., et al. (2008). Engineering Geology, 102(3-4), 112-131",
            "Varnes, D.J. (1984). Landslide hazard zonation. UNESCO, Paris"
        ],

        "normas_aplicadas": [
            "ISO 19157:2013 - Calidad de datos geográficos",
            "ISO 19115:2014 - Metadatos geográficos"
        ],

        "salidas_generadas": [
            "susceptibilidad_rf.tif",
            "susceptibilidad_gb.tif",
            "susceptibilidad_ensamble.tif",
            "susceptibilidad_clases.tif",
            "mapa_susceptibilidad.png",
            "histograma_susceptibilidad.png",
            "estadisticas_por_canton.csv"
        ]
    }

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(auditoria, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Auditoría guardada: {ruta_salida.name}")


def main():
    """Función principal del script."""
    tiempo_inicio = datetime.now()

    imprimir_banner()

    # Crear directorio de salida
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    # 1. Cargar modelos
    try:
        modelo_rf, modelo_gb, importancia = cargar_modelos(DIR_MODELOS)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        print("\n Ejecute primero SCRIPT_05 para entrenar los modelos.")
        return

    # Lista de variables en orden
    variables_orden = importancia['variable'].tolist()

    # 2. Obtener rutas de covariables
    rutas_covariables = obtener_rutas_covariables(importancia, DIR_VARIABLES_SELEC)

    if not rutas_covariables:
        print("\n ERROR: No se encontraron rasters de covariables.")
        return

    # 3. Obtener extensión común
    extension = obtener_extension_comun(rutas_covariables)

    # 4. Generar mapas de susceptibilidad
    print("\n" + "-" * 50)
    print(" GENERACIÓN DE MAPAS DE PROBABILIDAD")
    print("-" * 50)

    stats_mapas = generar_mapa_susceptibilidad(
        modelo_rf, modelo_gb,
        rutas_covariables, variables_orden,
        extension, DIR_SALIDA
    )

    # 5. Clasificar susceptibilidad
    print("\n" + "-" * 50)
    print(" CLASIFICACIÓN DE SUSCEPTIBILIDAD")
    print("-" * 50)

    stats_clases = clasificar_susceptibilidad(DIR_SALIDA)

    # 6. Generar visualización
    print("\n" + "-" * 50)
    print(" GENERACIÓN DE VISUALIZACIONES")
    print("-" * 50)

    generar_visualizacion(DIR_SALIDA, AOI_GPKG)

    # 7. Estadísticas por cantón
    if AOI_GPKG.exists():
        calcular_estadisticas_por_canton(DIR_SALIDA, AOI_GPKG)

    # 8. Generar auditoría
    generar_auditoria(
        stats_mapas, stats_clases,
        variables_orden,
        DIR_SALIDA / "AUDITORIA_MAPAS.json"
    )

    # Resumen final
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL - GENERACIÓN DE MAPAS")
    print("=" * 70)

    print(f"\n ESTADÍSTICAS DE PROCESAMIENTO:")
    print(f"   Píxeles totales: {stats_mapas['total_pixels']:,}")
    print(f"   Píxeles válidos: {stats_mapas['valid_pixels']:,} ({stats_mapas['porcentaje_valido']}%)")
    print(f"   Probabilidad media: {stats_mapas['probabilidad_media']:.4f}")

    print(f"\n DISTRIBUCIÓN DE SUSCEPTIBILIDAD:")
    for nombre, data in stats_clases.items():
        print(f"   {nombre}: {data['porcentaje']}%")

    print(f"\n ARCHIVOS GENERADOS EN: {DIR_SALIDA}")
    print("   - susceptibilidad_rf.tif")
    print("   - susceptibilidad_gb.tif")
    print("   - susceptibilidad_ensamble.tif")
    print("   - susceptibilidad_clases.tif")
    print("   - mapa_susceptibilidad.png")
    print("   - histograma_susceptibilidad.png")
    print("   - estadisticas_por_canton.csv")
    print("   - AUDITORIA_MAPAS.json")

    print(f"\n Duración: {tiempo_total}")
    print("=" * 70)
    print(" ✅ GENERACIÓN DE MAPAS COMPLETADA EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    main()
