import os
import sys
import time
import base64
import requests
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from player_site_app.models import Esence_Items_Shop

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    Image = None


# Definice 30 unikátních fantasy rámečků
FRAMES_CATALOG = [
    {
        "name": "Dračí rámeček",
        "slug": "draci_ram",
        "filename": "draci_ram.png",
        "cost": 250,
        "style": "Dračí šupiny, tepaná mosaz a dvě dračí hlavy s planoucíma očima",
        "prompt": (
            "Fantasy RPG ornate circular dragon avatar border frame, crafted from dark oxidized brass "
            "and glowing golden dragon scales, with dragon heads at top and bottom. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows, "
            "no checkerboard, no grid. The frame itself is isolated on solid flat white. Highly detailed 2D fantasy game UI asset."
        ),
        "theme": {"primary": (180, 140, 50), "secondary": (60, 45, 20), "glow": (240, 190, 60), "type": "scales"}
    },
    {
        "name": "Mrazivý rámeček",
        "slug": "mrazivy_ram",
        "filename": "mrazivy_ram.png",
        "cost": 200,
        "style": "Severní stříbro, ledové krystaly, rampouchy a zářící azurové runy",
        "prompt": (
            "Fantasy RPG ornate circular glacial frost avatar border frame, forged from ancient Norse silver "
            "and sharp jagged blue ice crystals, frozen icicles, with glowing icy blizzard cyan mist aura and carved frost runes. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows, "
            "no checkerboard, no grid. The frame itself is isolated on solid flat white. Highly detailed 2D fantasy game UI asset."
        ),
        "theme": {"primary": (130, 200, 240), "secondary": (40, 90, 140), "glow": (180, 230, 255), "type": "crystals"}
    },
    {
        "name": "Plamenný rámeček",
        "slug": "plamenny_ram",
        "filename": "plamenny_ram.png",
        "cost": 220,
        "style": "Sopečná láva, černý obsidián, plamenná koróna a ohnivé runy",
        "prompt": (
            "Fantasy RPG ornate circular molten fire avatar border frame, forged from glowing volcanic magma "
            "and blackened obsidian steel, blazing orange flames licking the outer rim, glowing fire runes. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows, "
            "no checkerboard, no grid. The frame itself is isolated on solid flat white. Highly detailed 2D fantasy game UI asset."
        ),
        "theme": {"primary": (230, 90, 20), "secondary": (70, 20, 10), "glow": (255, 160, 30), "type": "fire"}
    },
    {
        "name": "Nekromantický rámeček",
        "slug": "nekromanticky_ram",
        "filename": "nekromanticky_ram.png",
        "cost": 260,
        "style": "Bělené lebky, prastaré kosti páteře a zelené spektrální plameny duší",
        "prompt": (
            "Fantasy RPG ornate circular necromantic avatar border frame, forged from ancient bleached human skulls, "
            "cracked vertebrae, and aged dark bone with glowing ghostly green ethereal soul flame aura and necromantic runes. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows, "
            "no checkerboard, no grid. The frame itself is isolated on solid flat white. Highly detailed 2D fantasy game UI asset."
        ),
        "theme": {"primary": (180, 175, 150), "secondary": (40, 50, 40), "glow": (50, 220, 120), "type": "skulls"}
    },
    {
        "name": "Nebeský rámeček",
        "slug": "nebesky_ram",
        "filename": "nebesky_ram.png",
        "cost": 280,
        "style": "Andělská sněhobílá peří, svatá sluneční záře a leštěné nebeské zlato",
        "prompt": (
            "Fantasy RPG ornate circular celestial angelic avatar border frame, forged from polished celestial gold "
            "and radiant white angelic feathered wings wrapping around the circular rim, divine golden halo rays and white sapphire gems. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows, "
            "no checkerboard, no grid. The frame itself is isolated on solid flat white. Highly detailed 2D fantasy game UI asset."
        ),
        "theme": {"primary": (240, 200, 80), "secondary": (230, 230, 240), "glow": (255, 235, 160), "type": "wings"}
    },
    {
        "name": "Rytířský rámeček",
        "slug": "rytirsky_ram",
        "filename": "rytirsky_ram.png",
        "cost": 150,
        "style": "Tvrzená damašková ocel, lví znak a stříbrné královské pláty",
        "prompt": (
            "Fantasy RPG ornate circular knightly armor avatar border frame, forged from polished damascus steel plates, "
            "silver heraldic lion reliefs, studded iron rivets, and deep sapphire inlays. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (170, 180, 195), "secondary": (60, 70, 85), "glow": (100, 150, 240), "type": "armor"}
    },
    {
        "name": "Druidský rámeček",
        "slug": "druidsky_ram",
        "filename": "druidsky_ram.png",
        "cost": 180,
        "style": "Prastarý dub, propletené kořeny, břečťan a světélkující lesní mech",
        "prompt": (
            "Fantasy RPG ornate circular druidic nature avatar border frame, woven from ancient living oak wood roots, "
            "ivy vines with dew drops, blooming golden forest acorns, and a soft emerald moss luminescence. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (110, 75, 45), "secondary": (50, 130, 50), "glow": (80, 220, 100), "type": "roots"}
    },
    {
        "name": "Hvězdný rámeček",
        "slug": "hvezdny_ram",
        "filename": "hvezdny_ram.png",
        "cost": 300,
        "style": "Kosmická temná modř, zářící souhvězdí a meteorické zlato",
        "prompt": (
            "Fantasy RPG ornate circular celestial cosmic star avatar border frame, forged from deep midnight blue meteoric iron, "
            "interlocking golden astrological constellations, glowing silver starburst gems, and astral nebula dust. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (50, 60, 140), "secondary": (20, 25, 60), "glow": (130, 180, 255), "type": "stars"}
    },
    {
        "name": "Stínový rámeček",
        "slug": "stinovy_ram",
        "filename": "stinovy_ram.png",
        "cost": 210,
        "style": "Černý kouř stínové říše, temné trny a fialový přízračný opar",
        "prompt": (
            "Fantasy RPG ornate circular Shadowfell dark shadow avatar border frame, composed of twisting smoky black tendrils, "
            "jagged void spikes, and an eerie dark violet ethereal haze with pulsing twilight sigils. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (40, 30, 55), "secondary": (15, 10, 25), "glow": (140, 70, 220), "type": "void"}
    },
    {
        "name": "Krvavý rámeček",
        "slug": "krvavy_ram",
        "filename": "krvavy_ram.png",
        "cost": 240,
        "style": "Gotické černé železo, rubínové kapky a netopýří křídla upírů",
        "prompt": (
            "Fantasy RPG ornate circular vampiric blood avatar border frame, gothic blackened iron forged with sculpted bat wings, "
            "translucent glowing blood rubies, and ornate baroquian filigree with crimson liquid accents. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (160, 20, 30), "secondary": (35, 10, 15), "glow": (220, 40, 50), "type": "ruby"}
    },
    {
        "name": "Bleskový rámeček",
        "slug": "bleskovy_ram",
        "filename": "bleskovy_ram.png",
        "cost": 230,
        "style": "Elektrická bouře, nabitý magnetit a rozvětvené blesky",
        "prompt": (
            "Fantasy RPG ornate circular storm lightning avatar border frame, crafted from dark magnetized blue alloy, "
            "crackling vibrant electric arcs, stormcloud vapors, and charged sapphire capacitors emitting spark filaments. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (80, 150, 230), "secondary": (30, 50, 100), "glow": (140, 220, 255), "type": "lightning"}
    },
    {
        "name": "Podmořský rámeček",
        "slug": "podmorsky_ram",
        "filename": "podmorsky_ram.png",
        "cost": 190,
        "style": "Hlubinné chapadla krakatice, perleť, korály a mořské chaluhy",
        "prompt": (
            "Fantasy RPG ornate circular deep sea ocean avatar border frame, featuring coiled kraken tentacles, "
            "iridescent glowing pearls, bioluminescent turquoise sea flora, and aged bronze with barnacle textures. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (30, 140, 150), "secondary": (15, 60, 75), "glow": (70, 220, 210), "type": "ocean"}
    },
    {
        "name": "Faraonský rámeček",
        "slug": "faraonsky_ram",
        "filename": "faraonsky_ram.png",
        "cost": 250,
        "style": "Starověký egyptský lazurit, ryzí zlato a skarabové slunce",
        "prompt": (
            "Fantasy RPG ornate circular Pharaoh desert avatar border frame, made of pure polished Egyptian gold and royal lapis lazuli, "
            "hieroglyphic engravings, and a winged golden sun scarab crest. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (230, 180, 40), "secondary": (30, 70, 160), "glow": (255, 215, 70), "type": "gold"}
    },
    {
        "name": "Hodinový rámeček",
        "slug": "hodinovy_ram",
        "filename": "hodinovy_ram.png",
        "cost": 170,
        "style": "Steampunková mosazná ozubená kola, ciferníky a bronzové písty",
        "prompt": (
            "Fantasy RPG ornate circular clockwork steampunk avatar border frame, intricate interlocking brass cogs and copper gears, "
            "small mechanical watch hands, pressure gauges, and subtle glowing steam exhausts. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (190, 130, 60), "secondary": (130, 60, 30), "glow": (240, 180, 80), "type": "gears"}
    },
    {
        "name": "Pavoučí rámeček",
        "slug": "pavouci_ram",
        "filename": "pavouci_ram.png",
        "cost": 200,
        "style": "Chitinové nohy pavouka, stříbrná pavučina a jedovaté zelené kapky",
        "prompt": (
            "Fantasy RPG ornate circular arachnid spider avatar border frame, jointed black chitinous spider legs curving into a ring, "
            "delicate silver silk webs, and glowing toxic emerald venom droplets suspended in corners. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (40, 40, 45), "secondary": (20, 20, 25), "glow": (80, 230, 50), "type": "chitin"}
    },
    {
        "name": "Královský rámeček",
        "slug": "kralovsky_ram",
        "filename": "kralovsky_ram.png",
        "cost": 350,
        "style": "Královská koruna, ryzí zlato, sametové polstrování a diamanty",
        "prompt": (
            "Fantasy RPG ornate circular royal monarch avatar border frame, majestic 24k gold filigree crowned with a king's coronet, "
            "deep royal purple velvet underlay, and brilliant cut sparkling diamonds. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (245, 195, 45), "secondary": (90, 20, 90), "glow": (255, 230, 130), "type": "crown"}
    },
    {
        "name": "Magický rámeček",
        "slug": "magicky_ram",
        "filename": "magicky_ram.png",
        "cost": 220,
        "style": "Arkanická levitující písmena, fialová manová aura a křišťály",
        "prompt": (
            "Fantasy RPG ornate circular arcane spellcaster avatar border frame, forged of dark platinum with glowing violet magical glyphs "
            "orbiting in rings, pulsating arcane mana crystals and soft swirling sorcery aura. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (150, 70, 220), "secondary": (50, 20, 90), "glow": (210, 140, 255), "type": "arcane"}
    },
    {
        "name": "Vikingský rámeček",
        "slug": "vikingsky_ram",
        "filename": "vikingsky_ram.png",
        "cost": 160,
        "style": "Borovicové dřevo, kované železné obruče a runy staršího futharku",
        "prompt": (
            "Fantasy RPG ornate circular Viking round shield avatar border frame, dark weathered pine planks, riveted forged iron rim, "
            "carved ancient Elder Futhark runes, and crossed battle axe motives. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (130, 85, 50), "secondary": (80, 85, 90), "glow": (200, 150, 90), "type": "shield"}
    },
    {
        "name": "Hlubinný rámeček",
        "slug": "hlubinny_ram",
        "filename": "hlubinny_ram.png",
        "cost": 290,
        "style": "Eldritch kosmické chapadla, cizí oči prázdnoty a temná fialová hmota",
        "prompt": (
            "Fantasy RPG ornate circular Lovecraftian eldritch void avatar border frame, twisted dark purple flesh tendrils, "
            "several unblinking golden alien eyes embedded in the frame, and a faint shimmering cosmos void abyss. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (80, 30, 100), "secondary": (25, 10, 40), "glow": (170, 70, 220), "type": "eldritch"}
    },
    {
        "name": "Sopečný rámeček",
        "slug": "sopecny_ram",
        "filename": "sopecny_ram.png",
        "cost": 210,
        "style": "Ostré černé sklo obsidiánu s prasklinami plnými tekutého ohně",
        "prompt": (
            "Fantasy RPG ornate circular volcanic obsidian avatar border frame, razor-sharp black volcanic glass shards "
            "threaded with deep cracks of boiling orange-red magma and glowing ember coals. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (30, 25, 30), "secondary": (180, 50, 10), "glow": (255, 100, 20), "type": "obsidian"}
    },
    {
        "name": "Měsíční rámeček",
        "slug": "mesicni_ram",
        "filename": "mesicni_ram.png",
        "cost": 270,
        "style": "Stříbrný měsíční srpek, perleťové bílé květy a hvězdný svit",
        "prompt": (
            "Fantasy RPG ornate circular elven lunar moonlight avatar border frame, sculpted from pale silver moon metal, "
            "delicate white lotus blossoms, luminous star pearls, and a cool silvery-blue celestial shimmer. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (210, 225, 240), "secondary": (120, 140, 170), "glow": (230, 245, 255), "type": "moon"}
    },
    {
        "name": "Barbarský rámeček",
        "slug": "barbarsky_ram",
        "filename": "barbarsky_ram.png",
        "cost": 160,
        "style": "Mamutí kly, hrubá kůže, kožešina a válečné malování kmene",
        "prompt": (
            "Fantasy RPG ornate circular barbarian tribal avatar border frame, bound mammoth ivory tusks, coarse brown leather strapping, "
            "bear fur trimming, and rough red ochre war paint markings. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (190, 175, 145), "secondary": (95, 55, 35), "glow": (180, 50, 30), "type": "tusks"}
    },
    {
        "name": "Mykologický rámeček",
        "slug": "mykologicky_ram",
        "filename": "mykologicky_ram.png",
        "cost": 190,
        "style": "Světélkující fialové houby, spory, mech a vlhká lesní kůra",
        "prompt": (
            "Fantasy RPG ornate circular mushroom underworld avatar border frame, twisted damp subterranean wood roots adorned with "
            "clusters of glowing bioluminescent purple and cyan mushrooms, drifting glowing spore particles. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (60, 45, 40), "secondary": (130, 50, 160), "glow": (60, 210, 200), "type": "mushrooms"}
    },
    {
        "name": "Paladinský rámeček",
        "slug": "paladinsky_ram",
        "filename": "paladinsky_ram.png",
        "cost": 270,
        "style": "Svatá záře slunce, zlatý kříž, čistá ocel a posvátná modlitba",
        "prompt": (
            "Fantasy RPG ornate circular holy paladin avatar border frame, gleaming white and gold crusader steel, embossed sacred scripture, "
            "a radiant sunburst emblem at the crest, and pure warm golden light aura. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (235, 210, 120), "secondary": (190, 195, 205), "glow": (255, 240, 170), "type": "sunburst"}
    },
    {
        "name": "Iluzorní rámeček",
        "slug": "iluzorni_ram",
        "filename": "iluzorni_ram.png",
        "cost": 230,
        "style": "Stříbrné zrcadlové střepy, prismatické lomy duhy a iluze",
        "prompt": (
            "Fantasy RPG ornate circular illusionist mirror avatar border frame, made of shattered crystalline silver mirror shards "
            "refracting iridescent rainbow spectrum flares, floating chrome ribbons and shifting spectral geometry. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (200, 210, 230), "secondary": (130, 140, 170), "glow": (230, 180, 240), "type": "mirror"}
    },
    {
        "name": "Alchymistický rámeček",
        "slug": "alchymisticky_ram",
        "filename": "alchymisticky_ram.png",
        "cost": 200,
        "style": "Měděné trubičky, skleněné baňky s bublající tekutinou a rtuť",
        "prompt": (
            "Fantasy RPG ornate circular alchemist laboratory avatar border frame, coiled copper pipework, miniature glass vials "
            "filled with bubbling glowing emerald and magenta elixirs, brass dials and shimmering mercury drops. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (175, 100, 50), "secondary": (60, 140, 80), "glow": (100, 230, 120), "type": "vials"}
    },
    {
        "name": "Diamantový rámeček",
        "slug": "diamantovy_ram",
        "filename": "diamantovy_ram.png",
        "cost": 400,
        "style": "Broušené diamanty, čistý křišťál a zářivé lomy bílého světla",
        "prompt": (
            "Fantasy RPG ornate circular pure diamond crystal avatar border frame, large precision-faceted clear gemstones, "
            "white gold setting, sparkling prisms reflecting dazzling bright white light rays. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (220, 240, 255), "secondary": (160, 190, 220), "glow": (255, 255, 255), "type": "diamond"}
    },
    {
        "name": "Rámeček Zatmění",
        "slug": "zatmeni_ram",
        "filename": "zatmeni_ram.png",
        "cost": 320,
        "style": "Černé slunce, zlatá sluneční koróna a temná prstencová záře",
        "prompt": (
            "Fantasy RPG ornate circular solar eclipse avatar border frame, representing a total eclipse with a pitch black solar disc, "
            "encircled by brilliant golden plasma flares, dark solar flares, and mystical cosmic rings. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (30, 25, 35), "secondary": (200, 150, 40), "glow": (255, 200, 60), "type": "eclipse"}
    },
    {
        "name": "Písečný rámeček",
        "slug": "pisecny_ram",
        "filename": "pisecny_ram.png",
        "cost": 170,
        "style": "Větrný pískovec, pouštní písek, zářící topazy a jantar",
        "prompt": (
            "Fantasy RPG ornate circular desert sand avatar border frame, weathered golden sandstone carved by desert winds, "
            "inlaid with raw radiant golden topaz crystals, desert dunes motif, and glowing amber dust. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (210, 160, 80), "secondary": (130, 90, 40), "glow": (245, 190, 90), "type": "sand"}
    },
    {
        "name": "Titánský rámeček",
        "slug": "titansky_ram",
        "filename": "titansky_ram.png",
        "cost": 310,
        "style": "Monumentální horská žula, prastaré runy titánů a modrá blesková síla",
        "prompt": (
            "Fantasy RPG ornate circular mountain titan avatar border frame, megalithic carved mountain granite blocks "
            "pulsing with ancient glowing sapphire titan power runes, indestructible primordial stone masonry. "
            "IMPORTANT: The interior center cutout and the entire outer area surrounding the frame "
            "MUST BE completely SOLID FLAT PURE SOLID WHITE (#FFFFFF), perfectly uniform flat solid white with no shadows."
        ),
        "theme": {"primary": (110, 115, 125), "secondary": (50, 55, 65), "glow": (60, 150, 240), "type": "granite"}
    }
]


def convert_image_to_transparent_frame(image_bytes_or_pil):
    """
    Převede obrázek na transparentní RGBA PNG.
    Automaticky vyřízne bílé pozadí zvenku i zevnitř (střed rámečku).
    """
    if Image is None:
        raise RuntimeError("Knihovna Pillow (PIL) není nainstalována.")

    if isinstance(image_bytes_or_pil, (bytes, bytearray)):
        import io
        img = Image.open(io.BytesIO(image_bytes_or_pil)).convert('RGBA')
    else:
        img = image_bytes_or_pil.convert('RGBA')

    width, height = img.size
    pixels = img.load()

    # Vyčištění bílého pozadí s měkkým přechodem (feathering)
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # Pixely velmi blízké čistě bílé (#FFFFFF)
            if r > 240 and g > 240 and b > 240:
                pixels[x, y] = (255, 255, 255, 0)
            elif r > 215 and g > 215 and b > 215:
                # Jemné zjemnění hran
                alpha = int((255 - max(r, g, b)) / 25 * 255)
                pixels[x, y] = (r, g, b, min(a, alpha))

    return img


def generate_procedural_fantasy_frame(frame_meta):
    """
    Vygeneruje procedurální kvalitní fantasy rámeček pomocí Pillow,
    pokud není k dispozici API klíč k Gemini nebo při chybě sítě.
    """
    size = 720
    center = size // 2
    outer_radius = size // 2 - 20
    inner_radius = size // 2 - 95

    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    theme = frame_meta.get("theme", {})
    col_primary = theme.get("primary", (180, 150, 50))
    col_secondary = theme.get("secondary", (60, 45, 30))
    col_glow = theme.get("glow", (240, 200, 80))
    frame_type = theme.get("type", "ornate")

    # 1. Vnější magická aura / záře
    glow_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    for r_offset in range(30, 0, -5):
        alpha_val = int(25 * (1 - r_offset / 30))
        glow_draw.ellipse(
            [center - outer_radius - r_offset, center - outer_radius - r_offset,
             center + outer_radius + r_offset, center + outer_radius + r_offset],
            outline=(*col_glow, alpha_val), width=6
        )
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(8))
    img.paste(glow_img, (0, 0), glow_img)

    # 2. Vnější kovaný okraj rámečku
    draw.ellipse(
        [center - outer_radius, center - outer_radius, center + outer_radius, center + outer_radius],
        outline=(*col_secondary, 255), width=18
    )

    # 3. Hlavní prstenec rámečku
    mid_outer = outer_radius - 10
    mid_inner = inner_radius + 10
    for r in range(mid_inner, mid_outer, 2):
        factor = (r - mid_inner) / max(1, (mid_outer - mid_inner))
        col_r = int(col_secondary[0] + factor * (col_primary[0] - col_secondary[0]))
        col_g = int(col_secondary[1] + factor * (col_primary[1] - col_secondary[1]))
        col_b = int(col_secondary[2] + factor * (col_primary[2] - col_secondary[2]))
        draw.ellipse(
            [center - r, center - r, center + r, center + r],
            outline=(col_r, col_g, col_b, 255), width=3
        )

    # 4. Vnitřní vyřezávaný lem
    draw.ellipse(
        [center - inner_radius, center - inner_radius, center + inner_radius, center + inner_radius],
        outline=(*col_secondary, 255), width=14
    )
    draw.ellipse(
        [center - inner_radius + 4, center - inner_radius + 4, center + inner_radius - 4, center + inner_radius - 4],
        outline=(*col_primary, 255), width=4
    )

    # 5. Ozdobné drahokamy a runové znaky po obvodu (8 bodů: N, NE, E, SE, S, SW, W, NW)
    import math
    for i in range(8):
        angle = i * (math.pi / 4)
        gem_dist = (outer_radius + inner_radius) // 2
        gx = int(center + gem_dist * math.cos(angle))
        gy = int(center + gem_dist * math.sin(angle))
        gem_size = 22 if i % 2 == 0 else 14

        # Kosočtverečný drahokam
        draw.polygon([
            (gx, gy - gem_size),
            (gx + gem_size, gy),
            (gx, gy + gem_size),
            (gx - gem_size, gy)
        ], fill=(*col_glow, 255), outline=(*col_secondary, 255))

        # Lesk na drahokamu
        draw.polygon([
            (gx, gy - gem_size + 4),
            (gx + gem_size - 4, gy),
            (gx, gy),
            (gx - gem_size + 4, gy)
        ], fill=(255, 255, 255, 180))

    # 6. Vrcholový erb / hlava
    crest_y = center - outer_radius - 6
    draw.polygon([
        (center, crest_y - 28),
        (center + 32, crest_y + 14),
        (center, crest_y + 24),
        (center - 32, crest_y + 14)
    ], fill=(*col_primary, 255), outline=(*col_secondary, 255))
    draw.polygon([
        (center, crest_y - 20),
        (center + 20, crest_y + 10),
        (center, crest_y + 18),
        (center - 20, crest_y + 10)
    ], fill=(*col_glow, 255))

    # 7. Spodní spona / pečeť
    bottom_y = center + outer_radius + 6
    draw.polygon([
        (center, bottom_y + 28),
        (center + 32, bottom_y - 14),
        (center, bottom_y - 24),
        (center - 32, bottom_y - 14)
    ], fill=(*col_primary, 255), outline=(*col_secondary, 255))
    draw.polygon([
        (center, bottom_y + 20),
        (center + 20, bottom_y - 10),
        (center, bottom_y - 18),
        (center - 20, bottom_y - 10)
    ], fill=(*col_glow, 255))

    # Ujistíme se, že střed je 100% průhledný kruh
    mask_inner = Image.new('L', (size, size), 255)
    mask_draw = ImageDraw.Draw(mask_inner)
    mask_draw.ellipse(
        [center - inner_radius + 8, center - inner_radius + 8,
         center + inner_radius - 8, center + inner_radius - 8],
        fill=0
    )
    img.putalpha(Image.composite(img.getchannel('A'), mask_inner, mask_inner))

    return img


class Command(BaseCommand):
    help = "Generuje 30 unikátních fantasy avatar rámečků pomocí Google Gemini API a registruje je do Esence Shopu."

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            default=None,
            help='Google Gemini API klíč (pokud není zadán, čte se z proměnné prostředí GEMINI_API_KEY nebo .env).'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Vynutí přegenerování všech rámečků, i když už na disku existují.'
        )
        parser.add_argument(
            '--procedural',
            action='store_true',
            help='Použije lokální procedurální fantasy generátor bez volání externího Gemini API.'
        )
        parser.add_argument(
            '--sync-db-only',
            action='store_true',
            help='Pouze zaregistruje existující PNG rámečky z media/esence_items/ do databáze Esence_Items_Shop.'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=30,
            help='Počet rámečků ke zpracování (výchozí 30).'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("═══════════════════════════════════════════════════════════"))
        self.stdout.write(self.style.MIGRATE_HEADING("  DnD Atarax: Generátor 30 unikátních avatar rámečků       "))
        self.stdout.write(self.style.MIGRATE_HEADING("═══════════════════════════════════════════════════════════"))

        media_dir = Path(settings.MEDIA_ROOT) / "esence_items"
        media_dir.mkdir(parents=True, exist_ok=True)

        if Image is None:
            self.stderr.write(self.style.ERROR("Knihovna Pillow není nainstalována. Spusťte: pip install pillow"))
            return

        # Zjištění API klíče
        api_key = options.get('api_key') or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            # Pokusíme se načíst z .env
            env_path = Path(settings.BASE_DIR) / '.env'
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('GEMINI_API_KEY=') or line.startswith('GOOGLE_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break

        force = options.get('force', False)
        procedural = options.get('procedural', False)
        sync_only = options.get('sync_db_only', False)
        limit = options.get('limit', 30)

        catalog_to_process = FRAMES_CATALOG[:limit]
        self.stdout.write(f"Celkem rámečků v katalogu: {len(catalog_to_process)}")
        self.stdout.write(f"Cílová složka: {media_dir}")

        if not api_key and not procedural and not sync_only:
            self.stdout.write(self.style.WARNING(
                "\n[i] UPOZORNĚNÍ: Nebyl nalezen žádný GEMINI_API_KEY.\n"
                "    Rámečky, které již máte vygenerované v media/esence_items/, budou zachovány a zaregistrovány do DB.\n"
                "    Pro chybějící rámečky se automaticky použije vestavěný fantasy generátor.\n"
                "    (Pokud chcete použít přímo Gemini Imagen, předejte klíč: python manage.py generate_frames --api-key VAŠE_KEY)\n"
            ))

        generated_count = 0
        db_created_count = 0
        db_updated_count = 0

        for idx, item in enumerate(catalog_to_process, 1):
            name = item["name"]
            filename = item["filename"]
            cost = item["cost"]
            prompt = item["prompt"]
            dest_file = media_dir / filename

            self.stdout.write(f"\n[{idx}/{len(catalog_to_process)}] {name} ({filename}) - {cost} TE")

            # 1. Získání nebo vytvoření obrázku
            if dest_file.exists() and not force:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Soubor již existuje na disku: {filename}"))
            elif sync_only:
                self.stdout.write(self.style.WARNING(f"  ⚠ Režim sync-only: Soubor {filename} na disku chybí."))
            else:
                # Generování přes Gemini API nebo Procedurální generátor
                img_obj = None

                if api_key and not procedural:
                    self.stdout.write(f"  → Odesílám prompt na Gemini Imagen API...")
                    img_obj = self.call_gemini_imagen_api(api_key, prompt)
                    if img_obj:
                        self.stdout.write(self.style.SUCCESS("  ✓ Obrázek z Gemini úspěšně stažen a vyčištěn na průhledné PNG"))
                    else:
                        self.stdout.write(self.style.WARNING("  ⚠ Gemini API vrátilo chybu. Používám záložní generátor..."))
                        img_obj = generate_procedural_fantasy_frame(item)
                else:
                    self.stdout.write(f"  → Vytvářím procedurální fantasy rámeček...")
                    img_obj = generate_procedural_fantasy_frame(item)

                if img_obj:
                    img_obj.save(dest_file, "PNG")
                    generated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Uloženo do: {dest_file}"))

            # 2. Synchronizace se záznamem v databázi Esence_Items_Shop
            db_item, created = Esence_Items_Shop.objects.update_or_create(
                name=name,
                defaults={
                    "category": "borders",
                    "image": f"esence_items/{filename}",
                    "cost": cost
                }
            )

            if created:
                db_created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Vytvořen nový předmět v Esence Shopu (ID: {db_item.id})"))
            else:
                db_updated_count += 1
                self.stdout.write(f"  ✓ Aktualizován existující předmět v Esence Shopu (ID: {db_item.id})")

        self.stdout.write(self.style.MIGRATE_HEADING("\n═══════════════════════════════════════════════════════════"))
        self.stdout.write(self.style.SUCCESS(f"Hotovo! Nově vygenerováno souborů: {generated_count}"))
        self.stdout.write(self.style.SUCCESS(f"Předmětů v Esence Shopu: vytvořeno {db_created_count}, aktualizováno {db_updated_count}"))
        self.stdout.write(self.style.MIGRATE_HEADING("═══════════════════════════════════════════════════════════"))

    def call_gemini_imagen_api(self, api_key, prompt, retries=3):
        """
        Zavolá REST koncový bod Google Gemini Imagen 3 s automatickým opakováním při chybě.
        """
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "outputMimeType": "image/jpeg"
            }
        }
        headers = {"Content-Type": "application/json"}

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(endpoint, json=payload, headers=headers, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    predictions = data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        raw_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                        return convert_image_to_transparent_frame(raw_bytes)
                elif response.status_code == 429:
                    wait_time = attempt * 5
                    self.stdout.write(self.style.WARNING(f"  [429 Rate Limit] Čekám {wait_time}s před pokusem {attempt + 1}..."))
                    time.sleep(wait_time)
                else:
                    self.stdout.write(self.style.ERROR(f"  Chyba API ({response.status_code}): {response.text[:200]}"))
                    time.sleep(2)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Síťová chyba: {e}"))
                time.sleep(2)

        return None
