#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ANID Scraper

Este script extrae información detallada de los concursos publicados en el sitio web de ANID
(Agencia Nacional de Investigación y Desarrollo de Chile).

Funcionalidades:
- Extrae URLs de concursos desde https://anid.cl/concursos/
- Compara con concursos ya registrados para obtener solo los nuevos
- Extrae información detallada de cada concurso
- Guarda la información en formato CSV

Author: mlorca
Date: 2023
"""

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
import random

def get_user_agent():
    """
    Retorna un User-Agent aleatorio para simular diferentes navegadores.
    
    Returns:
        str: User-Agent aleatorio seleccionado de una lista predefinida
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    ]
    return random.choice(user_agents)

def get_anid_urls():
    """
    Obtiene las URLs de los concursos y las compara con el CSV existente.
    
    Returns:
        tuple: (new_urls, existing_urls)
            - new_urls (list): Lista de nuevas URLs encontradas
            - existing_urls (set): Conjunto de URLs existentes en el CSV
    """
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
    """
    Extrae la información detallada de un concurso usando requests y BeautifulSoup.
    Si falla, utiliza Selenium como método de respaldo.
    
    Args:
        url (str): URL del concurso a procesar
        
    Returns:
        dict: Diccionario con la información detallada del concurso o None si hay error
    """
    headers = {
        'User-Agent': get_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers'
    }
    
    try:
        # Agregar un pequeño retraso aleatorio para evitar ser bloqueado
        time.sleep(random.uniform(1, 3))
        
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=10)
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
        
    except requests.exceptions.RequestException as e:
        print(f"Error procesando concurso {url}: {str(e)}")
        # Si falla con requests, intentar con Selenium como respaldo
        return get_concurso_details_selenium(url)
    except Exception as e:
        print(f"Error inesperado procesando concurso {url}: {str(e)}")
        return None

def get_concurso_details_selenium(url):
    """
    Método de respaldo que usa Selenium para extraer información cuando requests falla.
    
    Args:
        url (str): URL del concurso a procesar
        
    Returns:
        dict: Diccionario con la información detallada del concurso o None si hay error
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'user-agent={get_user_agent()}')
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        time.sleep(2)
        
        details = {
            'URL': url,
            'FECHA_EXTRACCION': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Extraer información básica
        try:
            estado = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.estado"))
            )
            details['ESTADO'] = estado.text.strip()
        except:
            details['ESTADO'] = ''
        
        # Extraer fechas
        for field, text in [('INICIO', 'Inicio:'), ('CIERRE', 'Cierre:'), ('FALLO', 'Fallo estimado:')]:
            try:
                element = driver.find_element(By.XPATH, 
                    f"//div[contains(@class, 'jet-listing-dynamic-field__content') and contains(., '{text}')]")
                details[field] = element.text.split(text)[1].strip()
            except:
                details[field] = ''
        
        # Extraer tipo y nombre
        try:
            tipo = driver.find_element(By.CSS_SELECTOR, "p.elementor-heading-title.elementor-size-default")
            details['TIPO'] = tipo.text.strip()
        except:
            details['TIPO'] = ''
        
        try:
            nombre = driver.find_element(By.CSS_SELECTOR, "h1.elementor-heading-title.elementor-size-default")
            details['NOMBRE'] = nombre.text.strip()
        except:
            details['NOMBRE'] = ''
        
        # Extraer contenido de las pestañas
        tabs = {
            'PRESENTACIÓN': '1911',
            'PÚBLICO OBJETIVO': '1912',
            'BITÁCORA': '1913',
            'RESULTADOS': '1914',
            'DOCUMENTOS': '1915'
        }
        
        for tab_name, tab_id in tabs.items():
            try:
                tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"#jet-tabs-control-{tab_id}"))
                )
                driver.execute_script("arguments[0].click();", tab)
                time.sleep(1)
                
                content = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f"#jet-tabs-content-{tab_id}"))
                )
                
                text = content.text.strip()
                if tab_name == 'PRESENTACIÓN':
                    text = text.split('Dirija sus consultas')[0].strip()
                details[tab_name] = text
            except:
                details[tab_name] = ''
        
        return details
    except Exception as e:
        print(f"Error en método Selenium para {url}: {str(e)}")
        return None
    finally:
        driver.quit()

def update_csv_with_new_urls(new_urls, existing_urls):
    """
    Actualiza el CSV con las nuevas URLs encontradas.
    
    Args:
        new_urls (list): Lista de nuevas URLs a agregar
        existing_urls (set): Conjunto de URLs ya existentes
        
    Returns:
        pandas.DataFrame: DataFrame actualizado o None si hay error
    """
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
    """
    Proceso principal que coordina la extracción y actualización de información.
    
    Este proceso:
    1. Obtiene nuevas URLs de concursos
    2. Actualiza el CSV con las nuevas URLs
    3. Extrae información detallada de cada concurso
    4. Guarda toda la información en un nuevo CSV
    """
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
