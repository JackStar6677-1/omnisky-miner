import logging
import random
import config
import importlib
import inspect
from modules.sources.base import DataSource
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
        self.plugins = []
        self._load_plugins()

    def _load_plugins(self):
        """Dynamic loading of enabled source plugins"""
        self.plugins = []
        for source_name in config.ENABLED_SOURCES:
            try:
                mod_path = f"modules.sources.{source_name}"
                mod = importlib.import_module(mod_path)
                
                # Find the DataSource subclass
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if inspect.isclass(attr) and issubclass(attr, DataSource) and attr is not DataSource:
                        self.plugins.append(attr())
                        logging.info(f"🔌 Plugin Loaded: {attr_name} ({source_name})")
                        break
            except Exception as e:
                logging.error(f"❌ Failed to load plugin {source_name}: {e}")

    def find_new_targets(self):
        logging.info("🕵️ Initiating Discovery Protocol (Plugin System Active)")
        new_targets_objs = []
        
        # 1. Execute Plugins
        for plugin in self.plugins:
            try:
                targets = plugin.discover()
                if targets:
                    logging.info(f"   -> {plugin.name} found {len(targets)} candidates")
                    new_targets_objs.extend(targets)
            except Exception as e:
                logging.error(f"Plugin {plugin.name} crashed: {e}")

        # 2. Extract URLs for DB Check
        # Convert Target objects to list of URLs for compatibility with pipeline/dedupe
        candidate_urls = [t.url for t in new_targets_objs]

        # 3. DB Deduplication
        valid_targets = []
        conn = self.db.get_connection()
        c = conn.cursor()
        
        for t_obj in new_targets_objs:
            # Check ID/URL
            c.execute("SELECT 1 FROM artifacts WHERE source_url = ?", (t_obj.url,))
            if not c.fetchone():
                valid_targets.append(t_obj.url)
                # Ideally we pass the full Target object to pipeline, 
                # but legacy pipeline expects simple URLs list logic currently.
                # TODO: Upgrade pipeline to accept Objects or store metadata now?
                # For now, keep interface: return list of URLs. 
                # (Harvesters will re-parse or we rely on them downloading)
            else:
                pass # Already known
        
        conn.close()
                
        logging.info(f"✨ New Valid Targets: {len(valid_targets)}")
        return valid_targets

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
