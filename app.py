import requests
from bs4 import BeautifulSoup

def get_togo_results():
    # Exemple pour loterie-togo.com
    url = "https://www.loterie-togo.com"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Tu cherches les balises qui contiennent "5 Premiers numéros"
        # et tu extrais "33 - 49 - 21 - 46 - 86"
        return soup.text[:500] # à affiner
    except:
        return None

def get_lonaci_results():
    url = "https://pmu-pmub.com/resultats-lonaci/"
    # Même logique, tu cherches "ARRIVEE DU"
    pass
