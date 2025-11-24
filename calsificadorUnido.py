import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from openai import OpenAI
import wikipedia
import requests
import time
import json

# --- CONFIGURACIÓN OPENAI ---
client = OpenAI(api_key="")  # reemplaza con tu API Key

# --- CONFIGURACIÓN SELENIUM ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
driver = webdriver.Chrome(options=chrome_options)

# --- CARGAR EXCEL ---
archivo = r'C:\Users\cris_\Downloads\clasificacion_git\empresas_wikicid.xlsx'
df = pd.read_excel(archivo)

# --- FUNCIONES AUXILIARES ---

def consultar_open_corporates(nombre):
    try:
        url_api = f"https://api.opencorporates.com/v0.4/companies/search?q={nombre}"
        response = requests.get(url_api, timeout=10)
        data = response.json()
        if data['results']['companies']:
            company = data['results']['companies'][0]['company']
            info = f"Nombre: {company.get('name')}, Jurisdicción: {company.get('jurisdiction_code')}, Estado: {company.get('current_status')}, Fecha de creación: {company.get('incorporation_date')}"
            return info
        return None
    except Exception:
        return None

def consultar_crunchbase(nombre, api_key):
    try:
        url_api = f"https://api.crunchbase.com/api/v4/entities/organizations?user_key={api_key}&query={nombre}"
        response = requests.get(url_api, timeout=10)
        data = response.json()
        if data.get('data', {}).get('items'):
            company = data['data']['items'][0]['properties']
            info = f"Nombre: {company.get('name')}, Fundada: {company.get('founded_on')}, Estado: {company.get('status')}, Categoría: {company.get('category')}"
            return info
        return None
    except Exception:
        return None

#def analizar_ia(nombre, resumen, contenido_web=""):

    # Construimos el JSON como texto normal, NO dentro de un f-string
#    json_schema = """
#{
#  "sectores": ["Sector"],
#  "tipo_ia": "IA tradicional ML clásico" o "IA Generativa (Gen IA)" o "IA Agéntica",
#  "casos_uso": {"Sector": ["Caso exacto"]},
#  "descripcion_relevante": "Qué hace y cómo usa IA",
#  "proporciona_ia": "sí" o "no",
#  "nivel_ajuste": 1,
#  "observaciones": ""
#}
#"""

#    # Ahora sí usamos f-string, pero el JSON ya está fuera
#    prompt = f"""
#Analiza si esta empresa ofrece soluciones de Inteligencia Artificial.

#**INFORMACIÓN:**
#Nombre: {nombre}
#Descripción resumida: {resumen}
#Contenido web: {contenido_web[:1000]}

#**SECTORES Y CASOS DE IA:**

#FINANCIERO:
#- ML: Fraude tiempo real, Scoring crediticio
#- GenIA: Agente LLM bancario, Resumen KYC/auditorías
#- Agéntica: Agente AML/KYC, Agente financiero autoservicio

#TELECOMUNICACIONES:
#- ML: Predicción churn, Optimización red
#- GenIA: Agentes atención (WhatsApp/voz), Resumen tickets
#- Agéntica: Agente postventa, Agente operaciones red

#RETAIL:
#- ML: Forecasting demanda, Pricing dinámico
#- GenIA: Product descriptions, Atención conversacional
#- Agéntica: Agentes tiendas, Marketing automatizado

#SALUD:
#- ML: Diagnóstico imágenes, Modelos riesgo
#- GenIA: Resumen expediente, Notas médicas
#- Agéntica: Agente administrativo, Soporte clínico

#si no pertenece a estos sectores y usa IA solo dime que no funciona con IA y cualquier otro sector puedes mencionar que no pertenece a estos solo con NO y descartarlo

#Responde JSON EXACTO (sin markdown):
#{json_schema}
#"""

#   response = client.chat.completions.create(
#        model="gpt-4.1-mini",
#        messages=[
#            {"role": "system", "content": "Eres un asistente experto en empresas y su informacion en sus sectores de Salud,Retail, Comunicacione y financiero que clasifica empresas según uso de Inteligencia Artificial y sector."},
#            {"role": "user", "content": prompt}
#        ]
#    )

