import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.message import EmailMessage
import re
import os
from dotenv import load_dotenv
load_dotenv()

# https://www.fac-habitat.com/fr/residences-etudiantes/id-56-mis-pour-etudiants done
# done "https://www.fac-habitat.com/fr/residences-etudiantes/id-53-val-de-bievre",https://www.fac-habitat.com/fr/residences-etudiantes/id-80-residence-etudiante-erwin-guldner-sceaux"
# https://www.fac-habitat.com/fr/residences-etudiantes/id-99-compas check whdk
# https://www.fac-habitat.com/fr/residences-etudiantes/id-116-hortense-wild ostoriya g
# "https://www.fac-habitat.com/fr/residences-etudiantes/id-27-les-trois-arpents"
# https://www.fac-habitat.com/fr/residences-etudiantes/id-82-residence-etudiante-pierre-ringenbach-sceaux 1h15
# "https://www.fac-habitat.com/fr/residences-etudiantes/id-48-l-arche" ghalya

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL") 

fac=["https://www.fac-habitat.com/fr/residences-etudiantes/id-116-hortense-wild",
     "https://www.fac-habitat.com/fr/residences-etudiantes/id-27-les-trois-arpents",
    #  "https://www.fac-habitat.com/fr/residences-etudiantes/id-46-belle-isle",
     "https://www.fac-habitat.com/fr/residences-etudiantes/id-26-pablo-picasso",
    #  "https://www.fac-habitat.com/fr/residences-etudiantes/id-85-residence-etudiante-emergence-bois-colombes",
    #  "https://www.fac-habitat.com/fr/residences-etudiantes/id-23-simone-de-beauvoir",
     "https://www.fac-habitat.com/fr/residences-etudiantes/id-81-residence-etudiante-julie-victoire-daubie-malakoff",
     "https://www.fac-habitat.com/fr/residences-etudiantes/id-91-ecrivains",
    #  "https://www.fac-habitat.com/fr/residences-etudiantes/id-80-residence-etudiante-erwin-guldner-sceaux",
    #  "https://www.fac-habitat.com/fr/residences-etudiantes/id-39-claude-monet",
    #  "https://www.fac-habitat.com/fr/residences-etudiantes/id-82-residence-etudiante-pierre-ringenbach-sceaux"
     ]

studefi=[
	"https://www.studefi.fr/main.php?srv=Residence&op=show&cdGroupe=798G"
]

crous="https://trouverunlogement.lescrous.fr/tools/37/search?bounds=1.4462445_49.241431_3.5592208_48.1201456"

free_fachabitat_not_available = []
free_fachabitat_available = []
free_studefi = []
free_crous = []

def send_email(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def check_studefi_disponibility():
    for url in studefi:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for keywords indicating availability
            if "je réserve" in soup.text.lower():
                if url not in free_studefi:
                    free_studefi.append(url)
                    send_email(
                        subject="STUDEFI Availability Detected!",
                        body=f"There is an available spot at: {url}"
                    )
            
        except requests.RequestException as e:
            print(f"Error accessing {url}: {e}")

def check_fachabitat_universities():
    for url in fac:
        response = requests.get(url, timeout=10)
        iframe=response.text.split('iframe class="reservation" width="100%" height="150" src="')[1].split('"')[0]
        if "Disponibilit&eacute; imm&eacute;diate" in requests.get(iframe).text:
            if url not in free_fachabitat_available:
                free_fachabitat_available.append(url)
                send_email(
                    subject="Instant Availability Detected at FAC-HABITAT!",
                    body=f"There is an available spot at: {url}"
                )
        elif "D&eacute;poser une demande" in requests.get(iframe).text:
                if url not in free_fachabitat_not_available:
                    free_fachabitat_not_available.append(url)
                    send_email(
                        subject="Availability Detected at FAC-HABITAT!",
                        body=f"There is an available spot at: {url}"
                    )
        else:
            if url in free_fachabitat_available:
                free_fachabitat_available.remove(url)
            if url in free_fachabitat_not_available:
                free_fachabitat_not_available.remove(url)

def check_crous_disponibility():
    try:
        response = requests.get(crous, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        cards = soup.find_all("div", class_="fr-card__content")

        free_crous[:] = [entry for entry in free_crous if entry in [card.find("a", href=True)["href"] for card in cards]]

        for card in cards:
            desc_tag = card.find("p", class_="fr-card__desc")
            if desc_tag and re.search(r'(78|75|92)\d{3}', desc_tag.text):
                link_tag = card.find("a", href=True)
                if link_tag and link_tag["href"] not in [entry for entry in free_crous]:
                    free_crous.append(link_tag["href"])
                    send_email(
                        subject="Crous Availability Detected!",
                        body=f"New Crous availability detected:\n\nTitle: {card.find('h3', class_='fr-card__title').text.strip()}\nDescription: {desc_tag.text.strip()}\nLink: https://trouverunlogement.lescrous.fr{link_tag['href']}"
                    )
    except requests.RequestException as e:
        print(f"Error fetching Crous data: {e}")

    return free_crous


# crous="https://trouverunlogement.lescrous.fr/tools/36/search?maxPrice=600&occupationModes=alone&bounds=2.224122_48.902156_2.4697602_48.8155755"
# if "Aucun logement trouv" not in requests.get(crous).text and "Serveur	 satur" not in requests.get(crous).text:
# 	print(crous)

def main():
    while True:
        check_studefi_disponibility()
        check_fachabitat_universities()
        check_crous_disponibility()
        
        time.sleep(3 * 60)  # Wait for 5 minutes

if __name__ == "__main__":
    main()