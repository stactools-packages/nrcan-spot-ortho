from ftplib import FTP
from time import sleep


class GeobaseSpotFTP:
    """
    Get a listing of files from Geobase FTP
    geobase = GeobaseSpotFTP()
    files = geobase.list_contents('s5_14121_6904_20080820')
    """
    def __init__(self):
        self.spot_location = "/pub/nrcan_rncan/image/spot/geobase_orthoimages"
        self.ftp_site = "ftp.geogratis.gc.ca"

        num_retries = 10
        for i in range(num_retries):
            print(f"Connecting to Geobase FTP, attempt {i+1}/{num_retries}")
            try:
                self.ftp = FTP(self.ftp_site, timeout=30)
                self.ftp.login()
                err = False
                break
            except Exception:
                err = True
                sleep(10)
        if err:
            raise Exception("Couldn't connect to Geobase FTP")

    def list_contents(self, spot_id=""):
        """
        Get a listing of the children in a given path
        returns a list of absolute file paths
        """
        files = []
        for f in self.ftp.nlst(f"{self.spot_location}{spot_id.lower()}"):
            files.append(f"{self.ftp_site}{self.ftp_site}/{f}")
        return files

    def get_thumbnail(self, spot_id=""):
        """
        Get the thumbnail image associated with the SPOT data
        """
        return f"{self.ftp_site}{self.spot_location}/images/{spot_id.lower()}_tn.jpg"
