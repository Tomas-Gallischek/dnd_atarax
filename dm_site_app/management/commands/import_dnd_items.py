import time
import requests
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from dm_site_app.models import CompendiumItem

class Command(BaseCommand):
    help = 'Stáhne vybavení z DnD 5e API, bezpečně (a pomalu) přeloží a uloží do databáze'

    def safe_translate(self, text, translator):
        """Pomocná funkce pro bezpečný překlad s dlouhou časovou prodlevou."""
        if not text:
            return ""
        
        # Tvrdý limit 2 sekundy před každým jednotlivým překladem
        time.sleep(2) 
        
        try:
            return translator.translate(text)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Limit překladače zasažen ({e}). Chladím spojení na 10 vteřin..."))
            time.sleep(10)  # Výrazně delší pauza pro resetování banu
            try:
                return translator.translate(text)
            except:
                self.stdout.write(self.style.ERROR("Druhý pokus selhal, ukládám původní anglický text."))
                return text

    def handle(self, *args, **kwargs):
        translator = GoogleTranslator(source='en', target='cs')
        base_url = "https://www.dnd5eapi.co"
        
        self.stdout.write("Stahuji hlavní seznam vybavení z API...")
        response = requests.get(f"{base_url}/api/equipment")
        items_list = response.json().get('results', [])
        
        # Zde můžeš smazat "[:10]", pokud chceš stáhnout celou databázi
        for item_ref in items_list:
            item_url = f"{base_url}{item_ref['url']}"
            
            # Bezpečnostní pauza 2 sekundy i pro samotné DnD 5e API
            time.sleep(2)
            try:
                item_data = requests.get(item_url).json()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Chyba při stahování {item_url}: {e}"))
                continue
            
            index = item_data.get('index')
            name_en = item_data.get('name')
            
            if CompendiumItem.objects.filter(api_index=index).exists():
                self.stdout.write(self.style.WARNING(f"Předmět {name_en} už existuje, přeskakuji (šetřím API)."))
                continue

            self.stdout.write(f"Zpracovávám: {name_en} (To chvíli potrvá...)")
            
            # 1. Překlad základních textů
            name_cz = self.safe_translate(name_en, translator)
            category_en = item_data.get('equipment_category', {}).get('name', '')
            category_cz = self.safe_translate(category_en, translator)
            
            # 2. Převod měny na Zlaťáky a Stříbrňáky
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

            # 3. Zpracování poškození
            damage_str = ""
            if 'damage' in item_data:
                dmg_dice = item_data['damage'].get('damage_dice', '')
                dmg_type_en = item_data['damage'].get('damage_type', {}).get('name', '')
                dmg_type_cz = self.safe_translate(dmg_type_en, translator)
                damage_str = f"{dmg_dice} {dmg_type_cz}".strip()

            # 4. Zpracování vlastností zbraní
            props = [p['name'] for p in item_data.get('properties', [])]
            props_en = ", ".join(props) if props else ""
            props_cz = self.safe_translate(props_en, translator)
            
            # 5. Popis
            desc_list = item_data.get('desc', [])
            desc_en = "\n".join(desc_list)
            desc_cz = self.safe_translate(desc_en, translator)
            
            # 6. Uložení do databáze
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
            
        self.stdout.write(self.style.SUCCESS('Import a překlad dokončen! Můžeš to zkontrolovat v administraci.'))