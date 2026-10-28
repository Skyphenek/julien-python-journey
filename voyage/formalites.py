"""Formalités par pays (visa, passeport, santé, à faire avant le départ) — table tenue à la main.

Une fiche par pays hors Europe parmi les plus visités par les Français. Chaque fiche garde
sa source officielle et sa date de vérification ; au-delà de 6 mois, la page affiche
« à revérifier » (les règles changent). Pays absent -> tâche « vérifier sur France Diplomatie ».
UE + Schengen : aucune fiche, la carte d'identité suffit (valise.SANS_PASSEPORT).

Champs d'une fiche :
- passeport_mois   : validité exigée APRÈS LE RETOUR, en mois (0 = valide pendant le séjour).
                     Règle « 6 mois après l'entrée » -> 6 (prudent : compté depuis le retour).
                     Non précisée par la source -> 6 par prudence.
- sans_visa_jusqua : séjour max sans visa, en jours ; None = visa ou autorisation toujours requis.
- visa / visa_lien : ce qu'il faut demander quand le séjour dépasse l'exemption (ou toujours).
- sante            : "centre" (zone tropicale : consultation en centre de vaccinations, J-60)
                     ou None. Les simples recommandations (hépatite A, typhoïde…) ne sont pas
                     affichées : feedback Julien 28/10/2026, « je ne me fais pas vacciner pour le Maroc ».
- sante_note       : précision affichée dans la tâche santé.
- assurance        : None = pas de tâche assurance ; sinon pourquoi elle compte ici (obligatoire,
                     soins très chers pour un touriste).
- ariane           : None = pas de Fil d'Ariane ; sinon les zones orange ou rouges du pays.
                     zones notées de mémoire le 28/10/2026, à confirmer sur la carte du pays.
- taches           : [(jours avant le départ, id, texte, lien ou None)] propres au pays.

Sources : France Diplomatie, Conseils aux voyageurs (pages Entrée / séjour et Santé),
consultées le 27/10/2026.
"""
from datetime import date

DIPLOMATIE = "https://www.diplomatie.gouv.fr/fr/conseils-aux-voyageurs/conseils-par-pays-destination/"
VERIFIE = date(2026, 10, 27)


def _pages(slug):
    base = f"https://www.diplomatie.gouv.fr/fr/information-par-pays/{slug}/conseils-aux-voyageurs-"
    return {"entree": base + "entree-sejour", "page_sante": base + "sante"}


def _fiche(pays, slug, passeport_mois, sans_visa_jusqua, visa=None, visa_lien=None, sante=None,
           sante_note=None, assurance=None, ariane=None, taches=()):
    return {"pays": pays, "verifie_le": VERIFIE, **_pages(slug),
            "passeport_mois": passeport_mois, "sans_visa_jusqua": sans_visa_jusqua,
            "visa": visa, "visa_lien": visa_lien, "sante": sante, "sante_note": sante_note,
            "assurance": assurance, "ariane": ariane, "taches": list(taches)}


