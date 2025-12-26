#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT 01B: ANÁLISIS DE SESGO ESPACIAL EN EL INVENTARIO
================================================================================
Proyecto: Modelamiento de Susceptibilidad a Deslizamientos - Imbabura, Ecuador
Autor: Víctor Hugo Pinto Páez
Fecha: Diciembre 2025

Descripción:
    Este script cuantifica el sesgo de reporte espacial en el inventario de
    deslizamientos. El sesgo de reporte es un problema común en inventarios
    basados en registros institucionales, donde algunas áreas pueden tener
    mayor o menor reporte debido a factores como accesibilidad, densidad
    poblacional, o capacidad institucional local.

Importancia metodológica:
    El sesgo de reporte puede afectar significativamente los modelos de
    susceptibilidad si no se considera. Un área con bajo reporte podría
    aparecer como "segura" cuando en realidad simplemente no se reportan
    los eventos. Este análisis permite:
    1. Identificar cantones con posible sub-reporte
    2. Ajustar el muestreo de pseudo-ausencias
    3. Interpretar correctamente los resultados del modelo

Metodología:
    1. Calcular densidad de deslizamientos por cantón (eventos/km²)
    2. Normalizar por población (proxy de capacidad de reporte)
    3. Calcular índices de sesgo relativo
    4. Identificar cantones con anomalías significativas

Referencias bibliográficas:
    - Petschko, H., et al. (2014). Assessing the quality of landslide
      susceptibility maps–case study Lower Austria. Natural Hazards and
      Earth System Sciences, 14(1), 95-118.
      https://doi.org/10.5194/nhess-14-95-2014

    - Steger, S., et al. (2016). Exploring discrepancies between quantitative
      validation results and the geomorphic plausibility of statistical
      landslide susceptibility maps. Geomorphology, 262, 8-23.
      https://doi.org/10.1016/j.geomorph.2016.03.015

    - Bornaetxea, T., et al. (2018). Effective surveyed area and its role
      in statistical landslide susceptibility assessments. Natural Hazards
      and Earth System Sciences, 18(9), 2455-2469.

Normas aplicadas:
    - ISO 19157:2013 (Calidad de datos geográficos)

Entradas:
    - inventario_deslizamientos.gpkg (SCRIPT_01)
    - AOI_IMBABURA_CANTON.gpkg (polígonos de cantones)

Salidas:
    - analisis_sesgo_espacial.csv
    - mapa_densidad_deslizamientos.png
    - mapa_sesgo_relativo.png
    - AUDITORIA_SESGO_ESPACIAL.json
================================================================================
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

try:
    import geopandas as gpd
except ImportError:
    print("ERROR: geopandas no está instalado. Ejecute: pip install geopandas")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Ruta base
BASE_PATH = Path(r"D:\POSGRADOS\ESPCIALIZACIÓN EN GEOINFORMACIÓN PARA PROYECTOS DE INGENIERÍA\ARTICULO CIENTÍFICO\DATOS")

# Archivos de entrada
INVENTARIO_GPKG = BASE_PATH / "Investigacion" / "01_PROCESSED" / "inventario_deslizamientos.gpkg"
AOI_GPKG = Path(r"D:\DATA\AOI_IMBABURA_CANTON.gpkg")

# Directorio de salida
DIR_SALIDA = BASE_PATH / "Investigacion" / "01_PROCESSED" / "analisis_sesgo"

# Datos poblacionales por cantón (INEC 2022)
# Fuente: Instituto Nacional de Estadística y Censos
POBLACION_CANTONES = {
    "IBARRA": 217469,
    "OTAVALO": 114360,
    "COTACACHI": 53081,
    "ANTONIO ANTE": 53771,
    "PIMAMPIRO": 13366,
    "SAN MIGUEL DE URCUQUI": 17969,
    "URCUQUI": 17969,  # Alias
}

# CRS del proyecto
CRS_PROYECTO = "EPSG:32717"


def imprimir_banner():
    """Imprime el banner inicial del script."""
    print("=" * 70)
    print(" SCRIPT 01B: ANÁLISIS DE SESGO ESPACIAL")
    print("=" * 70)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Referencia: Petschko et al. (2014), Steger et al. (2016)")
    print(f" Output: {DIR_SALIDA}")
    print("=" * 70)