#    try:
#        resultado = response.choices[0].message.content
#        return json.loads(resultado)
#    except Exception:
#        return {"error": "No se pudo parsear JSON", "raw_response": response.choices[0].message.content}


def procesar_todo(nombre, fuentes):
    """
    Genera resumen + análisis de IA + clasificación en una sola llamada.
    """

    # Unir todas las fuentes en texto
    texto_fuentes = ""
    for fuente, contenido in fuentes.items():
        if contenido:
            texto_fuentes += f"\n--- {fuente} ---\n{contenido[:2000]}\n"

    schema_json = """
{
  "resumen": "Resumen profesional basado en las fuentes",
  "sector": "Financiero | Telecomunicaciones | Retail | Energia | Salud | No aplica",
  "tipo_ia": "IA tradicional | IA Generativa | IA Agéntica | No aplica",
  "proporciona_ia": "sí | no",
  "casos_uso": {"Sector": ["caso exacto"]},
  "descripcion_relevante": "Cómo usa o proporciona IA la empresa",
  "observaciones": ""
}
"""

    prompt = f"""
Analiza la siguiente empresa basándote exclusivamente en las fuentes proporcionadas
y luego devuelve un JSON EXACTO en español que siga el esquema de abajo.

NOMBRE DE LA EMPRESA:
{nombre}

FUENTES:
{texto_fuentes}

INSTRUCCIONES:
1. Genera un RESUMEN profesional claro y conciso.
2. Clasifica el SECTOR entre:
   - Financiero
   - Telecomunicaciones
   - Retail / Ecommerce
   - Energía
   - Salud
   Si no corresponde → usar "No aplica".
3. Determina si usa o proporciona IA (sí o no).
4. Clasifica el TIPO DE IA:
   - IA tradicional (ML clásico)
   - IA Generativa (Gen IA)
   - IA Agéntica
   - No aplica
5. Especifica los CASOS DE USO aplicables según sector
#**SECTORES Y CASOS DE IA:**

#FINANCIERO:
#- ML: Fraude tiempo real, Scoring crediticio
#- GenIA: Agente LLM bancario, Resumen KYC/auditorías
#- Agéntica: Agente AML/KYC, Agente financiero autoservicio

#TELECOMUNICACIONES:
#- ML: Predicción churn, Optimización red
#- GenIA: Agentes atención (WhatsApp/voz), Resumen tickets
#- Agéntica: Agente postventa, Agente operaciones red

#RETAIL:
#- ML: Forecasting demanda, Pricing dinámico
#- GenIA: Product descriptions, Atención conversacional
#- Agéntica: Agentes tiendas, Marketing automatizado

#SALUD:
#- ML: Diagnóstico imágenes, Modelos riesgo
#- GenIA: Resumen expediente, Notas médicas
#- Agéntica: Agente administrativo, Soporte clínico

#si no pertenece a estos sectores y usa IA solo dime que no funciona con IA y cualquier otro sector puedes mencionar que no pertenece a estos solo con NO y descartarlo.
    -
6. Completa el JSON EXACTO:

{schema_json}

NO agregues comentarios, explicaciones ni texto fuera del JSON.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Eres un experto en análisis de empresas y clasificación de IA."},
            {"role": "user", "content": prompt}
        ]
    )

    output = response.choices[0].message.content

    try:
        return json.loads(output)
    except:
        return {"error": "JSON no válido", "raw": output}



# --- BUCLE PRINCIPAL ---
resumenes = []

for idx, row in enumerate(df.itertuples(), start=1):
    nombre = getattr(row, "Nombre")
    url = getattr(row, "Website")
    
    print(f"\n====================")
    print(f"Línea {idx}: Empresa -> {nombre}")
    print(f"Línea {idx}: Tomando URL -> {url}")
    
    prompt = ""
    fuente = ""
    contenido_web = ""
    
    fuentes_disponibles = {}
    contenido_web = ""
    resumen_wiki = ""
    info_oc = ""
    info_cb = ""

    # Website
    try:
        driver.get(url)
        time.sleep(5)
        contenido_web = driver.find_element(By.TAG_NAME, "body").text[:4000]
        fuentes_disponibles["Web"] = contenido_web
    except Exception:
        pass

    # Wikipedia
    try:
        resumen_wiki = wikipedia.summary(nombre, sentences=3, auto_suggest=True, redirect=True)
        fuentes_disponibles["Wikipedia"] = resumen_wiki
    except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
        pass

    # OpenCorporates
    info_oc = consultar_open_corporates(nombre)
    if info_oc:
        fuentes_disponibles["OpenCorporates"] = info_oc

    # Crunchbase
    try:
        info_cb = consultar_crunchbase(nombre, crunchbase_key)
        if info_cb:
            fuentes_disponibles["Crunchbase"] = info_cb
    except NameError:
        # Esto se ejecuta si crunchbase_key no está definida
        pass
    except Exception:
        # Captura cualquier otro error de Crunchbase
        pass


    print(f"linea{idx}: IA procesando informacion")


    ia = procesar_todo(nombre,fuentes_disponibles)

    #resumenes.append({
    #   "Empresa": nombre,  3
    #    "URL":url,
    #    "IA_info":ia
    #})

    print("Resultados:", ia)

    #prompt = f"Genera un resumen conciso y profesional sobre la empresa {nombre} usando toda la información disponible en:\n\n"

    #for fuente, contenido in fuentes_disponibles.items():
        #prompt += f"--- {fuente} ---\n{contenido}\n\n"

    #prompt += "Prioriza la información más relevante y genera un resumen claro y coherente."



#    try:
#       driver.get(url)
#        time.sleep(5)
#        contenido_web = driver.find_element(By.TAG_NAME, "body").text
#        texto_corto = contenido_web[:4000]
#        prompt = f"Describe brevemente de qué trata esta página web:\n{texto_corto}"
#        fuente = "web"
##    except Exception as e:
#        print(f"Línea {idx}: No se pudo acceder a la URL -> {e}")
#        try:
#            resumen_wiki = wikipedia.summary(nombre, sentences=3, auto_suggest=True, redirect=True)
#            prompt = f"Proporciona un resumen conciso sobre la empresa {nombre} basado en la siguiente información de Wikipedia:\n{resumen_wiki}"
#            fuente = "Wikipedia"
#        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
#            info_oc = consultar_open_corporates(nombre)
#            if info_oc:
#                prompt = f"Proporciona un resumen conciso sobre la empresa {nombre} basado en la siguiente información de OpenCorporates:\n{info_oc}"
#                fuente = "OpenCorporates"
#            else:
#                crunchbase_key = "TU_CRUNCHBASE_KEY"  # reemplaza con tu key
#                info_cb = consultar_crunchbase(nombre, crunchbase_key)
#                if info_cb:
#                    prompt = f"Proporciona un resumen conciso sobre la empresa {nombre} basado en la siguiente información de Crunchbase:\n{info_cb}"
#                    fuente = "Crunchbase"
#                else:
#                    prompt = f"Proporciona un resumen conciso y profesional sobre la empresa {nombre} basado en información pública conocida"
#                   fuente = "fuente pública"

    # --- Generar resumen con GPT ---
    print(f"Línea {idx}: Procesando IA ({fuente})...")
    start_time = time.time()
    #respuesta = client.chat.completions.create(
    #    model="gpt-5-mini",
    #    messages=[
    #        {"role": "system", "content": "Eres un asistente que genera resúmenes claros y concisos sobre empresas. Ademas clasificas con precision exlusivamente los siguientes sectores:Financiero, Telecomunicaciones,Retail o ecommerce,Energia y Salud. Donde en el sector finciero clasificaras que tipo de IA utiliza o proporciona la empresa para Fraude en tiempo real, Scoring crediticio, Agentes LLM para atencion y soporte bancario, Resumen de inteligencia o auditoria, Agentes AML con razonamiento, Agenetes financieros de autoservicios"
    #        "para el sector de Telecomunicaciones clasificas que tipo de IA usa y proporciona y despues categorizas si hacen prediccion de churn, Optimizacion de Red, Agentes de atencion y soporte, Resumen inteligente de interacciones , Agentes de postventa multicanal, Agentes de operaciones de red"
    #        "para el sector de Retail o ecommerce clasificas por el tipo de IA que usan o proporcionan ademas si este sector si realiza Forecasting de demanda, pricing dinamico,Product Description, Atencion o venta conversacional, Agentes de Operaciones en tienda, Agentes de Marketing automatizado"
    #        "para el sector de energia clasificas que tipo de IA usa o proporciona y luego clasificas si hacen prediccion de demanda, Deteccion de perdidas, Asistencia de soporte tecnico, Documentacion y analisis de insepcciones, Agentes de despacho, Agentes de atencion para fallas masivas"
    #        "para el sector de salud clasificas que tipo de IA usa o proporciona despues clasificas si hacen Diagnostico por imagenes asistido, modelos de riesgos de enfermedades, Resumenes de expediente clinico, generacion de notas medicas y documentacion, Agente administrativos, Agentes de soporte"
    #        "Y LOS CASOS EN DONDE NO PROPORCIONEN IA NO LOS COLOQUES. DESCARTA ESAS EMPRESAS Y CUANDO LOS CASOS DE USO NO SEAN SOLO MENCIONA QUE NO APLICA"},
    #        {"role": "user", "content": prompt}
    #    ]
    #)
    #resumen = respuesta.choices[0].message.content

    # --- Analizar si es empresa de IA ---
    #info_ia = analizar_ia(nombre, resumen, contenido_web)

    resumenes.append({
        "Empresa": nombre,
        "URL": url,
        "Resumen": ia.get("resumen",""),
        "IA_info": ia
    })

    end_time = time.time()
    print(f"Línea {idx}: IA procesada en {end_time - start_time:.2f} segundos")
    #print(f"Línea {idx}: Resumen -> {resumen[:200]}...\n")

# --- Guardar resultados ---

filas = []

for r in resumenes:
    empresa = r["Empresa"]
    url = r["URL"]
    resumen = r["Resumen"]
    ia = r["IA_info"]

    if isinstance(ia, dict) and "error" not in ia:
        sectores = ia.get("sector","")
        tipo_ia = ia.get("tipo_ia", "")

        # Casos de uso
        casos_dict = ia.get("casos_uso", {})
        if isinstance(casos_dict, dict):
            casos_uso = "; ".join(
                [f"{sector}: {', '.join(casos)}" for sector, casos in casos_dict.items()]
            )
        else:
            casos_uso = casos_dict if casos_dict else ""

        descripcion = ia.get("descripcion_relevante", "")
        proporciona_ia = ia.get("proporciona_ia", "")
        nivel = ia.get("nivel_ajuste", "")
        observ = ia.get("observaciones", "")
    else:
        sectores = ""
        tipo_ia = ""
        casos_uso = ""
        descripcion = ""
        proporciona_ia = ""
        nivel = ""
        observ = ""

    filas.append({
        "Empresa": empresa,
        "URL": url,
        "Resumen": resumen[:100],
        "Sector": sectores,
        "Tipo_IA": tipo_ia,
        "Casos_Uso": casos_uso,
        "Descripcion_Relevante": descripcion[:50],
        "Proporciona_IA": proporciona_ia,
        "Observaciones": observ[:50]
    })


df_final = pd.DataFrame(filas)

# Filtrar empresas que **sí proporcionan IA**
df_final = df_final[df_final["Proporciona_IA"].str.lower() != "no"]

# ordenar por sector y tipo de IA
df_final = df_final.sort_values(by=["Sector", "Tipo_IA"], ascending=True)

df_final.to_excel("resumen_websites.xlsx", index=False)

print("Resúmenes guardados en resumen_websites.xlsx")