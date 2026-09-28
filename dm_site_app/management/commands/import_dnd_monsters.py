import time
import requests
from django.core.management.base import BaseCommand
from dm_site_app.models import CompendiumMonster

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


class MonsterTranslator:
    """
    Překladatel pro DnD 5e nestvůry:
    - Bohatý slovník oficiální české terminologie (velikosti, typy, přesvědčení, dovednosti,
      typy zranění, stavy, smysly a známé nestvůry) => stovky ušetřených dotazů na API.
    - Sdružování všech dynamických textů jedné nestvůry (jméno, akce, schopnosti) do 1 jediného dotazu.
    - Automatické čekání a retry při rate limitu (HTTP 429).
    """

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout
        self.style = style
        self.cache = {}
        self.api_calls_count = 0

        # 1. Velikosti nestvůr
        self.sizes = {
            'tiny': 'Drobná',
            'small': 'Malá',
            'medium': 'Střední',
            'large': 'Velká',
            'huge': 'Obrovská',
            'gargantuan': 'Gigantická',
        }

        # 2. Typy nestvůr
        self.types = {
            'aberration': 'Obluda',
            'beast': 'Zvíře',
            'celestial': 'Nebešťan',
            'construct': 'Výtvor',
            'dragon': 'Drak',
            'elemental': 'Elementál',
            'fey': 'Víla',
            'fiend': 'Běs',
            'giant': 'Obr',
            'humanoid': 'Humanoid',
            'monstrosity': 'Zrůda',
            'ooze': 'Sliz',
            'plant': 'Rostlina',
            'undead': 'Nemrtvý',
        }

        # 3. Přesvědčení
        self.alignments = {
            'lawful good': 'Zákonně dobré',
            'neutral good': 'Neutrálně dobré',
            'chaotic good': 'Zmateně dobré',
            'lawful neutral': 'Zákonně neutrální',
            'neutral': 'Neutrální',
            'true neutral': 'Pravdivě neutrální',
            'chaotic neutral': 'Zmateně neutrální',
            'lawful evil': 'Zákonně zlé',
            'neutral evil': 'Neutrálně zlé',
            'chaotic evil': 'Zmateně zlé',
            'unaligned': 'Bez přesvědčení',
            'any alignment': 'Jakékoli přesvědčení',
            'any non-good alignment': 'Jakékoli nedobré přesvědčení',
            'any non-lawful alignment': 'Jakékoli nezákonné přesvědčení',
            'any chaotic alignment': 'Jakékoli zmatené přesvědčení',
            'any evil alignment': 'Jakékoli zlé přesvědčení',
        }

        # 4. Dovednosti (Skills)
        self.skills = {
            'acrobatics': 'Akrobacie',
            'animal handling': 'Ovládání zvířat',
            'arcana': 'Mystika',
            'athletics': 'Atletika',
            'deception': 'Klamání',
            'history': 'Historie',
            'insight': 'Vhled',
            'intimidation': 'Zastrašování',
            'investigation': 'Pátrání',
            'medicine': 'Lékařství',
            'nature': 'Příroda',
            'perception': 'Vnímání',
            'performance': 'Vystupování',
            'persuasion': 'Přesvědčování',
            'religion': 'Náboženství',
            'sleight of hand': 'Hbitost rukou',
            'stealth': 'Nenápadnost',
            'survival': 'Přežití',
        }

        # 5. Typy zranění
        self.damage_types = {
            'acid': 'Kyselinové',
            'bludgeoning': 'Drtivé',
            'cold': 'Chladové',
            'fire': 'Ohnivé',
            'force': 'Silové',
            'lightning': 'Bleskové',
            'necrotic': 'Nekrotické',
            'piercing': 'Bodné',
            'poison': 'Jedové',
            'psychic': 'Psychické',
            'radiant': 'Zářivé',
            'slashing': 'Sečné',
            'thunder': 'Hromové',
        }

        # 6. Stavy (Conditions)
        self.conditions = {
            'blinded': 'Oslepení',
            'charmed': 'Zmámení',
            'deafened': 'Ohluchnutí',
            'exhaustion': 'Vyčerpání',
            'frightened': 'Vystrašení',
            'grappled': 'Uchopení',
            'incapacitated': 'Neschopnost akce',
            'invisible': 'Neviditelnost',
            'paralyzed': 'Ochromení',
            'petrified': 'Zkamenění',
            'poisoned': 'Otrávení',
            'prone': 'Sražení k zemi',
            'restrained': 'Zadržení',
            'stunned': 'Omráčení',
            'unconscious': 'Bezvědomí',
        }

        # 7. Smysly a rychlosti
        self.senses_map = {
            'darkvision': 'vidění ve tmě',
            'blindsight': 'mimosmyslové vidění',
            'tremorsense': 'vnímání otřesů',
            'truesight': 'pravdivé vidění',
            'passive_perception': 'pasivní Vnímání',
        }
        self.speed_map = {
            'walk': 'chůze',
            'swim': 'plavání',
            'fly': 'létání',
            'burrow': 'hrabání',
            'climb': 'šplhání',
            'hover': 'vznášení',
        }

        # 8. Známé nestvůry podle oficiálního překladového klíče DnD 5e
        self.monster_names = {
            'aboleth': 'Aboleth',
            'acolyte': 'Akolyta',
            'adult black dragon': 'Dospělý černý drak',
            'adult blue dragon': 'Dospělý modrý drak',
            'adult brass dragon': 'Dospělý mosazný drak',
            'adult bronze dragon': 'Dospělý bronzový drak',
            'adult copper dragon': 'Dospělý měděný drak',
            'adult gold dragon': 'Dospělý zlatý drak',
            'adult green dragon': 'Dospělý zelený drak',
            'adult red dragon': 'Dospělý červený drak',
            'adult silver dragon': 'Dospělý stříbrný drak',
            'adult white dragon': 'Dospělý bílý drak',
            'ancient black dragon': 'Prastarý černý drak',
            'ancient blue dragon': 'Prastarý modrý drak',
            'ancient brass dragon': 'Prastarý mosazný drak',
            'ancient bronze dragon': 'Prastarý bronzový drak',
            'ancient copper dragon': 'Prastarý měděný drak',
            'ancient gold dragon': 'Prastarý zlatý drak',
            'ancient green dragon': 'Prastarý zelený drak',
            'ancient red dragon': 'Prastarý červený drak',
            'ancient silver dragon': 'Prastarý stříbrný drak',
            'ancient white dragon': 'Prastarý bílý drak',
            'young black dragon': 'Mladý černý drak',
            'young blue dragon': 'Mladý modrý drak',
            'young brass dragon': 'Mladý mosazný drak',
            'young bronze dragon': 'Mladý bronzový drak',
            'young copper dragon': 'Mladý měděný drak',
            'young gold dragon': 'Mladý zlatý drak',
            'young green dragon': 'Mladý zelený drak',
            'young red dragon': 'Mladý červený drak',
            'young silver dragon': 'Mladý stříbrný drak',
            'young white dragon': 'Mladý bílý drak',
            'black dragon wyrmling': 'Dráče černého draka',
            'blue dragon wyrmling': 'Dráče modrého draka',
            'green dragon wyrmling': 'Dráče zeleného draka',
            'red dragon wyrmling': 'Dráče červeného draka',
            'white dragon wyrmling': 'Dráče bílého draka',
            'animated armor': 'Oživená zbroj',
            'ankheg': 'Ankheg',
            'ape': 'Opice',
            'archmage': 'Arcimág',
            'assassin': 'Vrah',
            'awakened shrub': 'Procitlý keř',
            'awakened tree': 'Procitlý strom',
            'baboon': 'Pavián',
            'badger': 'Jezevec',
            'balor': 'Balor',
            'bandit': 'Bandita',
            'bandit captain': 'Kapitán banditů',
            'basilisk': 'Bazilišek',
            'bat': 'Netopýr',
            'bearded devil': 'Vousatý ďábel',
            'behir': 'Behir',
            'berserker': 'Berserk',
            'black bear': 'Černý medvěd',
            'blink dog': 'Mžikový pes',
            'blood hawk': 'Krvavý jestřáb',
            'boar': 'Divočák',
            'bone devil': 'Kostěný ďábel',
            'brown bear': 'Hnědý medvěd',
            'bugbear': 'Skřetobor',
            'bulette': 'Buleta',
            'camel': 'Velbloud',
            'cat': 'Kočka',
            'centaur': 'Kentaur',
            'chimera': 'Chiméra',
            'clay golem': 'Hliněný golem',
            'cloaker': 'Pláštník',
            'cloud giant': 'Oblačný obr',
            'cockatrice': 'Kokatris',
            'commoner': 'Prostý občan',
            'constrictor snake': 'Hroznýš',
            'couatl': 'Kuatl',
            'crab': 'Krab',
            'crocodile': 'Krokodýl',
            'cult fanatic': 'Kultovní fanatik',
            'cultist': 'Kultista',
            'darkmantle': 'Temnoplášť',
            'death dog': 'Smrtící pes',
            'deer': 'Jelen',
            'deva': 'Déva',
            'dire wolf': 'Děsivý vlk',
            'djinni': 'Džin',
            'doppelganger': 'Dvojník',
            'draft horse': 'Tažný kůň',
            'dragon turtle': 'Dračí želva',
            'drow': 'Drow',
            'druid': 'Druid',
            'dryad': 'Dryáda',
            'duergar': 'Duergar',
            'dust mephit': 'Prachový mefit',
            'eagle': 'Orel',
            'efreeti': 'Ifrít',
            'elephant': 'Slon',
            'elk': 'Los',
            'ettercap': 'Pavoučí muž (Ettercap)',
            'ettin': 'Ettin',
            'fire elemental': 'Ohnivý elementál',
            'fire giant': 'Ohnivý obr',
            'flesh golem': 'Golem z masa',
            'flying snake': 'Létající had',
            'flying sword': 'Létající meč',
            'frog': 'Žába',
            'frost giant': 'Mrazivý obr',
            'gargoyle': 'Chrlič',
            'gelatinous cube': 'Rosolovitá krychle',
            'ghast': 'Gast',
            'ghost': 'Duch',
            'ghoul': 'Ghúl',
            'giant ape': 'Obří lidoop',
            'giant badger': 'Obří jezevec',
            'giant bat': 'Obří netopýr',
            'giant boar': 'Obří kanec',
            'giant centipede': 'Obří stonožka',
            'giant constrictor snake': 'Obří hroznýš',
            'giant crab': 'Obří krab',
            'giant crocodile': 'Obří krokodýl',
            'giant eagle': 'Obří orel',
            'giant elk': 'Obří jelen',
            'giant fire beetle': 'Obří světluška',
            'giant frog': 'Obří žába',
            'giant goat': 'Obří koza',
            'giant hyena': 'Obří hyena',
            'giant lizard': 'Obří ještěr',
            'giant octopus': 'Obří chobotnice',
            'giant owl': 'Obří sova',
            'giant poisonous snake': 'Obří jedovatý had',
            'giant rat': 'Obří krysa',
            'giant scorpion': 'Obří štír',
            'giant seahorse': 'Obří mořský koník',
            'giant shark': 'Obří žralok',
            'giant spider': 'Obří pavouk',
            'giant toad': 'Obří ropucha',
            'giant vulture': 'Obří sup',
            'giant wasp': 'Obří vosa',
            'giant weasel': 'Obří lasička',
            'giant wolf spider': 'Obří slíďák',
            'gibbering mouther': 'Blábolící tlama',
            'glabrezu': 'Glabrezu',
            'gladiator': 'Gladiátor',
            'gnoll': 'Gnoll',
            'goat': 'Koza',
            'goblin': 'Goblin',
            'gorgon': 'Gorgona',
            'gray ooze': 'Šedý sliz',
            'green hag': 'Zelená ježibaba',
            'grick': 'Grik',
            'griffon': 'Gryf',
            'grimlock': 'Grimlok',
            'guard': 'Strážný',
            'guardian naga': 'Nága strážkyně',
            'harpy': 'Harpyje',
            'hawk': 'Jestřáb',
            'hell hound': 'Pekelný pes',
            'hezrou': 'Hezrou',
            'hill giant': 'Horský obr',
            'hippogriff': 'Hypogryf',
            'hobgoblin': 'Hobgoblin',
            'homunculus': 'Homunkulus',
            'horned devil': 'Rohatý ďábel',
            'hunter shark': 'Lovící žralok',
            'hydra': 'Hydra',
            'hyena': 'Hyena',
            'ice devil': 'Ledový ďábel',
            'ice mephit': 'Ledový mefit',
            'imp': 'Rarášek (Imp)',
            'invisible stalker': 'Neviditelný stopař',
            'iron golem': 'Železný golem',
            'jackal': 'Šakal',
            'killer whale': 'Kosatka',
            'knight': 'Rytíř',
            'kobold': 'Kobold',
            'kraken': 'Kraken',
            'lamia': 'Lamia',
            'lemure': 'Lemur (Běs)',
            'lich': 'Lich',
            'lion': 'Lev',
            'lizard': 'Ještěrka',
            'lizardfolk': 'Ještěrec',
            'mage': 'Mág',
            'magma mephit': 'Magmatický mefit',
            'magmin': 'Magmín',
            'mammoth': 'Mamut',
            'manticore': 'Mantichora',
            'marilith': 'Marilit',
            'mastiff': 'Mastif',
            'medusa': 'Medúza',
            'merfolk': 'Mořský lid',
            'merrow': 'Merrow',
            'mimic': 'Mimik',
            'minotaur': 'Minotaurus',
            'minotaur skeleton': 'Kostlivec minotaura',
            'mud mephit': 'Bahnitý mefit',
            'mummy': 'Mumie',
            'mummy lord': 'Mumifikovaný pán',
            'nalfeshnee': 'Nalfeshnee',
            'night hag': 'Noční ježibaba',
            'nightmare': 'Noční můra (Oř)',
            'noble': 'Šlechtic',
            'nothic': 'Notik',
            'ochre jelly': 'Okrový rosol',
            'octopus': 'Chobotnice',
            'ogre': 'Zlobr',
            'ogre zombie': 'Zombie zlobra',
            'oni': 'Oni (Lidožrout)',
            'orc': 'Ork',
            'orog': 'Orog',
            'owl': 'Sova',
            'owlbear': 'Sovomedvěd',
            'panther': 'Panter',
            'pegasus': 'Pegas',
            'phase spider': 'Fázový pavouk',
            'pit fiend': 'Propastný běs',
            'planetar': 'Planetar',
            'plesiosaurus': 'Plesiosaurus',
            'poisonous snake': 'Jedovatý had',
            'polar bear': 'Polární medvěd',
            'pony': 'Pony',
            'priest': 'Kněz',
            'pseudodragon': 'Pseudodrak',
            'purple worm': 'Purpurový červ',
            'quasit': 'Kvazit',
            'quipper': 'Kousavec (Ryba)',
            'rakshasa': 'Rakšasa',
            'rat': 'Krysa',
            'raven': 'Krkavec',
            'reef shark': 'Útesový žralok',
            'remorhaz': 'Remorhaz',
            'rhinoceros': 'Nosorožec',
            'riding horse': 'Jezdecký kůň',
            'roc': 'Pták Noh (Roc)',
            'roper': 'Lanař (Roper)',
            'rust monster': 'Rzivec',
            'saber-toothed tiger': 'Šavlozubý tygr',
            'sahuagin': 'Sahuagin',
            'salamander': 'Salamandr',
            'satyr': 'Satyr',
            'scorpion': 'Štír',
            'scout': 'Průzkumník',
            'sea hag': 'Mořská ježibaba',
            'sea horse': 'Mořský koník',
            'shadow': 'Stín',
            'shambling mound': 'Pajdavá kupa',
            'shield guardian': 'Štítový strážce',
            'skeleton': 'Kostlivec',
            'smoke mephit': 'Kouřový mefit',
            'solar': 'Solar',
            'specter': 'Přízrak',
            'spy': 'Špeh',
            'steam mephit': 'Parní mefit',
            'stirge': 'Stirga',
            'stone giant': 'Kamenný obr',
            'stone golem': 'Kamenný golem',
            'storm giant': 'Bouřný obr',
            'succubus/incubus': 'Sukuba / Inkubus',
            'swarm of bats': 'Hejno netopýrů',
            'swarm of insects': 'Roj hmyzu',
            'swarm of poisonous snakes': 'Klubko jedovatých hadů',
            'swarm of rats': 'Hejno krys',
            'swarm of ravens': 'Hejno krkavců',
            'tarrasque': 'Tarrasque',
            'thug': 'Hrdlořez',
            'tiger': 'Tygr',
            'treant': 'Stromovec',
            'tribal warrior': 'Kmenový válečník',
            'triceratops': 'Triceratops',
            'troll': 'Trol',
            'tyrannosaurus rex': 'Tyranosaurus Rex',
            'unicorn': 'Jednorožec',
            'vampire': 'Upír',
            'vampire spawn': 'Upíří zplozenec',
            'veteran': 'Veterán',
            'vine blight': 'Úponková zhouba',
            'vrock': 'Vrock',
            'vulture': 'Sup',
            'warhorse': 'Bojový kůň',
            'warhorse skeleton': 'Kostlivec bojového koně',
            'water elemental': 'Vodní elementál',
            'weasel': 'Lasička',
            'werebear': 'Medvědodlak',
            'wereboar': 'Kancodlak',
            'wererat': 'Krysodlak',
            'weretiger': 'Tygrodlak',
            'werewolf': 'Vlkodlak',
            'white dragon': 'Bílý drak',
            'wight': 'Mohylový duch (Wight)',
            'will-o\'-wisp': 'Bludička',
            'winter wolf': 'Zimní vlk',
            'wolf': 'Vlk',
            'worg': 'Varg',
            'wraith': 'Přízrak (Wraith)',
            'wyvern': 'Wyverna',
            'xorn': 'Xorn',
            'yeti': 'Yeti',
            'zombie': 'Zombie',
        }

    def _call_google_api(self, text: str) -> str:
        self.api_calls_count += 1
        url = 'https://translate.googleapis.com/translate_a/single'
        params = {'client': 'gtx', 'sl': 'en', 'tl': 'cs', 'dt': 't', 'q': text}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            return ''.join([part[0] for part in resp.json()[0] if part and part[0]])
        elif resp.status_code == 429:
            raise requests.exceptions.HTTPError("429 Too Many Requests", response=resp)
        else:
            resp.raise_for_status()

    def translate_with_retry(self, text: str, max_retries: int = 3) -> str:
        if not text or not text.strip():
            return ""

        for attempt in range(max_retries):
            try:
                try:
                    return self._call_google_api(text)
                except Exception as api_err:
                    if "429" in str(api_err):
                        raise
                    if GoogleTranslator:
                        t = GoogleTranslator(source='en', target='cs')
                        self.api_calls_count += 1
                        return t.translate(text)
                    raise api_err
            except Exception as e:
                is_rate_limit = "429" in str(e)
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1) if is_rate_limit else 2
                    msg = f"  [API prodleva/limit] Čekám {wait_time} s před opakováním ({attempt + 1}/{max_retries})..."
                    if self.stdout and self.style:
                        self.stdout.write(self.style.WARNING(msg))
                    else:
                        print(msg)
                    time.sleep(wait_time)
                else:
                    msg = f"  [Chyba] Překlad selhal po {max_retries} pokusech: {e}. Ponechávám originál."
                    if self.stdout and self.style:
                        self.stdout.write(self.style.ERROR(msg))
                    else:
                        print(msg)
                    return text

    def translate_name(self, name_en: str) -> str:
        if not name_en:
            return ""
        clean = name_en.strip().lower()
        if clean in self.monster_names:
            return self.monster_names[clean]
        if name_en in self.cache:
            return self.cache[name_en]
        res = self.translate_with_retry(name_en)
        self.cache[name_en] = res
        return res

    def translate_size(self, size_en: str) -> str:
        return self.sizes.get((size_en or '').lower(), size_en or '')

    def translate_type(self, type_en: str) -> str:
        return self.types.get((type_en or '').lower(), type_en or '')

    def translate_alignment(self, align_en: str) -> str:
        return self.alignments.get((align_en or '').lower(), align_en or '')

    def translate_damage_list(self, damage_items) -> str:
        results = []
        for item in damage_items:
            name = item.get('name') if isinstance(item, dict) else str(item)
            cz = self.damage_types.get(name.lower(), name)
            results.append(cz)
        return ", ".join(results)

    def translate_condition_list(self, cond_items) -> str:
        results = []
        for item in cond_items:
            name = item.get('name') if isinstance(item, dict) else str(item)
            cz = self.conditions.get(name.lower(), name)
            results.append(cz)
        return ", ".join(results)

    def translate_actions_batch(self, items_to_translate: list) -> list:
        """
        Přeloží seznam textových bloků (např. schopnosti a akce) najednou přes jediný HTTP dotaz.
        """
        if not items_to_translate:
            return []

        delimiter = "\n|||\n"
        combined = delimiter.join(items_to_translate)

        # Pokud je text příliš dlouhý, rozdělit (Google limit ~5000 znaků)
        if len(combined) > 4000:
            half = len(items_to_translate) // 2
            part1 = self.translate_actions_batch(items_to_translate[:half])
            part2 = self.translate_actions_batch(items_to_translate[half:])
            return part1 + part2

        translated_combined = self.translate_with_retry(combined)

        if "|||" in translated_combined:
            parts = [p.strip() for p in translated_combined.split("|||")]
            if len(parts) == len(items_to_translate):
                return parts

        # Fallback pokud oddělovač nebyl zachován
        results = []
        for item in items_to_translate:
            results.append(self.translate_with_retry(item))
        return results


