"""Le prix d'un panier parisien (01/11/2026) : pour chaque article du catalogue, son unité type et son prix.

L'unité type est ce qu'on achète d'habitude pour deux (« filets de poulet » = une barquette de 2) ; le prix
est un ordre de grandeur en supérette parisienne (Monoprix, Franprix, Carrefour City), marques courantes,
estimé par Claude (connaissances jusqu'à mi-2026, pas un relevé en magasin). Précision attendue : ±15 à 25 %
sur un panier, plus large article par article. À corriger quand le ticket de caisse dit autre chose.
Une ligne : nom | unité type | prix en euros.
"""

_TABLE = """
pommes de terre | filet de 2,5 kg | 3.50
pommes de terre grenaille | barquette de 750 g | 2.90
pommes de terre à frites | filet de 2,5 kg | 3.90
patates douces | 2 pièces (800 g) | 3.20
oignons | filet de 1 kg | 2.20
oignons rouges | filet de 500 g | 1.90
oignons blancs | botte | 1.90
ail | 3 têtes | 2.20
ail rose | tresse de 500 g | 6.50
échalotes | filet de 250 g | 1.90
échalotes grises | barquette de 250 g | 3.50
oignons grelots | barquette de 250 g | 2.90
courge butternut | 1 pièce (1 kg) | 2.90
potimarron | 1 pièce (1,2 kg) | 3.90
citrouille | tranche de 1 kg | 3.50
tomates | 1 kg | 3.90
tomates cerises | barquette de 250 g | 2.50
tomates cœur de bœuf | 2 pièces (600 g) | 4.20
tomates grappe | 1 kg | 4.50
carottes | sachet de 1 kg | 1.90
carottes fanes | botte | 2.90
courgettes | 1 kg | 3.20
courgettes rondes | 4 pièces (800 g) | 3.90
aubergines | 2 pièces (600 g) | 2.90
poivrons | lot de 3 | 3.50
poivrons rouges | 2 pièces | 2.80
poivrons jaunes | 2 pièces | 2.80
poivrons verts | 2 pièces | 2.20
concombre | 1 pièce | 1.20
salade | 1 pièce | 1.50
sucrine | sachet de 2 | 1.90
laitue | 1 pièce | 1.30
batavia | 1 pièce | 1.40
roquette | sachet de 125 g | 2.20
mâche | sachet de 150 g | 2.50
mesclun | sachet de 200 g | 2.50
jeunes pousses | sachet de 125 g | 2.30
épinards frais | sachet de 300 g | 2.90
endives | sachet de 1 kg | 3.20
chou blanc | 1 pièce | 2.50
chou rouge | 1 pièce | 2.50
chou vert | 1 pièce | 2.90
chou frisé | 1 pièce | 2.90
chou chinois | 1 pièce | 2.80
pak choï | barquette de 2 | 2.90
chou-fleur | 1 pièce | 2.90
brocoli | 1 pièce (500 g) | 2.50
choux de Bruxelles | barquette de 500 g | 3.20
chou-rave | 1 pièce | 1.90
fenouil | 2 bulbes | 3.20
céleri | 1 pied | 2.20
céleri-rave | 1 pièce | 2.90
poireaux | botte de 3 | 2.90
oignons nouveaux | botte | 1.90
cébette | botte | 1.80
ciboule | botte | 1.80
haricots verts | barquette de 500 g | 3.90
haricots plats | barquette de 500 g | 3.90
petits pois frais | 1 kg (en cosse) | 5.90
pois gourmands | barquette de 250 g | 3.50
fèves | 1 kg (en cosse) | 4.90
asperges vertes | botte de 500 g | 6.50
asperges blanches | botte de 500 g | 7.50
artichauts | 2 pièces | 3.80
betteraves | sachet de 500 g cuites | 1.90
radis | botte | 1.80
radis noir | 1 pièce | 1.90
radis blanc | 1 pièce | 2.20
navets | botte | 2.50
panais | 500 g | 2.50
topinambours | 500 g | 2.90
rutabaga | 1 pièce | 2.20
champignons de Paris | barquette de 500 g | 2.90
champignons | barquette de 500 g | 2.90
pleurotes | barquette de 200 g | 3.50
shiitakés | barquette de 150 g | 3.90
girolles | barquette de 200 g | 7.90
cèpes | barquette de 200 g | 9.90
champignons noirs | sachet de 50 g séchés | 2.90
pousses de soja | sachet de 300 g | 2.20
germes de haricot mungo | sachet de 300 g | 2.20
maïs en épi | 2 épis | 2.50
avocats | filet de 2 | 2.90
gingembre | 1 morceau (150 g) | 1.50
curcuma frais | 100 g | 1.90
citronnelle fraîche | 3 tiges | 1.90
piment | 2 pièces | 1.00
piments verts | barquette de 100 g | 1.90
piment oiseau | barquette de 50 g | 1.90
persil | botte | 1.20
persil plat | botte | 1.20
coriandre | botte | 1.20
basilic | pot | 2.50
menthe | botte | 1.30
ciboulette | botte | 1.30
aneth | botte | 1.40
cerfeuil | botte | 1.40
estragon | botte | 1.50
sauge | barquette de 20 g | 1.90
romarin frais | barquette de 20 g | 1.90
thym frais | barquette de 20 g | 1.90
laurier frais | barquette de 15 g | 1.90
origan frais | barquette de 20 g | 1.90
basilic thaï | botte | 1.90
feuilles de combava | sachet de 20 g | 2.50
shiso | sachet de 10 feuilles | 2.90
citrons | filet de 4 | 2.20
citrons verts | filet de 4 | 2.20
oranges | filet de 2 kg | 4.50
oranges sanguines | filet de 1 kg | 3.50
clémentines | filet de 1 kg | 3.50
mandarines | filet de 1 kg | 3.50
pamplemousse | 2 pièces | 2.40
pommes | sachet de 1,5 kg | 3.90
poires | 1 kg | 3.90
bananes | régime de 1 kg | 2.20
kiwis | barquette de 6 | 2.90
ananas | 1 pièce | 2.90
mangue | 1 pièce | 2.20
papaye | 1 pièce | 3.50
fruit de la passion | 3 pièces | 2.50
grenade | 1 pièce | 1.90
kakis | 3 pièces | 2.50
litchis | barquette de 500 g | 3.90
coings | 1 kg | 3.90
noix de coco | 1 pièce | 2.20
fraises | barquette de 500 g | 4.50
framboises | barquette de 125 g | 2.90
myrtilles | barquette de 125 g | 2.90
mûres | barquette de 125 g | 2.90
groseilles | barquette de 125 g | 2.90
cassis | barquette de 125 g | 3.20
cerises | barquette de 500 g | 5.90
raisin | barquette de 500 g | 2.90
abricots | 1 kg | 4.90
pêches | 1 kg | 3.90
nectarines | 1 kg | 3.90
prunes | 1 kg | 3.90
mirabelles | barquette de 500 g | 3.90
figues | barquette de 6 | 3.90
melon | 1 pièce | 2.90
pastèque | 1/4 de pièce | 3.50
rhubarbe | botte de 500 g | 3.90
œufs | boîte de 12 | 4.20
lait | bouteille de 1 L | 1.20
lait entier | bouteille de 1 L | 1.35
lait demi-écrémé | bouteille de 1 L | 1.20
lait d'avoine | brique de 1 L | 2.30
lait d'amande | brique de 1 L | 2.50
lait de soja | brique de 1 L | 1.90
beurre | plaquette de 250 g | 2.90
beurre doux | plaquette de 250 g | 2.90
beurre demi-sel | plaquette de 250 g | 3.10
crème fraîche | pot de 20 cl | 1.70
crème fraîche épaisse | pot de 40 cl | 2.90
crème liquide | brique de 20 cl | 1.40
crème fleurette | brique de 20 cl | 1.60
crème entière | brique de 50 cl | 3.20
crème de soja | brique de 20 cl | 1.50
yaourts | pack de 4 | 1.90
yaourt nature | pack de 8 | 2.20
yaourt grec | pot de 500 g | 2.90
fromage blanc | pot de 500 g | 2.30
faisselle | pack de 4 | 2.90
skyr | pot de 450 g | 2.90
petits-suisses | pack de 6 | 1.90
crème dessert | pack de 4 | 2.50
kéfir | bouteille de 1 L | 3.20
ribot | bouteille de 1 L | 2.50
parmesan | morceau de 200 g | 5.90
pecorino | morceau de 200 g | 5.50
grana padano | morceau de 200 g | 4.20
comté | morceau de 250 g | 5.50
beaufort | morceau de 200 g | 6.50
emmental | morceau de 250 g | 3.20
gruyère | morceau de 250 g | 4.50
abondance | morceau de 200 g | 5.90
cantal | morceau de 250 g | 4.50
mimolette | morceau de 250 g | 4.20
gouda | morceau de 250 g | 3.50
cheddar | morceau de 200 g | 3.50
cheddar râpé | sachet de 150 g | 2.50
cheddar en tranches | paquet de 10 tranches | 2.50
raclette | barquette de 400 g | 6.90
tomme | morceau de 250 g | 4.50
reblochon | 1 pièce (450 g) | 7.50
camembert | 1 pièce (250 g) | 2.90
brie | part de 200 g | 3.20
coulommiers | 1 pièce (350 g) | 3.50
munster | 1 pièce (200 g) | 3.50
maroilles | 1 pièce (200 g) | 4.50
saint-nectaire | part de 250 g | 5.50
morbier | morceau de 250 g | 4.90
mont d'or | boîte de 450 g | 10.90
roquefort | morceau de 150 g | 4.20
bleu d'Auvergne | morceau de 150 g | 2.90
fourme d'Ambert | morceau de 150 g | 2.90
gorgonzola | morceau de 200 g | 3.90
chèvre | bûche de 180 g | 2.90
bûche de chèvre | 1 bûche (180 g) | 2.90
crottin de chavignol | 1 pièce (60 g) | 2.50
feta | bloc de 200 g | 3.20
halloumi | bloc de 225 g | 3.90
mozzarella | boule de 125 g | 1.40
mozzarella di bufala | boule de 125 g | 2.90
burrata | 1 pièce (125 g) | 3.50
stracciatella | pot de 150 g | 3.90
ricotta | pot de 250 g | 2.50
mascarpone | pot de 250 g | 2.90
scamorza | 1 pièce (250 g) | 3.90
provolone | morceau de 200 g | 3.90
taleggio | morceau de 200 g | 4.50
fromage frais | pot de 150 g | 2.20
Saint Môret | pot de 150 g | 2.30
Boursin | 1 pièce (150 g) | 2.90
fromage râpé | sachet de 200 g | 2.50
emmental râpé | sachet de 200 g | 2.30
kiri | boîte de 12 | 3.50
vache qui rit | boîte de 16 | 2.90
jambon | 4 tranches | 3.20
jambon blanc | 4 tranches | 3.20
jambon cru | 6 tranches | 3.50
jambon de Bayonne | 6 tranches | 4.20
jambon de Parme | 6 tranches (80 g) | 4.90
prosciutto | 6 tranches (80 g) | 4.90
speck | 8 tranches (100 g) | 3.90
coppa | 8 tranches (80 g) | 3.50
bresaola | 8 tranches (80 g) | 4.50
lardons | 2 barquettes de 100 g | 2.30
lardons fumés | 2 barquettes de 100 g | 2.30
allumettes de bacon | 2 barquettes de 100 g | 2.50
guanciale ou pancetta | barquette de 150 g | 4.50
guanciale | morceau de 200 g | 6.50
pancetta | barquette de 120 g | 3.50
chorizo | 1 pièce (250 g) | 3.90
saucisson | 1 pièce (250 g) | 4.50
saucisson sec | 1 pièce (250 g) | 4.50
rosette | 1 pièce (250 g) | 4.20
salami | 12 tranches (100 g) | 2.90
mortadelle | 8 tranches (120 g) | 3.20
nduja | pot de 180 g | 5.90
pâté de campagne | terrine de 180 g | 2.50
rillettes | pot de 220 g | 3.20
terrine | terrine de 180 g | 3.50
blanc de dinde | 4 tranches | 2.90
knacks | paquet de 6 | 2.50
saucisses de Strasbourg | paquet de 6 | 2.50
saucisses de Francfort | paquet de 4 | 2.70
pâte brisée | 1 rouleau | 1.50
pâte feuilletée | 1 rouleau | 1.60
pâte sablée | 1 rouleau | 1.60
pâte à pizza | 1 rouleau | 2.00
gnocchi | paquet de 500 g | 2.30
pâtes fraîches | paquet de 400 g | 2.50
tagliatelles fraîches | paquet de 250 g | 2.20
raviolis frais | paquet de 250 g | 3.20
tortellini | paquet de 250 g | 3.20
ravioles | 4 plaques | 3.50
tofu | bloc de 250 g | 2.50
tofu fumé | bloc de 200 g | 2.70
tempeh | bloc de 200 g | 3.50
houmous | pot de 200 g | 2.50
tzatziki | pot de 200 g | 2.50
taramasalata | pot de 100 g | 2.20
guacamole | pot de 200 g | 2.90
surimi | paquet de 12 bâtonnets | 2.50
saumon fumé | 4 tranches (120 g) | 5.90
truite fumée | 4 tranches (120 g) | 5.20
harengs | barquette de 200 g | 3.20
tarama | pot de 100 g | 2.20
levure fraîche | cube de 42 g | 0.60
levure boulangère fraîche | cube de 42 g | 0.60
galettes de sarrasin | paquet de 6 | 2.90
crêpes | paquet de 6 | 2.50
blinis | paquet de 16 | 2.30
taboulé | barquette de 500 g | 4.50
flammekueche | 1 pièce (350 g) | 3.90
bœuf | 500 g | 9.90
bœuf haché | 500 g (15 % MG) | 7.50
steak | 2 pièces (250 g) | 6.90
pièce du boucher | 2 pièces (300 g) | 9.90
entrecôte | 1 pièce (350 g) | 11.90
faux-filet | 2 pièces (300 g) | 10.90
bavette | 2 pièces (250 g) | 7.90
onglet | 2 pièces (300 g) | 9.50
rumsteck | 2 pièces (300 g) | 10.50
côte de bœuf | 1 pièce (1 kg) | 29.90
rôti de bœuf | 800 g | 19.90
paleron | 1 kg | 15.90
joue de bœuf | 1 kg | 16.90
paleron ou joue de bœuf | 1 kg | 15.90
bœuf à bourguignon | 1 kg | 14.90
plat de côtes | 1 kg | 10.90
queue de bœuf | 1 kg | 10.90
carpaccio | barquette de 2 (200 g) | 6.90
tartare | 2 portions (300 g) | 8.90
veau | 1 kg | 22.90
escalopes de veau | 2 pièces (250 g) | 8.90
blanquette de veau | 1,2 kg | 23.90
osso buco de veau | 4 tranches (1,2 kg) | 22.90
tendron de veau | 1 kg | 16.90
épaule de veau | 1 kg | 21.90
rôti de veau | 800 g | 21.90
côtes de veau | 2 pièces (500 g) | 13.90
porc | 1 kg | 9.90
porc haché | 500 g | 5.50
échine de porc | 1 kg | 9.50
filet mignon | 1 pièce (500 g) | 9.90
côtes de porc | 2 pièces (400 g) | 4.50
rôti de porc | 1 kg | 10.90
travers de porc | 1 kg | 8.90
poitrine de porc | 500 g | 5.90
palette de porc | 1 kg | 8.50
jarret | 1 pièce (1 kg) | 6.90
saucisses | 4 pièces | 4.50
chipolatas | 6 pièces | 4.20
merguez | 6 pièces | 4.50
saucisses de Toulouse | 4 pièces | 4.90
salsiccia | 4 pièces (400 g) | 5.90
boudin noir | 2 pièces | 3.50
boudin blanc | 2 pièces | 4.50
andouillette | 2 pièces | 6.50
agneau | 1 kg | 19.90
gigot d'agneau | 1 pièce (1,5 kg) | 32.90
épaule d'agneau | 1 pièce (1,2 kg) | 21.90
côtelettes d'agneau | 6 pièces (450 g) | 12.90
souris d'agneau | 2 pièces (700 g) | 13.90
navarin | 1 kg | 17.90
poulet | 1 pièce (1,3 kg) | 8.90
poulet entier | 1 pièce (1,3 kg) | 8.90
poulet fermier | 1 pièce (1,5 kg) | 14.90
filets de poulet | barquette de 2 (300 g) | 5.50
blancs de poulet | barquette de 2 (300 g) | 5.50
cuisses de poulet | barquette de 2 (600 g) | 4.20
hauts de cuisse de poulet | barquette de 4 (600 g) | 5.20
pilons de poulet | barquette de 6 (700 g) | 4.50
ailes de poulet | barquette de 1 kg | 5.90
dinde | 500 g | 6.50
escalopes de dinde | barquette de 2 (250 g) | 4.20
canard | 1 pièce (2 kg) | 18.90
magret de canard | 1 pièce (350 g) | 8.90
cuisses de canard confites | boîte de 2 | 9.90
foie gras | bloc de 180 g | 12.90
lapin | 1 pièce (1,3 kg) | 14.90
pintade | 1 pièce (1,2 kg) | 12.90
caille | barquette de 2 | 6.90
chair à saucisse | 500 g | 5.50
foies de volaille | barquette de 400 g | 3.50
veau haché | barquette de 400 g | 8.90
agneau haché | barquette de 400 g | 9.50
os à moelle | 2 pièces | 3.50
saumon | 2 pavés (250 g) | 7.90
pavés de saumon | 2 pavés (250 g) | 7.90
filets de saumon | 2 pièces (250 g) | 7.90
cabillaud | 2 pièces (300 g) | 8.90
dos de cabillaud | 2 pièces (300 g) | 10.90
lieu noir | 2 pièces (300 g) | 5.90
colin | 2 pièces (300 g) | 6.90
merlu | 2 pièces (300 g) | 6.50
églefin | 2 pièces (300 g) | 6.90
haddock | 2 pièces (300 g) | 7.50
bar | 1 pièce (400 g) | 8.90
dorade | 1 pièce (400 g) | 7.90
sole | 2 pièces (500 g) | 16.90
sardines fraîches | 500 g | 5.90
maquereau | 2 pièces (500 g) | 5.90
thon frais | 2 pavés (300 g) | 11.90
truite | 2 filets (250 g) | 6.90
lotte | 2 médaillons (300 g) | 14.90
raie | 1 aile (500 g) | 9.90
Saint-Jacques | 8 noix (200 g) | 14.90
crevettes | barquette de 200 g cuites | 5.50
crevettes crues | barquette de 300 g | 7.90
gambas | 6 pièces (300 g) | 9.90
moules | 1,5 kg | 7.50
palourdes | 500 g | 7.90
coques | 500 g | 5.90
huîtres | bourriche de 12 | 14.90
calamars | 400 g | 7.50
encornets | 400 g | 7.50
poulpe | 500 g | 12.90
seiche | 500 g | 8.90
crabe | 1 pièce (800 g) | 12.90
homard | 1 pièce (500 g) | 24.90
langoustines | 500 g | 16.90
bulots | 500 g cuits | 6.50
morue salée | morceau de 400 g | 9.90
demi-baguettes | sachet de 4 précuites | 2.50
pains burger | sachet de 4 | 2.20
steaks hachés | 2 pièces (250 g) | 4.50
bacon | 10 tranches (150 g) | 2.70
mozzarella râpée | sachet de 200 g | 2.50
pain | 1 pain (400 g) | 2.20
baguettes | 1 baguette | 1.20
pain de campagne | 1 pain (500 g) | 3.20
pain complet | 1 pain (400 g) | 2.50
pain aux céréales | 1 pain (400 g) | 2.80
pain de seigle | 1 pain (400 g) | 2.80
pain de mie | paquet de 500 g | 2.20
pain de mie complet | paquet de 500 g | 2.40
pain brioché | paquet de 500 g | 2.50
brioche | 1 pièce (400 g) | 2.90
croissants | 4 pièces | 4.40
pains au chocolat | 4 pièces | 4.80
pains hot-dog | sachet de 6 | 2.20
pains à hot dog | sachet de 6 | 2.20
pains pita | sachet de 6 | 1.90
naan | sachet de 2 | 2.20
focaccia | 1 pièce (300 g) | 3.50
ciabatta | 1 pièce (300 g) | 2.50
bagels | sachet de 4 | 2.90
muffins anglais | sachet de 6 | 2.20
pain polaire | sachet de 8 | 2.20
biscottes | paquet de 36 | 2.20
pain grillé | paquet de 250 g | 2.50
gressins | paquet de 125 g | 1.90
crackers | paquet de 200 g | 2.20
spaghetti | paquet de 500 g | 1.50
spaghettoni | paquet de 500 g | 1.90
linguine | paquet de 500 g | 1.70
tagliatelles | paquet de 500 g | 2.20
pappardelle | paquet de 500 g | 2.50
fettuccine | paquet de 500 g | 2.30
rigatoni | paquet de 500 g | 1.60
penne | paquet de 500 g | 1.40
mezze maniche | paquet de 500 g | 1.90
fusilli | paquet de 500 g | 1.40
farfalle | paquet de 500 g | 1.50
conchiglie | paquet de 500 g | 1.60
orecchiette | paquet de 500 g | 2.20
trofie | paquet de 500 g | 2.50
paccheri | paquet de 500 g | 2.50
macaroni | paquet de 500 g | 1.30
coquillettes | paquet de 500 g | 1.30
lasagnes | boîte de 500 g | 2.20
feuilles de lasagne | boîte de 500 g | 2.20
cannelloni | boîte de 250 g | 2.20
vermicelles | paquet de 250 g | 1.20
pâtes | paquet de 500 g | 1.40
pâtes complètes | paquet de 500 g | 1.90
orzo | paquet de 500 g | 2.30
riz | paquet de 1 kg | 2.20
riz basmati | paquet de 1 kg | 3.50
riz long | paquet de 1 kg | 2.20
riz complet | paquet de 1 kg | 2.80
riz rond | paquet de 1 kg | 2.50
riz carnaroli | paquet de 1 kg | 4.90
riz arborio | paquet de 1 kg | 3.90
riz pour risotto | paquet de 1 kg | 3.90
riz sauvage | paquet de 500 g | 4.50
riz à sushi | paquet de 1 kg | 4.20
crozets | paquet de 400 g | 3.50
semoule | paquet de 500 g | 1.30
couscous | paquet de 1 kg | 2.50
boulgour | paquet de 500 g | 1.90
quinoa | paquet de 400 g | 3.20
polenta | paquet de 500 g | 2.20
épeautre | paquet de 500 g | 2.90
orge perlé | paquet de 500 g | 2.20
sarrasin | paquet de 500 g | 2.90
lentilles | paquet de 500 g | 1.90
lentilles vertes | paquet de 500 g | 2.50
lentilles corail | paquet de 500 g | 2.30
lentilles beluga | paquet de 500 g | 2.90
pois cassés | paquet de 500 g | 1.90
pois chiches | boîte de 400 g | 1.10
haricots rouges | boîte de 400 g | 1.10
haricots blancs | boîte de 400 g | 1.10
haricots noirs | boîte de 400 g | 1.50
flageolets | boîte de 400 g | 1.40
fèves sèches | paquet de 500 g | 2.50
flocons d'avoine | paquet de 500 g | 1.70
purée en flocons | paquet de 4 sachets | 2.20
tomates pelées | boîte de 400 g | 1.20
tomates concassées | boîte de 400 g | 1.10
passata | bouteille de 700 g | 1.60
coulis de tomate | bouteille de 500 g | 1.40
sauce tomate | pot de 400 g | 1.90
pulpe de tomate | brique de 500 g | 1.30
tomates séchées | pot de 280 g | 3.50
thon | boîte de 140 g | 2.50
thon au naturel | lot de 3 boîtes | 6.50
sardines | boîte de 135 g | 2.20
maquereaux en conserve | boîte de 169 g | 2.30
anchois à l'huile | boîte de 50 g | 2.50
maïs | boîte de 285 g | 1.10
petits pois en conserve | boîte de 400 g | 1.20
haricots verts en conserve | boîte de 400 g | 1.40
flageolets en conserve | boîte de 400 g | 1.40
cœurs d'artichaut | boîte de 240 g | 2.90
cœurs de palmier | boîte de 220 g | 2.90
poivrons grillés | bocal de 290 g | 2.90
olives | pot de 200 g | 2.50
olives vertes | pot de 200 g | 2.30
olives noires | pot de 200 g | 2.50
câpres | pot de 90 g | 1.90
citron confit | bocal de 4 | 3.90
cornichons | bocal de 350 g | 2.20
champignons en conserve | boîte de 230 g | 1.50
lait de coco | boîte de 400 ml | 1.90
crème de coco | brique de 200 ml | 1.90
bouillon | boîte de 10 cubes | 1.90
bouillon de volaille | boîte de 10 cubes | 1.90
bouillon de légumes | boîte de 10 cubes | 1.90
bouillon de bœuf | boîte de 10 cubes | 1.90
fond de veau | boîte de 110 g | 2.90
fumet de poisson | boîte de 110 g | 2.90
soupe | brique de 1 L | 2.90
velouté | brique de 1 L | 2.90
chips | sachet de 150 g | 1.90
cacahuètes | sachet de 200 g | 1.90
pistaches | sachet de 200 g | 4.90
noix de cajou | sachet de 200 g | 4.20
amandes | sachet de 200 g | 3.90
noisettes | sachet de 200 g | 3.90
noix | sachet de 200 g | 3.50
noix de pécan | sachet de 150 g | 4.90
pignons | sachet de 75 g | 4.50
graines de courge | sachet de 200 g | 2.90
graines de tournesol | sachet de 200 g | 1.90
sésame | sachet de 100 g | 1.90
graines de sésame | sachet de 100 g | 1.90
graines de chia | sachet de 200 g | 3.50
graines de lin | sachet de 250 g | 2.50
raisins secs | sachet de 250 g | 2.20
abricots secs | sachet de 250 g | 3.50
châtaignes | bocal de 200 g cuites | 4.50
dattes | barquette de 250 g | 3.20
pruneaux | sachet de 250 g | 3.20
figues sèches | sachet de 250 g | 3.50
cranberries séchées | sachet de 150 g | 2.90
tortillas | paquet de 8 | 2.20
wraps | paquet de 6 | 2.20
tacos | boîte de 12 coques | 2.90
chapelure | paquet de 250 g | 1.50
croûtons | sachet de 90 g | 1.50
oignons frits | pot de 100 g | 1.90
purée de tomates | brique de 500 g | 1.30
sauce pesto | pot de 190 g | 2.90
pesto | pot de 190 g | 2.90
tapenade | pot de 90 g | 2.50
ketchup | flacon de 500 g | 2.50
concentré de tomate | tube de 200 g | 1.50
mayonnaise | pot de 235 g | 2.20
sauce barbecue | flacon de 300 g | 2.50
sauce burger | flacon de 300 g | 2.50
sauce samouraï | flacon de 300 g | 2.50
sauce béarnaise | pot de 185 g | 2.20
pâte de piment | tube de 70 g | 1.90
harissa | tube de 70 g | 1.50
sauce tomate entamée | pot de 400 g | 1.90
huile d'olive | bouteille de 75 cl | 8.90
huile d'olive de finition | bouteille de 50 cl | 12.90
huile neutre | bouteille de 1 L | 3.20
huile de tournesol | bouteille de 1 L | 2.90
huile de colza | bouteille de 1 L | 3.20
huile d'arachide | bouteille de 1 L | 4.50
huile de friture | bouteille de 1 L | 3.50
huile de noix | bouteille de 25 cl | 5.90
huile de noisette | bouteille de 25 cl | 6.50
huile de pépins de raisin | bouteille de 50 cl | 4.50
huile pimentée | flacon de 10 cl | 2.90
vinaigre | bouteille de 50 cl | 1.50
vinaigre de vin | bouteille de 50 cl | 1.50
vinaigre de vin rouge | bouteille de 50 cl | 1.60
vinaigre de vin blanc | bouteille de 50 cl | 1.60
vinaigre de xérès | bouteille de 50 cl | 3.50
vinaigre balsamique | bouteille de 50 cl | 3.50
crème de balsamique | flacon de 250 ml | 3.50
vinaigre de cidre | bouteille de 50 cl | 1.90
vinaigre blanc | bouteille de 1 L | 1.20
vinaigre d'alcool | bouteille de 1 L | 1.20
sel | paquet de 1 kg | 0.90
gros sel | paquet de 1 kg | 0.90
fleur de sel | pot de 125 g | 3.90
sel fin | paquet de 1 kg | 0.90
sel de Guérande | paquet de 1 kg | 2.90
poivre | moulin de 45 g | 3.50
poivre en grains | flacon de 50 g | 3.20
poivre noir | flacon de 50 g | 3.20
poivre blanc | flacon de 40 g | 3.50
baies roses | flacon de 25 g | 3.50
poivre de Sichuan | flacon de 20 g | 3.90
piment d'Espelette | pot de 40 g | 6.90
piment en flocons | flacon de 40 g | 2.90
piment de cayenne | flacon de 40 g | 2.50
paprika | flacon de 50 g | 2.50
paprika doux | flacon de 50 g | 2.50
paprika fumé | flacon de 50 g | 2.90
cumin | flacon de 40 g | 2.50
cumin en graines | flacon de 40 g | 2.50
coriandre en graines | flacon de 30 g | 2.50
coriandre moulue | flacon de 35 g | 2.50
curcuma | flacon de 45 g | 2.50
curry | flacon de 45 g | 2.50
curry en poudre | flacon de 45 g | 2.50
garam masala | flacon de 40 g | 2.90
ras el hanout | flacon de 40 g | 2.90
cannelle | flacon de 40 g | 2.50
cannelle en bâton | sachet de 5 bâtons | 2.90
noix de muscade | flacon de 4 noix | 2.90
clous de girofle | flacon de 30 g | 3.20
badiane | flacon de 15 g | 3.20
anis vert | flacon de 30 g | 2.90
cardamome | flacon de 25 g | 4.50
piment de la Jamaïque | flacon de 30 g | 3.20
fenugrec | flacon de 40 g | 2.90
graines de moutarde | flacon de 50 g | 2.50
graines de fenouil | flacon de 30 g | 2.50
carvi | flacon de 30 g | 2.50
quatre-épices | flacon de 35 g | 2.50
cinq-épices | flacon de 35 g | 2.90
épices tacos | sachet de 30 g | 1.50
épices cajun | flacon de 40 g | 2.90
zaatar | pot de 50 g | 3.50
sumac | pot de 50 g | 3.50
safran | dosette de 0,1 g | 3.90
gingembre en poudre | flacon de 35 g | 2.50
ail en poudre | flacon de 50 g | 2.50
oignon en poudre | flacon de 45 g | 2.50
chipotle | flacon de 40 g | 3.90
herbes de Provence | flacon de 20 g | 2.20
thym | flacon de 15 g | 2.20
laurier | sachet de 10 g | 1.90
origan | flacon de 10 g | 2.20
romarin | flacon de 15 g | 2.20
sarriette | flacon de 15 g | 2.20
estragon séché | flacon de 10 g | 2.50
aneth séché | flacon de 10 g | 2.50
persil séché | flacon de 10 g | 2.20
ciboulette séchée | flacon de 10 g | 2.50
bouquet garni | sachet de 6 | 1.90
vanille | 2 gousses | 5.90
gousses de vanille | 2 gousses | 5.90
extrait de vanille | flacon de 50 ml | 4.90
sucre vanillé | paquet de 10 sachets | 1.50
moutarde | pot de 370 g | 2.20
moutarde de Dijon | pot de 370 g | 2.20
moutarde à l'ancienne | pot de 210 g | 2.50
moutarde au miel | pot de 200 g | 2.50
sauce piquante | flacon de 150 ml | 2.90
tabasco | flacon de 60 ml | 3.50
sauce Worcestershire | flacon de 150 ml | 3.20
sriracha | flacon de 435 ml | 4.50
tahini | pot de 300 g | 4.50
purée de sésame | pot de 300 g | 4.50
miel | pot de 500 g | 6.50
sirop d'érable | bouteille de 250 ml | 6.90
sirop d'agave | flacon de 350 g | 4.50
mélasse | pot de 450 g | 4.90
farine | paquet de 1 kg | 1.20
farine T45 | paquet de 1 kg | 1.40
farine T55 | paquet de 1 kg | 1.20
farine T65 | paquet de 1 kg | 1.60
farine complète | paquet de 1 kg | 2.20
farine de blé | paquet de 1 kg | 1.20
farine de sarrasin | paquet de 500 g | 2.50
farine de maïs | paquet de 500 g | 2.20
farine de riz | paquet de 500 g | 2.50
farine de pois chiches | paquet de 500 g | 2.90
fécule de maïs | boîte de 400 g | 2.20
maïzena | boîte de 400 g | 2.20
fécule de pomme de terre | boîte de 250 g | 1.90
levure chimique | paquet de 6 sachets | 1.20
levure boulangère | paquet de 5 sachets | 1.50
levure de boulanger sèche | paquet de 5 sachets | 1.50
bicarbonate de soude | boîte de 400 g | 1.90
sucre | paquet de 1 kg | 1.40
sucre en poudre | paquet de 1 kg | 1.40
sucre semoule | paquet de 1 kg | 1.40
sucre glace | paquet de 500 g | 1.60
sucre roux | paquet de 1 kg | 2.50
cassonade | paquet de 500 g | 2.20
vergeoise | paquet de 500 g | 2.50
sucre de canne | paquet de 1 kg | 2.80
sucre en morceaux | boîte de 1 kg | 1.90
chocolat noir | tablette de 200 g | 2.90
chocolat pâtissier | tablette de 200 g | 2.70
chocolat au lait | tablette de 100 g | 1.70
chocolat blanc | tablette de 100 g | 1.90
pépites de chocolat | sachet de 100 g | 1.90
cacao | boîte de 250 g | 4.50
cacao en poudre | boîte de 250 g | 4.50
poudre d'amande | sachet de 125 g | 2.90
amandes effilées | sachet de 125 g | 2.90
noix de coco râpée | sachet de 125 g | 1.90
gélatine | boîte de 9 feuilles | 2.20
agar-agar | boîte de 4 sachets | 2.90
pâte d'amande | paquet de 250 g | 3.50
pâte à tartiner | pot de 400 g | 3.90
nutella | pot de 400 g | 3.90
confiture | pot de 370 g | 2.90
compote | pack de 4 gourdes | 2.50
crème de marrons | boîte de 250 g | 2.90
lait concentré sucré | tube de 300 g | 2.50
caramel | pot de 200 g | 3.20
sirop de grenadine | bouteille de 75 cl | 2.90
sirop de menthe | bouteille de 75 cl | 2.90
boudoirs | paquet de 175 g | 1.90
biscuits à la cuillère | paquet de 175 g | 1.90
biscuits | paquet de 200 g | 2.20
petits-beurre | paquet de 200 g | 1.90
spéculoos | paquet de 250 g | 2.20
sablés | paquet de 150 g | 2.20
madeleines | sachet de 12 | 2.50
gâteaux secs | paquet de 200 g | 2.20
céréales | boîte de 375 g | 3.50
muesli | paquet de 500 g | 3.50
granola | paquet de 400 g | 3.90
café | paquet de 250 g moulu | 4.50
café moulu | paquet de 250 g | 4.50
café en grains | paquet de 500 g | 8.90
capsules de café | boîte de 10 | 3.90
café soluble | pot de 100 g | 4.90
thé | boîte de 25 sachets | 3.20
thé vert | boîte de 25 sachets | 3.20
thé noir | boîte de 25 sachets | 3.20
infusion | boîte de 20 sachets | 2.90
tisane | boîte de 20 sachets | 2.90
chicorée | pot de 100 g | 3.20
chocolat en poudre | boîte de 450 g | 3.50
cookies | paquet de 200 g | 2.50
barres de céréales | paquet de 6 | 2.50
bonbons | sachet de 250 g | 2.50
frites | sachet de 1 kg | 2.90
glaces | bac de 500 ml | 4.50
sorbet | bac de 500 ml | 4.50
bâtonnets glacés | boîte de 6 | 4.20
pizza | 1 pièce | 3.90
nuggets | boîte de 400 g | 4.50
poisson pané | boîte de 10 | 3.90
légumes pour wok | sachet de 750 g | 3.50
poêlée de légumes | sachet de 750 g | 3.50
edamame | sachet de 400 g | 3.50
gyoza | sachet de 20 | 5.50
nems | boîte de 10 | 4.90
raviolis chinois | sachet de 20 | 4.90
dim sum | boîte de 12 | 5.90
pâte à raviolis | paquet de 40 feuilles | 3.20
gnocchi surgelés | sachet de 750 g | 3.50
fruits rouges | sachet de 500 g | 4.50
framboises surgelées | sachet de 300 g | 3.90
crevettes surgelées | sachet de 400 g | 7.90
galettes de pommes de terre | sachet de 10 | 3.20
rösti | sachet de 8 | 3.20
croquettes de pommes de terre | sachet de 600 g | 2.90
pommes dauphines | sachet de 450 g | 3.20
pommes noisettes | sachet de 750 g | 3.20
glaçons | sachet de 2 kg | 2.20
petits pois surgelés | sachet de 1 kg | 3.20
épinards surgelés | sachet de 750 g (galets) | 2.50
herbes surgelées | pot de 50 g | 2.20
haricots verts surgelés | sachet de 1 kg | 3.20
brocolis surgelés | sachet de 1 kg | 3.20
oignons surgelés | sachet de 600 g | 2.20
ail surgelé | pot de 50 g | 2.20
poivrons surgelés | sachet de 750 g | 2.90
frites surgelées | sachet de 1 kg | 2.90
eau | pack de 6 × 1,5 L | 3.50
pack d'eau | pack de 6 × 1,5 L | 3.50
eau plate | pack de 6 × 1,5 L | 3.50
eau gazeuse | pack de 6 × 1 L | 4.50
eau pétillante | pack de 6 × 1 L | 4.50
eau Volvic citron | pack de 6 × 1,5 L | 6.90
Volvic | pack de 6 × 1,5 L | 4.20
Evian | pack de 6 × 1,5 L | 4.90
Badoit | pack de 6 × 1 L | 5.50
Perrier | pack de 4 × 1 L | 4.90
San Pellegrino | pack de 6 × 1 L | 5.90
jus d'orange | bouteille de 1 L | 2.90
jus de pomme | bouteille de 1 L | 2.20
jus de raisin | bouteille de 1 L | 2.50
jus de fruits | bouteille de 1 L | 2.50
smoothie | bouteille de 75 cl | 3.90
limonade | bouteille de 1,5 L | 1.90
soda | bouteille de 1,5 L | 2.20
Coca-Cola | bouteille de 1,5 L | 2.50
Coca zéro | bouteille de 1,5 L | 2.50
Orangina | bouteille de 1,5 L | 2.70
Schweppes | bouteille de 1,5 L | 2.50
tonic | pack de 4 × 25 cl | 3.50
ginger beer | pack de 4 × 25 cl | 4.50
ice tea | bouteille de 1,5 L | 2.20
thé glacé | bouteille de 1,5 L | 2.20
kombucha | bouteille de 75 cl | 4.50
sirop | bouteille de 75 cl | 2.90
vin | bouteille de 75 cl | 7.90
vin rouge | bouteille de 75 cl | 7.90
vin blanc | bouteille de 75 cl | 7.50
vin rosé | bouteille de 75 cl | 7.50
champagne | bouteille de 75 cl | 29.90
crémant | bouteille de 75 cl | 11.90
prosecco | bouteille de 75 cl | 9.90
bières | pack de 6 × 25 cl | 5.90
cidre | bouteille de 75 cl | 3.90
porto | bouteille de 75 cl | 12.90
martini | bouteille de 1 L | 12.90
apérol | bouteille de 70 cl | 15.90
spritz | bouteille de 70 cl | 15.90
pastis | bouteille de 70 cl | 19.90
rhum | bouteille de 70 cl | 19.90
whisky | bouteille de 70 cl | 24.90
vodka | bouteille de 70 cl | 17.90
gin | bouteille de 70 cl | 24.90
tequila | bouteille de 70 cl | 24.90
cognac | bouteille de 70 cl | 34.90
calvados | bouteille de 70 cl | 24.90
limoncello | bouteille de 50 cl | 14.90
amaretto | bouteille de 70 cl | 16.90
liqueur | bouteille de 50 cl | 14.90
Marsala | bouteille de 75 cl | 9.90
vin blanc sec | bouteille de 75 cl | 7.50
saké | bouteille de 72 cl | 14.90
saké de cuisine | bouteille de 50 cl | 5.90
sauce poisson | bouteille de 200 ml | 2.90
nuoc-mâm | bouteille de 200 ml | 2.90
nước mắm | bouteille de 200 ml | 2.90
sauce huître | bouteille de 255 g | 3.20
sauce hoisin | pot de 240 g | 3.20
sauce teriyaki | bouteille de 250 ml | 3.50
sauce ponzu | bouteille de 250 ml | 5.50
sauce okonomiyaki | bouteille de 300 g | 5.90
sauce tonkatsu | bouteille de 300 ml | 5.50
sauce aigre-douce | bouteille de 250 ml | 2.90
sauce satay | pot de 250 g | 3.50
sauce chili douce | bouteille de 300 ml | 2.90
sauce soja | bouteille de 250 ml | 3.20
sauce soja salée | bouteille de 250 ml | 3.20
sauce soja sucrée | bouteille de 250 ml | 3.20
mirin | bouteille de 300 ml | 4.90
vinaigre de riz | bouteille de 300 ml | 3.50
vinaigre noir | bouteille de 500 ml | 3.50
huile de sésame | bouteille de 250 ml | 4.90
huile de sésame grillé | bouteille de 250 ml | 4.90
pâte de curry | pot de 110 g | 2.90
pâte de curry rouge | pot de 110 g | 2.90
pâte de curry vert | pot de 110 g | 2.90
pâte de curry jaune | pot de 110 g | 2.90
pâte de crevettes | pot de 200 g | 3.50
miso | pot de 300 g | 5.50
miso blanc | pot de 300 g | 5.50
miso rouge | pot de 300 g | 5.50
gochujang | pot de 500 g | 6.90
doenjang | pot de 500 g | 6.50
sambal oelek | pot de 200 g | 3.20
pâte de haricots | pot de 230 g | 3.50
toban djan | pot de 230 g | 3.90
dashi | sachet de 5 doses | 4.90
dashi en poudre | sachet de 50 g | 4.90
bonite séchée | sachet de 25 g | 4.90
katsuobushi | sachet de 25 g | 4.90
furikake | flacon de 45 g | 4.50
togarashi | flacon de 15 g | 3.90
shichimi | flacon de 15 g | 3.90
wasabi | tube de 43 g | 2.90
gingembre mariné | pot de 190 g | 2.90
kecap manis | bouteille de 275 ml | 3.50
sauce soja japonaise | bouteille de 250 ml | 4.20
mayonnaise japonaise | flacon de 300 g | 5.50
kewpie | flacon de 300 g | 5.50
riz jasmin | paquet de 1 kg | 3.50
riz gluant | paquet de 1 kg | 3.50
vermicelles de riz | paquet de 400 g | 2.20
nouilles de riz | paquet de 400 g | 2.50
nouilles | paquet de 400 g | 2.50
nouilles chinoises | paquet de 400 g | 2.50
nouilles aux œufs | paquet de 400 g | 2.50
nouilles udon | paquet de 3 portions | 3.90
udon | paquet de 3 portions | 3.90
soba | paquet de 300 g | 3.90
ramen | paquet de 5 portions | 4.50
nouilles instantanées | paquet de 5 | 3.50
galettes de riz | paquet de 400 g | 2.50
feuilles de riz | paquet de 400 g | 2.50
chapelure panko | sachet de 200 g | 2.90
panko | sachet de 200 g | 2.90
algues nori | paquet de 10 feuilles | 3.90
nori | paquet de 10 feuilles | 3.90
wakamé | sachet de 50 g | 3.50
kombu | sachet de 50 g | 3.90
farine de riz gluant | paquet de 400 g | 2.20
fécule de tapioca | paquet de 400 g | 1.90
perles de tapioca | paquet de 400 g | 2.50
champignons noirs séchés | sachet de 50 g | 2.90
shiitakés séchés | sachet de 50 g | 3.90
lait de coco asiatique | boîte de 400 ml | 1.90
crevettes séchées | sachet de 100 g | 4.50
cacahuètes grillées | sachet de 200 g | 2.20
oignons frits asiatiques | pot de 100 g | 2.50
sucre de palme | pot de 200 g | 2.90
tamarin | bloc de 200 g | 2.50
citronnelle | sachet de 4 tiges | 2.20
feuilles de citron kaffir | sachet de 20 g | 2.50
galanga | morceau de 100 g | 2.50
raviolis japonais | sachet de 20 | 5.50
kimchi | pot de 400 g | 5.50
tofu soyeux | bloc de 300 g | 2.20
tofu ferme | bloc de 400 g | 2.50
radis daikon | 1 pièce | 2.90
pâte de soja | pot de 500 g | 4.90
tomates San Marzano | boîte de 400 g | 3.20
anchois | bocal de 80 g | 4.50
filets d'anchois | bocal de 80 g | 4.50
colatura di alici | flacon de 100 ml | 9.90
pâtes de Gragnano | paquet de 500 g | 3.50
fregola | paquet de 500 g | 3.90
farine 00 | paquet de 1 kg | 2.50
semoule de blé dur | paquet de 1 kg | 2.90
taralli | sachet de 250 g | 3.20
grissini | paquet de 125 g | 2.50
amaretti | sachet de 200 g | 3.90
savoiardi | paquet de 200 g | 2.90
artichauts à l'huile | bocal de 280 g | 4.90
tomates confites | pot de 280 g | 4.50
bottarga | sachet de 40 g râpée | 7.90
pecorino romano | morceau de 200 g | 5.90
parmigiano reggiano | morceau de 200 g | 6.50
guanciale entier | morceau de 300 g | 8.50
papier toilette | paquet de 12 rouleaux | 6.90
essuie-tout | paquet de 4 rouleaux | 4.50
sopalin | paquet de 4 rouleaux | 4.50
mouchoirs | boîte de 120 | 2.20
liquide vaisselle | flacon de 750 ml | 2.50
tablettes lave-vaisselle | boîte de 40 | 8.90
sel lave-vaisselle | paquet de 2 kg | 2.90
liquide de rinçage | flacon de 500 ml | 2.90
lessive | bidon de 1,5 L (30 lavages) | 9.90
adoucissant | bidon de 1,5 L | 3.90
détachant | flacon de 1 L | 5.90
éponges | lot de 3 | 2.20
sacs poubelle | rouleau de 20 × 30 L | 2.90
papier cuisson | rouleau de 8 m | 2.50
papier aluminium | rouleau de 20 m | 2.90
film alimentaire | rouleau de 30 m | 2.20
sacs de congélation | boîte de 20 | 2.90
sacs congélation | boîte de 20 | 2.90
nettoyant multi-usage | flacon de 750 ml | 3.50
vinaigre ménager | bouteille de 1 L | 2.20
javel | bouteille de 1 L | 1.90
cristaux de soude | paquet de 1 kg | 3.50
savon noir | flacon de 1 L | 4.50
nettoyant WC | flacon de 750 ml | 2.90
pastilles WC | lot de 3 | 3.90
désinfectant | flacon de 750 ml | 4.20
lingettes | paquet de 40 | 3.20
gants de ménage | 1 paire | 2.50
piles | lot de 4 AA | 5.90
ampoules | 1 ampoule LED | 4.90
allumettes | boîte de 3 | 1.50
bougies | lot de 10 chauffe-plats | 3.50
dentifrice | tube de 75 ml | 2.90
brosses à dents | lot de 2 | 3.90
fil dentaire | bobine de 50 m | 3.50
bain de bouche | flacon de 500 ml | 4.50
shampoing | flacon de 250 ml | 4.20
après-shampoing | flacon de 200 ml | 4.50
gel douche | flacon de 250 ml | 2.90
savon | 2 pains | 2.50
savon liquide | flacon de 300 ml | 2.50
déodorant | 1 pièce | 4.20
crème hydratante | pot de 200 ml | 6.90
crème solaire | flacon de 200 ml | 12.90
coton | sachet de 80 disques | 1.90
cotons-tiges | boîte de 200 | 1.90
rasoirs | lot de 4 | 6.90
mousse à raser | bombe de 200 ml | 3.50
protections hygiéniques | paquet de 20 | 4.50
tampons | boîte de 16 | 3.90
serviettes hygiéniques | paquet de 14 | 3.50
mouchoirs en papier | boîte de 120 | 2.20
litière | sac de 10 L | 7.90
croquettes | sac de 2 kg | 14.90
croquettes pour chat | sac de 2 kg | 14.90
pâtée | lot de 12 sachets | 7.50
pâtée pour chat | lot de 12 sachets | 7.50
friandises pour chat | sachet de 60 g | 2.50
"""


