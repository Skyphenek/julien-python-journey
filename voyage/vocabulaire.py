"""Vocabulaire de destination (rubrique Sur place) : les phrases qui servent vraiment, dans la
langue de chaque pays du voyage, avec une prononciation « à la française » et la voix du
téléphone (🔊) quand elle existe. Une phrase touchée s'affiche en grand, pour la montrer.

Le son : des MP3 préenregistrés par une voix neuronale native (Microsoft, via edge-tts), générés
une fois par generer_audios.py et rangés dans static/audio/ ; la voix du téléphone ne sert qu'en
secours. Les transcriptions sont approximatives : le son fait foi.
Pays francophones (France, Belgique, Sénégal, Maurice…) : pas de bloc.
"""
from html import escape as echapper

# Les phrases, par thème : (clé, en français). Chaque langue les donne toutes.
PHRASES = [
    ("Politesse", [("bonjour", "Bonjour"), ("merci", "Merci"), ("svp", "S'il vous plaît"),
                   ("pardon", "Pardon / excusez-moi"), ("oui", "Oui"), ("non", "Non"),
                   ("au_revoir", "Au revoir")]),
    ("Au marché", [("combien", "C'est combien ?"), ("trop_cher", "C'est trop cher"),
                   ("baisser", "Vous pouvez baisser ?"), ("regarder", "Je regarde seulement")]),
    ("Au restaurant", [("addition", "L'addition, s'il vous plaît"), ("pas_epice", "Pas épicé"),
                       ("eau", "De l'eau"), ("delicieux", "C'est délicieux !")]),
    ("Se déplacer", [("toilettes", "Où sont les toilettes ?"), ("ici", "Arrêtez-vous ici")]),
    ("En cas de pépin", [("aide", "Au secours !"), ("medecin", "J'ai besoin d'un médecin"),
                         ("comprends_pas", "Je ne comprends pas")]),
]
NOMBRES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "100", "1 000"]


def _langue(nom, voix, lang, neurale, phrases, nombres, note=""):
    """phrases : "écrit | prononciation" par clé, dans l'ordre de PHRASES ; nombres : idem (12)."""
    cles = [cle for _, liste in PHRASES for cle, _ in liste]
    assert len(phrases) == len(cles) and len(nombres) == len(NOMBRES), nom
    def couple(texte):
        ecrit, prononciation = texte.split(" | ")
        return ecrit.strip(), prononciation.strip()
    return {"nom": nom, "voix": voix, "lang": lang, "neurale": neurale, "note": note,
            "phrases": dict(zip(cles, map(couple, phrases))), "nombres": [couple(n) for n in nombres]}


