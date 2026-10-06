import time
import requests
from django.core.management.base import BaseCommand
from dm_site_app.models import Spells_All_db

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


class DnDSpellTranslator:
    """
    Inteligentní překladač kouzel DnD 5e s:
    1. Bohatým vestavěným slovníkem oficiální české DnD 5e terminologie a názvů kouzel (0 dotazů na API).
    2. Mezipamětí (cache) pro opakující se texty.
    3. Spolehlivým koncovým bodem Google API s browser User-Agentem.
    4. Automatickým opakováním s exponenciálním čekáním při chybě 429 (Too Many Requests).
    """

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout
        self.style = style
        self.cache = {}
        self.api_calls_count = 0

        # Magické školy
        self.schools_dict = {
            'abjuration': 'Vymítání',
            'conjuration': 'Vyvolávání',
            'divination': 'Věštění',
            'enchantment': 'Očarování',
            'evocation': 'Evokace',
            'illusion': 'Iluze',
            'necromancy': 'Nekromancie',
            'transmutation': 'Proměny',
        }

        # Povolání
        self.classes_dict = {
            'barbarian': 'Barbar',
            'bard': 'Bard',
            'cleric': 'Klerik',
            'druid': 'Druid',
            'fighter': 'Bojovník',
            'monk': 'Mnich',
            'paladin': 'Paladin',
            'ranger': 'Hraničář',
            'rogue': 'Tulák',
            'sorcerer': 'Čaroděj',
            'warlock': 'Černokněžník',
            'wizard': 'Kouzelník',
        }

        # Typy poškození
        self.damage_dict = {
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

        # Běžné parametry
        self.terms_dict = {
            '1 action': '1 akce',
            '1 bonus action': '1 bonusová akce',
            '1 reaction': '1 reakce',
            '1 minute': '1 minuta',
            '10 minutes': '10 minut',
            '1 hour': '1 hodina',
            '8 hours': '8 hodin',
            '24 hours': '24 hodin',
            'instantaneous': 'Ihned',
            'touch': 'Dotyk',
            'self': 'Sám sebe',
            'sight': 'Dohled',
            'special': 'Zvláštní',
            'str': 'Síla (STR)',
            'dex': 'Obratnost (DEX)',
            'con': 'Odolnost (CON)',
            'int': 'Inteligence (INT)',
            'wis': 'Moudrost (WIS)',
            'cha': 'Charisma (CHA)',
            'ranged': 'Na dálku',
            'melee': 'Na blízko',
        }

        # Oficiální české překlady známých kouzel (Černý kodex / PHB 5e)
        self.spell_names_dict = {
            'acid arrow': 'Kyselinový šíp',
            'acid splash': 'Kyselinová sprška',
            'aid': 'Pomoc',
            'alarm': 'Poplach',
            'alter self': 'Změň sebe sama',
            'animal friendship': 'Přátelství se zvířaty',
            'animal messenger': 'Zvířecí posel',
            'animal shapes': 'Zvířecí podoby',
            'animate dead': 'Oživ mrtvé',
            'animate objects': 'Oživ předměty',
            'antilife shell': 'Štít proti životu',
            'antimagic field': 'Antimagické pole',
            'antipathy/sympathy': 'Antipatie/Sympatie',
            'arcane eye': 'Mysticko oko',
            'arcane hand': 'Mystická ruka',
            'arcane lock': 'Mystický zámek',
            'arcane sword': 'Mystický meč',
            'arcanist\'s magic aura': 'Mágova magická aura',
            'astral projection': 'Astrální projekce',
            'augury': 'Věštba',
            'awaken': 'Procitnutí',
            'bane': 'Zkáza',
            'banishment': 'Vyhoštění',
            'barkskin': 'Kůrovitost',
            'beacon of hope': 'Maják naděje',
            'bestow curse': 'Uval prokletí',
            'black tentacles': 'Černá chapadla',
            'blade barrier': 'Bariéra čepelí',
            'blade ward': 'Ochrana čepelí',
            'bless': 'Požehnání',
            'blight': 'Zkáza úrody',
            'blindness/deafness': 'Slepota/Hluchota',
            'blink': 'Mžik',
            'blur': 'Rozmazání',
            'burning hands': 'Hořící ruce',
            'call lightning': 'Přivolej blesky',
            'calm emotions': 'Uklidni emoce',
            'chain lightning': 'Řetězový blesk',
            'charm person': 'Okouzli osobu',
            'chill touch': 'Mrazivý dotyk',
            'circle of death': 'Kruh smrti',
            'clairvoyance': 'Jasnovidnost',
            'clone': 'Klon',
            'cloudkill': 'Mrak smrti',
            'color spray': 'Barevná sprška',
            'command': 'Příkaz',
            'commune': 'Rozmluva s bohy',
            'commune with nature': 'Rozmluva s přírodou',
            'comprehend languages': 'Porozumění jazykům',
            'cone of cold': 'Kužel mrazu',
            'confusion': 'Zmatení',
            'conjure animals': 'Vyvolej zvířata',
            'conjure celestial': 'Vyvolej nebešťana',
            'conjure elemental': 'Vyvolej elementála',
            'conjure fey': 'Vyvolej vílu',
            'conjure minor elementals': 'Vyvolej menší elementály',
            'conjure woodland beings': 'Vyvolej lesní tvory',
            'contact other plane': 'Spoj se s jinou sférou',
            'contagion': 'Nákaza',
            'contingency': 'Pohotovost',
            'continual flame': 'Věčný plamen',
            'control water': 'Ovládej vodu',
            'control weather': 'Ovládej počasí',
            'counterspell': 'Protikouzlo',
            'create food and water': 'Stvoř jídlo a vodu',
            'create undead': 'Stvoř nemrtvé',
            'create or destroy water': 'Stvoř nebo znič vodu',
            'cure wounds': 'Vyleč zranění',
            'dancing lights': 'Tančící světla',
            'darkness': 'Temnota',
            'darkvision': 'Vidění ve tmě',
            'daylight': 'Denní světlo',
            'death ward': 'Ochrana před smrtí',
            'delayed blast fireball': 'Zpožděná ohnivá koule',
            'demiplane': 'Polosféra',
            'detect evil and good': 'Odhal zlo a dobro',
            'detect magic': 'Odhal magii',
            'detect poison and disease': 'Odhal jed a nemoc',
            'detect thoughts': 'Odhal myšlenky',
            'dimension door': 'Dimenziální dveře',
            'disguise self': 'Změň podobu',
            'disintegrate': 'Rozklad',
            'dispel evil and good': 'Zažeň dobro a zlo',
            'dispel magic': 'Rozptyl magii',
            'divination': 'Věštectví',
            'divine favor': 'Božská přízeň',
            'divine word': 'Božské slovo',
            'dominate beast': 'Ovládni zvíře',
            'dominate monster': 'Ovládni nestvůru',
            'dominate person': 'Ovládni osobu',
            'dream': 'Sen',
            'earthquake': 'Zemětřesení',
            'eldritch blast': 'Tajemný výboj',
            'enhance ability': 'Vylepši vlastnost',
            'enlarge/reduce': 'Zvětši/Zmenši',
            'entangle': 'Zamotání',
            'enthrall': 'Poutání pozornosti',
            'etherealness': 'Éteričnost',
            'expeditious retreat': 'Rychlý ústup',
            'eyebite': 'Zlý pohled',
            'fabricate': 'Výroba',
            'faerie fire': 'Vílí oheň',
            'faithful hound': 'Věrný pes',
            'false life': 'Falešný život',
            'fear': 'Strach',
            'feather fall': 'Pomalý pád',
            'feeblemind': 'Slabomyslnost',
            'find familiar': 'Najdi společníka',
            'find steed': 'Najdi oře',
            'find the path': 'Najdi cestu',
            'find traps': 'Najdi pasti',
            'finger of death': 'Prst smrti',
            'fire ball': 'Ohnivá koule',
            'fireball': 'Ohnivá koule',
            'fire bolt': 'Ohnivá střela',
            'fire shield': 'Ohnivý štít',
            'fire storm': 'Ohnivá bouře',
            'flame blade': 'Plamenná čepel',
            'flame strike': 'Úder plamene',
            'flaming sphere': 'Planoucí koule',
            'fly': 'Létej',
            'fog cloud': 'Mlžný oblak',
            'forbiddance': 'Zapovězení',
            'forcecage': 'Silová klec',
            'foresight': 'Předvídavost',
            'freedom of movement': 'Volnost pohybu',
            'freezing sphere': 'Mrazivá koule',
            'gaseous form': 'Plynné tělo',
            'gate': 'Brána',
            'geas': 'Kletba závazku',
            'gentle repose': 'Klidný odpočinek',
            'glibness': 'Pohotovost mluvy',
            'globe of invulnerability': 'Koule nezranitelnosti',
            'glyph of warding': 'Ochranná glyfa',
            'goodberry': 'Léčivé bobule',
            'grease': 'Mazadlo',
            'greater invisibility': 'Větší neviditelnost',
            'greater restoration': 'Větší obnovení',
            'guardian of faith': 'Strážce víry',
            'guards and wards': 'Stráže a ochrany',
            'guidance': 'Vedení',
            'guiding bolt': 'Naváděcí blesk',
            'gust of wind': 'Poryv větru',
            'hallow': 'Posvěcení',
            'hallucinatory terrain': 'Halucinační terén',
            'harm': 'Ublížení',
            'haste': 'Zrychlení',
            'heal': 'Uzdravení',
            'healing word': 'Léčivé slovo',
            'heat metal': 'Rozpal kov',
            'hellish rebuke': 'Pekelná odveta',
            'heroes\' feast': 'Hostina hrdinů',
            'heroism': 'Hrdinství',
            'hideous laughter': 'Šílený smích',
            'hold monster': 'Zadrž nestvůru',
            'hold person': 'Zadrž osobu',
            'holy aura': 'Svatá aura',
            'hunter\'s mark': 'Lovcova značka',
            'hypnotic pattern': 'Hypnotický vzorec',
            'ice storm': 'Ledová bouře',
            'identify': 'Identifikuj',
            'illusory script': 'Ilu رونí písmo',
            'imprisonment': 'Uvěznění',
            'incendiary cloud': 'Zápalný oblak',
            'inflict wounds': 'Způsob zranění',
            'insect plague': 'Mor kobylek',
            'instant summons': 'Okamžité přivolání',
            'invisibility': 'Neviditelnost',
            'jump': 'Skok',
            'knock': 'Zaklepání',
            'legend lore': 'Legendy a mýty',
            'lesser restoration': 'Menší obnovení',
            'levitate': 'Levitace',
            'light': 'Světlo',
            'lightning bolt': 'Blesk',
            'locate animals or plants': 'Lokalizuj zvířata a rostliny',
            'locate creature': 'Lokalizuj tvora',
            'locate object': 'Lokalizuj předmět',
            'longstrider': 'Dlouhý krok',
            'mage armor': 'Mágova zbroj',
            'mage hand': 'Mágova ruka',
            'magic circle': 'Magický kruh',
            'magic jar': 'Magická nádoba',
            'magic missile': 'Magická střela',
            'magic mouth': 'Magická ústa',
            'magic weapon': 'Magická zbraň',
            'magnificent mansion': 'Velkolepé sídlo',
            'major image': 'Velký obraz',
            'mass cure wounds': 'Hromadné vyléčení zranění',
            'mass heal': 'Hromadné uzdravení',
            'mass healing word': 'Hromadné léčivé slovo',
            'mass suggestion': 'Hromadné vnuknutí',
            'maze': 'Bludiště',
            'meld into stone': 'Splynutí s kamenem',
            'mending': 'Záplata',
            'message': 'Zpráva',
            'meteor swarm': 'Roj meteorů',
            'mind blank': 'Vyprázdnění mysli',
            'minor illusion': 'Drobná iluze',
            'mirage arcane': 'Mystická fata morgána',
            'mirror image': 'Zrcadlový obraz',
            'mislead': 'Zmatení stopy',
            'misty step': 'Mlžný krok',
            'modify memory': 'Uprav vzpomínky',
            'moonbeam': 'Měsíční paprsek',
            'move earth': 'Pohni zemí',
            'nondetection': 'Nezjistitelnost',
            'pass without trace': 'Projdi beze stopy',
            'passwall': 'Průchod zdí',
            'phantasmal killer': 'Přízračný vrah',
            'planar ally': 'Sférový spojenec',
            'planar binding': 'Sférové spoutání',
            'plane shift': 'Sférový posun',
            'plant growth': 'Růst rostlin',
            'poison spray': 'Oblak jedu',
            'polymorph': 'Proměna',
            'power word kill': 'Slovo moci: Zabij',
            'power word stun': 'Slovo moci: Omrač',
            'prayer of healing': 'Modlitba léčení',
            'prestidigitation': 'Představení',
            'prismatic spray': 'Duhová sprška',
            'prismatic wall': 'Duhová zeď',
            'produce flame': 'Vytvoř plamen',
            'programmed illusion': 'Naprogramovaná iluze',
            'project image': 'Promítni obraz',
            'protection from energy': 'Ochrana před energií',
            'protection from evil and good': 'Ochrana před dobrem a zlem',
            'protection from poison': 'Ochrana před jedem',
            'purify food and drink': 'Očisti jídlo a pití',
            'raise dead': 'Vzkříšení',
            'ray of enfeeblement': 'Paprsek oslabení',
            'ray of frost': 'Mrazivý paprsek',
            'regenerate': 'Regenerace',
            'reincarnate': 'Reinkarnace',
            'remove curse': 'Sejmi prokletí',
            'resilient sphere': 'Odolná koule',
            'resistance': 'Odolnost',
            'resurrection': 'Zmrtvýchvstání',
            'reverse gravity': 'Obrácená gravitace',
            'revivify': 'Oživení',
            'rope trick': 'Trik s lanem',
            'sacred flame': 'Posvátný plamen',
            'sanctuary': 'Útočiště',
            'scrying': 'Špehování',
            'secret chest': 'Tajná truhla',
            'see invisibility': 'Vidění neviditelného',
            'seeming': 'Zdání',
            'sending': 'Poselství',
            'sequester': 'Izolace',
            'shapechange': 'Změna tvaru',
            'shatter': 'Roztříštění',
            'shield': 'Štít',
            'shield of faith': 'Štít víry',
            'shillelagh': 'Kouzelná hůl',
            'shocking grasp': 'Šokující sevření',
            'silence': 'Ticho',
            'silent image': 'Tichý obraz',
            'simulacrum': 'Dvojník',
            'sleep': 'Spánek',
            'sleet storm': 'Vánice',
            'slow': 'Zpomalení',
            'speak with animals': 'Mluv se zvířaty',
            'speak with dead': 'Mluv s mrtvými',
            'speak with plants': 'Mluv s rostlinami',
            'spider climb': 'Pavoučí šplh',
            'spike growth': 'Růst bodlin',
            'spiritual weapon': 'Duchovní zbraň',
            'spirit guardians': 'Duchovní strážci',
            'stinking cloud': 'Páchnoucí oblak',
            'stone shape': 'Tvaruj kámen',
            'stoneskin': 'Kamenná kůže',
            'storm of vengeance': 'Bouře pomsty',
            'suggestion': 'Vnuknutí',
            'sunbeam': 'Sluneční paprsek',
            'sunburst': 'Sluneční výbuch',
            'telekinesis': 'Telekineze',
            'telepathic bond': 'Telepatické pouto',
            'teleport': 'Teleportace',
            'teleportation circle': 'Teleportační kruh',
            'thaumaturgy': 'Taumaturgie',
            'thunderwave': 'Hromová vlna',
            'time stop': 'Zastavení času',
            'tiny hut': 'Chýše',
            'tongues': 'Jazyky',
            'true polymorph': 'Pravá proměna',
            'true resurrection': 'Pravé zmrtvýchvstání',
            'true seeing': 'Pravdivé vidění',
            'true strike': 'Pravdivý úder',
            'unseen servant': 'Neviditelný sluha',
            'vampiric touch': 'Upíří dotyk',
            'vicious mockery': 'Zraňující výsměch',
            'wall of fire': 'Ohnivá zeď',
            'wall of force': 'Silová zeď',
            'wall of ice': 'Ledová zeď',
            'wall of stone': 'Kamenná zeď',
            'wall of thorns': 'Trnová zeď',
            'water breathing': 'Dýchání pod vodou',
            'water walk': 'Chůze po vodě',
            'web': 'Pavučina',
            'weird': 'Přízrak hrůzy',
            'wind walk': 'Chůze větrem',
            'wind wall': 'Větrná zeď',
            'wish': 'Přání',
            'witch bolt': 'Čarodějný blesk',
            'word of recall': 'Slovo návratu',
            'zone of truth': 'Zóna pravdy',
        }

    def _call_google_api(self, text: str) -> str:
        self.api_calls_count += 1
        url = 'https://translate.googleapis.com/translate_a/single'
        params = {'client': 'gtx', 'sl': 'en', 'tl': 'cs', 'dt': 't', 'q': text}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, params=params, headers=headers, timeout=14)
        if resp.status_code == 200:
            return ''.join([part[0] for part in resp.json()[0] if part and part[0]])
        elif resp.status_code == 429:
            raise requests.exceptions.HTTPError("429 Too Many Requests", response=resp)
        else:
            resp.raise_for_status()

    def translate_with_retry(self, text: str, max_retries: int = 3) -> str:
        if not text or not text.strip() or text.strip() == "-":
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
                    msg = f"  [API rate limit] Čekám {wait_time} s před dalším pokusem ({attempt + 1}/{max_retries})..."
                    if self.stdout and self.style:
                        self.stdout.write(self.style.WARNING(msg))
                    time.sleep(wait_time)
                else:
                    msg = f"  [Chyba překladu]: {e}. Ponechávám originál."
                    if self.stdout and self.style:
                        self.stdout.write(self.style.ERROR(msg))
                    return text

    def translate_spell_name(self, name_en: str) -> str:
        key = name_en.strip().lower()
        if key in self.spell_names_dict:
            return self.spell_names_dict[key]
        if key in self.cache:
            return self.cache[key]
        translated = self.translate_with_retry(name_en)
        self.cache[key] = translated
        return translated

    def translate_school(self, school_en: str) -> str:
        return self.schools_dict.get(school_en.strip().lower(), school_en)

    def translate_class(self, class_en: str) -> str:
        return self.classes_dict.get(class_en.strip().lower(), class_en)

    def translate_damage_type(self, dmg_en: str) -> str:
        return self.damage_dict.get(dmg_en.strip().lower(), dmg_en)

    def translate_term(self, term_en: str) -> str:
        if not term_en:
            return ""
        key = term_en.strip().lower()
        if key in self.terms_dict:
            return self.terms_dict[key]
        if key in self.cache:
            return self.cache[key]
        tr = self.translate_with_retry(term_en)
        self.cache[key] = tr
        return tr


