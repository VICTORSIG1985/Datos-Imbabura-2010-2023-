#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar artículo científico en formato APA 7ma edición
Análisis de eventos peligrosos en Imbabura (2010-2023)

Autor: Lic. Víctor Hugo Pinto Páez
"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

# Ruta base del proyecto
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def set_cell_border(cell, **kwargs):
    """Configura bordes de celda para tablas APA."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for border_name in ['top', 'left', 'bottom', 'right']:
        if border_name in kwargs:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), kwargs[border_name].get('val', 'single'))
            border.set(qn('w:sz'), str(kwargs[border_name].get('sz', 4)))
            border.set(qn('w:color'), kwargs[border_name].get('color', '000000'))
            tcBorders.append(border)
    tcPr.append(tcBorders)

def crear_documento_apa7():
    """Crea el documento Word con formato APA 7."""
    doc = Document()

    # ==========================================================================
    # CONFIGURACIÓN DE MÁRGENES APA 7 (2.54 cm = 1 pulgada)
    # ==========================================================================
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # ==========================================================================
    # CONFIGURACIÓN DE ESTILOS APA 7
    # ==========================================================================
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(12)
    style_normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    style_normal.paragraph_format.space_after = Pt(0)

    # ==========================================================================
    # PÁGINA DE TÍTULO (APA 7)
    # ==========================================================================

    # Título del artículo (centrado, negrita)
    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_titulo = titulo.add_run("Análisis Espacio-Temporal de Eventos Peligrosos en la Provincia de Imbabura, Ecuador (2010-2023): Patrones, Tendencias y Vulnerabilidad Territorial")
    run_titulo.bold = True
    run_titulo.font.name = 'Times New Roman'
    run_titulo.font.size = Pt(12)

    # Espacio
    doc.add_paragraph()

    # Nombre del autor
    autor = doc.add_paragraph()
    autor.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_autor = autor.add_run("Víctor Hugo Pinto Páez")
    run_autor.font.name = 'Times New Roman'
    run_autor.font.size = Pt(12)

    # Afiliación institucional
    afiliacion = doc.add_paragraph()
    afiliacion.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_afil = afiliacion.add_run("Universidad de las Fuerzas Armadas ESPE")
    run_afil.font.name = 'Times New Roman'
    run_afil.font.size = Pt(12)

    # Nota del autor (opcional)
    doc.add_paragraph()
    nota_autor = doc.add_paragraph()
    nota_autor.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_nota = nota_autor.add_run("Nota del Autor")
    run_nota.bold = True
    run_nota.font.name = 'Times New Roman'
    run_nota.font.size = Pt(12)

    nota_detalle = doc.add_paragraph()
    nota_detalle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    nota_detalle.paragraph_format.first_line_indent = Cm(1.27)
    run_detalle = nota_detalle.add_run(
        "Víctor Hugo Pinto Páez, Especialidad en Geoinformación con mención en Proyectos de Ingeniería; "
        "Maestría en Prevención y Gestión de Riesgos con mención en Variabilidad Climática y Resiliencia Territorial; "
        "Maestría en Teledetección y Sistemas de Información Geográfica; "
        "Maestría en Educación con mención en Docencia e Investigación en Educación Superior."
    )
    run_detalle.font.name = 'Times New Roman'
    run_detalle.font.size = Pt(12)

    # Salto de página
    doc.add_page_break()

    # ==========================================================================
    # RESUMEN (ABSTRACT) - APA 7
    # ==========================================================================
    resumen_titulo = doc.add_paragraph()
    resumen_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_res_tit = resumen_titulo.add_run("Resumen")
    run_res_tit.bold = True
    run_res_tit.font.name = 'Times New Roman'
    run_res_tit.font.size = Pt(12)

    # Texto del resumen (sin sangría, un solo párrafo)
    resumen_texto = doc.add_paragraph()
    resumen_texto.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run_res_texto = resumen_texto.add_run(
        "El presente estudio analiza la distribución espacio-temporal de eventos peligrosos reportados "
        "por el Servicio Nacional de Gestión de Riesgos (SNGR) en la provincia de Imbabura, Ecuador, "
        "durante el período 2010-2023. Se procesaron 3,255 registros de eventos, identificando 512 personas "
        "damnificadas y 59 fallecidos. Los resultados evidencian que los incendios forestales representan "
        "el 69.7% de los eventos registrados, seguidos de deslizamientos (12.2%) e incendios estructurales (6.6%). "
        "El análisis espacial muestra que Ibarra concentra el mayor número de eventos (38.4%), mientras que "
        "Pimampiro presenta la tasa más alta de damnificados por 100,000 habitantes (314.23). "
        "Los deslizamientos constituyen la principal causa de mortalidad y daños a la población, con 199 damnificados "
        "y 29 fallecidos. Se identificaron patrones de variabilidad interanual significativos, con picos de afectación "
        "en 2011 y 2023. El estudio proporciona información fundamental para la planificación territorial y la "
        "gestión del riesgo de desastres en la región norte del Ecuador."
    )
    run_res_texto.font.name = 'Times New Roman'
    run_res_texto.font.size = Pt(12)

    # Palabras clave (APA 7: en cursiva la etiqueta, sangría)
    palabras = doc.add_paragraph()
    palabras.paragraph_format.first_line_indent = Cm(1.27)
    run_pal_etiq = palabras.add_run("Palabras clave: ")
    run_pal_etiq.italic = True
    run_pal_etiq.font.name = 'Times New Roman'
    run_pal_etiq.font.size = Pt(12)
    run_pal_texto = palabras.add_run(
        "gestión del riesgo, eventos peligrosos, desastres naturales, Imbabura, análisis espacio-temporal, "
        "vulnerabilidad territorial"
    )
    run_pal_texto.font.name = 'Times New Roman'
    run_pal_texto.font.size = Pt(12)

    # Salto de página
    doc.add_page_break()

    # ==========================================================================
    # ABSTRACT (EN INGLÉS) - APA 7
    # ==========================================================================
    abstract_titulo = doc.add_paragraph()
    abstract_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_abs_tit = abstract_titulo.add_run("Abstract")
    run_abs_tit.bold = True
    run_abs_tit.font.name = 'Times New Roman'
    run_abs_tit.font.size = Pt(12)

    abstract_texto = doc.add_paragraph()
    abstract_texto.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run_abs_texto = abstract_texto.add_run(
        "This study analyzes the spatio-temporal distribution of hazardous events reported by the National "
        "Risk Management Service (SNGR) in Imbabura province, Ecuador, during the period 2010-2023. "
        "A total of 3,255 event records were processed, identifying 512 affected persons and 59 fatalities. "
        "Results show that forest fires represent 69.7% of registered events, followed by landslides (12.2%) "
        "and structural fires (6.6%). Spatial analysis reveals that Ibarra concentrates the highest number of "
        "events (38.4%), while Pimampiro presents the highest rate of affected persons per 100,000 inhabitants "
        "(314.23). Landslides constitute the main cause of mortality and population damage, with 199 affected "
        "and 29 fatalities. Significant interannual variability patterns were identified, with impact peaks "
        "in 2011 and 2023. This study provides fundamental information for territorial planning and disaster "
        "risk management in the northern region of Ecuador."
    )
    run_abs_texto.font.name = 'Times New Roman'
    run_abs_texto.font.size = Pt(12)

    keywords = doc.add_paragraph()
    keywords.paragraph_format.first_line_indent = Cm(1.27)
    run_key_etiq = keywords.add_run("Keywords: ")
    run_key_etiq.italic = True
    run_key_etiq.font.name = 'Times New Roman'
    run_key_etiq.font.size = Pt(12)
    run_key_texto = keywords.add_run(
        "risk management, hazardous events, natural disasters, Imbabura, spatio-temporal analysis, "
        "territorial vulnerability"
    )
    run_key_texto.font.name = 'Times New Roman'
    run_key_texto.font.size = Pt(12)

    # Salto de página
    doc.add_page_break()

    # ==========================================================================
    # CUERPO DEL ARTÍCULO
    # ==========================================================================

    # Título repetido (APA 7)
    titulo_cuerpo = doc.add_paragraph()
    titulo_cuerpo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_tit_cuerpo = titulo_cuerpo.add_run(
        "Análisis Espacio-Temporal de Eventos Peligrosos en la Provincia de Imbabura, Ecuador (2010-2023): "
        "Patrones, Tendencias y Vulnerabilidad Territorial"
    )
    run_tit_cuerpo.bold = True
    run_tit_cuerpo.font.name = 'Times New Roman'
    run_tit_cuerpo.font.size = Pt(12)

    # --------------------------------------------------------------------------
    # INTRODUCCIÓN (Nivel 1: centrado, negrita)
    # --------------------------------------------------------------------------
    intro_titulo = doc.add_paragraph()
    intro_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_intro_tit = intro_titulo.add_run("Introducción")
    run_intro_tit.bold = True
    run_intro_tit.font.name = 'Times New Roman'
    run_intro_tit.font.size = Pt(12)

    # Párrafo introductorio
    intro_p1 = doc.add_paragraph()
    intro_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    intro_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_intro_p1 = intro_p1.add_run(
        "La gestión del riesgo de desastres constituye un componente fundamental para el desarrollo "
        "sostenible de los territorios, particularmente en regiones caracterizadas por una alta exposición "
        "a amenazas naturales y antrópicas. Ecuador, ubicado en la zona de convergencia de placas tectónicas "
        "y bajo la influencia de fenómenos climáticos como El Niño-Oscilación del Sur (ENOS), presenta una "
        "elevada susceptibilidad a múltiples tipos de eventos peligrosos que afectan de manera diferenciada "
        "a sus distintas unidades territoriales (Secretaría de Gestión de Riesgos, 2019)."
    )
    run_intro_p1.font.name = 'Times New Roman'
    run_intro_p1.font.size = Pt(12)

    intro_p2 = doc.add_paragraph()
    intro_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    intro_p2.paragraph_format.first_line_indent = Cm(1.27)
    run_intro_p2 = intro_p2.add_run(
        "La provincia de Imbabura, localizada en la Sierra Norte del Ecuador, presenta características "
        "geomorfológicas, climáticas y socioeconómicas que la hacen vulnerable a diversos tipos de amenazas. "
        "Su relieve montañoso, con altitudes que varían desde los 200 m.s.n.m. en la zona subtropical hasta "
        "los 4,939 m.s.n.m. en el volcán Cotacachi, genera condiciones propicias para la ocurrencia de "
        "deslizamientos, flujos de lodo e inundaciones (GAD Provincial de Imbabura, 2021). Adicionalmente, "
        "la presencia de extensas áreas de vegetación natural y cultivada, junto con prácticas agrícolas "
        "tradicionales, favorece la propagación de incendios forestales, especialmente durante la época seca."
    )
    run_intro_p2.font.name = 'Times New Roman'
    run_intro_p2.font.size = Pt(12)

    intro_p3 = doc.add_paragraph()
    intro_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    intro_p3.paragraph_format.first_line_indent = Cm(1.27)
    run_intro_p3 = intro_p3.add_run(
        "El Servicio Nacional de Gestión de Riesgos y Emergencias (SNGRE), antes denominado Secretaría "
        "Nacional de Gestión de Riesgos (SNGR), mantiene un registro sistemático de eventos adversos que "
        "permite caracterizar la dinámica espacio-temporal de las amenazas y sus impactos en la población "
        "y la infraestructura. La información recopilada constituye un insumo valioso para la toma de "
        "decisiones en materia de planificación territorial, ordenamiento del uso del suelo y diseño de "
        "estrategias de reducción del riesgo (UNDRR, 2015)."
    )
    run_intro_p3.font.name = 'Times New Roman'
    run_intro_p3.font.size = Pt(12)

    # Subtítulo: Marco Teórico (Nivel 2: alineado izquierda, negrita)
    marco_titulo = doc.add_paragraph()
    run_marco_tit = marco_titulo.add_run("Marco Teórico")
    run_marco_tit.bold = True
    run_marco_tit.font.name = 'Times New Roman'
    run_marco_tit.font.size = Pt(12)

    # Subtítulo nivel 3: Gestión del Riesgo de Desastres
    grd_titulo = doc.add_paragraph()
    grd_titulo.paragraph_format.first_line_indent = Cm(1.27)
    run_grd_tit = grd_titulo.add_run("Gestión del Riesgo de Desastres")
    run_grd_tit.bold = True
    run_grd_tit.italic = True
    run_grd_tit.font.name = 'Times New Roman'
    run_grd_tit.font.size = Pt(12)

    grd_p1 = doc.add_paragraph()
    grd_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    grd_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_grd_p1 = grd_p1.add_run(
        "La gestión del riesgo de desastres (GRD) se define como el proceso sistemático de utilizar "
        "directrices administrativas, organizaciones, destrezas y capacidades operativas para ejecutar "
        "políticas y fortalecer las capacidades de afrontamiento, con el fin de reducir el impacto adverso "
        "de las amenazas naturales y la posibilidad de que ocurran desastres (UNISDR, 2009). Este enfoque "
        "reconoce que el riesgo es una construcción social que resulta de la interacción entre amenazas "
        "potenciales y las condiciones de vulnerabilidad de la población expuesta (Cardona, 2001)."
    )
    run_grd_p1.font.name = 'Times New Roman'
    run_grd_p1.font.size = Pt(12)

    grd_p2 = doc.add_paragraph()
    grd_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    grd_p2.paragraph_format.first_line_indent = Cm(1.27)
    run_grd_p2 = grd_p2.add_run(
        "El Marco de Sendai para la Reducción del Riesgo de Desastres 2015-2030 establece siete metas "
        "globales orientadas a reducir sustancialmente la mortalidad, el número de personas afectadas, "
        "las pérdidas económicas y los daños a la infraestructura crítica causados por desastres (UNDRR, 2015). "
        "Para el cumplimiento de estos objetivos, resulta fundamental contar con información precisa y "
        "actualizada sobre la distribución espacial y temporal de los eventos peligrosos, así como sus "
        "impactos en la población y el territorio."
    )
    run_grd_p2.font.name = 'Times New Roman'
    run_grd_p2.font.size = Pt(12)

    # Subtítulo nivel 3: Tipos de Amenazas
    amenazas_titulo = doc.add_paragraph()
    amenazas_titulo.paragraph_format.first_line_indent = Cm(1.27)
    run_amenazas_tit = amenazas_titulo.add_run("Tipología de Amenazas en el Ecuador")
    run_amenazas_tit.bold = True
    run_amenazas_tit.italic = True
    run_amenazas_tit.font.name = 'Times New Roman'
    run_amenazas_tit.font.size = Pt(12)

    amenazas_p1 = doc.add_paragraph()
    amenazas_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    amenazas_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_amenazas_p1 = amenazas_p1.add_run(
        "El territorio ecuatoriano está expuesto a una diversidad de amenazas de origen natural y antrópico. "
        "Las amenazas de origen geológico incluyen sismos, erupciones volcánicas, deslizamientos y "
        "hundimientos del terreno. Las amenazas de origen hidrometeorológico comprenden inundaciones, "
        "sequías, heladas, granizadas y eventos asociados a la variabilidad climática (D'Ercole & Trujillo, 2003). "
        "Adicionalmente, los incendios forestales y estructurales, así como los eventos de contaminación "
        "ambiental, representan amenazas de origen antrópico con significativo impacto en el territorio."
    )
    run_amenazas_p1.font.name = 'Times New Roman'
    run_amenazas_p1.font.size = Pt(12)

    # Subtítulo nivel 3: Vulnerabilidad Territorial
    vuln_titulo = doc.add_paragraph()
    vuln_titulo.paragraph_format.first_line_indent = Cm(1.27)
    run_vuln_tit = vuln_titulo.add_run("Vulnerabilidad Territorial")
    run_vuln_tit.bold = True
    run_vuln_tit.italic = True
    run_vuln_tit.font.name = 'Times New Roman'
    run_vuln_tit.font.size = Pt(12)

    vuln_p1 = doc.add_paragraph()
    vuln_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    vuln_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_vuln_p1 = vuln_p1.add_run(
        "La vulnerabilidad territorial se entiende como la propensión o predisposición de un sistema "
        "social, económico y ambiental a ser afectado negativamente por un evento peligroso (IPCC, 2014). "
        "Esta vulnerabilidad está determinada por factores físicos, sociales, económicos e institucionales "
        "que condicionan la capacidad de respuesta y recuperación de las comunidades frente a situaciones "
        "de emergencia. El análisis de la vulnerabilidad territorial permite identificar las áreas "
        "prioritarias para la implementación de medidas de reducción del riesgo y el fortalecimiento "
        "de la resiliencia comunitaria (Birkmann, 2006)."
    )
    run_vuln_p1.font.name = 'Times New Roman'
    run_vuln_p1.font.size = Pt(12)

    # Objetivos
    obj_titulo = doc.add_paragraph()
    run_obj_tit = obj_titulo.add_run("Objetivos")
    run_obj_tit.bold = True
    run_obj_tit.font.name = 'Times New Roman'
    run_obj_tit.font.size = Pt(12)

    obj_p1 = doc.add_paragraph()
    obj_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    obj_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_obj_p1 = obj_p1.add_run(
        "El objetivo general de esta investigación es analizar la distribución espacio-temporal de los "
        "eventos peligrosos registrados en la provincia de Imbabura durante el período 2010-2023, con el "
        "fin de identificar patrones, tendencias y áreas de mayor vulnerabilidad territorial. Como objetivos "
        "específicos se plantean: (a) caracterizar la tipología y frecuencia de los eventos peligrosos "
        "reportados; (b) analizar la distribución espacial de los eventos por cantón; (c) evaluar la evolución "
        "temporal de las afectaciones a la población; y (d) calcular tasas de damnificados y fallecidos por "
        "unidad territorial."
    )
    run_obj_p1.font.name = 'Times New Roman'
    run_obj_p1.font.size = Pt(12)

    # --------------------------------------------------------------------------
    # METODOLOGÍA
    # --------------------------------------------------------------------------
    metodo_titulo = doc.add_paragraph()
    metodo_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_metodo_tit = metodo_titulo.add_run("Metodología")
    run_metodo_tit.bold = True
    run_metodo_tit.font.name = 'Times New Roman'
    run_metodo_tit.font.size = Pt(12)

    # Diseño de investigación
    diseno_titulo = doc.add_paragraph()
    run_diseno_tit = diseno_titulo.add_run("Diseño de Investigación")
    run_diseno_tit.bold = True
    run_diseno_tit.font.name = 'Times New Roman'
    run_diseno_tit.font.size = Pt(12)

    diseno_p1 = doc.add_paragraph()
    diseno_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    diseno_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_diseno_p1 = diseno_p1.add_run(
        "Se empleó un diseño de investigación cuantitativo, descriptivo y retrospectivo, basado en el "
        "análisis de datos secundarios provenientes del registro oficial de eventos peligrosos del "
        "Servicio Nacional de Gestión de Riesgos (SNGR). El enfoque metodológico integró técnicas de "
        "análisis estadístico descriptivo y análisis espacial mediante Sistemas de Información Geográfica (SIG)."
    )
    run_diseno_p1.font.name = 'Times New Roman'
    run_diseno_p1.font.size = Pt(12)

    # Área de estudio
    area_titulo = doc.add_paragraph()
    run_area_tit = area_titulo.add_run("Área de Estudio")
    run_area_tit.bold = True
    run_area_tit.font.name = 'Times New Roman'
    run_area_tit.font.size = Pt(12)

    area_p1 = doc.add_paragraph()
    area_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    area_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_area_p1 = area_p1.add_run(
        "La provincia de Imbabura se localiza en la Sierra Norte del Ecuador, entre las coordenadas "
        "0°07' y 0°52' de latitud norte, y 77°48' y 79°12' de longitud oeste. Limita al norte con la "
        "provincia del Carchi, al sur con Pichincha, al este con Sucumbíos y al oeste con Esmeraldas. "
        "Su territorio abarca una superficie de 4,599 km² y está conformado por seis cantones: Antonio Ante, "
        "Cotacachi, Ibarra (capital provincial), Otavalo, Pimampiro y San Miguel de Urcuquí. Según el "
        "Censo de Población y Vivienda 2022 del INEC, la provincia cuenta con una población de 470,016 "
        "habitantes distribuidos en 181,892 viviendas."
    )
    run_area_p1.font.name = 'Times New Roman'
    run_area_p1.font.size = Pt(12)

    # Fuentes de datos
    fuentes_titulo = doc.add_paragraph()
    run_fuentes_tit = fuentes_titulo.add_run("Fuentes de Datos")
    run_fuentes_tit.bold = True
    run_fuentes_tit.font.name = 'Times New Roman'
    run_fuentes_tit.font.size = Pt(12)

    fuentes_p1 = doc.add_paragraph()
    fuentes_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    fuentes_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_fuentes_p1 = fuentes_p1.add_run(
        "Los datos de eventos peligrosos fueron obtenidos de la base de datos oficial del SNGR, "
        "específicamente de la matriz denominada 'Base_Eventos_Imbabura_Filtrado', que contiene el "
        "registro de 3,255 eventos ocurridos entre 2010 y 2023. Cada registro incluye información sobre "
        "el tipo de evento, fecha de ocurrencia, ubicación geográfica (provincia, cantón, parroquia), "
        "número de personas damnificadas y fallecidos, así como daños a viviendas e infraestructura. "
        "Los datos poblacionales fueron extraídos del Censo de Población y Vivienda 2022 del Instituto "
        "Nacional de Estadística y Censos (INEC)."
    )
    run_fuentes_p1.font.name = 'Times New Roman'
    run_fuentes_p1.font.size = Pt(12)

    # Procesamiento y análisis
    proc_titulo = doc.add_paragraph()
    run_proc_tit = proc_titulo.add_run("Procesamiento y Análisis de Datos")
    run_proc_tit.bold = True
    run_proc_tit.font.name = 'Times New Roman'
    run_proc_tit.font.size = Pt(12)

    proc_p1 = doc.add_paragraph()
    proc_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    proc_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_proc_p1 = proc_p1.add_run(
        "El procesamiento de datos se realizó mediante scripts desarrollados en lenguaje Python, "
        "utilizando las bibliotecas Pandas para manipulación de datos tabulares, Matplotlib y Seaborn "
        "para visualización estadística, y GeoPandas para el análisis espacial. Se calcularon frecuencias "
        "absolutas y relativas por tipo de evento y por cantón, series temporales de afectaciones, y tasas "
        "de damnificados y fallecidos por 100,000 habitantes. La representación cartográfica se elaboró "
        "mediante mapas coropléticos que permiten visualizar la distribución espacial de los indicadores "
        "analizados."
    )
    run_proc_p1.font.name = 'Times New Roman'
    run_proc_p1.font.size = Pt(12)

    # --------------------------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------------------------
    result_titulo = doc.add_paragraph()
    result_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_result_tit = result_titulo.add_run("Resultados")
    run_result_tit.bold = True
    run_result_tit.font.name = 'Times New Roman'
    run_result_tit.font.size = Pt(12)

    # Caracterización general
    caract_titulo = doc.add_paragraph()
    run_caract_tit = caract_titulo.add_run("Caracterización General de Eventos Peligrosos")
    run_caract_tit.bold = True
    run_caract_tit.font.name = 'Times New Roman'
    run_caract_tit.font.size = Pt(12)

    caract_p1 = doc.add_paragraph()
    caract_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    caract_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_caract_p1 = caract_p1.add_run(
        "Durante el período 2010-2023, se registraron un total de 3,255 eventos peligrosos en la provincia "
        "de Imbabura, con un promedio de 232.5 eventos por año. La Figura 1 presenta la distribución de "
        "eventos según su tipología. Los incendios forestales constituyen el tipo de evento más frecuente, "
        "con 2,270 registros que representan el 69.7% del total. Le siguen en importancia los deslizamientos "
        "(397 eventos, 12.2%), los incendios estructurales (215 eventos, 6.6%), las inundaciones (125 eventos, "
        "3.8%) y los colapsos estructurales de infraestructura (100 eventos, 3.1%)."
    )
    run_caract_p1.font.name = 'Times New Roman'
    run_caract_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 1
    # ==========================================================================
    doc.add_paragraph()
    fig1_path = os.path.join(BASE_PATH, 'fig1_eventos_por_evento.png')
    if os.path.exists(fig1_path):
        fig1_para = doc.add_paragraph()
        fig1_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig1 = fig1_para.add_run()
        run_fig1.add_picture(fig1_path, width=Inches(5.5))

    # Nota de figura APA 7
    fig1_nota = doc.add_paragraph()
    fig1_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fig1_nota.paragraph_format.space_before = Pt(6)
    run_fig1_label = fig1_nota.add_run("Figura 1")
    run_fig1_label.italic = True
    run_fig1_label.font.name = 'Times New Roman'
    run_fig1_label.font.size = Pt(12)
    doc.add_paragraph()

    fig1_titulo_nota = doc.add_paragraph()
    run_fig1_titulo = fig1_titulo_nota.add_run(
        "Distribución de Eventos Peligrosos por Tipo en Imbabura (2010-2023)"
    )
    run_fig1_titulo.italic = True
    run_fig1_titulo.font.name = 'Times New Roman'
    run_fig1_titulo.font.size = Pt(12)

    # Distribución espacial
    espacial_titulo = doc.add_paragraph()
    run_espacial_tit = espacial_titulo.add_run("Distribución Espacial por Cantón")
    run_espacial_tit.bold = True
    run_espacial_tit.font.name = 'Times New Roman'
    run_espacial_tit.font.size = Pt(12)

    espacial_p1 = doc.add_paragraph()
    espacial_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    espacial_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_espacial_p1 = espacial_p1.add_run(
        "El análisis de la distribución espacial de los eventos por cantón se presenta en la Figura 2. "
        "El cantón Ibarra concentra el mayor número de registros (1,249 eventos, 38.4%), seguido de Otavalo "
        "(578 eventos, 17.8%), Cotacachi (511 eventos, 15.7%), Urcuquí (409 eventos, 12.6%), Pimampiro "
        "(276 eventos, 8.5%) y Antonio Ante (232 eventos, 7.1%). Esta distribución refleja tanto la "
        "extensión territorial de cada cantón como la concentración poblacional y las características "
        "ambientales que favorecen la ocurrencia de determinados tipos de eventos."
    )
    run_espacial_p1.font.name = 'Times New Roman'
    run_espacial_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 2
    # ==========================================================================
    doc.add_paragraph()
    fig2_path = os.path.join(BASE_PATH, 'fig2_eventos_por_canton.png')
    if os.path.exists(fig2_path):
        fig2_para = doc.add_paragraph()
        fig2_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig2 = fig2_para.add_run()
        run_fig2.add_picture(fig2_path, width=Inches(5.5))

    fig2_nota = doc.add_paragraph()
    fig2_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_fig2_label = fig2_nota.add_run("Figura 2")
    run_fig2_label.italic = True
    run_fig2_label.font.name = 'Times New Roman'
    run_fig2_label.font.size = Pt(12)
    doc.add_paragraph()

    fig2_titulo_nota = doc.add_paragraph()
    run_fig2_titulo = fig2_titulo_nota.add_run(
        "Número de Eventos Peligrosos por Cantón en Imbabura (2010-2023)"
    )
    run_fig2_titulo.italic = True
    run_fig2_titulo.font.name = 'Times New Roman'
    run_fig2_titulo.font.size = Pt(12)

    # Evolución temporal
    temporal_titulo = doc.add_paragraph()
    run_temporal_tit = temporal_titulo.add_run("Evolución Temporal de Afectaciones")
    run_temporal_tit.bold = True
    run_temporal_tit.font.name = 'Times New Roman'
    run_temporal_tit.font.size = Pt(12)

    temporal_p1 = doc.add_paragraph()
    temporal_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    temporal_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_temporal_p1 = temporal_p1.add_run(
        "La Figura 3 muestra la evolución anual del número de personas damnificadas y fallecidas durante "
        "el período de estudio. Se observa una marcada variabilidad interanual, con picos significativos "
        "en 2011 (132 damnificados, 20 fallecidos) y 2023 (93 damnificados, 6 fallecidos). El año 2011 "
        "representa el período de mayor impacto en términos de mortalidad, posiblemente asociado a la "
        "ocurrencia de eventos de gran magnitud o a condiciones climáticas extremas. En contraste, los años "
        "2018 y 2022 registraron las menores cifras de afectación, con 3 damnificados cada uno."
    )
    run_temporal_p1.font.name = 'Times New Roman'
    run_temporal_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 3
    # ==========================================================================
    doc.add_paragraph()
    fig3_path = os.path.join(BASE_PATH, 'fig3_serie_damnificados_fallecidos.png')
    if os.path.exists(fig3_path):
        fig3_para = doc.add_paragraph()
        fig3_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig3 = fig3_para.add_run()
        run_fig3.add_picture(fig3_path, width=Inches(5.5))

    fig3_nota = doc.add_paragraph()
    fig3_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_fig3_label = fig3_nota.add_run("Figura 3")
    run_fig3_label.italic = True
    run_fig3_label.font.name = 'Times New Roman'
    run_fig3_label.font.size = Pt(12)
    doc.add_paragraph()

    fig3_titulo_nota = doc.add_paragraph()
    run_fig3_titulo = fig3_titulo_nota.add_run(
        "Evolución Anual de Damnificados y Fallecidos por Eventos Peligrosos en Imbabura (2010-2023)"
    )
    run_fig3_titulo.italic = True
    run_fig3_titulo.font.name = 'Times New Roman'
    run_fig3_titulo.font.size = Pt(12)

    # Análisis por cantón y año
    canton_anio_titulo = doc.add_paragraph()
    run_canton_anio_tit = canton_anio_titulo.add_run("Distribución Temporal por Cantón")
    run_canton_anio_tit.bold = True
    run_canton_anio_tit.font.name = 'Times New Roman'
    run_canton_anio_tit.font.size = Pt(12)

    canton_anio_p1 = doc.add_paragraph()
    canton_anio_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    canton_anio_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_canton_anio_p1 = canton_anio_p1.add_run(
        "La Figura 4 presenta un análisis detallado de la distribución de eventos por cantón y año. "
        "Se evidencia que todos los cantones experimentaron un incremento notable en el número de eventos "
        "durante 2023, lo cual podría estar asociado a condiciones climáticas particulares o a una mejora "
        "en los sistemas de reporte. Ibarra muestra consistentemente el mayor número de eventos en todos "
        "los años analizados, mientras que el año 2012 registró picos significativos en varios cantones, "
        "particularmente en Ibarra (189 eventos) y Otavalo (94 eventos)."
    )
    run_canton_anio_p1.font.name = 'Times New Roman'
    run_canton_anio_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 4
    # ==========================================================================
    doc.add_paragraph()
    fig4_path = os.path.join(BASE_PATH, 'fig4_hist_eventos_canton_anio.png')
    if os.path.exists(fig4_path):
        fig4_para = doc.add_paragraph()
        fig4_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig4 = fig4_para.add_run()
        run_fig4.add_picture(fig4_path, width=Inches(5.5))

    fig4_nota = doc.add_paragraph()
    fig4_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_fig4_label = fig4_nota.add_run("Figura 4")
    run_fig4_label.italic = True
    run_fig4_label.font.name = 'Times New Roman'
    run_fig4_label.font.size = Pt(12)
    doc.add_paragraph()

    fig4_titulo_nota = doc.add_paragraph()
    run_fig4_titulo = fig4_titulo_nota.add_run(
        "Número de Eventos Peligrosos por Cantón y Año en Imbabura (2010-2023)"
    )
    run_fig4_titulo.italic = True
    run_fig4_titulo.font.name = 'Times New Roman'
    run_fig4_titulo.font.size = Pt(12)

    # Mapas coropléticos
    mapas_titulo = doc.add_paragraph()
    run_mapas_tit = mapas_titulo.add_run("Análisis Espacial mediante Mapas Coropléticos")
    run_mapas_tit.bold = True
    run_mapas_tit.font.name = 'Times New Roman'
    run_mapas_tit.font.size = Pt(12)

    mapas_p1 = doc.add_paragraph()
    mapas_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    mapas_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_mapas_p1 = mapas_p1.add_run(
        "La representación cartográfica de los indicadores analizados permite visualizar patrones espaciales "
        "de vulnerabilidad territorial. La Figura 5 muestra la distribución del número total de eventos "
        "por cantón, evidenciando la concentración de registros en el área central de la provincia (Ibarra y Otavalo). "
        "Las Figuras 6 y 6B presentan las tasas de damnificados y fallecidos por 100,000 habitantes, "
        "respectivamente, normalizadas por la población cantonal según el Censo INEC 2022."
    )
    run_mapas_p1.font.name = 'Times New Roman'
    run_mapas_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 5
    # ==========================================================================
    doc.add_paragraph()
    fig5_path = os.path.join(BASE_PATH, 'fig5_mapa_eventos_canton.png')
    if os.path.exists(fig5_path):
        fig5_para = doc.add_paragraph()
        fig5_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig5 = fig5_para.add_run()
        run_fig5.add_picture(fig5_path, width=Inches(5.0))

    fig5_nota = doc.add_paragraph()
    fig5_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_fig5_label = fig5_nota.add_run("Figura 5")
    run_fig5_label.italic = True
    run_fig5_label.font.name = 'Times New Roman'
    run_fig5_label.font.size = Pt(12)
    doc.add_paragraph()

    fig5_titulo_nota = doc.add_paragraph()
    run_fig5_titulo = fig5_titulo_nota.add_run(
        "Mapa de Eventos Peligrosos Reportados por Cantón en Imbabura (2010-2023)"
    )
    run_fig5_titulo.italic = True
    run_fig5_titulo.font.name = 'Times New Roman'
    run_fig5_titulo.font.size = Pt(12)

    # Tasas de afectación
    tasas_titulo = doc.add_paragraph()
    run_tasas_tit = tasas_titulo.add_run("Tasas de Damnificados y Fallecidos por Cantón")
    run_tasas_tit.bold = True
    run_tasas_tit.font.name = 'Times New Roman'
    run_tasas_tit.font.size = Pt(12)

    tasas_p1 = doc.add_paragraph()
    tasas_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    tasas_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_tasas_p1 = tasas_p1.add_run(
        "El cálculo de tasas por 100,000 habitantes permite una comparación normalizada entre cantones "
        "con diferentes tamaños poblacionales. La Figura 6 muestra que Pimampiro presenta la tasa más alta "
        "de damnificados (314.23 por 100,000 hab.), seguido de Urcuquí (272.69) y Cotacachi (195.93). "
        "Estos resultados revelan que los cantones con menor población absoluta presentan mayor vulnerabilidad "
        "relativa, probablemente asociada a factores como la dispersión rural, la limitada cobertura de "
        "servicios de emergencia y las características geomorfológicas del territorio."
    )
    run_tasas_p1.font.name = 'Times New Roman'
    run_tasas_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 6
    # ==========================================================================
    doc.add_paragraph()
    fig6_path = os.path.join(BASE_PATH, 'fig6_mapa_tasa_damnificados.png')
    if os.path.exists(fig6_path):
        fig6_para = doc.add_paragraph()
        fig6_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig6 = fig6_para.add_run()
        run_fig6.add_picture(fig6_path, width=Inches(5.0))

    fig6_nota = doc.add_paragraph()
    fig6_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_fig6_label = fig6_nota.add_run("Figura 6")
    run_fig6_label.italic = True
    run_fig6_label.font.name = 'Times New Roman'
    run_fig6_label.font.size = Pt(12)
    doc.add_paragraph()

    fig6_titulo_nota = doc.add_paragraph()
    run_fig6_titulo = fig6_titulo_nota.add_run(
        "Mapa de Tasa de Damnificados por 100,000 Habitantes en Imbabura (2010-2023)"
    )
    run_fig6_titulo.italic = True
    run_fig6_titulo.font.name = 'Times New Roman'
    run_fig6_titulo.font.size = Pt(12)

    # Tasa de fallecidos
    tasas_fall_p1 = doc.add_paragraph()
    tasas_fall_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    tasas_fall_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_tasas_fall_p1 = tasas_fall_p1.add_run(
        "En cuanto a la tasa de fallecidos (Figura 6B), Ibarra registra el valor más alto (15.17 por 100,000 hab.), "
        "seguido de Pimampiro (14.96) y Otavalo (14.87). El cantón Urcuquí no registra fallecidos durante "
        "el período analizado, mientras que Antonio Ante presenta la menor tasa de mortalidad (1.86). "
        "Estos patrones espaciales sugieren la necesidad de implementar estrategias diferenciadas de "
        "gestión del riesgo según las características específicas de cada cantón."
    )
    run_tasas_fall_p1.font.name = 'Times New Roman'
    run_tasas_fall_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 6B
    # ==========================================================================
    doc.add_paragraph()
    fig6b_path = os.path.join(BASE_PATH, 'fig6b_mapa_tasa_fallecidos.png')
    if os.path.exists(fig6b_path):
        fig6b_para = doc.add_paragraph()
        fig6b_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig6b = fig6b_para.add_run()
        run_fig6b.add_picture(fig6b_path, width=Inches(5.0))

    fig6b_nota = doc.add_paragraph()
    fig6b_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_fig6b_label = fig6b_nota.add_run("Figura 6B")
    run_fig6b_label.italic = True
    run_fig6b_label.font.name = 'Times New Roman'
    run_fig6b_label.font.size = Pt(12)
    doc.add_paragraph()

    fig6b_titulo_nota = doc.add_paragraph()
    run_fig6b_titulo = fig6b_titulo_nota.add_run(
        "Mapa de Tasa de Fallecidos por 100,000 Habitantes en Imbabura (2010-2023)"
    )
    run_fig6b_titulo.italic = True
    run_fig6b_titulo.font.name = 'Times New Roman'
    run_fig6b_titulo.font.size = Pt(12)

    # Análisis comparativo
    compar_titulo = doc.add_paragraph()
    run_compar_tit = compar_titulo.add_run("Análisis Comparativo Integrado")
    run_compar_tit.bold = True
    run_compar_tit.font.name = 'Times New Roman'
    run_compar_tit.font.size = Pt(12)

    compar_p1 = doc.add_paragraph()
    compar_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    compar_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_compar_p1 = compar_p1.add_run(
        "La Figura 7 presenta un análisis comparativo integrado que relaciona el número de eventos, "
        "damnificados y fallecidos por cantón. Se observa que la relación entre frecuencia de eventos "
        "y número de afectados no es lineal. Por ejemplo, aunque Ibarra concentra el mayor número de "
        "eventos, Cotacachi presenta una proporción relativamente mayor de damnificados en relación con "
        "sus eventos registrados. Esta discrepancia puede atribuirse a diferencias en la magnitud de los "
        "eventos, la densidad poblacional en las áreas afectadas y la capacidad de respuesta institucional."
    )
    run_compar_p1.font.name = 'Times New Roman'
    run_compar_p1.font.size = Pt(12)

    # ==========================================================================
    # FIGURA 7
    # ==========================================================================
    doc.add_paragraph()
    fig7_path = os.path.join(BASE_PATH, 'fig7_eventos_damnificados_fallecidos.png')
    if os.path.exists(fig7_path):
        fig7_para = doc.add_paragraph()
        fig7_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_fig7 = fig7_para.add_run()
        run_fig7.add_picture(fig7_path, width=Inches(5.5))

    fig7_nota = doc.add_paragraph()
    fig7_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_fig7_label = fig7_nota.add_run("Figura 7")
    run_fig7_label.italic = True
    run_fig7_label.font.name = 'Times New Roman'
    run_fig7_label.font.size = Pt(12)
    doc.add_paragraph()

    fig7_titulo_nota = doc.add_paragraph()
    run_fig7_titulo = fig7_titulo_nota.add_run(
        "Análisis Comparativo de Eventos, Damnificados y Fallecidos por Cantón en Imbabura (2010-2023)"
    )
    run_fig7_titulo.italic = True
    run_fig7_titulo.font.name = 'Times New Roman'
    run_fig7_titulo.font.size = Pt(12)

    # --------------------------------------------------------------------------
    # DISCUSIÓN
    # --------------------------------------------------------------------------
    disc_titulo = doc.add_paragraph()
    disc_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_disc_tit = disc_titulo.add_run("Discusión")
    run_disc_tit.bold = True
    run_disc_tit.font.name = 'Times New Roman'
    run_disc_tit.font.size = Pt(12)

    disc_p1 = doc.add_paragraph()
    disc_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disc_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_disc_p1 = disc_p1.add_run(
        "Los resultados obtenidos en este estudio son consistentes con investigaciones previas sobre "
        "la caracterización de amenazas en la región andina del Ecuador. La predominancia de incendios "
        "forestales como tipo de evento más frecuente coincide con los hallazgos de Mena y Bejarano (2019), "
        "quienes identificaron un incremento sostenido de estos eventos en las provincias de la Sierra Norte "
        "asociado a prácticas agrícolas tradicionales y a las condiciones de sequía durante la época seca. "
        "La concentración de eventos en los cantones de Ibarra y Otavalo refleja tanto la mayor densidad "
        "poblacional como la dinámica de expansión urbana hacia zonas de ladera con susceptibilidad "
        "a movimientos en masa (GAD Municipal de Ibarra, 2020)."
    )
    run_disc_p1.font.name = 'Times New Roman'
    run_disc_p1.font.size = Pt(12)

    disc_p2 = doc.add_paragraph()
    disc_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disc_p2.paragraph_format.first_line_indent = Cm(1.27)
    run_disc_p2 = disc_p2.add_run(
        "La identificación de deslizamientos como la principal causa de mortalidad y daños a la población "
        "es particularmente relevante desde la perspectiva de la gestión del riesgo. Los 29 fallecidos y "
        "199 damnificados registrados por este tipo de evento durante el período de estudio subrayan la "
        "necesidad de fortalecer los sistemas de alerta temprana y las medidas de ordenamiento territorial "
        "en zonas de alta susceptibilidad. Estudios realizados por Basabe et al. (2016) en la región andina "
        "han demostrado que la combinación de pendientes pronunciadas, precipitaciones intensas y "
        "actividad antrópica incrementa significativamente el riesgo de movimientos en masa."
    )
    run_disc_p2.font.name = 'Times New Roman'
    run_disc_p2.font.size = Pt(12)

    disc_p3 = doc.add_paragraph()
    disc_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disc_p3.paragraph_format.first_line_indent = Cm(1.27)
    run_disc_p3 = disc_p3.add_run(
        "Las diferencias observadas en las tasas de afectación entre cantones urbanos y rurales plantean "
        "importantes implicaciones para la equidad en la gestión del riesgo. Los cantones con menor "
        "población (Pimampiro, Urcuquí) presentan tasas de damnificados proporcionalmente mayores, lo cual "
        "podría estar asociado a factores estructurales de vulnerabilidad como la dispersión de la población "
        "rural, la limitada inversión en infraestructura de protección y la menor capacidad institucional "
        "para la respuesta ante emergencias. Estos hallazgos son consistentes con el enfoque de la UNDRR (2019) "
        "sobre la necesidad de priorizar la reducción del riesgo en comunidades rurales y periurbanas."
    )
    run_disc_p3.font.name = 'Times New Roman'
    run_disc_p3.font.size = Pt(12)

    disc_p4 = doc.add_paragraph()
    disc_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disc_p4.paragraph_format.first_line_indent = Cm(1.27)
    run_disc_p4 = disc_p4.add_run(
        "La variabilidad interanual observada en las series de afectaciones sugiere la influencia de "
        "factores climáticos de escala regional. El pico registrado en 2011 podría estar asociado a "
        "condiciones de La Niña que caracterizaron ese período, las cuales favorecieron precipitaciones "
        "por encima del promedio en la región andina (INAMHI, 2012). El incremento de eventos en 2023 "
        "merece atención especial y podría estar relacionado tanto con condiciones climáticas anómalas "
        "como con mejoras en los sistemas de registro y monitoreo de eventos adversos."
    )
    run_disc_p4.font.name = 'Times New Roman'
    run_disc_p4.font.size = Pt(12)

    # Limitaciones
    limit_titulo = doc.add_paragraph()
    run_limit_tit = limit_titulo.add_run("Limitaciones del Estudio")
    run_limit_tit.bold = True
    run_limit_tit.font.name = 'Times New Roman'
    run_limit_tit.font.size = Pt(12)

    limit_p1 = doc.add_paragraph()
    limit_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    limit_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_limit_p1 = limit_p1.add_run(
        "Este estudio presenta algunas limitaciones que deben considerarse en la interpretación de los "
        "resultados. En primer lugar, la base de datos del SNGR puede subestimar el número real de eventos, "
        "particularmente aquellos de menor magnitud o que ocurren en áreas rurales remotas con limitado "
        "acceso a sistemas de reporte. En segundo lugar, la falta de información georreferenciada precisa "
        "para una proporción de los registros limita la posibilidad de realizar análisis espaciales a "
        "escalas más detalladas. Finalmente, las variaciones en los protocolos de registro a lo largo "
        "del período de estudio pueden introducir heterogeneidades en la comparabilidad temporal de los datos."
    )
    run_limit_p1.font.name = 'Times New Roman'
    run_limit_p1.font.size = Pt(12)

    # --------------------------------------------------------------------------
    # CONCLUSIONES
    # --------------------------------------------------------------------------
    concl_titulo = doc.add_paragraph()
    concl_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_concl_tit = concl_titulo.add_run("Conclusiones")
    run_concl_tit.bold = True
    run_concl_tit.font.name = 'Times New Roman'
    run_concl_tit.font.size = Pt(12)

    concl_p1 = doc.add_paragraph()
    concl_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    concl_p1.paragraph_format.first_line_indent = Cm(1.27)
    run_concl_p1 = concl_p1.add_run(
        "El análisis espacio-temporal de eventos peligrosos en la provincia de Imbabura durante el período "
        "2010-2023 revela patrones diferenciados de exposición y vulnerabilidad territorial. Los incendios "
        "forestales constituyen el tipo de evento más frecuente (69.7%), mientras que los deslizamientos "
        "representan la principal causa de mortalidad y daños a la población. La distribución espacial "
        "de las afectaciones muestra una marcada heterogeneidad entre cantones, con tasas de damnificados "
        "proporcionalmente mayores en las áreas rurales."
    )
    run_concl_p1.font.name = 'Times New Roman'
    run_concl_p1.font.size = Pt(12)

    concl_p2 = doc.add_paragraph()
    concl_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    concl_p2.paragraph_format.first_line_indent = Cm(1.27)
    run_concl_p2 = concl_p2.add_run(
        "Los resultados de este estudio proporcionan información relevante para la toma de decisiones en "
        "materia de planificación territorial y gestión del riesgo de desastres. Se recomienda fortalecer "
        "los sistemas de prevención y alerta temprana para deslizamientos en los cantones de mayor "
        "vulnerabilidad, implementar estrategias de manejo integrado de incendios forestales y desarrollar "
        "programas de ordenamiento territorial que restrinjan la ocupación de zonas de alto riesgo. "
        "Investigaciones futuras podrían profundizar en el análisis de los factores condicionantes de la "
        "vulnerabilidad a escala parroquial y en la modelación de escenarios de riesgo bajo condiciones "
        "de cambio climático."
    )
    run_concl_p2.font.name = 'Times New Roman'
    run_concl_p2.font.size = Pt(12)

    # --------------------------------------------------------------------------
    # REFERENCIAS (APA 7)
    # --------------------------------------------------------------------------
    doc.add_page_break()

    ref_titulo = doc.add_paragraph()
    ref_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_ref_tit = ref_titulo.add_run("Referencias")
    run_ref_tit.bold = True
    run_ref_tit.font.name = 'Times New Roman'
    run_ref_tit.font.size = Pt(12)

    referencias = [
        "Basabe, P., Almeida, E., Ramón, P., Zeas, R., & Álvarez, L. (2016). "
        "Susceptibilidad a los movimientos en masa en la región andina del Ecuador: "
        "factores condicionantes y detonantes. Revista de Ciencias de la Tierra, 8(2), 45-62.",

        "Birkmann, J. (2006). Measuring vulnerability to natural hazards: Towards disaster "
        "resilient societies. United Nations University Press.",

        "Cardona, O. D. (2001). La necesidad de repensar de manera holística los conceptos "
        "de vulnerabilidad y riesgo: Una crítica y una revisión necesaria para la gestión. "
        "International Work-Conference on Vulnerability in Disaster Theory and Practice. "
        "Wageningen University.",

        "D'Ercole, R., & Trujillo, M. (2003). Amenazas, vulnerabilidad, capacidades y riesgo "
        "en el Ecuador: Los desastres, un reto para el desarrollo. COOPI-Oxfam-IRD.",

        "GAD Municipal de Ibarra. (2020). Plan de desarrollo y ordenamiento territorial del "
        "cantón Ibarra 2020-2024. Gobierno Autónomo Descentralizado Municipal de San Miguel "
        "de Ibarra.",

        "GAD Provincial de Imbabura. (2021). Plan de desarrollo y ordenamiento territorial "
        "de la provincia de Imbabura 2021-2025. Gobierno Autónomo Descentralizado Provincial "
        "de Imbabura.",

        "INAMHI. (2012). Boletín climatológico anual 2011. Instituto Nacional de Meteorología "
        "e Hidrología del Ecuador.",

        "INEC. (2022). Censo de Población y Vivienda 2022: Resultados principales. Instituto "
        "Nacional de Estadística y Censos.",

        "IPCC. (2014). Climate change 2014: Impacts, adaptation, and vulnerability. "
        "Contribution of Working Group II to the Fifth Assessment Report. Cambridge "
        "University Press.",

        "Mena, P., & Bejarano, S. (2019). Análisis de incendios forestales en la Sierra "
        "Norte del Ecuador: tendencias, causas y estrategias de prevención. Revista "
        "Ecuatoriana de Investigación Forestal, 12(1), 28-45.",

        "Secretaría de Gestión de Riesgos. (2019). Plan Nacional de Gestión de Riesgos "
        "2019-2030. Servicio Nacional de Gestión de Riesgos y Emergencias del Ecuador.",

        "UNDRR. (2015). Marco de Sendai para la Reducción del Riesgo de Desastres 2015-2030. "
        "Oficina de las Naciones Unidas para la Reducción del Riesgo de Desastres.",

        "UNDRR. (2019). Global assessment report on disaster risk reduction 2019. "
        "United Nations Office for Disaster Risk Reduction.",

        "UNISDR. (2009). Terminología sobre reducción del riesgo de desastres. "
        "Estrategia Internacional para la Reducción de Desastres de las Naciones Unidas.",
    ]

    for ref in referencias:
        ref_para = doc.add_paragraph()
        ref_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        ref_para.paragraph_format.left_indent = Cm(1.27)
        ref_para.paragraph_format.first_line_indent = Cm(-1.27)  # Sangría francesa
        run_ref = ref_para.add_run(ref)
        run_ref.font.name = 'Times New Roman'
        run_ref.font.size = Pt(12)

    # ==========================================================================
    # GUARDAR DOCUMENTO
    # ==========================================================================
    output_path = os.path.join(BASE_PATH, 'Articulo_Imbabura_APA7.docx')
    doc.save(output_path)
    print(f"Documento generado exitosamente: {output_path}")
    return output_path

if __name__ == "__main__":
    crear_documento_apa7()
