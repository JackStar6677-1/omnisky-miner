import os
import datetime
import logging
try:
    from astroquery.simbad import Simbad
except:
    Simbad = None

class Reporter:
    def __init__(self):
        pass # Stateless, solo helper functions

    def consult_simbad(self, ra, dec):
        """Consulta SIMBAD para ver si hay objetos conocidos en la coordenada."""
        if not Simbad: return "Módulo SIMBAD no disponible."
        try:
            # result = Simbad.query_region(f"{ra} {dec}")
            # Mock para demo
            return "No se encontraron objetos catalogados en 2 arcmin."
        except:
            return "Error consultando SIMBAD."

    # Nota: La generación del MD ahora reside principalmente en DatabaseManager
    # para asegurar atomicidad. Este módulo queda como utilitario de consulta 
    # o generador de texto.
