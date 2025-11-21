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
archivo = r'C:\Users\cris_\Downloads\clasificador\wikicid-classifier\wikicid-classifier\empresas_testing.xlsx'
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

def analizar_ia(nombre, resumen, contenido_web=""):

    # Construimos el JSON como texto normal, NO dentro de un f-string
    json_schema = """
{
  "sectores": ["Sector"],
  "tipo_ia": "IA tradicional ML clásico" o "IA Generativa (Gen IA)" o "IA Agéntica",
  "casos_uso": {"Sector": ["Caso exacto"]},
  "descripcion_relevante": "Qué hace y cómo usa IA",
  "proporciona_ia": "sí" o "no",
  "nivel_ajuste": 1,
  "observaciones": ""
}
"""

    # Ahora sí usamos f-string, pero el JSON ya está fuera
    prompt = f"""
Analiza si esta empresa ofrece soluciones de Inteligencia Artificial.

**INFORMACIÓN:**
Nombre: {nombre}
Descripción resumida: {resumen}
Contenido web: {contenido_web[:1000]}

**SECTORES Y CASOS DE IA:**

FINANCIERO:
- ML: Fraude tiempo real, Scoring crediticio
- GenIA: Agente LLM bancario, Resumen KYC/auditorías
- Agéntica: Agente AML/KYC, Agente financiero autoservicio

TELECOMUNICACIONES:
- ML: Predicción churn, Optimización red
- GenIA: Agentes atención (WhatsApp/voz), Resumen tickets
- Agéntica: Agente postventa, Agente operaciones red

RETAIL:
- ML: Forecasting demanda, Pricing dinámico
- GenIA: Product descriptions, Atención conversacional
- Agéntica: Agentes tiendas, Marketing automatizado

SALUD:
- ML: Diagnóstico imágenes, Modelos riesgo
- GenIA: Resumen expediente, Notas médicas
- Agéntica: Agente administrativo, Soporte clínico

si no pertenece a estos sectores y usa IA solo dime que no funciona con IA y cualquier otro sector puedes mencionar que no pertenece a estos

Responde JSON EXACTO (sin markdown):
{json_schema}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente experto en empresas y su informacion en sus sectores de Salud,Retail, Comunicacione y financiero que clasifica empresas según uso de Inteligencia Artificial y sector."},
            {"role": "user", "content": prompt}
        ]
    )

    try:
        resultado = response.choices[0].message.content
        return json.loads(resultado)
    except Exception:
        return {"error": "No se pudo parsear JSON", "raw_response": response.choices[0].message.content}


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

    try:
        driver.get(url)
        time.sleep(5)
        contenido_web = driver.find_element(By.TAG_NAME, "body").text
        texto_corto = contenido_web[:4000]
        prompt = f"Describe brevemente de qué trata esta página web:\n{texto_corto}"
        fuente = "web"
    except Exception as e:
        print(f"Línea {idx}: No se pudo acceder a la URL -> {e}")
        try:
            resumen_wiki = wikipedia.summary(nombre, sentences=3, auto_suggest=True, redirect=True)
            prompt = f"Proporciona un resumen conciso sobre la empresa {nombre} basado en la siguiente información de Wikipedia:\n{resumen_wiki}"
            fuente = "Wikipedia"
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
            info_oc = consultar_open_corporates(nombre)
            if info_oc:
                prompt = f"Proporciona un resumen conciso sobre la empresa {nombre} basado en la siguiente información de OpenCorporates:\n{info_oc}"
                fuente = "OpenCorporates"
            else:
                crunchbase_key = "TU_CRUNCHBASE_KEY"  # reemplaza con tu key
                info_cb = consultar_crunchbase(nombre, crunchbase_key)
                if info_cb:
                    prompt = f"Proporciona un resumen conciso sobre la empresa {nombre} basado en la siguiente información de Crunchbase:\n{info_cb}"
                    fuente = "Crunchbase"
                else:
                    prompt = f"Proporciona un resumen conciso y profesional sobre la empresa {nombre} basado en información pública conocida"
                    fuente = "fuente pública"

    # --- Generar resumen con GPT ---
    print(f"Línea {idx}: Procesando IA ({fuente})...")
    start_time = time.time()
    respuesta = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente que genera resúmenes claros y concisos sobre empresas. Ademas clasificas con precision categorias"},
            {"role": "user", "content": prompt}
        ]
    )
    resumen = respuesta.choices[0].message.content

    # --- Analizar si es empresa de IA ---
    info_ia = analizar_ia(nombre, resumen, contenido_web)

    resumenes.append({
        "Empresa": nombre,
        "URL": url,
        "Resumen": resumen,
        "IA_info": info_ia
    })

    end_time = time.time()
    print(f"Línea {idx}: IA procesada en {end_time - start_time:.2f} segundos")
    print(f"Línea {idx}: Resumen -> {resumen[:200]}...\n")

# --- Guardar resultados ---

filas = []

for r in resumenes:
    empresa = r["Empresa"]
    url = r["URL"]
    resumen = r["Resumen"]
    ia = r["IA_info"]

    if isinstance(ia, dict) and "error" not in ia:
        sectores = ", ".join(ia.get("sectores", []))
        tipo_ia = ia.get("tipo_ia", "")
        
        # Convertir casos de uso: dict -> texto "Sector: caso1, caso2"
        casos_dict = ia.get("casos_uso", {})
        casos_uso = "; ".join(
            [f"{sector}: {', '.join(casos)}" for sector, casos in casos_dict.items()]
        )

        descripcion = ia.get("descripcion_relevante", "")
        proporciona_ia = ia.get("proporciona_ia", "")   # NUEVO
        nivel = ia.get("nivel_ajuste", "")
        observ = ia.get("observaciones", "")
    else:
        sectores = ""
        tipo_ia = ""
        casos_uso = ""
        descripcion = ""
        proporciona_ia = ""    # NUEVO
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
        "Proporciona_IA": proporciona_ia,   # NUEVA COLUMNA
        "Observaciones": observ[:50]
    })

df_final = pd.DataFrame(filas)

# ordenar por sector y tipo de IA
df_final = df_final.sort_values(by=["Sector", "Tipo_IA"], ascending=True)

df_final.to_excel("resumen_websites.xlsx", index=False)

print("Resúmenes guardados en resumen_websites.xlsx")

driver.quit()