LANGUES = {
    "vi": _langue("Vietnamien", "vi-VN", "vi", "vi-VN-HoaiMyNeural", [
        "Xin chào | sin tchao", "Cảm ơn | kam eun", "Làm ơn | lam eun", "Xin lỗi | sin loï",
        "Vâng | veung", "Không | khom", "Tạm biệt | tam biet",
        "Bao nhiêu tiền? | bao gnieou tienn", "Đắt quá! | dat goua", "Bớt đi được không? | beut di dueuk khom",
        "Tôi chỉ xem thôi | toï tchi sèm thoï",
        "Tính tiền | tinn tienn", "Không cay | khom kaï", "Nước | nueuk", "Ngon quá! | ngonn goua",
        "Nhà vệ sinh ở đâu? | gna vé sinn eu dô", "Dừng ở đây | zeung eu dé-i",
        "Cứu tôi với! | keu toï veuï", "Tôi cần bác sĩ | toï keun bak si", "Tôi không hiểu | toï khom hieu",
    ], ["một | mot", "hai | haï", "ba | ba", "bốn | bonn", "năm | nam", "sáu | saou", "bảy | baï",
        "tám | tam", "chín | tchinn", "mười | mueuï", "một trăm | mot tcham", "một nghìn | mot nguinn"],
        note="Langue à tons : la même syllabe change de sens selon la mélodie. Écoute la voix avant de te lancer."),
    "km": _langue("Khmer", "km-KH", "km", "km-KH-SreymomNeural", [
        "ជំរាបសួរ | tchom-reap sour", "អរគុណ | or-koun", "សូម | soum", "សុំទោស | som toh",
        "បាទ / ចាស | bat (homme) / tchas (femme)", "ទេ | té", "លាហើយ | lia haeuy",
        "ថ្លៃប៉ុន្មាន? | tlaï ponn-mane", "ថ្លៃពេក | tlaï pék", "ចុះថ្លៃបានទេ? | tchoh tlaï bane té",
        "ខ្ញុំគ្រាន់តែមើល | knhom kroan tè meul",
        "គិតលុយ | kit louy", "កុំដាក់ហឹរ | kom dak heu", "ទឹក | teuk", "ឆ្ងាញ់ | tchnganh",
        "បង្គន់នៅឯណា? | bang-konn nov ae na", "ឈប់នៅទីនេះ | chhop nov ti nih",
        "ជួយផង! | tchouy phang", "ខ្ញុំត្រូវការគ្រូពេទ្យ | knhom trov ka krou pét", "ខ្ញុំមិនយល់ទេ | knhom minn yol té",
    ], ["មួយ | mouy", "ពីរ | pi", "បី | beï", "បួន | bouonn", "ប្រាំ | pram", "ប្រាំមួយ | pram-mouy",
        "ប្រាំពីរ | pram-pi", "ប្រាំបី | pram-beï", "ប្រាំបួន | pram-bouonn", "ដប់ | dop", "មួយរយ | mouy roy",
        "មួយពាន់ | mouy poann"],
        note="Prix souvent en dollars à Siem Reap et Phnom Penh. Peu de téléphones ont la voix khmère : "
             "montre la phrase en grand."),
    "th": _langue("Thaï", "th-TH", "th", "th-TH-PremwadeeNeural", [
        "สวัสดีครับ / ค่ะ | sa-wat-di khrap (homme) / kha (femme)", "ขอบคุณครับ / ค่ะ | khop-khoun khrap / kha",
        "กรุณา | ka-rou-na", "ขอโทษ | kho-thôt", "ใช่ | tchaï", "ไม่ใช่ | maï tchaï", "ลาก่อน | la-kone",
        "เท่าไหร่? | thao-raï", "แพงไป | phèng paï", "ลดได้ไหม? | lot daï maï", "ดูก่อน | dou kone",
        "เช็คบิล | tchék binn", "ไม่เผ็ด | maï phèt", "น้ำเปล่า | nam plao", "อร่อย | a-roï",
        "ห้องน้ำอยู่ที่ไหน? | hong-nam you thi naï", "จอดที่นี่ | tchot thi-ni",
        "ช่วยด้วย! | tchouaï douaï", "ต้องการหมอ | tong-kann mo", "ไม่เข้าใจ | maï khao-tchaï",
    ], ["หนึ่ง | neung", "สอง | song", "สาม | sam", "สี่ | si", "ห้า | ha", "หก | hok", "เจ็ด | tchèt",
        "แปด | pèt", "เก้า | kao", "สิบ | sip", "หนึ่งร้อย | neung roï", "หนึ่งพัน | neung phann"],
        note="Termine tes phrases par « khrap » (homme) ou « kha » (femme) : c'est la politesse de base."),
    "ja": _langue("Japonais", "ja-JP", "ja", "ja-JP-NanamiNeural", [
        "こんにちは | konnichiwa", "ありがとうございます | arigatô gozaïmass", "お願いします | onégaï shimass",
        "すみません | soumimassenn", "はい | haï", "いいえ | iié", "さようなら | sayônara",
        "いくらですか? | ikoura dess ka", "高すぎます | takasoughimass", "安くできますか? | yassoukou dékimass ka",
        "見ているだけです | mité irou daké dess",
        "お会計お願いします | okaïkéï onégaï shimass", "辛くしないでください | karakou shinaïdé koudassaï",
        "お水 | omizou", "おいしい | oïshii",
        "トイレはどこですか? | toïré wa doko dess ka", "ここで止めてください | koko dé tomété koudassaï",
        "助けて! | tassoukété", "医者が必要です | isha ga hitsouyô dess", "わかりません | wakarimassenn",
    ], ["一 | ichi", "二 | ni", "三 | sann", "四 | yonn", "五 | go", "六 | rokou", "七 | nana", "八 | hachi",
        "九 | kyou", "十 | jou", "百 | hyakou", "千 | senn"],
        note="On ne marchande pas au Japon, et on ne laisse pas de pourboire."),
    "id": _langue("Indonésien", "id-ID", "id", "id-ID-GadisNeural", [
        "Halo | halo", "Terima kasih | térima kassi", "Tolong | tolong", "Maaf | ma-af", "Ya | ya",
        "Tidak | tidak", "Sampai jumpa | sampaï djoumpa",
        "Berapa harganya? | bérapa harganya", "Terlalu mahal | terlalou mahal", "Bisa kurang? | bissa kourang",
        "Saya lihat-lihat saja | saya lihat-lihat sadja",
        "Minta bon | minta bonn", "Tidak pedas | tidak pédass", "Air putih | aïr poutih", "Enak! | énak",
        "Di mana toilet? | di mana toïlèt", "Berhenti di sini | berhenti di sini",
        "Tolong! | tolong", "Saya perlu dokter | saya perlou doktèr", "Saya tidak mengerti | saya tidak mengerti",
    ], ["satu | satou", "dua | doua", "tiga | tiga", "empat | empat", "lima | lima", "enam | énam",
        "tujuh | toudjouh", "delapan | délapann", "sembilan | sembilann", "sepuluh | sépolouh",
        "seratus | sératouss", "seribu | séribou"]),
    "tr": _langue("Turc", "tr-TR", "tr", "tr-TR-EmelNeural", [
        "Merhaba | merhaba", "Teşekkür ederim | téchékkur édérim", "Lütfen | lutfenn",
        "Affedersiniz | affédersiniz", "Evet | évet", "Hayır | haïeur", "Hoşça kalın | hoch-tcha kaleunn",
        "Ne kadar? | né kadar", "Çok pahalı | tchok pahaleu", "İndirim olur mu? | indirim olour mou",
        "Sadece bakıyorum | sadédjé bakeuyoroum",
        "Hesap lütfen | hessap lutfenn", "Acısız olsun | adjeusseuz olsoun", "Su | sou",
        "Çok lezzetli | tchok lezzetli",
        "Tuvalet nerede? | touvalet nérédé", "Burada durun | bourada douroun",
        "İmdat! | imdat", "Doktora ihtiyacım var | doktora ihtiyadjeum var", "Anlamıyorum | anlameuyoroum",
    ], ["bir | bir", "iki | iki", "üç | utch", "dört | deurt", "beş | bech", "altı | alteu", "yedi | yédi",
        "sekiz | sékiz", "dokuz | dokouz", "on | onn", "yüz | yuz", "bin | binn"]),
    "hi": _langue("Hindi", "hi-IN", "hi", "hi-IN-SwaraNeural", [
        "नमस्ते | namasté", "धन्यवाद | dhanyavad", "कृपया | kripaya", "माफ़ कीजिए | maf kijié", "हाँ | haan",
        "नहीं | nahin", "फिर मिलेंगे | phir milengué",
        "कितने का है? | kitné ka haï", "बहुत महँगा है | bahout mahenga haï", "कम कीजिए | kam kijié",
        "बस देख रहा हूँ | bass dekh raha houn",
        "बिल दीजिए | bil dijié", "तीखा नहीं | tikha nahin", "पानी | pani", "बहुत स्वादिष्ट | bahout swadisht",
        "टॉयलेट कहाँ है? | toïlet kahan haï", "यहाँ रुकिए | yahan roukié",
        "बचाओ! | batchao", "मुझे डॉक्टर चाहिए | moujhé doctor tchahié", "मैं नहीं समझा | maïn nahin samjha",
    ], ["एक | ék", "दो | do", "तीन | tinn", "चार | tchar", "पाँच | panntch", "छह | tchhé", "सात | sat",
        "आठ | ath", "नौ | naou", "दस | dass", "सौ | saou", "हज़ार | hazar"],
        note="L'anglais passe presque partout en Inde ; ces mots font plaisir et aident au marché."),
    "ar-MA": _langue("Darija (arabe marocain)", "ar", "ar", "ar-MA-MounaNeural", [
        "السلام عليكم | salam alikoum", "شكرا | choukrane", "عافاك | afak", "سمح لي | smeh li", "إيه | iyèh",
        "لا | la", "بسلامة | bslama",
        "بشحال؟ | bchhal", "غالي بزاف | ghali bzaf", "نقص شوية | nqess chwiya", "غير كانشوف | ghir kanchouf",
        "الحساب عافاك | lhsab afak", "بلا حار | bla har", "الما | lma", "بنين | bnine",
        "فين الطواليت؟ | fine ttwalit", "وقف هنا | wqef hna",
        "عتقوني! | atqouni", "خصني طبيب | khassni tbib", "ما فهمتش | ma fhamtch",
    ], ["واحد | wahed", "جوج | jouj", "تلاتة | tlata", "ربعة | rbâa", "خمسة | khamsa", "ستة | setta",
        "سبعة | sebâa", "تمنية | tmenya", "تسعود | tsâoud", "عشرة | âchra", "مية | mya", "ألف | alf"],
        note="Le français est compris presque partout. La voix du téléphone est de l'arabe standard : "
             "fie-toi plutôt à la transcription."),
    "ar-EG": _langue("Arabe égyptien", "ar", "ar", "ar-EG-SalmaNeural", [
        "أهلاً | ahlann", "شكراً | choukrann", "من فضلك | minn fadlak", "لو سمحت | law samaht", "أيوه | aywa",
        "لأ | la'", "مع السلامة | maâ salama",
        "بكام؟ | bikam", "غالي أوي | ghali awi", "ممكن تنزل شوية؟ | momkenn tenazzel chwaya",
        "بتفرج بس | batfarrag bass",
        "الحساب لو سمحت | el hessab law samaht", "من غير شطة | menn gheir chatta", "مية | mayya",
        "حلو أوي | helw awi",
        "فين الحمام؟ | feinn el hammam", "هنا كويس | hena kwayess",
        "الحقوني! | elhaouni", "محتاج دكتور | mehtag doktor", "مش فاهم | mech fahem",
    ], ["واحد | wahed", "اتنين | etneinn", "تلاتة | talata", "أربعة | arbâa", "خمسة | khamsa", "ستة | setta",
        "سبعة | sabâa", "تمانية | tamanya", "تسعة | tesâa", "عشرة | âchara", "مية | meyya", "ألف | alf"],
        note="La voix du téléphone est de l'arabe standard : fie-toi plutôt à la transcription."),
    "es": _langue("Espagnol", "es", "es", "es-MX-DaliaNeural", [
        "Hola | ola", "Gracias | grassias", "Por favor | por fabor", "Disculpe | diskoulpé", "Sí | si",
        "No | no", "Adiós | adioss",
        "¿Cuánto cuesta? | kouanto kouesta", "Es muy caro | ès moui karo",
        "¿Me hace un descuento? | mé assé oun deskouennto", "Solo estoy mirando | solo estoï mirando",
        "La cuenta, por favor | la kouennta por fabor", "Sin picante | sinn pikannté", "Agua | agoua",
        "¡Delicioso! | délissioso",
        "¿Dónde está el baño? | donndé esta el bagno", "Pare aquí | paré aki",
        "¡Ayuda! | ayouda", "Necesito un médico | néssessito oun médiko", "No entiendo | no enntienndo",
    ], ["uno | ouno", "dos | doss", "tres | tress", "cuatro | kouatro", "cinco | sinnko", "seis | seïss",
        "siete | siété", "ocho | otcho", "nueve | nouébé", "diez | diess", "cien | sienn", "mil | mil"]),
    "pt": _langue("Portugais", "pt-PT", "pt", "pt-PT-RaquelNeural", [
        "Bom dia | bon dia", "Obrigado / Obrigada | obrigadou (homme) / obrigada (femme)",
        "Por favor | pour favor", "Desculpe | dechkoulp", "Sim | sĩ", "Não | nãou", "Adeus | adéouch",
        "Quanto custa? | kouanntou kouchta", "É muito caro | è mouïntou karou",
        "Faz um desconto? | fach oum dechkonntou", "Só estou a ver | so chtô a vér",
        "A conta, por favor | a konnta pour favor", "Sem picante | sãï pikannt", "Água | agoua",
        "Delicioso! | délissiozou",
        "Onde é a casa de banho? | onndé è a kaza dé bagnou", "Pare aqui | paré aki",
        "Socorro! | soukorrou", "Preciso de um médico | préssizou dé oum médikou",
        "Não percebo | nãou pérssébou",
    ], ["um | oum", "dois | doïch", "três | trèch", "quatro | kouatrou", "cinco | sinnkou", "seis | seïch",
        "sete | sèt", "oito | oïtou", "nove | nov", "dez | dèch", "cem | sãï", "mil | mil"]),
    "it": _langue("Italien", "it-IT", "it", "it-IT-ElsaNeural", [
        "Buongiorno | bouonn-djorno", "Grazie | gratsié", "Per favore | pèr favoré", "Mi scusi | mi skouzi",
        "Sì | si", "No | no", "Arrivederci | arrivédèrtchi",
        "Quanto costa? | kouannto kosta", "È troppo caro | è troppo karo", "Mi fa uno sconto? | mi fa ouno skonnto",
        "Sto solo guardando | sto solo gouardanndo",
        "Il conto, per favore | il konnto pèr favoré", "Non piccante | nonn pikannté", "Acqua | akoua",
        "Buonissimo! | bouonissimo",
        "Dov'è il bagno? | dovè il bagno", "Si fermi qui | si fermi koui",
        "Aiuto! | aïouto", "Ho bisogno di un medico | o bizogno di oun médiko", "Non capisco | nonn kapisko",
    ], ["uno | ouno", "due | doué", "tre | tré", "quattro | kouattro", "cinque | tchinnkoué", "sei | seï",
        "sette | setté", "otto | otto", "nove | nové", "dieci | diétchi", "cento | tchennto", "mille | millé"]),
    "de": _langue("Allemand", "de-DE", "de", "de-DE-KatjaNeural", [
        "Guten Tag | gouten tak", "Danke | dankeu", "Bitte | biteu", "Entschuldigung | enntchouldigoung",
        "Ja | ya", "Nein | naïnn", "Tschüss | tchuss",
        "Wie viel kostet das? | vi fil kostet dass", "Das ist zu teuer | dass ist tsou toïeur",
        "Geht es günstiger? | gét ess gunnstigueur", "Ich schaue nur | ich chaoueu nour",
        "Die Rechnung, bitte | di rèchnoung biteu", "Nicht scharf | nicht charf", "Wasser | vasseur",
        "Lecker! | lèkeur",
        "Wo ist die Toilette? | vo ist di toalèteu", "Halten Sie hier | halten zi hir",
        "Hilfe! | hilfeu", "Ich brauche einen Arzt | ich braoucheu aïnenn artst",
        "Ich verstehe nicht | ich fèrchtéeu nicht",
    ], ["eins | aïnns", "zwei | tsvaï", "drei | draï", "vier | fir", "fünf | funf", "sechs | zèks",
        "sieben | zibeunn", "acht | akht", "neun | noïnn", "zehn | tsénn", "hundert | houndeurt",
        "tausend | taouzennt"]),
    "en": _langue("Anglais", "en", "en", "en-GB-SoniaNeural", [
        "Hello | hèlo", "Thank you | sank you", "Please | pliz", "Excuse me | ekskiouz mi", "Yes | yèss",
        "No | nô", "Goodbye | goud-baï",
        "How much is it? | haou meutch iz it", "It's too expensive | its tou ekspènsiv",
        "Can you do a better price? | kèn you dou a bèteur praïss", "I'm just looking | aïm djeust louking",
        "The bill, please | ze bil pliz", "Not spicy, please | not spaïssi pliz", "Water | wôteur",
        "Delicious! | dilicheuss",
        "Where is the bathroom? | wèr iz ze bassroum", "Stop here, please | stop hir pliz",
        "Help! | hèlp", "I need a doctor | aï nid a dokteur", "I don't understand | aï dont eunndeurstènnd",
    ], ["one | wann", "two | tou", "three | sri", "four | for", "five | faïv", "six | siks", "seven | sèvn",
        "eight | eït", "nine | naïnn", "ten | tènn", "one hundred | wann heundred",
        "one thousand | wann saouzennd"],
        note="Aux États-Unis on dit « the check » plutôt que « the bill », et « restroom » pour les toilettes."),
}

