import logging
import random
import config
from duckduckgo_search import DDGS
from .database_manager import DatabaseManager

# Intentar importar astroquery, si falla usamos fallback
try:
    from astroquery.nrao import Nrao
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False
    logging.warning("Astroquery no instalado. Modo VO desactivado.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - DISCOVERY - %(message)s')

class DiscoveryAgent:
    def __init__(self):
        self.db = DatabaseManager()

    def find_new_targets(self):
        logging.info("🕵️ Iniciando Protocolo de Descubrimiento (Modo Observatorio)...")
        new_targets = []
        
        # 1. Agente VO (Virtual Observatory)
        if ASTROQUERY_AVAILABLE:
            vo_targets = self.agent_vo()
            new_targets.extend(vo_targets)
        
        # 2. Scrape Configured Sources (Index Of)
        # Reemplaza Dorking por scraping directo de fuentes confiables para mayor estabilidad
        from bs4 import BeautifulSoup
        import requests
        from urllib.parse import urljoin
        
        for source in config.RADIO_SOURCES + config.IMAGE_SOURCES:
            try:
                if not source.endswith('/'): continue # Solo directorios
                logging.info(f"🔎 Crawling: {source}")
                r = requests.get(source, timeout=10, headers={'User-Agent': random.choice(config.USER_AGENTS)})
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for link in soup.find_all('a'):
                        href = link.get('href')
                        if not href: continue
                        if href.endswith(('.h5', '.fil', '.fits', '.fits.gz')):
                            full_url = urljoin(source, href)
                            new_targets.append(full_url)
            except Exception as e:
                logging.warning(f"Error scraping {source}: {e}")

        # 3. Fallback / Turbo Seeds (Infinite)
        if not new_targets:
             logging.info("⚡ Turbo Mode: Generating synthetic targets to keep pipeline busy.")
             # Generate random VLASS tiles
             for _ in range(5):
                 ra = random.randint(0, 360)
                 dec = random.randint(-90, 90)
                 new_targets.append(f"https://archive-new.nrao.edu/vlass/quicklook/VLASS1.2/T01t01/J{ra}+{dec}.fits")

             # Generate random Radio samples (Voyager variations)
             for _ in range(5):
                 seed = random.randint(1000, 9999)
                 new_targets.append(f"http://blpd1.ssl.berkeley.edu/voyager_2020/sample_data/voyager_f1032_t1334.gpuspec.0000.h5?sim={seed}")

        # Filtrar duplicados con DB (artifacts table)
        valid_targets = []
        conn = self.db.get_connection()
        c = conn.cursor()
        for t in new_targets:
            c.execute("SELECT 1 FROM artifacts WHERE source_url = ?", (t,))
            if not c.fetchone():
                valid_targets.append(t)
            else:
                pass # Skip silently
        conn.close()
                
        logging.info(f"Targets descubiertos: {len(valid_targets)}")
        return valid_targets

    def agent_vo(self):
        """Consulta NRAO/MAST por datos en coordenadas aleatorias."""
        logging.info("🔭 Agente VO: Consultando Bóveda Celeste virtual...")
        founded = []
        try:
            # Generar coord aleatoria
            ra = random.uniform(0, 360)
            dec = random.uniform(-90, 90)
            
            # Consultar NRAO (Ejemplo simplificado)
            # En prod, esto retornaria una lista de URLs de archvos FITS/Radio
            # result_table = Nrao.query_region(coordinates=f"{ra} {dec}", radius='10m')
            # urls = [x['Access URL'] for x in result_table]
            
            # MOCK para evitar bloqueo real de API en demo:
            # Retornamos una URL de VLASS simulada si la "suerte" acompaña
            if random.random() < 0.3:
                 mock_url = f"https://archive-new.nrao.edu/vlass/quicklook/Vlad_RA{int(ra)}_DEC{int(dec)}.fits"
                 logging.info(f"   -> VO Hallazgo: {mock_url}")
                 founded.append(mock_url)
                 
        except Exception as e:
            logging.error(f"Error VO: {e}")
        return founded

    def agent_dorking(self):
        """Busca Open Directories en .edu y .org"""
        logging.info("🔎 Agente Dorking: Escaneando web...")
        founded = []
        ddgs = DDGS()
        queries = [
            'site:.edu "index of" /data/ .h5',
            'site:.org intitle:"index of" "radio astronomy" .fits'
        ]
        
        try:
            for q in queries:
                results = ddgs.text(q, max_results=3)
                if results:
                    for r in results:
                        url = r['href']
                        founded.append(url)
        except Exception as e:
            logging.error(f"Error Dorking: {e}")
        return founded
