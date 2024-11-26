from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

def get_anid_urls():
    """Obtiene las URLs de los concursos y las compara con el CSV existente."""
    # Configurar Chrome para modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    new_urls = []
    existing_urls = set()
    
    try:
        # Cargar URLs existentes si el archivo existe
        if os.path.exists('ANID_concursos.csv'):
            existing_df = pd.read_csv('ANID_concursos.csv')
            existing_urls = set(existing_df['URL'].tolist())
            print(f"CSV existente encontrado con {len(existing_urls)} URLs")
        
        driver.get("https://anid.cl/concursos/")
        time.sleep(2)
        
        while True:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jet-listing-grid__items"))
            )
            time.sleep(2)
            
            links = driver.find_elements(
                By.CSS_SELECTOR, 
                'a.elementor-button.elementor-button-link.elementor-size-sm'
            )
            
            found_existing = False
            for link in links:
                url = link.get_attribute('href')
                if url and not url.startswith('https://anid.cl/concursos/jsf/'):
                    if url in existing_urls:
                        found_existing = True
                        print(f"URL existente encontrada: {url}")
                        break
                    if url not in new_urls:
                        new_urls.append(url)
                        print(f"Nueva URL encontrada: {url}")
            
            if found_existing:
                print("Se encontró una URL existente, terminando búsqueda")
                break
                
            try:
                pagination = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jet-filters-pagination"))
                )
                
                next_button = pagination.find_element(
                    By.CSS_SELECTOR,
                    'div.jet-filters-pagination__item.prev-next.next'
                )
                
                if next_button.is_displayed():
                    next_button.click()
                    time.sleep(2)
                else:
                    print("No hay más páginas disponibles")
                    break
                    
            except Exception as e:
                print("Fin de la navegación")
                break
                
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()
    
    return new_urls, existing_urls

def get_concurso_details(url):
    """Extrae la información detallada de un concurso usando requests y BeautifulSoup."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        details = {
            'URL': url,
            'FECHA_EXTRACCION': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Extraer información básica
        estado = soup.select_one('span.estado')
        details['ESTADO'] = estado.text.strip() if estado else ''
        
        # Extraer fechas
        for field, text in [('INICIO', 'Inicio:'), ('CIERRE', 'Cierre:'), ('FALLO', 'Fallo estimado:')]:
            element = soup.find('div', class_='jet-listing-dynamic-field__content', string=lambda s: text in str(s))
            if element:
                details[field] = element.text.split(text)[1].strip()
            else:
                details[field] = ''
        
        # Extraer tipo y nombre
        tipo = soup.select_one('p.elementor-heading-title.elementor-size-default')
        details['TIPO'] = tipo.text.strip() if tipo else ''
        
        nombre = soup.select_one('h1.elementor-heading-title.elementor-size-default')
        details['NOMBRE'] = nombre.text.strip() if nombre else ''
        
        # Extraer contenido de las pestañas
        tabs = {
            'PRESENTACIÓN': '1911',
            'PÚBLICO OBJETIVO': '1912',
            'BITÁCORA': '1913',
            'RESULTADOS': '1914',
            'DOCUMENTOS': '1915'
        }
        
        for tab_name, tab_id in tabs.items():
            content = soup.select_one(f'#jet-tabs-content-{tab_id}')
            if content:
                text = content.text.strip()
                if tab_name == 'PRESENTACIÓN':
                    # Eliminar la línea de consultas
                    text = text.split('Dirija sus consultas')[0].strip()
                details[tab_name] = text
            else:
                details[tab_name] = ''
        
        return details
        
    except Exception as e:
        print(f"Error procesando concurso {url}: {str(e)}")
        return None

def update_csv_with_new_urls(new_urls, existing_urls):
    """Actualiza el CSV con las nuevas URLs."""
    try:
        if os.path.exists('ANID_concursos.csv'):
            df = pd.read_csv('ANID_concursos.csv')
        else:
            df = pd.DataFrame(columns=['ID', 'URL'])
        
        # Agregar nuevas URLs al principio del DataFrame
        if new_urls:
            new_df = pd.DataFrame({
                'URL': new_urls
            })
            df = pd.concat([new_df, df], ignore_index=True)
            df['ID'] = range(1, len(df) + 1)  # Actualizar IDs
        
        df.to_csv('ANID_concursos.csv', index=False)
        print(f"CSV actualizado con {len(new_urls)} nuevas URLs")
        return df
    except Exception as e:
        print(f"Error actualizando CSV: {str(e)}")
        return None

def process_concursos():
    """Proceso principal."""
    print("Iniciando extracción de URLs de ANID...")
    new_urls, existing_urls = get_anid_urls()
    
    if new_urls or existing_urls:
        df = update_csv_with_new_urls(new_urls, existing_urls)
        if df is not None:
            print("\nIniciando extracción de información detallada...")
            concursos_info = []
            
            for index, row in df.iterrows():
                print(f"\nProcesando concurso {index + 1}/{len(df)}")
                details = get_concurso_details(row['URL'])
                if details:
                    details['ID'] = row['ID']
                    concursos_info.append(details)
                    print("✓ Información extraída exitosamente")
                else:
                    print("✗ Error al extraer información")
            
            if concursos_info:
                # Crear DataFrame con toda la información
                new_df = pd.DataFrame(concursos_info)
                columns = ['ID', 'URL', 'ESTADO', 'NOMBRE', 'TIPO', 'INICIO', 'CIERRE', 'FALLO',
                          'PRESENTACIÓN', 'PÚBLICO OBJETIVO', 'BITÁCORA', 'RESULTADOS', 'DOCUMENTOS',
                          'FECHA_EXTRACCION']
                new_df = new_df[columns]
                new_df.to_csv('ANID_concursos_detallado.csv', index=False)
                print(f"\nSe guardaron {len(new_df)} concursos con información detallada")
            else:
                print("\nNo se pudo extraer información detallada")
    else:
        print("No se encontraron nuevas URLs para procesar")

if __name__ == "__main__":
    process_concursos()
