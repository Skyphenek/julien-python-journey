"""Numéros d'urgence et ambassade de France, pays par pays (mêmes pays que formalites.py).

Recopiés des pages « Contacts utiles » de France Diplomatie le 27/10/2026 (mises à jour du
15/09 au 23/10/2026). Règle : seulement ce que la page affiche ; un numéro mal formé sur la
page est omis (téléphone None) et la page officielle reste en lien. Une exception assumée :
le 000 australien, absent de la page (qui ne donne que la police non urgente, 131 444).
"""

VERIFIE = "27/10/2026"


def _ambassade(ville, adresse, telephone):
    return {"ville": ville, "adresse": adresse, "telephone": telephone}


URGENCES = {
    "GB": {"numeros": [("Urgences", "999")],
           "ambassade": _ambassade("Londres", "58 Knightsbridge, SW1X 7JT", "+44 20 70 73 1000"), "autres": []},
    "MA": {"numeros": [("Police (en ville)", "19"), ("Gendarmerie (hors ville)", "177"), ("Pompiers", "15"),
                       ("Urgences médicales à Marrakech", "141")],
           "ambassade": _ambassade("Rabat", "1, rue Ibn Hajar, Agdal", "+212 5 37 68 97 00"), "autres": []},
    "TN": {"numeros": [("Police", "197"), ("SAMU", "190")],
           "ambassade": _ambassade("Tunis", "2, place de l'Indépendance", "+216 31 315 000"), "autres": []},
    "TR": {"numeros": [("Urgences", "112"), ("Police", "155"), ("Pompiers", "110")],
           "ambassade": _ambassade("Ankara", "Paris Caddesi n° 70, Kavaklıdere", "+90 312 900 15 33"), "autres": []},
    "EG": {"numeros": [("Police", "126")],
           "ambassade": _ambassade("Le Caire", "29 avenue Charles de Gaulle, Guizeh", "+20 2 35 67 32 00"),
           "autres": []},
    "US": {"numeros": [("Urgences", "911")],
           "ambassade": _ambassade("Washington", "4101 Reservoir Road NW", None), "autres": []},
    "CA": {"numeros": [("Urgences", "911")],
           "ambassade": _ambassade("Ottawa", "42, promenade Sussex", "+1 613 789 1795"), "autres": []},
    "MX": {"numeros": [("Urgences", "911")],
           "ambassade": _ambassade("Mexico", "Campos Eliseos 339, Polanco", "+52 55 91 71 97 00"), "autres": []},
    "DO": {"numeros": [("Urgences", "911")],
           "ambassade": _ambassade("Saint-Domingue", "Edificio Corporativo 2015, piso 17, Piantini", None),
           "autres": []},
    "BR": {"numeros": [("Ambulance (SAMU)", "192"), ("Pompiers", "193")],
           "ambassade": _ambassade("Brasília", "SES, Avenida das Nações, lote 04, quadra 801", None), "autres": []},
    "PE": {"numeros": [],
           "ambassade": _ambassade("Lima", "Avenida Arequipa 3415, San Isidro", "+51 17 01 69 09"), "autres": []},
    "SN": {"numeros": [("Police", "17"), ("Pompiers", "18")],
           "ambassade": _ambassade("Dakar", "1, rue El Hadji Amadou Assane Ndoye", "+221 33 839 51 00"),
           "autres": []},
    "MU": {"numeros": [("Urgences", "999"), ("Urgences (autre)", "112"), ("Pompiers", "995")],
           "ambassade": _ambassade("Moka", "The Workplace, La Promenade, Telfair", "+33 3 59 39 71 85"),
           "autres": []},
    "VN": {"numeros": [("Police", "113"), ("Pompiers", "114"), ("Ambulance", "115")],
           "ambassade": _ambassade("Hanoï", "57 Tran Hung Dao", "+84 24 3944 57 00"), "autres": []},
    "KH": {"numeros": [("Police", "117"), ("Police (autre)", "118"), ("Ambulance (SAMU)", "119")],
           "ambassade": _ambassade("Phnom Penh", "1, boulevard Monivong", "+855 23 260 010"),
           "autres": [("Consul honoraire à Siem Reap", "+855 69 932 685")]},
    "TH": {"numeros": [("Police touristique", "1155")],
           "ambassade": _ambassade("Bangkok", "35 Charoenkrung soi 36 (rue de Brest), Bangrak", "+66 28 44 70 05"),
           "autres": [("Consulat à Chiang Mai", "+66 53 281 466"), ("Consulat à Phuket", "+66 76 390 536")]},
    "ID": {"numeros": [("Police à Bali", "911"), ("Police à Jakarta", "+62 21 523 43 33")],
           "ambassade": _ambassade("Jakarta", "Jl. M.H. Thamrin 20", "+62 21 23 55 80 00"),
           "autres": [("Consulat à Bali (Denpasar)", "+62 811 39601401")]},
    "IN": {"numeros": [("Urgences", "112")],
           "ambassade": _ambassade("New Delhi", "2/50-E Shantipath, Chanakyapuri", "+91 11 43 19 61 00"),
           "autres": []},
    "LK": {"numeros": [("Police touristique", "+94 112 433 342"), ("Ambulance (hôpital général)", "+94 11 2691 111")],
           "ambassade": _ambassade("Colombo", "89, Rosmead Place", "+94 11 263 94 00"), "autres": []},
    "JP": {"numeros": [("Police", "110"), ("Ambulance et pompiers", "119"),
                       ("Police, aide possible aux Français", "+81 3 3503 8484")],
           "ambassade": _ambassade("Tokyo", "4-11-44 Minami-Azabu, Minato-ku", "+81 3 57 98 60 00"), "autres": []},
    "AU": {"numeros": [("Urgences", "000"), ("Police (hors urgence vitale)", "131 444")],
           "ambassade": _ambassade("Canberra", "6 Perth Avenue, Yarralumla", "+61 2 621 601 00"), "autres": []},
}
