from .base import DataSource, Target

class BreakthroughListen(DataSource):
    @property
    def name(self):
        return "BREAKTHROUGH_LISTEN_OPEN"

    @property
    def kind(self):
        return "RADIO"

    def discover(self):
        # Mocking access to BL Open Data (e.g., GBT or Parkes data)
        # Using a placeholder URL that the Harvester knows how to simulate/mock-download for now
        # OR real small samples if available.
        
        targets = []
        
        # Simulated "Technosignature Candidate" signal
        targets.append(Target(
            url="http://bl-open-data.berkeley.edu/sample/voyager_f1093.fil", # Mock/Real
            kind="RADIO",
            object_name="VOYAGER-1_TEST",
            dataset="BL_GBT",
            metadata={"f_center": 8419.29, "bandwidth": 1.0}
        ))
        
        return targets