class Command(BaseCommand):
    help = 'Stáhne kouzla a triky z oficiálního D&D 5e API, přeloží je a uloží do databáze Spells_All_db'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Omezit počet kouzel (např. --limit 10 pro test). Výchozí: všechna dostupná.',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.8,
            help='Prodleva mezi kouzly v sekundách (výchozí: 0.8 s pro prevenci API limitů).',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Aktualizovat i kouzla, která již v databázi existují.',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        delay = options.get('delay', 0.8)
        update_existing = options.get('update', False)

        translator = DnDSpellTranslator(stdout=self.stdout, style=self.style)
        base_url = "https://www.dnd5eapi.co"

        self.stdout.write(self.style.NOTICE("🔍 Stahuji seznam kouzel z D&D 5e API..."))
        try:
            resp = requests.get(f"{base_url}/api/spells", timeout=15)
            resp.raise_for_status()
            spells_list = resp.json().get('results', [])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Chyba při stahování seznamu kouzel: {e}"))
            return

        total_available = len(spells_list)
        if limit:
            spells_to_process = spells_list[:limit]
            self.stdout.write(f"Nalezeno {total_available} kouzel, zpracuji prvních {len(spells_to_process)} (--limit {limit}).")
        else:
            spells_to_process = spells_list
            self.stdout.write(f"Nalezeno celkem {total_available} kouzel k importu.")

        imported_count = 0
        skipped_count = 0

        # Rasy se specifickými kouzly v základních pravidlech
        racial_spell_map = {
            'thaumaturgy': 'Tiefling',
            'hellish-rebuke': 'Tiefling',
            'darkness': 'Tiefling, Elf',
            'dancing-lights': 'Elf',
            'faerie-fire': 'Elf',
            'minor-illusion': 'Gnom',
            'light': 'Elf, Tiefling',
        }

        for i, s_ref in enumerate(spells_to_process, start=1):
            spell_url = f"{base_url}{s_ref['url']}"

            if delay > 0 and i > 1:
                time.sleep(delay)

            try:
                s_data = requests.get(spell_url, timeout=15).json()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{i}/{len(spells_to_process)}] Chyba stahování {spell_url}: {e}"))
                continue

            index = s_data.get('index')
            name_en = s_data.get('name', '')
            level = s_data.get('level', 0)
            is_cantrip = (level == 0)

            exists = Spells_All_db.objects.filter(api_index=index).exists()
            if exists and not update_existing:
                self.stdout.write(self.style.WARNING(f"[{i}/{len(spells_to_process)}] Kouzlo '{name_en}' již existuje v DB, přeskakuji."))
                skipped_count += 1
                continue

            # 1. Povolání
            raw_classes = [c.get('name', '') for c in s_data.get('classes', []) if isinstance(c, dict)]
            cz_classes = [translator.translate_class(c) for c in raw_classes if c]
            classes_str = ", ".join(cz_classes)

            # 2. Rasy
            races_str = racial_spell_map.get(index, '')

            # 3. Škola magie
            school_obj = s_data.get('school', {})
            school_en = school_obj.get('name', '') if isinstance(school_obj, dict) else str(school_obj or '')
            school_cz = translator.translate_school(school_en)

            # 4. Sesílání a dosah
            casting_time_en = s_data.get('casting_time', '')
            casting_time_cz = translator.translate_term(casting_time_en)
            range_en = s_data.get('range', '')
            range_cz = translator.translate_term(range_en)

            # 5. Složky
            comp_raw = s_data.get('components', [])
            components = ", ".join(comp_raw) if isinstance(comp_raw, list) else str(comp_raw or '')
            material_en = s_data.get('material', '')
            material_cz = translator.translate_with_retry(material_en) if material_en else ""

            # 6. Trvání
            duration_en = s_data.get('duration', '')
            duration_cz = translator.translate_term(duration_en)
            concentration = bool(s_data.get('concentration', False))
            ritual = bool(s_data.get('ritual', False))

            # 7. Bojové statistiky
            attack_type_en = s_data.get('attack_type', '')
            attack_type_cz = translator.translate_term(attack_type_en)

            # Poškození (v API může být damage buď list objektů nebo dict)
            damage_raw = s_data.get('damage', [])
            if isinstance(damage_raw, dict):
                damage_list = [damage_raw]
            elif isinstance(damage_raw, list):
                damage_list = damage_raw
            else:
                damage_list = []

            damage_types_cz = []
            damage_dices = []
            for d_item in damage_list:
                if not isinstance(d_item, dict):
                    continue
                dmg_type_obj = d_item.get('damage_type')
                dtype_name = ""
                if isinstance(dmg_type_obj, dict):
                    dtype_name = dmg_type_obj.get('name', '')
                elif isinstance(dmg_type_obj, str):
                    dtype_name = dmg_type_obj

                if dtype_name:
                    cz_dtype = translator.translate_damage_type(dtype_name)
                    if cz_dtype and cz_dtype not in damage_types_cz:
                        damage_types_cz.append(cz_dtype)

                dice = ""
                slot_map = d_item.get('damage_at_slot_level')
                if isinstance(slot_map, dict) and slot_map:
                    dice = slot_map.get(str(level)) or slot_map.get(str(min(map(int, slot_map.keys()))), "")
                else:
                    char_map = d_item.get('damage_at_character_level')
                    if isinstance(char_map, dict) and char_map:
                        dice = char_map.get('1') or char_map.get(str(min(map(int, char_map.keys()))), "")

                if dice and dice not in damage_dices:
                    damage_dices.append(dice)

            damage_type_cz = ", ".join(damage_types_cz)
            damage_dice = " + ".join(damage_dices)

            # Záchranný hod (dc)
            dc_raw = s_data.get('dc', {})
            dc_info = dc_raw[0] if isinstance(dc_raw, list) and dc_raw else (dc_raw if isinstance(dc_raw, dict) else {})
            saving_throw = ""
            if isinstance(dc_info, dict) and dc_info.get('dc_type'):
                dc_type_val = dc_info['dc_type']
                dc_name = dc_type_val.get('name', '') if isinstance(dc_type_val, dict) else str(dc_type_val)
                saving_throw = translator.translate_term(dc_name)

            # Léčení (heal_at_slot_level)
            heal_dice = ""
            heal_raw = s_data.get('heal_at_slot_level', {})
            heal_info = heal_raw[0] if isinstance(heal_raw, list) and heal_raw else (heal_raw if isinstance(heal_raw, dict) else {})
            if isinstance(heal_info, dict) and heal_info:
                heal_dice = heal_info.get(str(level)) or heal_info.get(str(min(map(int, heal_info.keys()))), "")

            # 8. Popis a vyšší úrovně
            desc_en_list = s_data.get('desc', [])
            desc_en = "\n\n".join(desc_en_list) if isinstance(desc_en_list, list) else str(desc_en_list or '')

            higher_en_list = s_data.get('higher_level', [])
            higher_en = "\n\n".join(higher_en_list) if isinstance(higher_en_list, list) else str(higher_en_list or '')

            # Překlad názvu a popisů
            name_cz = translator.translate_spell_name(name_en)

            # Spojený překlad popisu a vyšších úrovní pro úsporu API volání
            if higher_en:
                combined_desc = f"{desc_en}\n|||\n{higher_en}"
                tr_combined = translator.translate_with_retry(combined_desc)
                if "|||" in tr_combined:
                    desc_cz, higher_cz = tr_combined.split("|||", 1)
                    desc_cz = desc_cz.strip()
                    higher_cz = higher_cz.strip()
                else:
                    desc_cz = tr_combined
                    higher_cz = translator.translate_with_retry(higher_en)
            else:
                desc_cz = translator.translate_with_retry(desc_en)
                higher_cz = ""

            # Uložení do Spells_All_db
            spell_obj, created = Spells_All_db.objects.update_or_create(
                api_index=index,
                defaults={
                    'name_cz': name_cz,
                    'name_en': name_en,
                    'level': level,
                    'is_cantrip': is_cantrip,
                    'school': school_cz,
                    'school_en': school_en,
                    'casting_time': casting_time_cz or casting_time_en,
                    'range': range_cz or range_en,
                    'components': components,
                    'material': material_cz,
                    'duration': duration_cz or duration_en,
                    'concentration': concentration,
                    'ritual': ritual,
                    'attack_type': attack_type_cz or attack_type_en,
                    'damage_type': damage_type_cz,
                    'damage_dice': damage_dice,
                    'saving_throw': saving_throw,
                    'heal_dice': heal_dice,
                    'description': desc_cz,
                    'higher_levels': higher_cz,
                    'classes': classes_str,
                    'races': races_str,
                    'backgrounds': '',
                    'icon': 'spells/default_spell.jpg',
                    'icon_url': '/static/img/spells/default_spell.jpg',
                    'raw_data': s_data,
                }
            )

            status_str = "Vytvořeno" if created else "Aktualizováno"
            self.stdout.write(self.style.SUCCESS(
                f"[{i}/{len(spells_to_process)}] {status_str}: {name_cz} ({name_en}) - {'Trik' if is_cantrip else f'Level {level}'} [{classes_str}]"
            ))
            imported_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Import dokončen! Úspěšně zpracováno {imported_count} kouzel, přeskočeno {skipped_count}. (Celkem API volání překladače: {translator.api_calls_count})"
        ))