def cargar_datos(
    ruta_inventario: Path,
    ruta_aoi: Path
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Carga el inventario y los polígonos de cantones.

    Args:
        ruta_inventario: Ruta al GeoPackage del inventario
        ruta_aoi: Ruta al GeoPackage de cantones

    Returns:
        Tuple: (inventario, cantones)
    """
    print("\n[INFO] Cargando datos...")

    # Cargar inventario
    if not ruta_inventario.exists():
        raise FileNotFoundError(f"No se encontró: {ruta_inventario}")
    inventario = gpd.read_file(ruta_inventario)
    print(f"       Inventario: {len(inventario)} deslizamientos")

    # Cargar cantones
    if not ruta_aoi.exists():
        raise FileNotFoundError(f"No se encontró: {ruta_aoi}")
    cantones = gpd.read_file(ruta_aoi)

    # Asegurar CRS
    if inventario.crs != CRS_PROYECTO:
        inventario = inventario.to_crs(CRS_PROYECTO)
    if cantones.crs != CRS_PROYECTO:
        cantones = cantones.to_crs(CRS_PROYECTO)

    print(f"       Cantones: {len(cantones)}")

    return inventario, cantones


def identificar_columna_canton(gdf: gpd.GeoDataFrame) -> str:
    """Identifica la columna que contiene el nombre del cantón."""
    candidatos = ['CANTON', 'canton', 'DPA_CANTON', 'NOM_CANTON', 'nombre', 'NAME', 'DPA_DESCAN']
    for col in candidatos:
        if col in gdf.columns:
            return col
    return None


def calcular_metricas_por_canton(
    inventario: gpd.GeoDataFrame,
    cantones: gpd.GeoDataFrame
) -> pd.DataFrame:
    """
    Calcula métricas de densidad y sesgo por cantón.

    Métricas calculadas:
        - N_eventos: Número de deslizamientos
        - Area_km2: Área del cantón
        - Densidad: Eventos por km²
        - Poblacion: Población del cantón (INEC 2022)
        - Eventos_per_capita: Eventos por 10,000 habitantes
        - Sesgo_relativo: Desviación respecto a la media provincial

    Referencia:
        Bornaetxea et al. (2018) - Effective surveyed area

    Args:
        inventario: GeoDataFrame de deslizamientos
        cantones: GeoDataFrame de cantones

    Returns:
        pd.DataFrame: Métricas por cantón
    """
    print("\n[INFO] Calculando métricas por cantón...")

    col_canton = identificar_columna_canton(cantones)
    if col_canton is None:
        raise ValueError("No se encontró columna de nombre de cantón")

    resultados = []

    for idx, canton in cantones.iterrows():
        nombre = canton[col_canton].upper().strip()
        geom = canton.geometry

        # Área en km²
        area_km2 = geom.area / 1e6

        # Contar deslizamientos dentro del cantón
        dentro = inventario.geometry.within(geom)
        n_eventos = dentro.sum()

        # Densidad (eventos/km²)
        densidad = n_eventos / area_km2 if area_km2 > 0 else 0

        # Población
        poblacion = POBLACION_CANTONES.get(nombre, POBLACION_CANTONES.get(nombre.replace(" ", ""), 0))

        # Eventos per cápita (por 10,000 hab)
        eventos_per_capita = (n_eventos / poblacion * 10000) if poblacion > 0 else 0

        resultados.append({
            'canton': nombre,
            'n_eventos': n_eventos,
            'area_km2': round(area_km2, 2),
            'densidad_km2': round(densidad, 4),
            'poblacion': poblacion,
            'eventos_per_10k_hab': round(eventos_per_capita, 2)
        })

    df = pd.DataFrame(resultados)

    # Calcular sesgo relativo (desviación de la media)
    media_densidad = df['densidad_km2'].mean()
    df['sesgo_densidad'] = round((df['densidad_km2'] - media_densidad) / media_densidad * 100, 1)

    media_per_capita = df['eventos_per_10k_hab'].mean()
    df['sesgo_per_capita'] = round((df['eventos_per_10k_hab'] - media_per_capita) / media_per_capita * 100, 1)

    # Clasificar nivel de sesgo
    def clasificar_sesgo(valor):
        if valor < -50:
            return "Muy bajo (posible sub-reporte)"
        elif valor < -25:
            return "Bajo"
        elif valor < 25:
            return "Normal"
        elif valor < 50:
            return "Alto"
        else:
            return "Muy alto"

    df['clasificacion_sesgo'] = df['sesgo_densidad'].apply(clasificar_sesgo)

    return df


def analizar_sesgo_temporal(
    inventario: gpd.GeoDataFrame,
    col_anio: str = 'AÑO'
) -> pd.DataFrame:
    """
    Analiza la distribución temporal de eventos por cantón.

    Esto ayuda a identificar si hay cambios en los patrones de reporte
    a lo largo del tiempo (ej: mejora en sistemas de registro).

    Args:
        inventario: GeoDataFrame de deslizamientos
        col_anio: Nombre de la columna de año

    Returns:
        pd.DataFrame: Distribución temporal por cantón
    """
    print("\n[INFO] Analizando distribución temporal...")

    if col_anio not in inventario.columns:
        print(f"  ADVERTENCIA: No se encontró columna {col_anio}")
        return None

    # Identificar columna de cantón en inventario
    col_canton = identificar_columna_canton(inventario)
    if col_canton is None:
        col_canton = 'CANTON'

    # Tabla cruzada
    if col_canton in inventario.columns:
        tabla = pd.crosstab(
            inventario[col_anio],
            inventario[col_canton].str.upper()
        )
        return tabla

    return None


def generar_mapa_densidad(
    cantones: gpd.GeoDataFrame,
    metricas: pd.DataFrame,
    ruta_salida: Path
):
    """
    Genera mapa coroplético de densidad de deslizamientos.

    Args:
        cantones: GeoDataFrame de cantones
        metricas: DataFrame con métricas
        ruta_salida: Ruta para guardar el mapa
    """
    print("\n[INFO] Generando mapa de densidad...")

    # Unir métricas a cantones
    col_canton = identificar_columna_canton(cantones)
    cantones_plot = cantones.copy()
    cantones_plot['canton_upper'] = cantones_plot[col_canton].str.upper().str.strip()

    cantones_plot = cantones_plot.merge(
        metricas[['canton', 'densidad_km2', 'n_eventos']],
        left_on='canton_upper',
        right_on='canton',
        how='left'
    )

    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 10))

    # Mapa coroplético
    cantones_plot.plot(
        column='densidad_km2',
        ax=ax,
        legend=True,
        legend_kwds={
            'label': 'Densidad (eventos/km²)',
            'orientation': 'horizontal',
            'shrink': 0.6,
            'pad': 0.05
        },
        cmap='YlOrRd',
        edgecolor='black',
        linewidth=0.5
    )

    # Añadir etiquetas
    for idx, row in cantones_plot.iterrows():
        centroid = row.geometry.centroid
        label = f"{row['canton_upper']}\n({row['n_eventos']})"
        ax.annotate(
            label,
            xy=(centroid.x, centroid.y),
            ha='center',
            va='center',
            fontsize=8,
            fontweight='bold'
        )

    ax.set_title('Densidad de Deslizamientos por Cantón\nImbabura 2010-2023', fontsize=14)
    ax.set_xlabel('Este (m)')
    ax.set_ylabel('Norte (m)')

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_salida.name}")


def generar_mapa_sesgo(
    cantones: gpd.GeoDataFrame,
    metricas: pd.DataFrame,
    ruta_salida: Path
):
    """
    Genera mapa de sesgo relativo de reporte.

    Colores:
        - Azul: Sesgo negativo (posible sub-reporte)
        - Blanco: Normal
        - Rojo: Sesgo positivo (alto reporte)

    Args:
        cantones: GeoDataFrame de cantones
        metricas: DataFrame con métricas
        ruta_salida: Ruta para guardar el mapa
    """
    print("\n[INFO] Generando mapa de sesgo relativo...")

    # Unir métricas a cantones
    col_canton = identificar_columna_canton(cantones)
    cantones_plot = cantones.copy()
    cantones_plot['canton_upper'] = cantones_plot[col_canton].str.upper().str.strip()

    cantones_plot = cantones_plot.merge(
        metricas[['canton', 'sesgo_densidad', 'clasificacion_sesgo']],
        left_on='canton_upper',
        right_on='canton',
        how='left'
    )

    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 10))

    # Normalizar colores (centrado en 0)
    vmin = -100
    vmax = 100
    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)

    # Mapa coroplético
    cantones_plot.plot(
        column='sesgo_densidad',
        ax=ax,
        legend=True,
        legend_kwds={
            'label': 'Sesgo relativo (%)',
            'orientation': 'horizontal',
            'shrink': 0.6,
            'pad': 0.05
        },
        cmap='RdBu_r',
        norm=norm,
        edgecolor='black',
        linewidth=0.5
    )

    # Añadir etiquetas
    for idx, row in cantones_plot.iterrows():
        centroid = row.geometry.centroid
        sesgo = row['sesgo_densidad']
        label = f"{row['canton_upper']}\n({sesgo:+.0f}%)"
        ax.annotate(
            label,
            xy=(centroid.x, centroid.y),
            ha='center',
            va='center',
            fontsize=8,
            fontweight='bold'
        )

    ax.set_title('Sesgo Relativo de Reporte por Cantón\n(Azul=posible sub-reporte, Rojo=alto reporte)',
                 fontsize=12)
    ax.set_xlabel('Este (m)')
    ax.set_ylabel('Norte (m)')

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_salida.name}")


def generar_grafico_temporal(
    tabla_temporal: pd.DataFrame,
    ruta_salida: Path
):
    """
    Genera gráfico de evolución temporal por cantón.
    """
    if tabla_temporal is None:
        return

    print("\n[INFO] Generando gráfico temporal...")

    fig, ax = plt.subplots(figsize=(14, 6))

    tabla_temporal.plot(kind='line', ax=ax, marker='o', linewidth=2)

    ax.set_xlabel('Año')
    ax.set_ylabel('Número de deslizamientos')
    ax.set_title('Evolución Temporal de Deslizamientos por Cantón')
    ax.legend(title='Cantón', bbox_to_anchor=(1.02, 1), loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"       Guardado: {ruta_salida.name}")


def generar_recomendaciones(metricas: pd.DataFrame) -> List[Dict]:
    """
    Genera recomendaciones basadas en el análisis de sesgo.

    Referencia:
        Steger et al. (2016) - Interpretación de sesgos en modelos

    Args:
        metricas: DataFrame con métricas de sesgo

    Returns:
        List[Dict]: Lista de recomendaciones
    """
    print("\n[INFO] Generando recomendaciones...")

    recomendaciones = []

    # Cantones con posible sub-reporte
    sub_reporte = metricas[metricas['sesgo_densidad'] < -50]
    if len(sub_reporte) > 0:
        for _, row in sub_reporte.iterrows():
            recomendaciones.append({
                'canton': row['canton'],
                'tipo': 'POSIBLE_SUB_REPORTE',
                'sesgo': row['sesgo_densidad'],
                'recomendacion': f"El cantón {row['canton']} muestra una densidad de eventos {abs(row['sesgo_densidad']):.0f}% menor al promedio. "
                                 "Considerar: (1) verificar accesibilidad de la zona, (2) revisar capacidad institucional local, "
                                 "(3) reducir peso de pseudo-ausencias de este cantón en el modelo.",
                'referencia': "Steger et al. (2016). Geomorphology, 262, 8-23"
            })

    # Cantones con alto reporte
    alto_reporte = metricas[metricas['sesgo_densidad'] > 50]
    if len(alto_reporte) > 0:
        for _, row in alto_reporte.iterrows():
            recomendaciones.append({
                'canton': row['canton'],
                'tipo': 'ALTO_REPORTE',
                'sesgo': row['sesgo_densidad'],
                'recomendacion': f"El cantón {row['canton']} muestra una densidad de eventos {row['sesgo_densidad']:.0f}% mayor al promedio. "
                                 "Esto puede reflejar: (1) mayor susceptibilidad real, (2) mejor sistema de reporte, "
                                 "(3) mayor densidad poblacional. Verificar con expertos locales.",
                'referencia': "Petschko et al. (2014). NHESS, 14(1), 95-118"
            })

    # Recomendación general
    recomendaciones.append({
        'tipo': 'GENERAL',
        'recomendacion': "Para el muestreo de pseudo-ausencias (SCRIPT_03), considerar estratificación proporcional "
                         "que tenga en cuenta las diferencias de densidad entre cantones. Evitar sobremuestrear "
                         "ausencias en cantones con posible sub-reporte.",
        'referencia': "Bornaetxea et al. (2018). NHESS, 18(9), 2455-2469"
    })

    return recomendaciones


def generar_auditoria(
    metricas: pd.DataFrame,
    recomendaciones: List[Dict],
    ruta_salida: Path
):
    """
    Genera archivo de auditoría JSON.
    """
    auditoria = {
        "proceso": "ANALISIS_SESGO_ESPACIAL",
        "version": "1.0",
        "fecha_ejecucion": datetime.now().isoformat(),
        "autor": "Víctor Hugo Pinto Páez",

        "metodologia": {
            "descripcion": "Análisis de sesgo de reporte espacial en inventario de deslizamientos",
            "metricas_calculadas": [
                "Densidad de eventos por km²",
                "Eventos per cápita (por 10,000 hab)",
                "Sesgo relativo respecto a media provincial"
            ],
            "fuente_poblacional": "INEC - Censo 2022"
        },

        "resultados": {
            "metricas_por_canton": metricas.to_dict(orient='records'),
            "estadisticas_resumen": {
                "total_eventos": int(metricas['n_eventos'].sum()),
                "densidad_media": round(metricas['densidad_km2'].mean(), 4),
                "densidad_std": round(metricas['densidad_km2'].std(), 4),
                "rango_sesgo": [
                    round(metricas['sesgo_densidad'].min(), 1),
                    round(metricas['sesgo_densidad'].max(), 1)
                ]
            }
        },

        "recomendaciones": recomendaciones,

        "referencias_bibliograficas": [
            "Petschko, H., et al. (2014). NHESS, 14(1), 95-118",
            "Steger, S., et al. (2016). Geomorphology, 262, 8-23",
            "Bornaetxea, T., et al. (2018). NHESS, 18(9), 2455-2469"
        ],

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

    # 1. Cargar datos
    try:
        inventario, cantones = cargar_datos(INVENTARIO_GPKG, AOI_GPKG)
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        return

    # 2. Calcular métricas por cantón
    metricas = calcular_metricas_por_canton(inventario, cantones)

    # 3. Análisis temporal
    tabla_temporal = analizar_sesgo_temporal(inventario)

    # 4. Generar mapas
    generar_mapa_densidad(cantones, metricas, DIR_SALIDA / "mapa_densidad_deslizamientos.png")
    generar_mapa_sesgo(cantones, metricas, DIR_SALIDA / "mapa_sesgo_relativo.png")

    if tabla_temporal is not None:
        generar_grafico_temporal(tabla_temporal, DIR_SALIDA / "evolucion_temporal_cantones.png")

    # 5. Guardar métricas
    ruta_metricas = DIR_SALIDA / "analisis_sesgo_espacial.csv"
    metricas.to_csv(ruta_metricas, index=False)
    print(f"\n[INFO] Métricas guardadas: {ruta_metricas.name}")

    # 6. Generar recomendaciones
    recomendaciones = generar_recomendaciones(metricas)

    # 7. Generar auditoría
    generar_auditoria(metricas, recomendaciones, DIR_SALIDA / "AUDITORIA_SESGO_ESPACIAL.json")

    # Resumen final
    tiempo_total = datetime.now() - tiempo_inicio

    print("\n" + "=" * 70)
    print(" RESUMEN FINAL - ANÁLISIS DE SESGO ESPACIAL")
    print("=" * 70)

    print("\n MÉTRICAS POR CANTÓN:")
    print("-" * 70)
    print(f" {'Cantón':<25} {'N':<6} {'Dens/km²':<10} {'Sesgo %':<10} {'Clasificación':<20}")
    print("-" * 70)
    for _, row in metricas.sort_values('sesgo_densidad').iterrows():
        print(f" {row['canton']:<25} {row['n_eventos']:<6} {row['densidad_km2']:<10.4f} "
              f"{row['sesgo_densidad']:+<10.1f} {row['clasificacion_sesgo']:<20}")

    print("\n INTERPRETACIÓN:")
    print("   - Sesgo negativo: Posible sub-reporte (menos eventos de los esperados)")
    print("   - Sesgo positivo: Alto reporte o mayor susceptibilidad real")

    if len([r for r in recomendaciones if r.get('tipo') == 'POSIBLE_SUB_REPORTE']) > 0:
        print("\n ⚠️  ADVERTENCIA: Se detectaron cantones con posible sub-reporte.")
        print("    Revisar recomendaciones en la auditoría JSON.")

    print(f"\n Duración: {tiempo_total}")
    print(f" Archivos en: {DIR_SALIDA}")
    print("=" * 70)
    print(" ✅ ANÁLISIS DE SESGO ESPACIAL COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
