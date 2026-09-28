import time
import requests
from django.core.management.base import BaseCommand
from dm_site_app.models import CompendiumItem

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


class DnDTranslator:
    """
    Inteligentní překladač s:
    1. Vestavěným slovníkem oficiální české DnD 5e terminologie (0 API dotazů pro známé pojmy).
    2. Mezipamětí (cache), která brání opakovanému překladu stejných frází.
    3. Spojováním jména a popisu do jediného dotazu (namísto 5 samostatných dotazů na předmět).
    4. Spolehlivým koncovým bodem Google API s browser User-Agentem (namísto web scrapingu m.translate).
    5. Automatickým opakováním s exponenciálním čekáním při chybě 429 (Too Many Requests).
    """

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout
        self.style = style
        self.cache = {}
        self.api_calls_count = 0

        # Slovník oficiálních českých překladů pro DnD 5e (kategorie, typy zranění, vlastnosti zbraní a běžné předměty)
        self.dictionary = {
            # Kategorie vybavení
            'weapon': 'Zbraň',
            'armor': 'Zbroj',
            'adventuring gear': 'Dobrodružné vybavení',
            'tools': 'Nástroje a pomůcky',
            'mounts and vehicles': 'Jezdecká zvířata a vozidla',
            'ammunition': 'Střelivo',
            'arcane foci': 'Mystická ohniska',
            "artisan's tools": 'Řemeslnické nástroje',
            'druidic foci': 'Druidská ohniska',
            'equipment packs': 'Výbava a balíčky',
            'gaming sets': 'Herní sady',
            'heavy armor': 'Těžká zbroj',
            'holy symbols': 'Svaté symboly',
            'kits': 'Sady',
            'land vehicles': 'Pozemní vozidla',
            'light armor': 'Lehká zbroj',
            'martial melee weapons': 'Vojenské zbraně na blízko',
            'martial ranged weapons': 'Vojenské zbraně na dálku',
            'martial weapons': 'Vojenské zbraně',
            'medium armor': 'Střední zbroj',
            'melee weapons': 'Zbraně na blízko',
            'mounts and other animals': 'Jezdecká a jiná zvířata',
            'musical instruments': 'Hudební nástroje',
            'other tools': 'Ostatní nástroje',
            'potion': 'Lektvary',
            'ranged weapons': 'Zbraně na dálku',
            'ring': 'Prsteny',
            'rod': 'Žezla',
            'scroll': 'Svitky',
            'shields': 'Štíty',
            'simple melee weapons': 'Jednoduché zbraně na blízko',
            'simple ranged weapons': 'Jednoduché zbraně na dálku',
            'simple weapons': 'Jednoduché zbraně',
            'staff': 'Hole',
            'standard gear': 'Běžné vybavení',
            'tack, harness, and drawn vehicles': 'Postroje a tažená vozidla',
            'wand': 'Hůlky',
            'waterborne vehicles': 'Vodní plavidla',
            'wondrous items': 'Divotvorné předměty',

            # Typy poškození
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

            # Vlastnosti zbraní
            'ammunition': 'Střelivo',
            'finesse': 'Jemná',
            'heavy': 'Těžká',
            'light': 'Lehká',
            'loading': 'Nabíjecí',
            'monk': 'Mnichovská',
            'reach': 'Dosah',
            'special': 'Zvláštní',
            'thrown': 'Vrhací',
            'two-handed': 'Obouruční',
            'versatile': 'Všestranná',

            # Základní zbraně a zbroje
            'club': 'Kyj',
            'dagger': 'Dýka',
            'greatclub': 'Velký kyj',
            'handaxe': 'Sekyrka',
            'javelin': 'Oštěp',
            'light hammer': 'Lehké kladivo',
            'mace': 'Palcát',
            'quarterstaff': 'Hůl',
            'sickle': 'Srp',
            'spear': 'Kopí',
            'crossbow, light': 'Lehká kuše',
            'dart': 'Šipka',
            'shortbow': 'Krátký luk',
            'sling': 'Prak',
            'battleaxe': 'Bojová sekera',
            'flail': 'Cep',
            'glaive': 'Kůsa',
            'greataxe': 'Velká sekera',
            'greatsword': 'Obouruční meč',
            'halberd': 'Halapartna',
            'lance': 'Dřevce',
            'longsword': 'Dlouhý meč',
            'maul': 'Těžké kladivo',
            'morningstar': 'Řemdih',
            'pike': 'Píka',
            'rapier': 'Kord',
            'scimitar': 'Šavle',
            'shortsword': 'Krátký meč',
            'trident': 'Trojzubec',
            'war pick': 'Válečný krumpáč',
            'warhammer': 'Válečné kladivo',
            'whip': 'Bič',
            'blowgun': 'Foukačka',
            'crossbow, hand': 'Ruční kuše',
            'crossbow, heavy': 'Těžká kuše',
            'longbow': 'Dlouhý luk',
            'net': 'Síť',
            'padded armor': 'Prošívaná zbroj',
            'leather armor': 'Kožená zbroj',
            'studded leather armor': 'Pobíjená kožená zbroj',
            'hide armor': 'Kožešinová zbroj',
            'chain shirt': 'Kroužková košile',
            'scale mail': 'Šupinová zbroj',
            'breastplate': 'Kyrys',
            'half plate armor': 'Poloplátová zbroj',
            'ring mail': 'Kroužkový kabát',
            'chain mail': 'Kroužková zbroj',
            'splint armor': 'Lamelová zbroj',
            'plate armor': 'Plátová zbroj',
            'shield': 'Štít',
        }

    def _lookup_dict(self, text: str):
        if not text:
            return ""
        return self.dictionary.get(text.strip().lower())

    def _call_google_api(self, text: str) -> str:
        """Přímý dotaz na Google Translate API endpoint s browser User-Agentem."""
        self.api_calls_count += 1
        url = 'https://translate.googleapis.com/translate_a/single'
        params = {'client': 'gtx', 'sl': 'en', 'tl': 'cs', 'dt': 't', 'q': text}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, params=params, headers=headers, timeout=12)
        if resp.status_code == 200:
            return ''.join([part[0] for part in resp.json()[0] if part and part[0]])
        elif resp.status_code == 429:
            raise requests.exceptions.HTTPError("429 Too Many Requests", response=resp)
        else:
            resp.raise_for_status()

    def translate_with_retry(self, text: str, max_retries: int = 3) -> str:
        """Přeloží text s ošetřením chyb, 429 rate limitu a exponenciálním čekáním."""
        if not text or not text.strip() or text.strip() == "-":
            return ""

        for attempt in range(max_retries):
            try:
                try:
                    return self._call_google_api(text)
                except Exception as api_err:
                    if "429" in str(api_err):
                        raise
                    # Pokud selže primární API z jiného důvodu, zkusit fallback deep_translator
                    if GoogleTranslator:
                        t = GoogleTranslator(source='en', target='cs')
                        self.api_calls_count += 1
                        return t.translate(text)
                    raise api_err
            except Exception as e:
                is_rate_limit = "429" in str(e)
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1) if is_rate_limit else 2
                    msg = f"  [API rate limit / prodleva] Čekám {wait_time} s před dalším pokusem ({attempt + 1}/{max_retries})..."
                    if self.stdout and self.style:
                        self.stdout.write(self.style.WARNING(msg))
                    else:
                        print(msg)
                    time.sleep(wait_time)
                else:
                    msg = f"  [Chyba] Překlad selhal i po {max_retries} pokusech: {e}. Ponechávám originál."
                    if self.stdout and self.style:
                        self.stdout.write(self.style.ERROR(msg))
                    else:
                        print(msg)
                    return text

    def translate_term(self, text: str) -> str:
        """Přeloží krátký termín (kategorie, damage type, property) s využitím slovníku a mezipaměti."""
        if not text or text.strip() in ("", "-"):
            return ""

        dict_val = self._lookup_dict(text)
        if dict_val:
            return dict_val

        if text in self.cache:
            return self.cache[text]

        res = self.translate_with_retry(text)
        self.cache[text] = res
        return res

    def translate_name_and_desc(self, name_en: str, desc_en: str):
        """
        Přeloží název i popis předmětu najednou v 1 jediném HTTP dotazu namísto více samostatných.
        """
        name_cz = self._lookup_dict(name_en) or self.cache.get(name_en)
        desc_cz = self.cache.get(desc_en) if desc_en else ""

        needs_name = (name_cz is None)
        needs_desc = bool(desc_en and desc_cz is None)

        if needs_name and needs_desc:
            # Spojení názvu a popisu přes bezpečný oddělovač
            delimiter = "\n|||\n"
            combined = f"{name_en}{delimiter}{desc_en}"
            translated = self.translate_with_retry(combined)
            if "|||" in translated:
                parts = translated.split("|||")
                name_cz = parts[0].strip()
                desc_cz = parts[1].strip()
            else:
                name_cz = self.translate_with_retry(name_en)
                desc_cz = self.translate_with_retry(desc_en)
            self.cache[name_en] = name_cz
            self.cache[desc_en] = desc_cz
        elif needs_name:
            name_cz = self.translate_with_retry(name_en)
            self.cache[name_en] = name_cz
        elif needs_desc:
            desc_cz = self.translate_with_retry(desc_en)
            self.cache[desc_en] = desc_cz

        return name_cz or name_en, desc_cz or ""


