import time
import requests
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from dm_site_app.models import CompendiumItem

class Command(BaseCommand):
    help = 'Stáhne vybavení z DnD 5e API, přeloží ho dávkově (batch) a uloží do databáze'

    def handle(self, *args, **kwargs):
        translator = GoogleTranslator(source='en', target='cs')
        base_url = "https://www.dnd5eapi.co"
        
        self.stdout.write("Stahuji hlavní seznam vybavení z API...")
        response = requests.get(f"{base_url}/api/equipment")
        items_list = response.json().get('results', [])
        
        # Testovací vzorek (až si to ověříš, smaž "[:10]" pro import celého kompendia)
        for item_ref in items_list[:10]:
            item_url = f"{base_url}{item_ref['url']}"
            
            time.sleep(1) # Základní ohleduplnost k DnD API serverům
            try:
                item_data = requests.get(item_url).json()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Chyba při stahování {item_url}: {e}"))
                continue
            
            index = item_data.get('index')
            name_en = item_data.get('name', '')
            
            if CompendiumItem.objects.filter(api_index=index).exists():
                self.stdout.write(self.style.WARNING(f"Předmět {name_en} už existuje, přeskakuji (šetřím API)."))
                continue

            self.stdout.write(f"Zpracovávám: {name_en}...")
            
            # 1. Příprava dat pro překlad
            category_en = item_data.get('equipment_category', {}).get('name', '')
            dmg_dice = item_data.get('damage', {}).get('damage_dice', '')
            dmg_type_en = item_data.get('damage', {}).get('damage_type', {}).get('name', '')
            
            props = [p['name'] for p in item_data.get('properties', [])]
            props_en = ", ".join(props) if props else ""
            
            desc_list = item_data.get('desc', [])
            desc_en = "\n".join(desc_list) if desc_list else ""

            # Zabalení do jednoho pole pro dávkový překlad.
            # Deep-translator nemá rád prázdné stringy, proto dáváme "-" jako zástupný znak.
            texts_to_translate = [
                name_en if name_en else "-",
                category_en if category_en else "-",
                dmg_type_en if dmg_type_en else "-",
                props_en if props_en else "-",
                desc_en if desc_en else "-"
            ]

            time.sleep(3) # Brzda před odesláním jednoho velkého balíku
            
            # 2. Samotný dávkový překlad (translate_batch)
            try:
                translated = translator.translate_batch(texts_to_translate)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Google nás dočasně zablokoval. Chladím IP adresu na celou minutu..."))
                time.sleep(60)
                try:
                    translated = translator.translate_batch(texts_to_translate)
                except:
                    self.stdout.write(self.style.ERROR("I po minutě blokováno. Ukládám tento předmět v angličtině."))
                    translated = texts_to_translate # Fallback na angličtinu
            
            # 3. Rozbalení přeloženého listu
            name_cz = translated[0] if translated[0] != "-" else ""
            category_cz = translated[1] if translated[1] != "-" else ""
            dmg_type_cz = translated[2] if translated[2] != "-" else ""
            props_cz = translated[3] if translated[3] != "-" else ""
            desc_cz = translated[4] if translated[4] != "-" else ""

            damage_str = f"{dmg_dice} {dmg_type_cz}".strip()

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

            # 5. Uložení do databáze
            CompendiumItem.objects.create(
                api_index=index,
                name_en=name_en,
                name_cz=name_cz,
                category=category_cz,
                cost_gold=cost_gold,
                cost_silver=cost_silver,
                weight=item_data.get('weight', 0.0),
                damage=damage_str,
                armor_class=item_data.get('armor_class', {}).get('base', None),
                properties=props_cz,
                description=desc_cz
            )
            
        self.stdout.write(self.style.SUCCESS('Import a překlad dokončen!'))