# Portugais du Brésil : comme le Portugal, sauf ce qui se dit autrement
LANGUES["pt-BR"] = {**LANGUES["pt"], "nom": "Portugais (Brésil)", "voix": "pt-BR", "neurale": "pt-BR-FranciscaNeural",
                    "phrases": {**LANGUES["pt"]["phrases"],
                                "bonjour": ("Oi / Bom dia", "oï / bon djia"),
                                "au_revoir": ("Tchau", "tchaou"),
                                "regarder": ("Só estou olhando", "so estô olhanndou"),
                                "toilettes": ("Onde fica o banheiro?", "onndji fika ou bagnérou"),
                                "comprends_pas": ("Não entendo", "nãou enntenndou")}}

LANGUE_PAR_PAYS = {
    "VN": "vi", "KH": "km", "TH": "th", "JP": "ja", "ID": "id", "TR": "tr", "IN": "hi",
    "MA": "ar-MA", "EG": "ar-EG",
    **{p: "es" for p in ("ES", "MX", "PE", "DO", "AR", "CL", "CO", "CU", "CR", "BO", "EC", "UY", "PA", "GT")},
    "PT": "pt", "BR": "pt-BR", "IT": "it", "SM": "it", "MT": "en", "DE": "de", "AT": "de",
    **{p: "en" for p in ("GB", "IE", "US", "CA", "AU", "NZ", "ZA", "SG", "LK")},
}