def _lire():
    prix = {}
    for ligne in _TABLE.strip().splitlines():
        nom, unite, montant = (x.strip() for x in ligne.split("|"))
        prix[nom] = (unite, float(montant))
    return prix


PRIX = _lire()            # {nom du catalogue: (unité type, prix en euros)}


# --- Le coût d'un repas : la part de chaque produit qu'un dîner pour deux utilise --------------
# Sans quantités dans les recettes, une part par rayon : la viande ou le poisson achetés pour le plat
# comptent en entier, un paquet de pâtes ou une sauce d'épicerie pour une petite part.
PART_UTILISEE = {"boucherie": 1.0, "fruits-legumes": 0.5, "boulangerie": 0.5, "frais": 0.35, "surgeles": 0.3,
                 "boissons": 0.3, "epicerie": 0.2, "specialise": 0.15, "hygiene-maison": 0.0}


def _par_cle():
    from catalogue import cle_catalogue
    return {cle_catalogue(nom): valeur for nom, valeur in PRIX.items()}


_PAR_CLE = _par_cle()


def prix_de(nom):
    """(unité type, prix) d'un article, au singulier ou au pluriel ; None hors catalogue."""
    from catalogue import cle_catalogue
    return _PAR_CLE.get(cle_catalogue(nom))


def cout_repas(ingredients, recette=""):
    """Le coût estimé d'un dîner pour deux, en euros : la part utilisée de chaque ingrédient connu.
    Une recette « Pour 4 » (ou plus) est ramenée à deux : le reste fait un autre repas."""
    import re
    from catalogue import chercher
    total = 0.0
    for nom in ingredients:
        prix, rangement = prix_de(nom), chercher(nom)
        if prix and rangement:
            total += prix[1] * PART_UTILISEE.get(rangement[0], 0.2)
    portions = re.match(r"\s*Pour (\d+)", recette or "")
    if portions and int(portions.group(1)) > 2:
        total *= 2 / int(portions.group(1))
    return round(total, 2)
