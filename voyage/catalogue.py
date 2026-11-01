"""Le catalogue des ingrédients et articles (01/11/2026) : de quoi ranger d'office ce qu'ils saisissent.

Chaque article connu a son rayon (Courses) et sa zone (Placard). Un nom saisi tel quel, ou au singulier
ou au pluriel (« tomate » / « tomates »), est rangé par le catalogue ; un nom inconnu passe ensuite par
les mots-clés de courses.py. Les noms sont ceux des recettes et du placard (« tomates pelées »,
« riz carnaroli ») : c'est la même clé qui relie courses, placard et recettes.
Rayon « specialise » : ce qui s'achète à l'épicerie asiatique ou italienne (vague 2 de la checklist).
Le catalogue sert aussi de suggestions à la saisie.
"""

# (rayon, zone, articles séparés par des virgules[, magasin]) : un groupe « specialise » sans magasin est
# de l'épicerie asiatique
_GROUPES = [
    # --- Fruits et légumes --------------------------------------------------------------------
    ("fruits-legumes", "placard-sec", """pommes de terre, pommes de terre grenaille, pommes de terre à frites,
        patates douces, oignons, oignons rouges, oignons blancs, ail, ail rose, échalotes, échalotes grises,
        courge butternut, potimarron, citrouille"""),
    ("fruits-legumes", "frigo", """tomates, tomates cerises, tomates cœur de bœuf, tomates grappe, carottes,
        carottes fanes, courgettes, aubergines, poivrons, poivrons rouges, poivrons jaunes, poivrons verts,
        concombre, salade, sucrine, laitue, batavia, roquette, mâche, mesclun, jeunes pousses, épinards frais,
        endives, chou blanc, chou rouge, chou vert, chou frisé, chou chinois, pak choï, chou-fleur, brocoli,
        choux de Bruxelles, chou-rave, fenouil, céleri, céleri-rave, poireaux, oignons nouveaux, cébette,
        ciboule, haricots verts, haricots plats, petits pois frais, pois gourmands, fèves, asperges vertes,
        asperges blanches, artichauts, betteraves, radis, radis noir, radis blanc, navets, panais,
        topinambours, rutabaga, champignons de Paris, champignons, pleurotes, shiitakés, girolles, cèpes,
        champignons noirs, pousses de soja, germes de haricot mungo, maïs en épi, avocats, gingembre,
        curcuma frais, citronnelle fraîche, piment, piments verts, piment oiseau"""),
    ("fruits-legumes", "frigo", """persil, persil plat, coriandre, basilic, menthe, ciboulette, aneth, cerfeuil,
        estragon, sauge, romarin frais, thym frais, laurier frais, origan frais, basilic thaï, feuilles de
        combava, shiso"""),
    ("fruits-legumes", "placard-sec", """citrons, citrons verts, oranges, oranges sanguines, clémentines,
        mandarines, pamplemousse, pommes, poires, bananes, kiwis, ananas, mangue, papaye, fruit de la passion,
        grenade, kakis, litchis, coings, noix de coco"""),
    ("fruits-legumes", "frigo", """fraises, framboises, myrtilles, mûres, groseilles, cassis, cerises, raisin,
        abricots, pêches, nectarines, prunes, mirabelles, figues, melon, pastèque, rhubarbe"""),

    # --- Frais : crèmerie, fromages, charcuterie, traiteur ------------------------------------
    ("frais", "frigo", """œufs, lait, lait entier, lait demi-écrémé, lait d'avoine, lait d'amande, lait de soja,
        beurre, beurre doux, beurre demi-sel, crème fraîche, crème fraîche épaisse, crème liquide,
        crème fleurette, crème entière, crème de soja, yaourts, yaourt nature, yaourt grec,
        fromage blanc, faisselle, skyr, petits-suisses, crème dessert, kéfir, ribot"""),
    ("frais", "frigo", """parmesan, pecorino, grana padano, comté, beaufort, emmental, gruyère, abondance,
        cantal, mimolette, gouda, cheddar, cheddar râpé, cheddar en tranches, raclette, tomme, reblochon,
        camembert, brie, coulommiers, munster, maroilles, saint-nectaire, morbier, mont d'or, roquefort,
        bleu d'Auvergne, fourme d'Ambert, gorgonzola, chèvre, bûche de chèvre, crottin de chavignol, feta,
        halloumi, mozzarella, mozzarella di bufala, burrata, stracciatella, ricotta, mascarpone, scamorza,
        provolone, taleggio, fromage frais, Saint Môret, Boursin, fromage râpé, emmental râpé, kiri, vache qui rit"""),
    ("frais", "frigo", """jambon, jambon blanc, jambon cru, jambon de Bayonne, jambon de Parme, prosciutto,
        speck, coppa, bresaola, lardons, lardons fumés, allumettes de bacon, guanciale ou pancetta,
        guanciale, pancetta, chorizo, saucisson, saucisson sec, rosette, salami, mortadelle, nduja, pâté de campagne,
        rillettes, terrine, blanc de dinde, knacks, saucisses de Strasbourg,
        saucisses de Francfort"""),
    ("frais", "frigo", """pâte brisée, pâte feuilletée, pâte sablée, pâte à pizza, gnocchi, pâtes fraîches,
        tagliatelles fraîches, raviolis frais, tortellini, ravioles, tofu, tofu fumé, tempeh, houmous,
        tzatziki, taramasalata, guacamole, surimi, saumon fumé, truite fumée, harengs, tarama, levure fraîche,
        levure boulangère fraîche, galettes de sarrasin, crêpes, blinis"""),

    # --- Boucherie, volaille, poissonnerie ----------------------------------------------------
    ("boucherie", "frigo", """bœuf, bœuf haché, steak, pièce du boucher, entrecôte, faux-filet,
        bavette, onglet, rumsteck, côte de bœuf, rôti de bœuf, paleron, joue de bœuf, paleron ou joue de bœuf,
        bœuf à bourguignon, plat de côtes, queue de bœuf, carpaccio, tartare, veau, escalopes de veau,
        blanquette de veau, osso buco de veau, tendron de veau, rôti de veau, côtes de veau, porc, porc haché,
        échine de porc, filet mignon, côtes de porc, rôti de porc, travers de porc, poitrine de porc,
        palette de porc, jarret, saucisses, chipolatas, merguez, saucisses de Toulouse, salsiccia, boudin noir,
        boudin blanc, andouillette, agneau, gigot d'agneau, épaule d'agneau, côtelettes d'agneau,
        souris d'agneau, navarin, poulet, poulet entier, poulet fermier, filets de poulet,
        blancs de poulet, cuisses de poulet, hauts de cuisse de poulet, pilons de poulet, ailes de poulet,
        dinde, escalopes de dinde, canard, magret de canard, cuisses de canard confites, foie gras, lapin,
        pintade, caille, chair à saucisse, foies de volaille"""),
    ("boucherie", "frigo", """saumon, pavés de saumon, filets de saumon, cabillaud, dos de cabillaud, lieu noir,
        colin, merlu, églefin, haddock, bar, dorade, sole, sardines fraîches, maquereau, thon frais, truite,
        lotte, raie, Saint-Jacques, crevettes, crevettes crues, gambas, moules, palourdes, coques, huîtres,
        calamars, encornets, poulpe, seiche, crabe, homard, langoustines, bulots, morue salée"""),

    # --- Chez eux, au congélateur (placard v2) ----------------------------------------------
    ("boulangerie", "congelateur", "demi-baguettes, pains burger"),
    ("boucherie", "congelateur", "steaks hachés"),
    ("frais", "congelateur", "bacon, mozzarella râpée"),

    # --- Boulangerie --------------------------------------------------------------------------
    ("boulangerie", "placard-sec", """pain, baguettes, pain de campagne, pain complet,
        pain aux céréales, pain de seigle, pain de mie, pain de mie complet, pain brioché, brioche, croissants,
        pains au chocolat, pains hot-dog, pains pita, naan, focaccia,
        ciabatta, bagels, muffins anglais, pain polaire, biscottes, pain grillé, gressins, crackers"""),

    # --- Épicerie salée -----------------------------------------------------------------------
    ("epicerie", "placard-sec", """spaghetti, spaghettoni, linguine, tagliatelles, pappardelle, fettuccine,
        rigatoni, penne, mezze maniche, fusilli, farfalle, conchiglie, orecchiette, trofie, paccheri,
        macaroni, coquillettes, lasagnes, feuilles de lasagne, cannelloni, vermicelles, pâtes, pâtes complètes,
        orzo, riz, riz basmati, riz long, riz complet, riz rond, riz carnaroli, riz arborio, riz pour risotto,
        riz sauvage, riz à sushi, crozets, semoule, couscous, boulgour, quinoa, polenta, épeautre, orge perlé,
        sarrasin, lentilles, lentilles vertes, lentilles corail, lentilles beluga, pois cassés, pois chiches,
        haricots rouges, haricots blancs, haricots noirs, flageolets, fèves sèches, flocons d'avoine,
        purée en flocons"""),
    ("epicerie", "placard-sec", """tomates pelées, tomates concassées, passata, coulis de tomate, sauce tomate,
        pulpe de tomate, tomates séchées, thon, thon au naturel, sardines, maquereaux en conserve, anchois à l'huile,
        maïs, petits pois en conserve, haricots verts en conserve, flageolets en conserve, cœurs d'artichaut,
        cœurs de palmier, poivrons grillés, olives, olives vertes, olives noires, câpres, cornichons,
        champignons en conserve, lait de coco, crème de coco, bouillon, bouillon de volaille,
        bouillon de légumes, bouillon de bœuf, fond de veau, fumet de poisson, soupe, velouté, chips,
        cacahuètes, pistaches, noix de cajou, amandes, noisettes, noix, noix de pécan, pignons, graines de courge,
        graines de tournesol, sésame, graines de sésame, graines de chia, graines de lin, raisins secs,
        abricots secs, châtaignes, dattes, pruneaux, figues sèches, cranberries séchées, tortillas, wraps, tacos,
        chapelure, croûtons, oignons frits, purée de tomates, sauce pesto, pesto, tapenade, ketchup"""),
    ("epicerie", "frigo", """concentré de tomate, mayonnaise, sauce barbecue, sauce burger, sauce samouraï,
        sauce béarnaise, pâte de piment, harissa, sauce tomate entamée"""),
    ("epicerie", "epices", """huile d'olive, huile d'olive de finition, huile neutre, huile de tournesol,
        huile de colza, huile d'arachide, huile de friture, huile de noix, huile de noisette, huile de pépins de
        raisin, huile pimentée, vinaigre, vinaigre de vin, vinaigre de vin rouge, vinaigre de vin blanc,
        vinaigre de xérès, vinaigre balsamique, crème de balsamique, vinaigre de cidre, vinaigre blanc,
        vinaigre d'alcool, sel, gros sel, fleur de sel, sel fin, sel de Guérande, poivre, poivre en grains,
        poivre noir, poivre blanc, baies roses, poivre de Sichuan, piment d'Espelette, piment en flocons,
        piment de cayenne, paprika, paprika doux, paprika fumé, cumin, cumin en graines, coriandre en graines,
        coriandre moulue, curcuma, curry, curry en poudre, garam masala, ras el hanout, cannelle,
        cannelle en bâton, noix de muscade, clous de girofle, badiane, anis vert, cardamome, fenugrec,
        graines de moutarde, graines de fenouil, carvi, quatre-épices, cinq-épices, épices tacos,
        épices cajun, zaatar, sumac, safran, gingembre en poudre, ail en poudre, oignon en poudre, chipotle,
        herbes de Provence, thym, laurier, origan, romarin, sarriette, estragon séché, aneth séché,
        persil séché, ciboulette séchée, bouquet garni, vanille, gousses de vanille, extrait de vanille,
        sucre vanillé, moutarde, moutarde de Dijon, moutarde à l'ancienne, moutarde au miel, sauce piquante,
        tabasco, sauce Worcestershire, sriracha, tahini,
        purée de sésame, miel, sirop d'érable, sirop d'agave, mélasse"""),

    # --- Épicerie sucrée, petit-déjeuner, pâtisserie ------------------------------------------
    ("epicerie", "placard-sec", """farine, farine T45, farine T55, farine T65, farine complète, farine de blé,
        farine de sarrasin, farine de maïs, farine de riz, farine de pois chiches, fécule de maïs, maïzena,
        fécule de pomme de terre, levure chimique, levure boulangère, levure de boulanger sèche,
        bicarbonate de soude, sucre, sucre en poudre, sucre semoule, sucre glace, sucre roux, cassonade,
        vergeoise, sucre de canne, sucre en morceaux, chocolat noir, chocolat pâtissier, chocolat au lait,
        chocolat blanc, pépites de chocolat, cacao, cacao en poudre, poudre d'amande, amandes effilées,
        noix de coco râpée, gélatine, agar-agar, pâte d'amande, pâte à tartiner, nutella, confiture,
        compote, crème de marrons, lait concentré sucré, caramel, sirop de grenadine, sirop de menthe,
        boudoirs, biscuits, petits-beurre, spéculoos, sablés, madeleines, gâteaux secs, céréales, muesli,
        granola, café, café moulu, café en grains, capsules de café, café soluble, thé, thé vert, thé noir,
        infusion, tisane, chicorée, chocolat en poudre, cookies, barres de céréales, bonbons"""),

    # --- Surgelés -----------------------------------------------------------------------------
    ("surgeles", "congelateur", """frites, glaces, sorbet, bâtonnets glacés, pizza, nuggets, poisson pané,
        légumes pour wok, poêlée de légumes, edamame, gyoza, nems, raviolis chinois, dim sum, pâte à raviolis,
        gnocchi surgelés, fruits rouges, framboises surgelées, crevettes surgelées, galettes de pommes de terre,
        rösti, croquettes de pommes de terre, pommes noisettes, glaçons, petits pois surgelés,
        épinards surgelés, herbes surgelées, haricots verts surgelés, brocolis surgelés, oignons surgelés,
        ail surgelé, poivrons surgelés, frites surgelées"""),

    # --- Boissons -----------------------------------------------------------------------------
    ("boissons", "cave", """eau, eau plate, eau gazeuse, eau pétillante, eau Volvic citron, Volvic, Evian, Badoit,
        Perrier, San Pellegrino, jus d'orange, jus de pomme, jus de raisin, jus de fruits, smoothie, limonade,
        soda, Coca-Cola, Coca zéro, Orangina, Schweppes, tonic, ginger beer, ice tea, thé glacé, kombucha,
        sirop, vin, vin rouge, vin blanc, vin rosé, champagne, crémant, prosecco, bières, cidre, porto,
        martini, apérol, spritz, pastis, rhum, whisky, vodka, gin, tequila, cognac, calvados, limoncello,
        amaretto, liqueur, Marsala, vin blanc sec, saké, saké de cuisine"""),

    # --- Épiceries spécialisées : asiatique ---------------------------------------------------
    ("specialise", "epices", """sauce poisson, nuoc-mâm, nước mắm, sauce huître, sauce hoisin, sauce teriyaki,
        sauce ponzu, sauce okonomiyaki, sauce tonkatsu, sauce aigre-douce, sauce satay, sauce chili douce,
        sauce soja, sauce soja salée, sauce soja sucrée, mirin, vinaigre de riz, vinaigre noir, huile de sésame, huile de sésame grillé, pâte de curry,
        pâte de curry rouge, pâte de curry vert, pâte de curry jaune, pâte de crevettes, miso, miso blanc,
        miso rouge, gochujang, doenjang, sambal oelek, pâte de haricots, toban djan, dashi, dashi en poudre,
        bonite séchée, katsuobushi, furikake, togarashi, shichimi, wasabi, gingembre mariné, kecap manis,
        sauce soja japonaise, mayonnaise japonaise, kewpie"""),
    ("specialise", "placard-sec", """riz jasmin, riz gluant, vermicelles de riz, nouilles de riz, nouilles,
        nouilles chinoises, nouilles aux œufs, nouilles udon, udon, soba, ramen, nouilles instantanées,
        galettes de riz, feuilles de riz, chapelure panko, panko, algues nori, nori, wakamé, kombu,
        farine de riz gluant, fécule de tapioca, perles de tapioca, champignons noirs séchés,
        shiitakés séchés, lait de coco asiatique, crevettes séchées, cacahuètes grillées, oignons frits asiatiques,
        sucre de palme, tamarin"""),
    ("specialise", "congelateur", """citronnelle, feuilles de citron kaffir, galanga, raviolis japonais"""),
    ("specialise", "frigo", """kimchi, tofu soyeux, tofu ferme, radis daikon, pâte de soja"""),

    # --- Épiceries spécialisées : italienne ---------------------------------------------------
    ("specialise", "placard-sec", """tomates San Marzano, anchois, filets d'anchois, colatura di alici,
        pâtes de Gragnano, fregola, farine 00, semoule de blé dur, taralli, grissini, amaretti, savoiardi,
        artichauts à l'huile, tomates confites, bottarga""", "italien"),
    ("specialise", "frigo", """pecorino romano, parmigiano reggiano, guanciale entier""", "italien"),

    # --- Hygiène et maison --------------------------------------------------------------------
    ("hygiene-maison", "placard-sec", """papier toilette, essuie-tout, sopalin, mouchoirs, liquide vaisselle,
        tablettes lave-vaisselle, sel lave-vaisselle, liquide de rinçage, lessive, adoucissant, détachant,
        éponges, sacs poubelle, papier cuisson, papier aluminium, film alimentaire, sacs de congélation,
        sacs congélation, nettoyant multi-usage, vinaigre ménager, javel, cristaux de soude, savon noir,
        nettoyant WC, pastilles WC, désinfectant, lingettes, gants de ménage, piles, ampoules, allumettes,
        bougies, dentifrice, brosses à dents, fil dentaire, bain de bouche, shampoing, après-shampoing,
        gel douche, savon, savon liquide, déodorant, crème hydratante, crème solaire, coton, cotons-tiges,
        rasoirs, mousse à raser, protections hygiéniques, tampons, serviettes hygiéniques, mouchoirs en papier,
        litière, croquettes, croquettes pour chat, pâtée, pâtée pour chat, friandises pour chat"""),
]