def langues_du_voyage(itineraire):
    """Les langues des étapes, dans l'ordre du voyage, une seule fois chacune."""
    langues = []
    for etape in itineraire:
        code = LANGUE_PAR_PAYS.get(etape.get("code_pays"))
        if code and code not in langues:
            langues.append(code)
    return langues


def fichier_audio(code, cle):
    """Chemin du MP3 d'une phrase (servi sous la même adresse, relative à la page)."""
    return f"audio/{code}/{cle}.mp3"


def cles_audio(code):
    """(clé de fichier, texte écrit) de chaque phrase et nombre d'une langue."""
    langue = LANGUES[code]
    return ([(cle, langue["phrases"][cle][0]) for _, phrases in PHRASES for cle, _ in phrases]
            + [(f"nombre-{i:02d}", ecrit) for i, (ecrit, _) in enumerate(langue["nombres"], start=1)])


def texte_a_dire(ecrit, code=None):
    """« Obrigado / Obrigada » se dit « Obrigado, Obrigada » (la voix lirait « barre oblique »).

    Le thaï n'a pas de ponctuation latine : la voix thaïe refuse un texte qui contient « ? » ou « , ».
    Voix féminine : de « ครับ / ค่ะ » (khrap / kha), elle dit la forme féminine.
    """
    if code == "th":
        texte = ecrit.replace("ครับ / ค่ะ", "ค่ะ").replace(" / ", " ").replace("?", "").replace("!", "")
        return " ".join(texte.split())
    return ecrit.replace(" / ", ", ")


