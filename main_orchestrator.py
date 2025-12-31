import concurrent.futures
import time
import logging
import random
import config
from modules.heavy_harvester import HeavyHarvester
from modules.image_harvester import ImageHarvester
from modules.discovery import DiscoveryAgent
from modules.pipeline import PipelineManager
from modules.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - ORCHESTRATOR - %(message)s')

def main():
    # 1. Init System
    logging.info("=== OMNISKY MINER: ROBUST PIPELINE ACTIVATED ===")
    
    # Init DB
    db = DatabaseManager()
    
    # Init Modules
    heavy = HeavyHarvester()
    image = ImageHarvester()
    discovery = DiscoveryAgent()
    
    # Init Pipeline
    pipeline = PipelineManager(heavy, image)
    pipeline.start()
    
    # 2. Main Feeding Loop
    # Discovery Feeds the Pipeline
    while True:
        try:
            # 1. Ask Discovery (Scraping & VO)
            logging.info("📡 Scanning for new targets...")
            new_targets = discovery.find_new_targets()
            
            # 2. Add to Pipeline
            count = 0
            for url in new_targets:
                 # Infer type from extension or discovery source?
                 # For simplicity, assume .fits = IMAGE, else RADIO
                 job_type = "IMAGE" if ".fits" in url.lower() else "RADIO"
                 
                 if pipeline.submit_job(url, job_type):
                     count += 1
            
            logging.info(f"Orchestrator fed {count} jobs to pipeline.")
            
            # Smart Sleep based on activity
            if count == 0:
                logging.info("Lower activity. Sleeping 5s...")
                time.sleep(5)
            else:
                time.sleep(1) # Fast cycle
                
        except Exception as e:
            logging.error(f"Orchestrator Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