# Achetés à l'épicerie italienne d'après la checklist (vague 2), bien qu'ailleurs au catalogue
_ITALIEN_CHEZ_EUX = ["pecorino", "guanciale ou pancetta", "tomates pelées"]


def _articles():
    vus = []
    for rayon, zone, texte, *magasin in _GROUPES:
        for nom in texte.split(","):
            nom = " ".join(nom.split())
            if nom:
                vus.append((nom, rayon, zone, magasin[0] if magasin else None))
    return vus


CATALOGUE = [(nom, rayon, zone) for nom, rayon, zone, _ in _articles()]    # [(nom, rayon, zone)]
ITALIEN = [nom for nom, _, _, magasin in _articles() if magasin == "italien"] + _ITALIEN_CHEZ_EUX


def cle_catalogue(nom):
    """« Tomates  Cerises » et « tomate cerise » -> la même clé : normalisé, chaque mot sans s ou x final."""
    from courses import normaliser
    return " ".join(m[:-1] if len(m) > 3 and m[-1] in "sx" else m for m in normaliser(nom).split())


def chercher(nom):
    """(rayon, zone) d'un article du catalogue, ou None s'il n'y est pas."""
    return _INDEX.get(cle_catalogue(nom))


_INDEX = {}
for _nom, _rayon, _zone in CATALOGUE:
    _INDEX.setdefault(cle_catalogue(_nom), (_rayon, _zone))
