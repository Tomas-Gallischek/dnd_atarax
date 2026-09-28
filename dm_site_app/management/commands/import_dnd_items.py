from django.core.management.base import BaseCommand
import requests
from deep_translator import GoogleTranslator
from dm_site_app.models import CompendiumItem

class Command(BaseCommand):
    help = 'Stáhne vybavení z DnD 5e API, přeloží ho a uloží do databáze'

    def handle(self, *args, **kwargs):
        translator = GoogleTranslator(source='en', target='cs')
        base_url = "https://www.dnd5eapi.co"
        
        self.stdout.write("Stahuji seznam vybavení...")
        response = requests.get(f"{base_url}/api/equipment")
        items_list = response.json().get('results', [])
        
        # Pro ukázku a urychlení omezíme testovací běh na prvních 10 položek. 
        # Jakmile si ověříš, že to funguje, smaž "[:10]" pro import úplně všeho.
        for item_ref in items_list[:10]:
            item_url = f"{base_url}{item_ref['url']}"
            item_data = requests.get(item_url).json()
            
            index = item_data.get('index')
            name_en = item_data.get('name')
            
            # Pokud už předmět v DB je, přeskočíme ho (šetříme čas a limity překladače)
            if CompendiumItem.objects.filter(api_index=index).exists():
                self.stdout.write(self.style.WARNING(f"Předmět {name_en} už existuje, přeskakuji."))
                continue

            self.stdout.write(f"Zpracovávám: {name_en}...")
            
            # 1. Překlad základních textů
            name_cz = translator.translate(name_en)
            category_en = item_data.get('equipment_category', {}).get('name', '')
            category_cz = translator.translate(category_en) if category_en else ''
            
            # 2. Převod měny na Zlaťáky a Stříbrňáky (měďáky se zaokrouhlují nahoru)
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
                # Zjištění celkového počtu stříbrňáků (10 cp = 1 sp)
                total_sp = quantity // 10
                cost_gold = total_sp // 10
                cost_silver = total_sp % 10
                
                # Pokud předmět něco stál (např. 5 cp), ale matematicky to vyšlo na 0,
                # nastavíme minimální cenu 1 stříbrňák.
                if quantity > 0 and cost_gold == 0 and cost_silver == 0:
                    cost_silver = 1

            # 3. Zpracování poškození (zploštění objektu do textu)
            damage_str = ""
            if 'damage' in item_data:
                dmg_dice = item_data['damage'].get('damage_dice', '')
                dmg_type_en = item_data['damage'].get('damage_type', {}).get('name', '')
                dmg_type_cz = translator.translate(dmg_type_en) if dmg_type_en else ''
                damage_str = f"{dmg_dice} {dmg_type_cz}".strip()

            # 4. Zpracování vlastností zbraní (flatten do jednoho stringu)
            props = [p['name'] for p in item_data.get('properties', [])]
            props_cz = translator.translate(", ".join(props)) if props else ""
            
            # 5. Popis (může jich být v poli více)
            desc_list = item_data.get('desc', [])
            desc_en = "\n".join(desc_list)
            desc_cz = translator.translate(desc_en) if desc_en else ""
            
            # 6. Uložení do databáze
            CompendiumItem.objects.create(
                api_index=index,
                name_en=name_en,
                name_cz=name_cz,
                category=category_cz,
                cost_gold=cost_gold,
                cost_silver=cost_silver, # PŘIDANÝ PARAMETR
                weight=item_data.get('weight', 0.0),
                damage=damage_str,
                armor_class=item_data.get('armor_class', {}).get('base', None),
                properties=props_cz,
                description=desc_cz
            )
            
        self.stdout.write(self.style.SUCCESS('Import a překlad dokončen!'))