class Command(BaseCommand):
    help = 'Stáhne vybavení z DnD 5e API, šetrně a chytře ho přeloží a uloží do databáze'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Omezit počet importovaných předmětů (např. --limit 10 pro rychlý test). Výchozí: všechny.',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.8,
            help='Prodleva mezi předměty v sekundách (výchozí: 0.8 s pro naprostou bezpečnost vůči limitům).',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Aktualizovat i předměty, které již v databázi existují.',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        delay = options.get('delay', 0.8)
        update_existing = options.get('update', False)

        translator = DnDTranslator(stdout=self.stdout, style=self.style)
        base_url = "https://www.dnd5eapi.co"

        self.stdout.write("Stahuji hlavní seznam vybavení z API...")
        try:
            response = requests.get(f"{base_url}/api/equipment", timeout=15)
            response.raise_for_status()
            items_list = response.json().get('results', [])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Chyba při stahování seznamu vybavení: {e}"))
            return

        total_available = len(items_list)
        if limit:
            items_to_process = items_list[:limit]
            self.stdout.write(f"Nalezeno {total_available} předmětů, zpracuji prvních {len(items_to_process)} (zadáno --limit {limit}).")
        else:
            items_to_process = items_list
            self.stdout.write(f"Nalezeno celkem {total_available} předmětů k importu.")

        imported_count = 0
        skipped_count = 0

        for i, item_ref in enumerate(items_to_process, start=1):
            item_url = f"{base_url}{item_ref['url']}"

            # Základní prodleva mezi předměty
            if delay > 0 and i > 1:
                time.sleep(delay)

            try:
                item_data = requests.get(item_url, timeout=15).json()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Chyba při stahování {item_url}: {e}"))
                continue

            index = item_data.get('index')
            name_en = item_data.get('name', '')

            # Kontrola existence v databázi
            item_exists = CompendiumItem.objects.filter(api_index=index).exists()
            if item_exists and not update_existing:
                self.stdout.write(self.style.WARNING(f"[{i}/{len(items_to_process)}] Předmět '{name_en}' už existuje, přeskakuji."))
                skipped_count += 1
                continue

            # 1. Příprava dat
            category_en = item_data.get('equipment_category', {}).get('name', '')
            dmg_dice = item_data.get('damage', {}).get('damage_dice', '')
            dmg_type_en = item_data.get('damage', {}).get('damage_type', {}).get('name', '')

            props = [p['name'] for p in item_data.get('properties', [])]

            # Popis a speciální vlastnosti (např. u lance, net)
            desc_list = list(item_data.get('desc', []))
            special_list = item_data.get('special', [])
            for s in special_list:
                if s not in desc_list:
                    desc_list.append(s)
            desc_en = "\n".join(desc_list) if desc_list else ""

            # 2. Chytrý překlad: kategorie, typy poškození a vlastnosti zbraňových schopností
            # se překládají ze slovníku/cache bez jediného volání API!
            category_cz = translator.translate_term(category_en)
            dmg_type_cz = translator.translate_term(dmg_type_en)
            props_cz = ", ".join([translator.translate_term(p) for p in props]) if props else ""

            # Název a popis se přeloží dohromady v jediném dotazu (pokud nejsou ve slovníku/cache)
            api_calls_before = translator.api_calls_count
            name_cz, desc_cz = translator.translate_name_and_desc(name_en, desc_en)
            made_call = translator.api_calls_count > api_calls_before

            info_source = "přes API" if made_call else "ze slovníku/cache"
            self.stdout.write(f"[{i}/{len(items_to_process)}] {name_en} -> {name_cz} ({info_source})")

            # 3. Zpracování poškození
            if dmg_dice and dmg_type_cz:
                damage_str = f"{dmg_dice} {dmg_type_cz}".strip()
            elif dmg_dice:
                damage_str = str(dmg_dice).strip()
            elif dmg_type_cz:
                damage_str = str(dmg_type_cz).strip()
            else:
                damage_str = None

            # 4. Převod měny na Zlaťáky a Stříbrňáky
            cost_gold = 0
            cost_silver = 0
            cost_data = item_data.get('cost', {})
            quantity = cost_data.get('quantity', 0)
            unit = cost_data.get('unit', '')

            if unit == 'gp':
                cost_gold = quantity
            elif unit == 'sp':
                cost_gold = quantity // 10
                cost_silver = quantity % 10
            elif unit == 'cp':
                total_sp = quantity // 10
                cost_gold = total_sp // 10
                cost_silver = total_sp % 10
                if quantity > 0 and cost_gold == 0 and cost_silver == 0:
                    cost_silver = 1
            elif unit == 'ep':
                cost_gold = quantity // 2
                cost_silver = (quantity % 2) * 5
            elif unit == 'pp':
                cost_gold = quantity * 10

            # Bezpečná váha (pro případ None v datech)
            raw_weight = item_data.get('weight')
            weight = float(raw_weight) if raw_weight is not None else 0.0

            # Obranné číslo (AC)
            armor_class = item_data.get('armor_class', {}).get('base', None)

            # 5. Uložení nebo aktualizace v databázi
            defaults_data = {
                'name_en': name_en,
                'name_cz': name_cz,
                'category': category_cz,
                'cost_gold': cost_gold,
                'cost_silver': cost_silver,
                'weight': weight,
                'damage': damage_str,
                'armor_class': armor_class,
                'properties': props_cz,
                'description': desc_cz,
            }

            if update_existing:
                CompendiumItem.objects.update_or_create(
                    api_index=index,
                    defaults=defaults_data,
                )
            else:
                CompendiumItem.objects.create(
                    api_index=index,
                    **defaults_data,
                )

            imported_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImport dokončen! Zpracováno předmětů: {imported_count}, přeskočeno: {skipped_count}. "
            f"Celkem odesláno pouze {translator.api_calls_count} požadavků na překladové API."
        ))