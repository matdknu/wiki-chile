import requests
from bs4 import BeautifulSoup
import time
import csv

def obtener_sopa(url, intentos=3):
    """Realiza una solicitud HTTP y devuelve el contenido en una sopa de BeautifulSoup con manejo de reintentos."""
    for intento in range(intentos):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.Timeout:
            print(f"Tiempo de espera agotado para {url}. Reintentando ({intento + 1}/{intentos})...")
            time.sleep(5)
        except requests.RequestException as e:
            print(f"Error al acceder a {url}: {e}")
            return None
    return None

def extraer_familias(sopa):
    """Extrae las familias desde la página principal."""
    familias = []
    for div in sopa.find_all('div', class_='mw-category-group'):
        for li in div.find_all('li'):
            a_tag = li.find('a')
            if a_tag and 'Familia' in a_tag.text and 'Fundadoras' not in a_tag.text:
                familias.append((a_tag.text.strip(), 'https://es.wikipedia.org' + a_tag['href']))
    return familias

def extraer_miembros_familia(sopa):
    """Extrae los nombres de los miembros de una familia desde la sopa de la subcategoría."""
    miembros = set()
    for ul in sopa.find_all('div', class_='mw-category-group'):
        for li in ul.find_all('li'):
            a_tag = li.find('a')
            if a_tag:
                miembros.add((a_tag.text.strip(), 'https://es.wikipedia.org' + a_tag['href']))
    return miembros

def extraer_info_persona(url):
    """Extrae la información detallada de una persona desde su página de Wikipedia."""
    sopa = obtener_sopa(url)
    if not sopa:
        return None

    info = {
        "Nombre": "",
        "Fecha de nacimiento": "",
        "Residencia": "",
        "Nacionalidad": "",
        "Familiares": {},
        "Cargos": "",
        "Educación": "",
        "Empleador": "",
        "Área": "",
        "Medios": "",
        "Movimientos": "",
    }

    infobox = sopa.find("table", class_="infobox biography vcard")
    if infobox:
        rows = infobox.find_all("tr")
        for row in rows:
            header = row.find("th")
            data = row.find("td")
            if header and data:
                key = header.text.strip()
                value = data.get_text(" ", strip=True)
                if "Nombre" in key:
                    info["Nombre"] = value
                elif "Nacimiento" in key:
                    info["Fecha de nacimiento"] = value
                elif "Residencia" in key:
                    info["Residencia"] = value
                elif "Nacionalidad" in key:
                    info["Nacionalidad"] = value
                elif "Ocupación" in key:
                    info["Cargos"] = value
                elif "Educado en" in key:
                    info["Educación"] = value
                elif "Empleador" in key:
                    info["Empleador"] = value
                elif "Área" in key:
                    info["Área"] = value
                elif "Miembro de" in key:
                    info["Medios"] = value
                elif "Movimientos" in key:
                    info["Movimientos"] = value
                elif "Familiares" in key:
                    familiares = {}
                    count = 1
                    for relative in data.find_all("a"):
                        if "href" in relative.attrs:
                            familiares[relative.text.strip()] = f"[{count}] {relative['href']}"
                            count += 1
                    info["Familiares"] = familiares
    return info

def guardar_en_csv(familia, persona, info):
    """Guarda la información detallada de una persona en el CSV inmediatamente."""
    with open("familias_chilenas.csv", mode="a", newline="", encoding="utf-8") as archivo:
        escritor_csv = csv.writer(archivo)
        escritor_csv.writerow([familia, persona, info["Nombre"], info["Fecha de nacimiento"], info["Residencia"], info["Nacionalidad"],
                                info["Cargos"], info["Educación"], info["Empleador"], info["Área"], info["Medios"], info["Movimientos"],
                                info["Familiares"]])

def main():
    url_base = 'https://es.wikipedia.org'
    url_categorias_familias = f'{url_base}/wiki/Categor%C3%ADa:Familias_de_Chile'

    # Crear CSV y escribir encabezado
    with open("familias_chilenas.csv", mode="w", newline="", encoding="utf-8") as archivo:
        escritor_csv = csv.writer(archivo)
        escritor_csv.writerow(["Familia", "Miembro", "Nombre Completo", "Fecha de nacimiento", "Residencia", "Nacionalidad", "Cargos", "Educación", "Empleador", "Área", "Medios", "Movimientos", "Familiares"])

    # Obtener la sopa de la página principal
    sopa_principal = obtener_sopa(url_categorias_familias)
    if not sopa_principal:
        return

    # Extraer las familias
    familias = extraer_familias(sopa_principal)
    if not familias:
        print("No se encontraron familias.")
        return

    # Iterar sobre cada familia y extraer miembros
    for nombre_familia, url_familia in familias:
        print(f"Procesando {nombre_familia}...")
        sopa_familia = obtener_sopa(url_familia)
        if not sopa_familia:
            continue

        miembros = extraer_miembros_familia(sopa_familia)
        if not miembros:
            print(f"No se encontraron miembros para la {nombre_familia}.")
            continue

        for miembro, url_miembro in miembros:
            print(f"Extrayendo información de {miembro}...")
            info = extraer_info_persona(url_miembro)
            if info:
                guardar_en_csv(nombre_familia, miembro, info)

        time.sleep(1)

    print("Extracción completa. Datos guardados en 'familias_chilenas.csv'.")

if __name__ == '__main__':
    main()