HAUT_PARLEUR = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                '<path d="M11 5 6 9H3v6h3l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/></svg>')


def _ligne(francais, ecrit, prononciation, langue, audio):
    return (f'<li class="phrase" data-voix="{langue["voix"]}" data-audio="{audio}">'
            f'<span class="fr">{echapper(francais)}</span>'
            f'<span class="vo" lang="{langue["lang"]}">{echapper(ecrit)}</span>'
            f'<span class="prono">{echapper(prononciation)}</span>'
            f'<button type="button" class="ecouter" aria-label="Écouter">{HAUT_PARLEUR}</button></li>')


def bloc_vocabulaire(langues):
    """Un tiroir par langue (le premier ouvert) ; vide si aucune langue étrangère."""
    if not langues:
        return ""
    tiroirs = ""
    for i, code in enumerate(langues):
        langue = LANGUES[code]
        corps = (f'<p class="conseil">{echapper(langue["note"])}</p>' if langue["note"] else "")
        for theme, phrases in PHRASES:
            corps += f'<h4>{theme}</h4><ul>' + "".join(
                _ligne(francais, *langue["phrases"][cle], langue, fichier_audio(code, cle))
                for cle, francais in phrases) + "</ul>"
        corps += '<h4>Nombres</h4><ul class="nombres">' + "".join(
            _ligne(chiffre, ecrit, prononciation, langue, fichier_audio(code, f"nombre-{i:02d}"))
            for i, (chiffre, (ecrit, prononciation)) in enumerate(zip(NOMBRES, langue["nombres"]), start=1)) + "</ul>"
        tiroirs += (f'<details class="langue"{" open" if i == 0 else ""}><summary>{echapper(langue["nom"])}</summary>'
                    f'{corps}</details>')
    return (f'<div class="info vocabulaire"><h3>Vocabulaire</h3>'
            f'<p class="conseil">Touche une phrase pour l\'afficher en grand · le haut-parleur pour l\'écouter '
            f'(voix native, aussi hors ligne). Transcriptions approximatives : écoute le son.</p>{tiroirs}</div>')


