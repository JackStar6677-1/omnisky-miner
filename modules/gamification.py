import sqlite3
import config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - GAMIFICATION - %(message)s')

class GamificationManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        self.init_table()

    def init_table(self):
        """Crea tabla de estadísticas si no existe."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS usuario_stats (
                    id INTEGER PRIMARY KEY,
                    mb_procesados REAL DEFAULT 0,
                    hallazgos_total INTEGER DEFAULT 0,
                    xp_total REAL DEFAULT 0
                )
            ''')
            # Inicializar fila 1 si está vacía
            c.execute('SELECT COUNT(*) FROM usuario_stats')
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO usuario_stats (id, mb_procesados, hallazgos_total, xp_total) VALUES (1, 0, 0, 0)')
            conn.commit()

    def add_xp(self, mb=0, findings=0):
        """
        Suma XP basada en actividad.
        - 1 MB = 1 XP
        - 1 Hallazgo = 500 XP
        """
        xp_gain = (mb * 1) + (findings * 500)
        
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE usuario_stats 
                SET mb_procesados = mb_procesados + ?,
                    hallazgos_total = hallazgos_total + ?,
                    xp_total = xp_total + ?
                WHERE id = 1
            ''', (mb, findings, xp_gain))
            conn.commit()
            
        if findings > 0:
            logging.info(f"🏆 ¡Hallazgo Épico! +{xp_gain} XP")

    def get_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT mb_procesados, hallazgos_total, xp_total FROM usuario_stats WHERE id = 1')
            row = c.fetchone()
            if row:
                mb, count, xp = row
                rank, progress = self._calculate_rank(xp)
                return {
                    'mb': mb,
                    'count': count,
                    'xp': xp,
                    'rank': rank,
                    'progress': progress
                }
            return None

    def _calculate_rank(self, xp):
        """Retorna (Nombre Rango, Progreso %)"""
        ranks = [
            (0, "Observador Novato"),
            (1000, "Cadete Estelar"),
            (5000, "Operador de Radio"),
            (15000, "Cazador de Señales"),
            (50000, "Guardián de la Galaxia"),
            (100000, "Señor del Tiempo")
        ]
        
        current_rank = ranks[0][1]
        next_xp = 1000
        
        for threshold, name in ranks:
            if xp >= threshold:
                current_rank = name
            else:
                next_xp = threshold
                break
                
        # Calcular progreso al siguiente nivel
        # Simplificación: % respecto al cap del nivel actual no, sino absoluto al siguiente hito
        # Si xp=500, next=1000, prog=50%
        
        if xp >= ranks[-1][0]:
            return current_rank, 100.0
            
        progress = min(100, (xp / next_xp) * 100)
        return current_rank, progress
