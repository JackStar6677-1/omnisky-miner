from .base import DataSource, Target
import random

class VLASSQuicklook(DataSource):
    @property
    def name(self):
        return "VLASS_QUICKLOOK"

    @property
    def kind(self):
        return "IMAGE"

    def discover(self):
        # In a real scenario, this would scrape the NRAO archive or Query VO.
        # For this version, we use known seed URLs + some "discovered" variations
        
        base_urls = [
            "https://archive-new.nrao.edu/vlass/quicklook/VLASS1.2/T01t01/J000000+000000/J000000+000000.10.2048.v1.I.iter1.image.pbcor.tt0.subim.fits",
            "https://archive-new.nrao.edu/vlass/quicklook/VLASS1.2/T01t02/J000412+000631/J000412+000631.10.2048.v1.I.iter1.image.pbcor.tt0.subim.fits"
        ]
        
        targets = []
        for url in base_urls:
            # We add a random query param to simulate "new" discovery if needed for testing, 
            # or just return base. The pipeline dedupe handles the rest.
            
            # Simulated Discovery Logic
            targets.append(Target(
                url=url,
                kind="IMAGE",
                object_name=url.split('/')[-2],
                dataset="VLASS1.2",
                metadata={"telescope": "VLA", "epoch": "1.2"}
            ))
            
        return targets
