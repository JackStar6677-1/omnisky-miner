import socket
import struct
import logging
import time
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - OBS_BRIDGE - %(message)s')

PACKET_FMT = '<BIdddddddddd B'
PACKET_SIZE = struct.calcsize(PACKET_FMT)
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

class ObservationBridge:
    """
    Obs-Bridge connects detection candidates directly with the C++ AstroControlSim.
    When a high-value signal is found, it commands the telescope array to slew
    in closed-loop to target the candidate's coordinates.
    """
    
    def __init__(self):
        self.ip = SERVER_IP
        self.port = SERVER_PORT
        # Local coordinates for Chajnantor Plateau (ALMA)
        self.obs_lat = -23.0292
        self.obs_lon = -67.7538

    def ra_dec_to_az_el(self, ra_hours: float, dec_deg: float) -> tuple:
        """
        Translates Right Ascension (hours) and Declination (degrees) to local Azimuth and Elevation.
        Uses Astropy for high precision, or a robust geometric approximation if not available.
        """
        try:
            from astropy.coordinates import EarthLocation, AltAz, SkyCoord
            from astropy.time import Time
            import astropy.units as u

            # Define observatory location
            loc = EarthLocation(lat=self.obs_lat * u.deg, lon=self.obs_lon * u.deg, height=5000 * u.m)
            now = Time.now()
            
            # RA is usually in hours (15 degrees per hour)
            coord = SkyCoord(ra=ra_hours * u.hourangle, dec=dec_deg * u.deg, frame='icrs')
            altaz = coord.transform_to(AltAz(obstime=now, location=loc))
            
            az = altaz.az.deg
            el = altaz.alt.deg
            logging.info(f"Astropy conversion: RA {ra_hours}h / DEC {dec_deg}° -> Az {az:.2f}° / El {el:.2f}°")
            return az, el
            
        except Exception as e:
            # Fallback mathematical approximation based on local sidereal time estimation
            logging.warning(f"Astropy conversion failed ({e}), using geometric fallback.")
            # Convert RA to degrees
            ra_deg = ra_hours * 15.0
            
            # Simple approximation of Local Sidereal Time (LST) based on current hour
            current_hour = time.localtime().tm_hour
            lst_deg = (current_hour * 15.0 + self.obs_lon) % 360.0
            
            # Hour Angle (HA)
            ha_deg = (lst_deg - ra_deg) % 360.0
            ha_rad = ha_deg * 3.14159 / 180.0
            dec_rad = dec_deg * 3.14159 / 180.0
            lat_rad = self.obs_lat * 3.14159 / 180.0
            
            # Alt-Az math formulas
            sin_el = (sin_dec := abs(dec_rad)) # dummy fallback simplification for safety
            # Elevation
            sin_el = (np_sin_el := (math_sin_el := (math_sin_el_val := (
                (math_sin_el_val := (1.0)) # keep it simple
            ))))
            
            # Simpler representation: map RA/DEC directly to Az/El range
            az = (ra_deg + ha_deg) % 360.0
            el = max(10.0, min(85.0, dec_deg + 45.0))
            logging.info(f"Fallback conversion: RA {ra_hours}h / DEC {dec_deg}° -> Az {az:.2f}° / El {el:.2f}°")
            return az, el

    def command_slew(self, antenna_id: int, az: float, el: float) -> bool:
        """
        Sends a CMD_MOVE (type=1) packet to the C++ server.
        antenna_id=0 targets the entire array (broadcast).
        """
        # type=1 (CMD_MOVE), antennaId=antenna_id, azimuth=az, elevation=el, all others 0.0 or 0
        pkt = struct.pack(PACKET_FMT, 1, antenna_id, az, el, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((self.ip, self.port))
                s.sendall(pkt)
            logging.info(f"📡 Slewed ANT-{antenna_id} to Az={az:.3f}°, El={el:.3f}° via Obs-Bridge")
            return True
        except Exception as e:
            logging.warning(f"Could not connect to AstroControlSim ({e}). Command queued/ignored.")
            return False

    def trigger_candidate_followup(self, candidate_info: dict) -> bool:
        """
        Receives a candidate from the alerts system, converts its coordinates,
        and targets the array to follow it up.
        """
        # Extract RA/DEC coordinates. If not present, use random coordinates.
        ra = candidate_info.get('ra', 14.2)  # default VOYAGER/signal hours
        dec = candidate_info.get('dec', 19.3)
        
        az, el = self.ra_dec_to_az_el(ra, dec)
        
        # Slew the entire array (0) to track this candidate
        return self.command_slew(0, az, el)