STYLE_VOCABULAIRE = """
div.vocabulaire details.langue { border-top: 1px solid var(--ligne); padding: .4rem 0; }
div.vocabulaire details.langue > summary { font-weight: 600; cursor: pointer; }
div.vocabulaire h4 { margin: .7rem 0 .2rem; font-size: .8rem; color: var(--doux); text-transform: uppercase; letter-spacing: .04em; }
div.vocabulaire ul { list-style: none; margin: 0; padding: 0; }
div.vocabulaire li.phrase { display: grid; grid-template-columns: 1fr auto; gap: 0 .5rem; padding: .4rem 0;
    border-top: 1px solid var(--ligne); cursor: pointer; }
div.vocabulaire li.phrase:first-child { border-top: none; }
div.vocabulaire .fr { grid-column: 1; font-size: .8rem; color: var(--doux); }
div.vocabulaire .vo { grid-column: 1; font-size: 1.1rem; }
div.vocabulaire .prono { grid-column: 1; font-size: .85rem; font-style: italic; color: var(--doux); }
div.vocabulaire .ecouter { grid-column: 2; grid-row: 1 / span 3; align-self: center; border: none; background: var(--accent-doux);
    border-radius: 50%; width: 2.4rem; height: 2.4rem; font-size: 1.1rem; cursor: pointer; }
div.vocabulaire ul.nombres { display: grid; grid-template-columns: repeat(auto-fill, minmax(9rem, 1fr)); gap: 0 .6rem; }
div.vocabulaire ul.nombres li.phrase:first-child { border-top: 1px solid var(--ligne); }
#grand-texte { position: fixed; inset: 0; z-index: 20; background: var(--carte); display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 1rem; padding: 1.5rem; text-align: center; }
#grand-texte[hidden] { display: none; }
#grand-texte .vo { font-size: 2.6rem; line-height: 1.3; overflow-wrap: anywhere; }
#grand-texte .fr { font-size: 1rem; color: var(--doux); }
#grand-texte .fermer-grand { color: var(--doux); font-size: .85rem; }
"""

