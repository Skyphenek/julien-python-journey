"""Casa Binomerie — À finir : combien de jours un produit frais tient au frigo, fermé
(spec docs/superpowers/specs/2026-11-03-casa-a-finir-design.md).

Un défaut par rayon, des exceptions par produit ; des valeurs réalistes pour un frigo domestique, pas la prudence
maximale. Un produit entamé peut tourner plus vite : l'app ne le sait pas, [Fini] et [Encore bon] corrigent.
"""
from catalogue import cle_catalogue
from courses import deviner_rayon

PAR_RAYON = {"boucherie": 2, "frais": 7, "fruits-legumes": 5, "epicerie": 30, "specialise": 14}
DUREE_INCONNUE = 7

_EXCEPTIONS = {
    1: """bœuf haché, porc haché, steak haché, steaks hachés, chair à saucisse, tartare, carpaccio, foies de volaille,
        saumon, pavés de saumon, filets de saumon, cabillaud, dos de cabillaud, lieu noir, colin, merlu, églefin,
        haddock, bar, dorade, sole, sardines fraîches, maquereau, thon frais, truite, lotte, raie, Saint-Jacques,
        crevettes, crevettes crues, gambas, moules, palourdes, coques, huîtres, calamars, encornets, poulpe, seiche,
        crabe, homard, langoustines, bulots""",
    3: """fraises, framboises, myrtilles, mûres, groseilles, cassis, cerises, champignons de Paris, champignons,
        pleurotes, shiitakés, girolles, cèpes, pousses de soja, germes de haricot mungo""",
    4: """salade, sucrine, laitue, batavia, roquette, mâche, mesclun, jeunes pousses, épinards frais, persil,
        persil plat, coriandre, basilic, menthe, ciboulette, aneth, cerfeuil, estragon, basilic thaï""",
    5: "burrata, stracciatella",
    7: "lait, lait entier, lait demi-écrémé, ricotta, jambon, jambon blanc, blanc de dinde",
    10: """mozzarella, mozzarella di bufala, saumon fumé, truite fumée, carottes, chou blanc, chou rouge, chou vert,
        céleri-rave, poireaux, navets, panais, betteraves, radis noir, lardons, lardons fumés, allumettes de bacon,
        saucisses de Strasbourg, saucisses de Francfort, knacks, galettes de sarrasin, crêpes, pâte brisée,
        pâte feuilletée, pâte sablée, pâte à pizza, gnocchi, tortellini, raviolis frais, pâtes fraîches,
        tagliatelles fraîches, ravioles""",
    14: """crème fraîche, crème fraîche épaisse, crème liquide, crème fleurette, crème entière, mascarpone, yaourts,
        yaourt nature, yaourt grec, skyr, fromage blanc, faisselle, petits-suisses, crème dessert, kéfir,
        emmental râpé, fromage râpé, cheddar râpé, feta, halloumi, tofu, tofu fumé, chorizo, gingembre""",
    21: """parmesan, pecorino, pecorino romano, parmigiano reggiano, grana padano, comté, beaufort, emmental, gruyère,
        abondance, cantal, mimolette, gouda, cheddar, saucisson, saucisson sec, rosette, salami, guanciale,
        guanciale entier, pancetta, guanciale ou pancetta""",
    28: "œufs, beurre, beurre doux, beurre demi-sel",
}
_PAR_PRODUIT = {cle_catalogue(nom.strip()): jours for jours, noms in _EXCEPTIONS.items() for nom in noms.split(",")}


def duree(nom):
    """Les jours de conservation d'un produit fermé : son exception, sinon le défaut de son rayon, sinon 7."""
    return _PAR_PRODUIT.get(cle_catalogue(nom)) or PAR_RAYON.get(deviner_rayon(nom), DUREE_INCONNUE)