FORMALITES = {
    # --- Europe hors UE, Maghreb, Proche-Orient ---------------------------------------------
    "GB": _fiche("Royaume-Uni", "royaume-uni", 0, 180,
                 taches=[(30, "eta", "ETA obligatoire (20 £, valable 2 ans) — passeport exigé, "
                                     "carte d'identité refusée", "https://apply-for-an-eta.homeoffice.gov.uk/"),
                         (21, "ceam", "Carte européenne d'assurance maladie (encore valable au "
                                      "Royaume-Uni), à demander au moins 20 jours avant", None)]),
    "MA": _fiche("Maroc", "maroc", 0, 90),
    "TN": _fiche("Tunisie", "tunisie", 3, 90,
                 ariane="zones frontalières de l'Algérie et de la Libye, sud désertique"),
    "TR": _fiche("Turquie", "turquie", 5, 90, ariane="frontière syrienne"),     # 150 jours après l'entrée
    "EG": _fiche("Égypte", "egypte", 6, None,
                 ariane="nord du Sinaï, désert occidental, frontières libyenne et soudanaise",
                 visa="visa obligatoire (30 jours) : à l'arrivée à l'aéroport (30 USD en espèces) "
                      "ou au consulat, très en amont",
                 taches=[(7, "especes", "Prévoir 30 USD ou l'équivalent en euros en espèces pour le visa", None)]),
    # --- Amériques --------------------------------------------------------------------------
    "US": _fiche("États-Unis", "etats-unis", 0, 90,                 # 6 mois conseillés, pas exigés
                 assurance="indispensable aux États-Unis : soins très chers, aucune convention de sécurité sociale",
                 taches=[(30, "esta", "ESTA obligatoire, au moins 72 h avant — uniquement sur le site "
                                      "officiel (faux sites nombreux) ; passeport biométrique ; "
                                      "à refaire avec un nouveau passeport", "https://esta.cbp.dhs.gov/")]),
    "CA": _fiche("Canada", "canada", 0, 180, assurance="soins très chers pour un touriste au Canada",
                 taches=[(30, "ave", "AVE obligatoire (autorisation de voyage électronique, valable 5 ans), "
                                     "à demander suffisamment à l'avance",
                          "https://www.canada.ca/fr/immigration-refugies-citoyennete/services/visiter-canada/ave/demande.html")]),
    "MX": _fiche("Mexique", "mexique", 0, 180, ariane="plusieurs États du nord et de la côte Pacifique",
                 taches=[(7, "visitax", "Quintana Roo (Cancún, Tulum…) : payer la taxe de séjour Visitax, "
                                        "justificatif demandé à la sortie", "https://visitax.gob.mx/")]),
    "DO": _fiche("République dominicaine", "republique-dominicaine", 6, 30,
                 taches=[(3, "e-ticket", "Formulaire d'entrée e-ticket (gratuit, QR code ; amende de 80 $ "
                                         "sans QR code)", "https://eticket.migracion.gob.do/")]),
    "BR": _fiche("Brésil", "bresil", 6, 90, sante="centre",
                 sante_note="fièvre jaune recommandée avant tout voyage au Brésil"),
    "PE": _fiche("Pérou", "perou", 6, 90, sante="centre", ariane="vallée du VRAEM, frontière colombienne",
                 sante_note="fièvre jaune vivement recommandée pour l'Amazonie, paludisme dans certaines "
                            "régions (rien au-dessus de 2 000 m ni à Lima)"),
    # --- Afrique, océan Indien -------------------------------------------------------------
    "SN": _fiche("Sénégal", "senegal", 6, 90, sante="centre",
                 sante_note="fièvre jaune fortement recommandée, traitement préventif du paludisme"),
    "MU": _fiche("Maurice", "maurice", 0, 90,
                 taches=[(3, "formulaire", "Remplir le « Mauritius All in One Travel Form » avant le départ",
                          "https://safemauritius.govmu.org/")]),
    # --- Asie, Océanie ----------------------------------------------------------------------
    "VN": _fiche("Vietnam", "vietnam", 6, 45,
                 visa="e-visa (90 jours max) sur le portail officiel evisa.gov.vn, méfiance faux sites",
                 visa_lien="https://evisa.gov.vn/", sante="centre"),
    "KH": _fiche("Cambodge", "cambodge", 6, None,
                 visa="e-visa sur evisa.gov.kh, ou visa à l'arrivée à l'aéroport (environ 40 USD)",
                 visa_lien="https://www.evisa.gov.kh/", sante="centre",
                 sante_note="paludisme seulement dans certaines zones forestières",
                 assurance="obligatoire au Cambodge", ariane="frontière thaïlandaise (tensions, mines)",
                 taches=[(3, "e-arrival", "Remplir Cambodia e-arrival avant l'embarquement "
                                          "(QR code demandé à l'immigration)", None),
                         (7, "usd", "Prévoir des dollars US en espèces (visa, carte pas toujours acceptée)", None)]),
    "TH": _fiche("Thaïlande", "thailande", 6, 30, sante="centre",    # 30 j depuis le 15/09/2026 (60 avant)
                 ariane="provinces de l'extrême sud (Narathiwat, Pattani, Yala), frontière cambodgienne",
                 sante_note="paludisme aux frontières (Cambodge, Laos, Birmanie, Malaisie)",
                 taches=[(3, "tdac", "Carte d'arrivée en ligne TDAC, dans les 3 jours avant l'arrivée",
                          "https://tdac.immigration.go.th/")]),
    "ID": _fiche("Indonésie", "indonesie", 6, None,
                 visa="visa à l'arrivée (30 jours, payant, prolongeable une fois) ou e-visa sur evisa.imigrasi.go.id",
                 visa_lien="https://evisa.imigrasi.go.id/", sante="centre",
                 sante_note="pas de paludisme à Bali ni à Jakarta",
                 taches=[(3, "all-indonesia", "Formulaire All Indonesia (douane + santé) dans les 72 h "
                                              "avant l'arrivée (QR code)", None),
                         (7, "bali", "Bali : taxe touristique de 150 000 IDR (Love Bali ou à l'arrivée)", None)]),
    "IN": _fiche("Inde", "inde", 6, None,                            # 6 mois après la fin du visa
                 visa="e-visa obligatoire (e-Tourist 30 jours), à demander entre 30 et 4 jours avant le départ",
                 visa_lien="https://indianvisaonline.gov.in/", sante="centre",
                 ariane="Jammu-et-Cachemire, frontière pakistanaise, Manipur",
                 taches=[(3, "e-arrival", "e-Arrival Card en ligne, à partir de 72 h avant le vol", None)]),
    "LK": _fiche("Sri Lanka", "sri-lanka", 6, None,
                 visa="ETA obligatoire (30 jours, gratuite pour les Français depuis le 25/05/2026), "
                      "uniquement sur eta.gov.lk",
                 visa_lien="https://eta.gov.lk/slvisa/", sante="centre"),
    "JP": _fiche("Japon", "japon", 6, 90,                            # validité non précisée -> prudence
                 assurance="soins chers pour un touriste au Japon (aucune prise en charge)",
                 taches=[(7, "visit-japan-web", "Visit Japan Web : renseigner ses informations d'arrivée "
                                                "en ligne (conseillé)", None)]),
    "AU": _fiche("Australie", "australie", 6, None,                  # validité non précisée -> prudence
                 assurance="soins très chers pour un touriste en Australie",
                 visa="eVisitor (sous-classe 651, 3 mois max), une demande par personne, même passeport "
                      "que celui du voyage",
                 visa_lien="https://immi.homeaffairs.gov.au/",
                 taches=[(7, "aliments", "Australie : règles très strictes sur les aliments à l'entrée, "
                                         "tout déclarer sur la carte passager", None)]),
}