# Le son : les MP3 de la page, téléchargés en arrière-plan puis gardés en mémoire (blob) : un tap
# les joue tout de suite, même sur iPhone (pas d'attente réseau entre le geste et la lecture), et le
# service worker les garde pour le hors-ligne. Fichier introuvable : la voix du téléphone, en secours.
SCRIPT_VOCABULAIRE = """
(function () {
    const bloc = document.querySelector('div.vocabulaire');
    if (!bloc) return;
    const sons = {};                                        // adresse du MP3 -> adresse locale (blob)
    function charger(adresse) {
        if (sons[adresse]) return Promise.resolve(sons[adresse]);
        return fetch(adresse)
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.blob(); })
            .then(function (b) { sons[adresse] = URL.createObjectURL(b); return sons[adresse]; });
    }
    function prechargerTout() {
        bloc.querySelectorAll('li.phrase').forEach(function (li) { charger(li.dataset.audio).catch(function () {}); });
    }
    function voixPour(code) {
        if (!('speechSynthesis' in window)) return null;
        const voix = speechSynthesis.getVoices().map(function (v) { return { v: v, lang: v.lang.replace('_', '-').toLowerCase() }; });
        const cherche = code.toLowerCase();
        const exacte = voix.filter(function (x) { return x.lang === cherche; });
        const proche = voix.filter(function (x) { return x.lang.split('-')[0] === cherche.split('-')[0]; });
        const liste = exacte.length ? exacte : proche;
        return ((liste.filter(function (x) { return x.v.localService; })[0] || liste[0]) || {}).v || null;
    }
    function direAvecLeTelephone(li) {                      // secours : voix du téléphone, si elle existe
        const voix = voixPour(li.dataset.voix);
        if (!voix) return;
        speechSynthesis.cancel();
        const phrase = new SpeechSynthesisUtterance(li.querySelector('.vo').textContent);
        phrase.voice = voix; phrase.lang = voix.lang; phrase.rate = 0.8;
        speechSynthesis.speak(phrase);
    }
    let lecteur = null;
    function jouer(src) {
        if (lecteur) lecteur.pause();
        lecteur = new Audio(src);
        return lecteur.play();
    }
    function dire(li) {
        const adresse = li.dataset.audio;
        const pret = sons[adresse] ? jouer(sons[adresse]) : charger(adresse).then(jouer);
        Promise.resolve(pret).catch(function () { direAvecLeTelephone(li); });
    }
    // En grand, pour montrer l'écran à la personne en face
    const grand = document.createElement('div');
    grand.id = 'grand-texte'; grand.hidden = true;
    const grandVo = document.createElement('div'); grandVo.className = 'vo';
    const grandFr = document.createElement('div'); grandFr.className = 'fr';
    const grandFermer = document.createElement('div'); grandFermer.className = 'fermer-grand'; grandFermer.textContent = 'Touche pour fermer';
    grand.append(grandVo, grandFr, grandFermer);
    grand.addEventListener('click', function () { grand.hidden = true; });
    document.body.append(grand);
    function montrer(li) {
        const vo = li.querySelector('.vo');
        grandVo.textContent = vo.textContent; grandVo.lang = vo.lang;
        grandFr.textContent = li.querySelector('.fr').textContent + ' · ' + li.querySelector('.prono').textContent;
        grand.hidden = false;
    }
    bloc.addEventListener('click', function (ev) {
        const li = ev.target.closest('li.phrase');
        if (!li) return;
        if (ev.target.closest('.ecouter')) dire(li); else montrer(li);
    });
    if (navigator.onLine) setTimeout(prechargerTout, 1500);      // après l'affichage de la page
    else prechargerTout();                                     // hors ligne : depuis le cache du worker
})();
"""