class Command(BaseCommand):
    help = 'Stáhne nestvůry z DnD 5e API, přeloží je s využitím oficiálního klíče a uloží do databáze'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Omezit počet importovaných nestvůr (např. --limit 10 pro rychlý test). Výchozí: všechny.',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.8,
            help='Prodleva mezi nestvůrami v sekundách (výchozí: 0.8 s pro naprosté bezpečí vůči limitům).',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Aktualizovat i nestvůry, které již v databázi existují.',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        delay = options.get('delay', 0.8)
        update_existing = options.get('update', False)

        translator = MonsterTranslator(stdout=self.stdout, style=self.style)
        base_url = "https://www.dnd5eapi.co"

        self.stdout.write("Stahuji hlavní seznam nestvůr z API...")
        try:
            response = requests.get(f"{base_url}/api/monsters", timeout=15)
            response.raise_for_status()
            monsters_list = response.json().get('results', [])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Chyba při stahování seznamu nestvůr: {e}"))
            return

        total_available = len(monsters_list)
        if limit:
            monsters_to_process = monsters_list[:limit]
            self.stdout.write(f"Nalezeno {total_available} nestvůr, zpracuji prvních {len(monsters_to_process)} (--limit {limit}).")
        else:
            monsters_to_process = monsters_list
            self.stdout.write(f"Nalezeno celkem {total_available} nestvůr k importu.")

        imported_count = 0
        skipped_count = 0

        for i, monster_ref in enumerate(monsters_to_process, start=1):
            monster_url = f"{base_url}{monster_ref['url']}"

            if delay > 0 and i > 1:
                time.sleep(delay)

            try:
                monster_data = requests.get(monster_url, timeout=15).json()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Chyba při stahování {monster_url}: {e}"))
                continue

            index = monster_data.get('index')
            name_en = monster_data.get('name', '')

            # Kontrola existence v databázi
            monster_exists = CompendiumMonster.objects.filter(api_index=index).exists()
            if monster_exists and not update_existing:
                self.stdout.write(self.style.WARNING(f"[{i}/{len(monsters_to_process)}] Nestvůra '{name_en}' už existuje, přeskakuji."))
                skipped_count += 1
                continue

            # 1. Základní typologie a zařazení (překlad ze slovníku)
            size_cz = translator.translate_size(monster_data.get('size'))
            type_cz = translator.translate_type(monster_data.get('type'))
            subtype = monster_data.get('subtype') or ''
            alignment_cz = translator.translate_alignment(monster_data.get('alignment'))

            # 2. Bojové statistiky a životy
            ac_list = monster_data.get('armor_class', [])
            if ac_list and isinstance(ac_list, list):
                ac_val = ac_list[0].get('value', 10)
                ac_type = ac_list[0].get('type', '')
                armor_items = [a.get('name') for a in ac_list[0].get('armor', []) if a.get('name')]
                if armor_items:
                    ac_desc = ", ".join(armor_items)
                elif ac_type:
                    ac_desc = ac_type
                else:
                    ac_desc = ""
            else:
                ac_val = 10
                ac_desc = ""

            hit_points = monster_data.get('hit_points', 0)
            hit_dice = monster_data.get('hit_dice', '')

            # Rychlost (speed)
            speed_dict = monster_data.get('speed', {})
            speed_parts = []
            for k, v in speed_dict.items():
                v_str = str(v).replace('ft.', 'stop')
                k_cz = translator.speed_map.get(k, k)
                speed_parts.append(f"{k_cz} {v_str}")
            speed_str = ", ".join(speed_parts) if speed_parts else "0 stop"

            # 3. Záchranné hody a dovednosti
            saving_throws = []
            skills = []
            stat_abbr_map = {
                'STR': 'SIL', 'DEX': 'OBR', 'CON': 'ODL',
                'INT': 'INT', 'WIS': 'MDR', 'CHA': 'CHA'
            }
            for p in monster_data.get('proficiencies', []):
                prof_name = p.get('proficiency', {}).get('name', '')
                val = p.get('value', 0)
                sign = f"+{val}" if val >= 0 else str(val)
                if prof_name.startswith('Saving Throw: '):
                    stat = prof_name.replace('Saving Throw: ', '').strip()
                    stat_cz = stat_abbr_map.get(stat, stat)
                    saving_throws.append(f"{stat_cz} {sign}")
                elif prof_name.startswith('Skill: '):
                    skill_name = prof_name.replace('Skill: ', '').strip()
                    skill_cz = translator.skills.get(skill_name.lower(), skill_name)
                    skills.append(f"{skill_cz} {sign}")

            saving_throws_str = ", ".join(saving_throws)
            skills_str = ", ".join(skills)

            # 4. Zranitelnosti, odolnosti, imunity a smysly
            vuln_str = translator.translate_damage_list(monster_data.get('damage_vulnerabilities', []))
            resist_str = translator.translate_damage_list(monster_data.get('damage_resistances', []))
            dmg_imm_str = translator.translate_damage_list(monster_data.get('damage_immunities', []))
            cond_imm_str = translator.translate_condition_list(monster_data.get('condition_immunities', []))

            senses_dict = monster_data.get('senses', {})
            senses_parts = []
            for k, v in senses_dict.items():
                cz_k = translator.senses_map.get(k, k.replace('_', ' '))
                v_str = str(v).replace('ft.', 'stop')
                senses_parts.append(f"{cz_k} {v_str}")
            senses_str = ", ".join(senses_parts)

            languages_str = monster_data.get('languages', '')

            # 5. Nebezpečnost
            cr = float(monster_data.get('challenge_rating', 0))
            xp = monster_data.get('xp', 0)
            prof_bonus = monster_data.get('proficiency_bonus', 2)

            # 6. Sestavení bloků pro hromadný překlad schopností a akcí
            name_cz = translator.monster_names.get(name_en.lower())
            dynamic_blocks = []
            block_mapping = []  # ('name', None) nebo ('special', idx) nebo ('action', idx)

            if not name_cz:
                dynamic_blocks.append(name_en)
                block_mapping.append(('name', 0))

            spec_abilities = monster_data.get('special_abilities', [])
            for idx, a in enumerate(spec_abilities):
                dynamic_blocks.append(f"{a.get('name')}: {a.get('desc')}")
                block_mapping.append(('special', idx))

            actions = monster_data.get('actions', [])
            for idx, a in enumerate(actions):
                dynamic_blocks.append(f"{a.get('name')}: {a.get('desc')}")
                block_mapping.append(('action', idx))

            leg_actions = monster_data.get('legendary_actions', [])
            for idx, a in enumerate(leg_actions):
                dynamic_blocks.append(f"{a.get('name')}: {a.get('desc')}")
                block_mapping.append(('legendary', idx))

            reactions = monster_data.get('reactions', [])
            for idx, a in enumerate(reactions):
                dynamic_blocks.append(f"{a.get('name')}: {a.get('desc')}")
                block_mapping.append(('reaction', idx))

            # 7. Odeslání jediného sloučeného dotazu na překlad
            api_before = translator.api_calls_count
            translated_blocks = translator.translate_actions_batch(dynamic_blocks) if dynamic_blocks else []
            calls_made = translator.api_calls_count > api_before

            spec_cz = []
            act_cz = []
            leg_cz = []
            react_cz = []

            for (b_type, b_idx), text_cz in zip(block_mapping, translated_blocks):
                if b_type == 'name':
                    name_cz = text_cz
                elif b_type == 'special':
                    spec_cz.append(text_cz)
                elif b_type == 'action':
                    act_cz.append(text_cz)
                elif b_type == 'legendary':
                    leg_cz.append(text_cz)
                elif b_type == 'reaction':
                    react_cz.append(text_cz)

            name_cz = name_cz or name_en
            info_source = "přes API" if calls_made else "ze slovníku/cache"
            self.stdout.write(f"[{i}/{len(monsters_to_process)}] {name_en} -> {name_cz} (CR {monster_data.get('challenge_rating')}) [{info_source}]")

            # 8. Obrázek
            img_rel = monster_data.get('image')
            image_url = f"{base_url}{img_rel}" if img_rel else ""

            # 9. Uložení nebo aktualizace v databázi
            defaults_data = {
                'name_en': name_en,
                'name_cz': name_cz,
                'size': size_cz,
                'monster_type': type_cz,
                'subtype': subtype,
                'alignment': alignment_cz,
                'armor_class': ac_val,
                'armor_desc': ac_desc,
                'hit_points': hit_points,
                'hit_dice': hit_dice,
                'speed': speed_str,
                'strength': monster_data.get('strength', 10),
                'dexterity': monster_data.get('dexterity', 10),
                'constitution': monster_data.get('constitution', 10),
                'intelligence': monster_data.get('intelligence', 10),
                'wisdom': monster_data.get('wisdom', 10),
                'charisma': monster_data.get('charisma', 10),
                'saving_throws': saving_throws_str,
                'skills': skills_str,
                'damage_vulnerabilities': vuln_str,
                'damage_resistances': resist_str,
                'damage_immunities': dmg_imm_str,
                'condition_immunities': cond_imm_str,
                'senses': senses_str,
                'languages': languages_str,
                'challenge_rating': cr,
                'xp': xp,
                'proficiency_bonus': prof_bonus,
                'special_abilities': "\n\n".join(spec_cz),
                'actions': "\n\n".join(act_cz),
                'legendary_actions': "\n\n".join(leg_cz),
                'reactions': "\n\n".join(react_cz),
                'description': monster_data.get('desc', ''),
                'image_url': image_url,
                'raw_data': monster_data,
            }

            if update_existing:
                CompendiumMonster.objects.update_or_create(
                    api_index=index,
                    defaults=defaults_data,
                )
            else:
                CompendiumMonster.objects.create(
                    api_index=index,
                    **defaults_data,
                )

            imported_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImport nestvůr dokončen! Zpracováno: {imported_count}, přeskočeno: {skipped_count}. "
            f"Celkem odesláno pouze {translator.api_calls_count} požadavků na překladové API."
        ))
