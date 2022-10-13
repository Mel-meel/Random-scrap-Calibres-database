# Le but de ce script est de scrapper les informations concernants une liste d'url de calibres d'armes.
# Le but à long terme est la réalisation d'un logiciel libre et gratuit pouvant concurrencer GRT.
# Ce début d'un logiciel concurrent à GRT n'est pour l'heure qu'une idée. L'idée pourrait bien ne jamais aboutir en un projet viable.
# Licence : GNU GLP v3.0

# PS : Ce n'est pas l'arme qui est dangereuse, mais le crétin qui la tient.

import os
import requests
from bs4 import BeautifulSoup
from lxml import etree
import sqlite3
import time





def acces_base(nom) -> "Créé l'objet de connexion à la base de données" :
    """
    :name: acces_base
    :params: nom string
    :return: objet de connexion SQLite3
    :desc: Créé l'objet de connexion à la base de données et créé la table "caliber", si elle n'existe pas, que le programme viendra remplir.
    """
    conn = sqlite3.connect(nom)
    curseur = conn.cursor()
    curseur.execute('''
CREATE TABLE IF NOT EXISTS caliber (
    name VARCHAR(255) PRIMARY KEY, 
    description TEXT, 
    url VARCHAR(255) NOT NULL, 
    type VARCHAR(255) NOT NULL, 
    place_of_origin CHAR(3) NOT NULL, 
    designer VARCHAR(255) NOT NULL, 
    designed INTEGER NOT NULL, 
    produced INTEGER, 
    manufacturer VARCHAR(255) NOT NULL, 
    parent_case VARCHAR(255), 
    variants VARCHAR(255), 
    case_type VARCHAR(255), 
    bullet_diameter FLOAT NOT NULL DEFAULT 0.0, 
    neck_diameter FLOAT NOT NULL DEFAULT 0.0, 
    shoulder_diameter FLOAT NOT NULL DEFAULT 0.0, 
    base_diameter FLOAT NOT NULL DEFAULT 0.0, 
    rim_diameter FLOAT NOT NULL DEFAULT 0.0, 
    rim_thickness FLOAT NOT NULL DEFAULT 0.0, 
    case_length FLOAT NOT NULL DEFAULT 0.0, 
    overall_length FLOAT NOT NULL DEFAULT 0.0, 
    rifling_twist VARCHAR(10), 
    primer_type VARCHAR(255) NOT NULL,
    case_capacity FLOAT NOT NULL DEFAULT 0.0,
    maximum_pressure FLOAT NOT NULL DEFAULT 0.0,
    maximum_pressure_saami FLOAT NOT NULL DEFAULT 0.0,
    maximum_pressure_cip FLOAT NOT NULL DEFAULT 0.0,
    maximum_cup FLOAT NOT NULL DEFAULT 0.0
) ;
    ''')
    conn.commit()
    return conn


