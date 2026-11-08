"""
Data pro specifická kouzla a schopnosti z D&D 5e a Xanatharova průvodce vším (XGtE).
Obsahuje implementaci:
1. Hexblade's Curse (Kletba čepelníka)
2. Hex Warrior (Prokletý válečník)
3. Shield (Štít)
4. Wrathful Smite (Hněvivý úder)
"""

HEXBLADE_SPELLS_DATA = [
    {
        'api_index': 'hexblade-curse',
        'name_cz': 'Kletba čepelníka',
        'name_en': "Hexblade's Curse",
        'level': 1,
        'is_cantrip': False,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 bonusová akce',
        'range': '9 metrů (30 stop)',
        'components': 'V, S',
        'material': '',
        'duration': '1 minuta',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Zvláštní',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Jako bonusovou akci zvol jednoho tvora, kterého vidíš do 9 metrů (30 stop) od sebe. "
            "Cíl je na 1 minutu proklet. Kletba skončí předčasně, pokud cíl zemře, ty zemřeš, "
            "nebo jsi vyřazený z boje (incapacitated).\n\n"
            "Dokud kletba trvá, získáváš následující výhody:\n"
            "• K hodům na zranění proti prokletému cíli si přičítáš bonus rovnající se tvému zdatnostnímu bonusu.\n"
            "• Jakýkoliv tvůj hod na útok proti prokletému cíli je kritickým zásahem při hodu 19 nebo 20 na dvacetistěnné kostce (k20).\n"
            "• Pokud prokletý cíl zemře, obnovíš si životy ve výši tvé úrovně černokněžníka + tvé opravy Charismatu (minimálně 1 život).\n\n"
            "Tuto schopnost můžeš znovu použít až po dokončení krátkého nebo dlouhého odpočinku."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {
            'source': "Xanathar's Guide to Everything",
            'archetype': 'The Hexblade (Čepelník)',
            'page': 55,
            'feature_type': 'Patron Feature (1st level)'
        }
    },
    {
        'api_index': 'hex-warrior',
        'name_cz': 'Prokletý válečník',
        'name_en': 'Hex Warrior',
        'level': 1,
        'is_cantrip': False,
        'school': 'Vymítání',
        'school_en': 'Abjuration',
        'casting_time': '1 akce (po dlouhém odpočinku)',
        'range': 'Dotyk',
        'components': 'V, S, M',
        'material': 'Jednoruční zbraň, se kterou jsi zdatný',
        'duration': 'Do příštího dlouhého odpočinku (24 hodin)',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Získáš výcvik potřebný k efektivnímu vyzbrojení do boje: získáš zdatnost se středními zbrojemi, "
            "štíty a vojenskými zbraněmi.\n\n"
            "Vliv tvého patrona ti navíc umožňuje mysticky usměrnit svou vůli skrze konkrétní zbraň. "
            "Kdykoliv dokončíš dlouhý odpočinek, můžeš se dotknout jedné zbraně, se kterou jsi zdatný a která "
            "postrádá vlastnost obouruční. Když s touto zbraní útočíš, můžeš pro hody na útok a na zranění použít "
            "svou opravu Charismatu namísto Síly nebo Obratnosti. Tento prospěch trvá, dokud nedokončíš další dlouhý odpočinek.\n\n"
            "Pokud později získáš schopnost Pakt čepele (Pact of the Blade), tento prospěch se vztahuje na jakoukoliv zbraň paktu, "
            "kterou touto schopností vyvoláš, bez ohledu na typ zbraně."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {
            'source': "Xanathar's Guide to Everything",
            'archetype': 'The Hexblade (Čepelník)',
            'page': 55,
            'feature_type': 'Patron Feature (1st level)'
        }
    },
    {
        'api_index': 'shield',
        'name_cz': 'Štít',
        'name_en': 'Shield',
        'level': 1,
        'is_cantrip': False,
        'school': 'Vymítání',
        'school_en': 'Abjuration',
        'casting_time': '1 reakce (při zasažení útokem nebo zacílení magickou střelou)',
        'range': 'Sám sebe',
        'components': 'V, S',
        'material': '',
        'duration': '1 kolo',
        'concentration': False,
        'ritual': False,
        'attack_type': '',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Kouzlo sešleš jako reakci, když tě zasáhne útok nebo na tebe zacílí kouzlo Magická střela.\n\n"
            "Objeví se neviditelná bariéra magické síly a ochrání tě. Až do začátku tvého příštího tahu "
            "získáváš bonus +5 k OČ (AC), a to včetně spouštěcího útoku, a neutrpíš žádné poškození z kouzla Magická střela."
        ),
        'higher_levels': '',
        'classes': 'Čaroděj, Kouzelník, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {
            'source': "Player's Handbook 5e & Xanathar's Guide to Everything (The Hexblade Expanded Spell List)",
            'page': 275
        }
    },
    {
        'api_index': 'wrathful-smite',
        'name_cz': 'Hněvivý úder',
        'name_en': 'Wrathful Smite',
        'level': 1,
        'is_cantrip': False,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 bonusová akce',
        'range': 'Sám sebe',
        'components': 'V',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na blízko',
        'damage_type': 'Psychické',
        'damage_dice': '1k6',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Až v průběhu trvání tohoto kouzla příště zasáhneš tvora zbraní na blízko, tvůj útok způsobí "
            "dodatečné psychické zranění 1k6.\n\n"
            "Je-li cílem tvor, musí navíc uspět v záchranném hodu na Moudrost, jinak je z tebe vystrašený (frightened), "
            "dokud kouzlo neskončí. V rámci své akce může tvor provést ověření Moudrosti proti SO tvého kouzla, "
            "aby se vzpamatoval a ukončil kouzlo."
        ),
        'higher_levels': '',
        'classes': 'Paladin, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {
            'source': "Player's Handbook 5e & Xanathar's Guide to Everything (The Hexblade Expanded Spell List)",
            'page': 289
        }
    }
]