def acces_site(url) -> "Vérifie si l'url est accessible" :
    """
    :name: acces_site
    :params: url string
    :return: booléen
    :desc: blabla
    """
    
    res = False
    if requests.get(url, headers = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0'}).status_code == 200 :
        res = True
    return res


def lecture_liste_calibres(fichier) -> "Ouvre simplement un fichier" :
    """
    :name: lecture_liste_calibres
    :params: fichier string
    :return: liste
    :desc: Ouvre le fichier, renvoie son contenu sous forme de liste, un élément par ligne
    """
    
    with open(fichier) as f :
        lignes = [ligne.rstrip() for ligne in f]
    return lignes



def trouve_mm(chaine) -> "Trouve des données en mm dans une chaine de caractère" :
    """
    :name: trouve_mm
    :params: chaine string
    :return: float
    :desc: Les pages wikipédia étant toutes en anglais, les mesures par défaut sont en pouces. néanmoins, leur équivalent en milimètres est inscrit.
    Cette fonction ne récupère que la valeur en milimètres.
    """
    resultat_en_mm = 0.0
    
    if "mm" in chaine :
        chaine = chaine.replace("(", "")
        chaine = chaine.replace(")", "")
        chaine_en_liste = chaine.split(" ")
        resultat_en_mm = chaine_en_liste[chaine_en_liste.index("mm") - 1]
    
    return resultat_en_mm




def trouve_mpa(chaine) -> "Trouve des données en MPa dans une chaine de caractère" :
    """
    :name: trouve_mpa
    :params: chaine string
    :return: float
    :desc: Les pages wikipédia étant toutes en anglais, les mesures par défaut sont en psi. néanmoins, leur équivalent en MPa est inscrit.
    Cette fonction ne récupère que la valeur en MPa.
    """
    resultat_en_mpa = 0.0
    
    if "mm" in chaine :
        chaine = chaine.replace("(", "")
        chaine = chaine.replace(")", "")
        chaine_en_liste = chaine.split(" ")
        resultat_en_mpa = chaine_en_liste[chaine_en_liste.index("MPa") - 1]
    
    return resultat_en_mpa




def format_nom_caracteristiques(chaine) -> "Nettoie la chaine" :
    """
    :name: format_nom_caracteristiques
    :params: chaine string
    :return: string
    :desc: Nettoie la chaine en paramètre. retire les paranthèses, remplace les espaces par des underscores pour un meilleur traitement.
    """
    chaine = chaine.replace("(", "")
    chaine = chaine.replace(")", "")
    chaine = chaine.replace("\xa0", "_")
    chaine = chaine.replace(" ", "_")
    chaine = chaine.lower()
    
    return chaine

def format_valeur_caracteristiques(chaine) -> "Nettoie la chaine" :
    """
    :name: format_nom_caracteristiques
    :params: chaine string
    :return: string
    :desc: Nettoie la chaine en paramètre. retire les paranthèses, remplce les espaces par des underscores pour un meilleur traitement.
    """
    
    chaine = chaine.replace("\xa0", " ")
    
    return chaine


def scrap_page_calibre(url) -> "Scrape les informations du calibre" :
    calibre = {}
    
    """
    :name: scrap_page_calibre
    :params: url string
    :return: dict
    :desc: Coeur du programme. C'est ici que se déroule le scrapage (la scrapation?) de la page html.
    """
    
    # HTML de la page
    html = requests.get(url, headers = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0'}).content
    
    # Prépare la tambouille
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    
    # Capte la description du calibre en anglais (sera traduite ensuite par le logiciel mais pas dans la base de données)
    # La description est conservée telle qu'elle est, le logiciel comprendra un petit interpréteur HTML pour l'afficher
    description = soup.select_one("p").getText()
    
    # Rempli le dictionnaire de retour avec deux éléments de base : l'url et la descritpion
    calibre["url"] = url
    calibre["description"] = description
    
    # On souhaite récupérer la description et les informations techniques concernant le calibre
    # Les infos techniques sont dans 'table class="infobox"'
    # Pour la description, c'est moins simple, on verra plus tard si j'ai le temps, de toute façon, c'est même pas prévu dans la base de données
    table_infobox = soup.select("table[class='infobox'] tbody tr")
    
    # Parcours (le parcourationnage?) les informations techniques
    for ligne in table_infobox :
        th = ligne.findChild("th")
        if th != None :
            if type(th.get("class")) == list :
                # Le nom du calibre se trouve dans la ligne de classe "infobox-above"
                if "infobox-above" in th.get("class") :
                    clef = "name"
                    valeur = th.getText()
                    calibre[clef] = valeur
                # Toutes les autres infos sont dans des lignes de classe "infobox-label"
                elif "infobox-label" in th.get("class") :
                    clef = format_nom_caracteristiques(th.getText())
                    valeur = format_valeur_caracteristiques(ligne.findChild("td").getText())
                    # Si il s'agit d'une données numérique, on ne garde que sa valeur en mm, pas en pouces
                    if clef in ["bullet_diameter", "neck_diameter", "shoulder_diameter", "base_diameter", "rim_diameter", "rim_thickness", "case_length", "overall_length"] :
                        valeur = trouve_mm(valeur)
                    # Pareil pour les données concernant la pression mais cette faois on conserve (de haricot) les données en MPa
                    elif clef in ["maximum_pressure_saami", "maximum_pressure_cip"] :
                        valeur = trouve_mpa(valeur)
                    calibre[clef] = valeur
    
    return calibre
    


def enregistre_calibre(connexion, calibre) -> "Enregistre le calibre dans la base de données" :
    """
    :name: enregistre_calibre
    :params: connexion objet de connexion SQLite3, calibre dict
    :return: rien, même pas un None
    :desc: Enregistre le calibre dans la base de données
    """
    
    colones_requete = ""
    variables_requete = ""
    curseur = connexion.cursor()
    
    # Construction de la requête
    for clef in calibre :
        if colones_requete == "" :
            colones_requete = clef
            variables_requete = f":{clef}"
        else :
            colones_requete = f"{colones_requete}, {clef}"
            variables_requete = f"{variables_requete}, :{clef}"
    
    requete = f"INSERT INTO caliber ({colones_requete}) values ({variables_requete})"
    
    try :
        curseur.execute(requete, calibre)
        connexion.commit()
        print("OK")
    except :
        print("KO")



# Liste des calibres et de leurs pages wikipédia

if __name__ == "__main__" :
    
    connexion = acces_base("base_test.db")
    
    liste_liens = lecture_liste_calibres("liste_calibres_remington.txt")
    
    # Parcours les liens un à un
    for lien in liste_liens :
        print(lien)
        if acces_site(lien) :
            print("Page accessible")
            calibre = scrap_page_calibre(lien)
            enregistre_calibre(connexion, calibre)

# TODO : Seul la moitié des pages sont scrappés. Pour le moment, le problème n'est pas identifié mais il pourrait bien venir du fait que certaines
#        pages n'ont pas exactement le même schéma HTML que les autres.
#        Il conviendrait d'améliorer ce programme pour qu'il s'adapte à toutes les pages Wikipédia.
#        Dans un monde parfait, ce code serait fait en POO.
#        Et ça serait sypa de pouvoir passer le fichier txt d'url en paramètres. comme ça on changerait de liste sans devoir coder en dur.
#        Le temps que j'ai mis à commenté ce serait déjà fait...
