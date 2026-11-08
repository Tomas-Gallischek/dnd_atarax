"""
Kompletní databáze kouzel, triků, schopností a vzývání pro Čepelníka (The Hexblade Warlock)
a Temného elfa (Drow) z příruček:
- Xanatharův průvodce vším (Xanathar's Guide to Everything - XGtE)
- Dobrodruhův průvodce Mečovým pobřežím / Tasha (SCAG / TCE blade cantrips)
- Příručka hráče D&D 5e (PHB - rozšířený seznam kouzel Hexblade a ikonická kouzla Černokněžníka)

Všechny položky obsahují příznak `is_xhantar = True` pro přehledné rozlišení v aplikaci.
"""

HEXBLADE_SPELLS_DATA = [
    # =========================================================================
    # 0. ÚROVEŇ — MAGICKÉ TRIKY PRO HEXBLADE A ČERNOKNĚŽNÍKA Z XANATHARA
    # =========================================================================
    {
        'api_index': 'booming-blade',
        'name_cz': 'Dunivá čepel',
        'name_en': 'Booming Blade',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': 'Sám sebe (okruh 1,5 m)',
        'components': 'S, M',
        'material': 'Zbraň pro boj zblízka v hodnotě alespoň 1 st',
        'duration': '1 kolo',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko',
        'damage_type': 'Hromové',
        'damage_dice': '1k8',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Máchnutím zbraně použité při sesílání kouzla provedeš útok na blízko proti jednomu tvorovi do 1,5 metru od tebe. "
            "Při zásahu utrpí cíl normální účinky útoku zbraní a poté je obklopen dunivou energií až do začátku tvého příštího tahu.\n\n"
            "Pokud se cíl do té doby dobrovolně pohne o 1,5 metru nebo více, utrpí okamžitě hromové zranění 1k8 a kouzlo skončí."
        ),
        'higher_levels': (
            "Na 5. úrovni postavy způsobí útok na blízko při zásahu dodatečné hromové zranění 1k8 a zranění za pohyb cíle se zvýší na 2k8. "
            "Obě zranění se zvyšují o dalších 1k8 na 11. úrovni (2k8 a 3k8) a 17. úrovni (3k8 a 4k8)."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': 'Elf, Temný elf',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide / SCAG / TCE", 'archetype': 'The Hexblade'}
    },
    {
        'api_index': 'green-flame-blade',
        'name_cz': 'Čepel zeleného plamene',
        'name_en': 'Green-Flame Blade',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': 'Sám sebe (okruh 1,5 m)',
        'components': 'S, M',
        'material': 'Zbraň pro boj zblízka v hodnotě alespoň 1 st',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko',
        'damage_type': 'Ohnivé',
        'damage_dice': '1k8 + CHA',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Máchnutím zbraně použité při sesílání kouzla provedeš útok na blízko proti jednomu tvorovi do 1,5 metru od tebe. "
            "Při zásahu utrpí cíl normální účinky útoku zbraní a ze zbraně přeskočí zelený plamen na jiného tvora dle tvé volby, "
            "kterého vidíš do 1,5 metru od původního cíle.\n\n"
            "Druhý tvor utrpí ohnivé zranění rovné tvé opravě sesílací vlastnosti (u černokněžníka Charisma)."
        ),
        'higher_levels': (
            "Na 5. úrovni postavy způsobí útok zblízka při zásahu cíli dodatečné ohnivé zranění 1k8 a ohnivé zranění druhému tvorovi "
            "se zvýší na 1k8 + oprava tvé sesílací vlastnosti. Obě zranění se zvýší o 1k8 na 11. úrovni (2k8 a 2k8) a 17. úrovni (3k8 a 3k8)."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': 'Elf, Temný elf',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide / SCAG / TCE", 'archetype': 'The Hexblade'}
    },
    {
        'api_index': 'sword-burst',
        'name_cz': 'Výbuch mečů',
        'name_en': 'Sword Burst',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': 'Sám sebe (okruh 1,5 m)',
        'components': 'V',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Silové',
        'damage_dice': '1k6',
        'saving_throw': 'Obratnost (DEX)',
        'heal_dice': '',
        'description': (
            "Vytvoříš chvilkový kruh přízračných čepelí, které se oženou kolem tebe. "
            "Každý tvor v okruhu 1,5 metru od tebe (kromě tebe) musí uspět v záchranném hodu na Obratnost, jinak utrpí silové zranění 1k6."
        ),
        'higher_levels': (
            "Zranění tohoto kouzla se zvyšuje o 1k6, když dosáhneš 5. úrovně (2k6), 11. úrovně (3k6) a 17. úrovně (4k6)."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide / SCAG / TCE", 'archetype': 'The Hexblade'}
    },
    {
        'api_index': 'lightning-lure',
        'name_cz': 'Bleskové laso',
        'name_en': 'Lightning Lure',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': 'Sám sebe (dosah 4,5 m)',
        'components': 'V',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko',
        'damage_type': 'Bleskové',
        'damage_dice': '1k8',
        'saving_throw': 'Síla (STR)',
        'heal_dice': '',
        'description': (
            "Vytvoříš bič bleskové energie, který udeří jednoho tvora dle tvé volby, kterého vidíš do 4,5 metru (15 stop) od tebe. "
            "Cíl musí uspět v záchranném hodu na Sílu, jinak je přitažen až o 3 metry (10 stop) v přímé linii směrem k tobě "
            "a poté utrpí bleskové zranění 1k8, pokud skončí do 1,5 metru od tebe."
        ),
        'higher_levels': (
            "Zranění kouzla se zvyšuje o 1k8 na 5. úrovni (2k8), 11. úrovni (3k8) a 17. úrovni (4k8)."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide / SCAG / TCE", 'archetype': 'The Hexblade'}
    },
    {
        'api_index': 'toll-the-dead',
        'name_cz': 'Zvonění mrtvým',
        'name_en': 'Toll the Dead',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Nekrotické',
        'damage_dice': '1k8 / 1k12',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Ukážeš na jednoho tvora, kterého vidíš v dosahu, a ve vzduchu kolem něj se na okamžik rozezní truchlivý zvuk zvonu. "
            "Cíl musí uspět v záchranném hodu na Moudrost, jinak utrpí nekrotické zranění 1k8.\n\n"
            "Pokud cíli již chybí nějaké životy (není na svém maximu HP), utrpí místo toho nekrotické zranění 1k12."
        ),
        'higher_levels': (
            "Zranění kouzla se zvyšuje o jednu kostku, když dosáhneš 5. úrovně (2k8 nebo 2k12), "
            "11. úrovně (3k8 nebo 3k12) a 17. úrovně (4k8 nebo 4k12)."
        ),
        'classes': 'Černokněžník, Klerik, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 169}
    },
    {
        'api_index': 'create-bonfire',
        'name_cz': 'Rozdělej oheň',
        'name_en': 'Create Bonfire',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Ohnivé',
        'damage_dice': '1k8',
        'saving_throw': 'Obratnost (DEX)',
        'heal_dice': '',
        'description': (
            "Na zemi v místě, které vidíš v dosahu, stvoříš magickou vanku ohně, která vyplní krychli o hraně 1,5 metru. "
            "Jakýkoliv tvor v místě ohně při seslání kouzla musí uspět v záchranném hodu na Obratnost, jinak utrpí ohnivé zranění 1k8. "
            "Tvor musí tento záchranný hod provést i tehdy, když do ohně vstoupí poprvé v tahu nebo v něm skončí svůj tah."
        ),
        'higher_levels': (
            "Zranění kouzla se zvyšuje o 1k8 na 5. úrovni (2k8), 11. úrovni (3k8) a 17. úrovni (4k8)."
        ),
        'classes': 'Černokněžník, Druid, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 152}
    },
    {
        'api_index': 'frostbite',
        'name_cz': 'Omrzliny',
        'name_en': 'Frostbite',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Chladové',
        'damage_dice': '1k6',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Způsobíš, že jednoho tvora, kterého vidíš v dosahu, pokryje umrtvující mráz. "
            "Cíl musí uspět v záchranném hodu na Odolnost. Při neúspěchu utrpí chladové zranění 1k6 "
            "a má nevýhodu k příštímu hodu na útok zbraní, který provede před koncem svého příštího tahu."
        ),
        'higher_levels': (
            "Zranění kouzla se zvyšuje o 1k6 na 5. úrovni (2k6), 11. úrovni (3k6) a 17. úrovni (4k6)."
        ),
        'classes': 'Černokněžník, Druid, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 156}
    },
    {
        'api_index': 'infestation',
        'name_cz': 'Zamoření',
        'name_en': 'Infestation',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': '9 metrů (30 stop)',
        'components': 'V, S, M',
        'material': 'Živá blecha',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Jedové',
        'damage_dice': '1k6',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Způsobíš, že jednoho tvora, kterého vidíš v dosahu, na okamžik zahalí oblak roztočů, blech a jiné havěti. "
            "Cíl musí uspět v záchranném hodu na Odolnost, jinak utrpí jedové zranění 1k6 a pohne se o 1,5 metru náhodným směrem "
            "(urči hodem k4: 1 - sever, 2 - jih, 3 - východ, 4 - západ). Tento pohyb nevyvolává příležitostné útoky."
        ),
        'higher_levels': (
            "Zranění kouzla se zvyšuje o 1k6 na 5. úrovni (2k6), 11. úrovni (3k6) a 17. úrovni (4k6)."
        ),
        'classes': 'Černokněžník, Druid, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 158}
    },
    {
        'api_index': 'magic-stone',
        'name_cz': 'Magický kámen',
        'name_en': 'Magic Stone',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Proměny',
        'school_en': 'Transmutation',
        'casting_time': '1 bonusová akce',
        'range': 'Dotyk',
        'components': 'V, S',
        'material': '',
        'duration': '1 minuta',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Drtivé',
        'damage_dice': '1k6 + CHA',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Dotkneš se jednoho až tří oblázků a naplníš je magií. Ty nebo kdokoliv jiný může s oblázkem provést "
            "útok kouzlem na dálku tak, že ho hodí (dosah 18 m) nebo vystřelí z praku. Při zásahu způsobí cíli drtivé zranění "
            "1k6 + tvá oprava sesílací vlastnosti (Charisma)."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Druid',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 160}
    },
    {
        'api_index': 'thunderclap',
        'name_cz': 'Zahřmění',
        'name_en': 'Thunderclap',
        'level': 0,
        'is_cantrip': True,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': 'Sám sebe (okruh 1,5 m)',
        'components': 'S',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Hromové',
        'damage_dice': '1k6',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Vytvoříš výbuch hromového zvuku, který je slyšet do vzdálenosti 30 metrů (100 stop). "
            "Každý tvor v okruhu 1,5 metru od tebe (kromě tebe) musí uspět v záchranném hodu na Odolnost, jinak utrpí hromové zranění 1k6."
        ),
        'higher_levels': (
            "Zranění kouzla se zvyšuje o 1k6 na 5. úrovni (2k6), 11. úrovni (3k6) a 17. úrovni (4k6)."
        ),
        'classes': 'Černokněžník, Bard, Druid, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/cantrip_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 168}
    },

    # =========================================================================
    # 1. ÚROVEŇ — HEXBLADE SCHOPNOSTI, ROZŠÍŘENÁ KOUZLA A XGtE 1. KRUH
    # =========================================================================
    {
        'api_index': 'hexblade-curse',
        'name_cz': 'Kletba čepelníka',
        'name_en': "Hexblade's Curse",
        'level': 1,
        'is_cantrip': False,
        'is_xhantar': True,
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
        'damage_dice': '+Zdatnost',
        'saving_throw': '',
        'heal_dice': 'Úroveň + CHA',
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
        'is_xhantar': True,
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
        'is_xhantar': True,
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
        'is_xhantar': True,
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
    },
    {
        'api_index': 'cause-fear',
        'name_cz': 'Vyvolej strach',
        'name_en': 'Cause Fear',
        'level': 1,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Probudíš pocit smrtelného strachu v jednom tvorovi, kterého vidíš v dosahu. Výtvory (konstrukty) a nemrtví "
            "jsou vůči tomuto účinku imunní. Cíl musí uspět v záchranném hodu na Moudrost, jinak se tě bojí (frightened), dokud kouzlo neskončí.\n\n"
            "Vystrašený cíl může zopakovat tento záchranný hod na konci každého svého tahu a při úspěchu pro něj účinek skončí."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo použitím pozice kouzla 2. nebo vyšší úrovně, můžeš zacílit jednoho tvora navíc za každou úroveň pozice nad 1. "
            "Tvorové se při zacílení musí nacházet do 9 metrů od sebe."
        ),
        'classes': 'Černokněžník, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 151}
    },
    {
        'api_index': 'hex',
        'name_cz': 'Uřknutí (Hex)',
        'name_en': 'Hex',
        'level': 1,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 bonusová akce',
        'range': '27 metrů (90 stop)',
        'components': 'V, S, M',
        'material': 'Zkamenělé oko mloka',
        'duration': 'Soustředění, až 1 hodina',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Zvláštní',
        'damage_type': 'Nekrotické',
        'damage_dice': '1k6',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Uvalíš kletbu na tvora, kterého vidíš v dosahu. Dokud kouzlo neskončí, způsobíš cíli dodatečné nekrotické zranění 1k6, "
            "kdykoliv ho zasáhneš útokem. Zvol také jednu vlastnost při seslání kouzla; cíl má nevýhodu na ověření zvolené vlastnosti.\n\n"
            "Pokud cíl klesne na 0 životů před skončením kouzla, můžeš v následujícím tahu jako bonusovou akci přenést kletbu na nového tvora."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice 3. nebo 4. úrovně, udržíš soustředění až 8 hodin. "
            "Při použití pozice 5. nebo vyšší úrovně udržíš soustředění až 24 hodin."
        ),
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Player's Handbook 5e & Hexblade Core", 'page': 251}
    },
    {
        'api_index': 'armor-of-agathys',
        'name_cz': 'Zbroj Agathys',
        'name_en': 'Armor of Agathys',
        'level': 1,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vymítání',
        'school_en': 'Abjuration',
        'casting_time': '1 akce',
        'range': 'Sám sebe',
        'components': 'V, S, M',
        'material': 'Pohár vody',
        'duration': '1 hodina',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Obranné',
        'damage_type': 'Chladové',
        'damage_dice': '5',
        'saving_throw': '',
        'heal_dice': '+5 dočasných HP',
        'description': (
            "Obklopí tě ochranná magická síla v podobě přízračné jinovatky, která pokryje tebe a tvou výzbroj. "
            "Na dobu trvání kouzla získáš 5 dočasných životů.\n\n"
            "Pokud tě tvor zasáhne útokem na blízko v době, kdy máš tyto dočasné životy, utrpí útočník chladové zranění 5."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo použitím pozice kouzla 2. nebo vyšší úrovně, jak dočasné životy, tak chladové zranění "
            "se zvýší o 5 za každou úroveň pozice nad 1."
        ),
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Player's Handbook 5e & Hexblade Core", 'page': 215}
    },
    {
        'api_index': 'arms-of-hadar',
        'name_cz': 'Hadarovy paže',
        'name_en': 'Arms of Hadar',
        'level': 1,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': 'Sám sebe (okruh 3 m)',
        'components': 'V, S',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Nekrotické',
        'damage_dice': '2k6',
        'saving_throw': 'Síla (STR)',
        'heal_dice': '',
        'description': (
            "Povoláš moc Hadara, Temného hladu. Z tebe vyrazí úponky temné energie a bičují všechny tvory do 3 metrů (10 stop) od tebe. "
            "Každý tvor v této oblasti musí provést záchranný hod na Sílu. Při neúspěchu utrpí nekrotické zranění 2k6 a nemůže brát reakce "
            "do svého příštího tahu. Při úspěchu utrpí poloviční zranění."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 2. nebo vyšší úrovně, zranění se zvýší o 1k6 za každou úroveň pozice nad 1."
        ),
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Player's Handbook 5e & Hexblade Core", 'page': 215}
    },

    # =========================================================================
    # 2. ÚROVEŇ — HEXBLADE ROZŠÍŘENÁ KOUZLA, STÍNOVÁ ČEPEL & VZÝVÁNÍ
    # =========================================================================
    {
        'api_index': 'blur',
        'name_cz': 'Rozmazání',
        'name_en': 'Blur',
        'level': 2,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Iluze',
        'school_en': 'Illusion',
        'casting_time': '1 akce',
        'range': 'Sám sebe',
        'components': 'V',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Obranné',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Tvé tělo se rozmaže, vlní a mihotá pro všechny, kdo tě vidí. Po dobu trvání má jakýkoliv tvor nevýhodu "
            "k hodům na útok proti tobě.\n\n"
            "Útočník je vůči tomuto účinku imunní, pokud se nespoléhá na zrak (např. má mimozrakové vnímání / blindsight) "
            "nebo dokáže prohlédnout iluze (např. pravdivé vidění / truesight)."
        ),
        'higher_levels': '',
        'classes': 'Čaroděj, Kouzelník, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'branding-smite',
        'name_cz': 'Cejchující úder',
        'name_en': 'Branding Smite',
        'level': 2,
        'is_cantrip': False,
        'is_xhantar': True,
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
        'damage_type': 'Zářivé',
        'damage_dice': '2k6',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Až v průběhu trvání tohoto kouzla příště zasáhneš tvora útokem zbraní, tvá zbraň zazáří astrální září. "
            "Útok způsobí cíli dodatečné zářivé zranění 2k6.\n\n"
            "Cíl se navíc stane viditelným, pokud je neviditelný, vyzařuje slabé světlo v okruhu 1,5 metru a nemůže se stát neviditelným, "
            "dokud kouzlo neskončí."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo použitím pozice kouzla 3. nebo vyšší úrovně, dodatečné zranění se zvýší o 1k6 za každou úroveň pozice nad 2."
        ),
        'classes': 'Paladin, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'shadow-blade',
        'name_cz': 'Stínová čepel',
        'name_en': 'Shadow Blade',
        'level': 2,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Iluze',
        'school_en': 'Illusion',
        'casting_time': '1 bonusová akce',
        'range': 'Sám sebe',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na blízko / Vrhací',
        'damage_type': 'Psychické',
        'damage_dice': '2k8',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Utkáš vlákna stínu a vytvoříš ve své ruce meč ze ztuhlé temnoty. Tento magický meč vydrží po dobu trvání kouzla. "
            "Počítá se jako jednoduchá zbraň pro boj zblízka, se kterou jsi zdatný. Při zásahu způsobuje psychické zranění 2k8 "
            "a má vlastnosti vytříbená (finesse), lehká (light) a vrhací (dostřel 6/18 metrů).\n\n"
            "Navíc, když mečem zaútočíš na cíl, který se nachází v šeru nebo ve tmě, máš k hodu na útok výhodu.\n"
            "Pokud meč upustíš nebo hodíš, na konci tahu se rozplyne, ale můžeš ho bonusovou akcí znovu vyvolat do své ruky."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice 3. nebo 4. úrovně, zranění se zvýší na 3k8. "
            "Při použití pozice 5. nebo 6. úrovně se zranění zvýší na 4k8. Při pozici 7. nebo vyšší úrovně činí zranění 5k8."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': 'Elf, Temný elf',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 164}
    },
    {
        'api_index': 'mind-spike',
        'name_cz': 'Hrot mysli',
        'name_en': 'Mind Spike',
        'level': 2,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Věštění',
        'school_en': 'Divination',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'S',
        'material': '',
        'duration': 'Soustředění, až 1 hodina',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Psychické',
        'damage_dice': '3k8',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Vrazíš hrot psychické energie do mysli jednoho tvora, kterého vidíš v dosahu. Cíl musí provést záchranný hod na Moudrost. "
            "Při neúspěchu utrpí psychické zranění 3k8, při úspěchu poloviční.\n\n"
            "Při neúspěšném záchranném hodu navíc po dobu trvání kouzla vždy víš, kde se cíl nachází (pokud jste ve stejné sféře existence), "
            "a cíl se před tebou nemůže schovat."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 3. nebo vyšší úrovně, zranění se zvýší o 1k8 za každou úroveň pozice nad 2."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 162}
    },
    {
        'api_index': 'earthbind',
        'name_cz': 'Připoutání k zemi',
        'name_en': 'Earthbind',
        'level': 2,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Proměny',
        'school_en': 'Transmutation',
        'casting_time': '1 akce',
        'range': '90 metrů (300 stop)',
        'components': 'V',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': 'Síla (STR)',
        'heal_dice': '',
        'description': (
            "Zvol jednoho tvora, kterého vidíš v dosahu. Žluté pruhy magické energie se ovinou kolem tvora. "
            "Cíl musí uspět v záchranném hodu na Sílu, jinak je jeho rychlost létání (pokud nějakou má) snížena na 0 stop po dobu trvání kouzla. "
            "Letící tvor zasažený tímto kouzlem bezpečně klesá rychlostí 18 metrů (60 stop) za kolo, dokud nedosedne na zem nebo kouzlo neskončí."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Druid, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 154}
    },
    {
        'api_index': 'improved-pact-weapon',
        'name_cz': 'Vylepšená zbraň paktu',
        'name_en': 'Improved Pact Weapon',
        'level': 2,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Proměny',
        'school_en': 'Transmutation',
        'casting_time': 'Pasivní / Rituál paktu',
        'range': 'Sám sebe',
        'components': 'V, S',
        'material': 'Zbraň paktu čepele',
        'duration': 'Trvalé (dokud máš Pakt čepele)',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko / Na dálku',
        'damage_type': 'Magické',
        'damage_dice': '+1 k útoku a zranění',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Starší vzývání Paktu čepele z Xanatharova průvodce vším:\n"
            "• Jakoukoliv zbraň, kterou vyvoláš pomocí schopnosti Pakt čepele, můžeš používat jako sesílací ohnisko pro svá kouzla černokněžníka.\n"
            "• Zbraň paktu získává bonus +1 k hodům na útok a na zranění, pokud již není magickou zbraní s tímto či vyšším bonusem.\n"
            "• Tvá zbraň paktu může mít i podobu krátkého luku, dlouhého luku, lehké kuše nebo těžké kuše."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 57, 'feature_type': 'Eldritch Invocation'}
    },

    # =========================================================================
    # 3. ÚROVEŇ — HEXBLADE ROZŠÍŘENÁ KOUZLA, PŘÍZRAK, VZÝVÁNÍ & XGtE 3. KRUH
    # =========================================================================
    {
        'api_index': 'blink',
        'name_cz': 'Mžik',
        'name_en': 'Blink',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Proměny',
        'school_en': 'Transmutation',
        'casting_time': '1 akce',
        'range': 'Sám sebe',
        'components': 'V, S',
        'material': '',
        'duration': '1 minuta',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Obranné / Přesun',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Na konci každého svého tahu po dobu trvání kouzla hoď k20. Při hodu 11 nebo více zmizíš ze své současné sféry existence "
            "a objevíš se v Éterické sféře.\n\n"
            "Na začátku svého příštího tahu se vrátíš na tebou zvolené volné místo do 3 metrů (10 stop) od místa, ze kterého jsi zmizel. "
            "Dokud jsi v Éterické sféře, jsi vidět a slyšet jen pro tvory v ní a nemůžeš být zasažen útoky ani kouzly z původní sféry."
        ),
        'higher_levels': '',
        'classes': 'Čaroděj, Kouzelník, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'elemental-weapon',
        'name_cz': 'Živelná zbraň',
        'name_en': 'Elemental Weapon',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Proměny',
        'school_en': 'Transmutation',
        'casting_time': '1 akce',
        'range': 'Dotyk',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 hodina',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Posílení zbraně',
        'damage_type': 'Kyselinové / Chladové / Ohnivé / Bleskové / Hromové',
        'damage_dice': '+1 útok, +1k4 zranění',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Nemagická zbraň, které se dotkneš, se stane magickou zbraní. Zvol jeden z následujících typů poškození: "
            "kyselinové, chladové, ohnivé, bleskové nebo hromové.\n\n"
            "Po dobu trvání má zbraň bonus +1 k hodům na útok a při zásahu způsobuje dodatečné zranění 1k4 zvoleného typu."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice 5. nebo 6. úrovně, bonus k útoku se zvýší na +2 a dodatečné zranění na 2k4. "
            "Při použití pozice 7. nebo vyšší úrovně se bonus zvýší na +3 a dodatečné zranění na 3k4."
        ),
        'classes': 'Paladin, Černokněžník, Druid, Hraničář',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'accursed-specter',
        'name_cz': 'Prokletý přízrak',
        'name_en': 'Accursed Specter',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 reakce (při zabití humanoida)',
        'range': '18 metrů (60 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Do příštího dlouhého odpočinku',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Vyvolání nemrtvého',
        'damage_type': 'Nekrotické',
        'damage_dice': '3k6',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Schopnost Čepelníka (od 6. úrovně černokněžníka): Můžeš proklít duši člověka či humanoida, kterého zabiješ, "
            "a dočasně ji připoutat ke své službě. Když zabiješ humanoida, můžeš způsobit, že z jeho mrtvoly povstane Přízrak (Specter).\n\n"
            "Přízrak získá dočasné životy rovné polovině tvé úrovně černokněžníka, má vlastní iniciativu, poslouchá tvé slovní příkazy "
            "a získává bonus k hodům na útok rovný tvé opravě Charismatu (minimálně +0). Slouží ti až do tvého příštího dlouhého odpočinku."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 56, 'feature_type': 'Patron Feature (6th level)'}
    },
    {
        'api_index': 'eldritch-smite',
        'name_cz': 'Tajemný úder',
        'name_en': 'Eldritch Smite',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': 'Při zásahu zbraní paktu (1x za tah)',
        'range': 'Sám sebe',
        'components': 'Zbraň paktu',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko / Na dálku',
        'damage_type': 'Silové',
        'damage_dice': '1k8 + 1k8 za úroveň pozice',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Starší vzývání Paktu čepele z Xanatharova průvodce vším (od 5. úrovně černokněžníka):\n"
            "Jednou za tah, když zasáhneš tvora svou zbraní paktu, můžeš utratit kouzelnou pozici černokněžníka a způsobit cíli "
            "dodatečné silové zranění 1k8 plus dalších 1k8 za každou úroveň utracené kouzelné pozice.\n\n"
            "Navíc pokud je cíl Obrovský (Huge) nebo menší, můžeš ho tímto úderem automaticky srazit k zemi (prone) bez záchranného hodu."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 56, 'feature_type': 'Eldritch Invocation'}
    },
    {
        'api_index': 'thirsting-blade',
        'name_cz': 'Žíznivá čepel',
        'name_en': 'Thirsting Blade',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Proměny',
        'school_en': 'Transmutation',
        'casting_time': 'Pasivní (při akci Útok)',
        'range': 'Sám sebe',
        'components': 'Zbraň paktu',
        'material': '',
        'duration': 'Trvalé',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko / Na dálku',
        'damage_type': '',
        'damage_dice': '2x útok za akci',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Starší vzývání Paktu čepele (od 5. úrovně černokněžníka):\n"
            "Se svou zbraní paktu můžeš zaútočit dvakrát namísto jednou, kdykoliv ve svém tahu provedeš akci Útok."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Player's Handbook 5e & Hexblade Core", 'page': 111, 'feature_type': 'Eldritch Invocation'}
    },
    {
        'api_index': 'maddening-hex',
        'name_cz': 'Šílená kletba',
        'name_en': 'Maddening Hex',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 bonusová akce',
        'range': '9 metrů (30 stop)',
        'components': 'V',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Psychické',
        'damage_dice': 'Oprava CHA (min. 1)',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Starší vzývání z Xanatharova průvodce vším (od 5. úrovně černokněžníka):\n"
            "Jako bonusovou akci způsobíš psychické poruchy kolem cíle prokletého tvým kouzlem Uřknutí (Hex) nebo schopností "
            "Kletba čepelníka (Hexblade's Curse).\n\n"
            "Když tak učiníš, způsobíš psychické zranění prokletému cíli a každému tvorovi dle své volby, kterého vidíš do 1,5 metru "
            "od prokletého cíle. Psychické zranění se rovná tvé opravě Charismatu (minimálně 1). Pro použití této schopnosti musíš prokletý cíl vidět "
            "a nesmí být dále než 9 metrů od tebe."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 57, 'feature_type': 'Eldritch Invocation'}
    },
    {
        'api_index': 'thunder-step',
        'name_cz': 'Hromový krok',
        'name_en': 'Thunder Step',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': '27 metrů (90 stop)',
        'components': 'V',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Plošný efekt / Teleport',
        'damage_type': 'Hromové',
        'damage_dice': '3k10',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Teleportuješ se na volné místo, které vidíš v dosahu. Bezprostředně po tvém zmizení zahřmí ohlušující rána "
            "a každý tvor do 3 metrů (10 stop) od místa, které jsi opustil, musí provést záchranný hod na Odolnost. "
            "Při neúspěchu utrpí hromové zranění 3k10, při úspěchu poloviční. Hřmění je slyšet do vzdálenosti 90 metrů.\n\n"
            "S sebou můžeš vzít i jednoho dobrovolného tvora tvé nebo menší velikosti, který stojí do 1,5 metru od tebe."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 4. nebo vyšší úrovně, zranění se zvýší o 1k10 za každou úroveň pozice nad 3."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 168}
    },
    {
        'api_index': 'summon-lesser-demons',
        'name_cz': 'Vyvolej nižší démony',
        'name_en': 'Summon Lesser Demons',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, S, M',
        'material': 'Lahvička krve z humanoida zabitého během posledních 24 hodin',
        'duration': 'Soustředění, až 1 hodina',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Vyvolávání',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Vyslovíš rouhavá slova a povoláš démony z chaosu Propasti. Hoď k6 pro určení, co se objeví:\n"
            "• 1–2: Dva démoni s CR 1 nebo nižším\n"
            "• 3–4: Čtyři démoni s CR 1/2 nebo nižším\n"
            "• 5–6: Osm démonů s CR 1/4 nebo nižším\n\n"
            "Démoni jsou nepřátelští ke všem tvorům včetně tebe. V rámci sesílání můžeš krví nakreslit kruh na zemi kolem sebe, "
            "do kterého vyvolaní démoni nemohou vstoupit ani na nikoho uvnitř zaútočit."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice 6. nebo 7. úrovně, vyvoláš dvojnásobný počet démonů. "
            "Při použití pozice 8. nebo 9. úrovně vyvoláš trojnásobný počet démonů."
        ),
        'classes': 'Černokněžník, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 167}
    },
    {
        'api_index': 'enemies-abound',
        'name_cz': 'Nepřátelé všude kolem',
        'name_en': 'Enemies Abound',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 akce',
        'range': '36 metrů (120 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': 'Inteligence (INT)',
        'heal_dice': '',
        'description': (
            "Sáhneš do mysli jednoho tvora, kterého vidíš v dosahu, a přinutíš ho provést záchranný hod na Inteligenci. "
            "Tvor automaticky uspěje, pokud je imunní vůči vystrašení.\n\n"
            "Při neúspěchu ztratí cíl schopnost rozlišovat přátele od nepřátel a považuje všechny tvory, které vidí, za nepřátele. "
            "Kdykoliv si zasažený tvor vybírá cíl útoku či kouzla, musí náhodně vybrat z tvorů v dosahu. "
            "Kdykoliv utrpí zranění, může zopakovat záchranný hod na Inteligenci."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Bard, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 155}
    },
    {
        'api_index': 'hunger-of-hadar',
        'name_cz': 'Hadarův hlad',
        'name_en': 'Hunger of Hadar',
        'level': 3,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': '45 metrů (150 stop)',
        'components': 'V, S, M',
        'material': 'Nakládané chapadlo chobotnice',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Chladové + Kyselinové',
        'damage_dice': '2k6 + 2k6',
        'saving_throw': 'Obratnost (DEX)',
        'heal_dice': '',
        'description': (
            "Otevřeš bránu do temnoty mezi hvězdami, oblasti zamořené neznámými hrůzami. Koule černoty a mrazu o poloměru 6 metrů (20 stop) "
            "se objeví v bodě v dosahu. Oblast je těžkým terénem a tvory uvnitř zcela oslepí.\n\n"
            "Každý tvor, který v oblasti začne svůj tah, utrpí chladové zranění 2k6. Každý tvor, který v oblasti skončí svůj tah, "
            "musí uspět v záchranném hodu na Obratnost, jinak utrpí kyselinové zranění 2k6 od mléčně bílých chapadel."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Player's Handbook 5e & Hexblade Core", 'page': 251}
    },

    # =========================================================================
    # 4. ÚROVEŇ — HEXBLADE ROZŠÍŘENÁ KOUZLA, MOILŮV STÍN, VZÝVÁNÍ & XGtE 4. KRUH
    # =========================================================================
    {
        'api_index': 'phantasmal-killer',
        'name_cz': 'Přízračný zabiják',
        'name_en': 'Phantasmal Killer',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Iluze',
        'school_en': 'Illusion',
        'casting_time': '1 akce',
        'range': '36 metrů (120 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Psychické',
        'damage_dice': '4k10',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Pronikneš do nočních můr tvora, kterého vidíš v dosahu, a vytvoříš iluzorní zhmotnění jeho nejhlubších strachů, "
            "viditelné pouze pro tohoto tvora. Cíl musí provést záchranný hod na Moudrost.\n\n"
            "Při neúspěchu se cíl stane vystrašeným (frightened) po dobu trvání kouzla. Na konci každého ze svých tahů před skončením kouzla "
            "musí cíl uspět v záchranném hodu na Moudrost, jinak utrpí psychické zranění 4k10. Při úspěšném záchranném hodu kouzlo skončí."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 5. nebo vyšší úrovně, zranění se zvýší o 1k10 za každou úroveň pozice nad 4."
        ),
        'classes': 'Kouzelník, Bard, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'staggering-smite',
        'name_cz': 'Ohromující úder',
        'name_en': 'Staggering Smite',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
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
        'damage_dice': '4k6',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Až v průběhu trvání tohoto kouzla příště zasáhneš tvora útokem zbraní na blízko, tvá zbraň pronikne jak tělem, tak myslí "
            "a útok způsobí cíli dodatečné psychické zranění 4k6.\n\n"
            "Cíl musí navíc provést záchranný hod na Moudrost. Při neúspěchu má nevýhodu k hodům na útok a ověřením vlastností "
            "a nemůže brát reakce až do konce svého příštího tahu."
        ),
        'higher_levels': '',
        'classes': 'Paladin, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'shadow-of-moil',
        'name_cz': 'Moilův stín',
        'name_en': 'Shadow of Moil',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 akce',
        'range': 'Sám sebe',
        'components': 'V, S, M',
        'material': 'Oko nemrtvého zapouzdřené v drahokamu v hodnotě alespoň 150 zl',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Obranné / Odveta',
        'damage_type': 'Nekrotické',
        'damage_dice': '2k8',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Kolem tvého těla tančí plamenům podobné stíny po dobu trvání kouzla a způsobují, že jsi pro ostatní těžce zahalený (heavily obscured) "
            "— útočníci mají proti tobě nevýhodu a ty máš výhodu k útokům proti nim! Stíny mění jasné světlo do 3 metrů od tebe na šero "
            "a šero v téže oblasti na tmu.\n\n"
            "Dokud kouzlo neskončí, máš odolnost vůči zářivému (radiant) zranění. Navíc kdykoliv tě tvor do 3 metrů (10 stop) od tebe "
            "zasáhne útokem, stíny po něm vyšlehnou a způsobí mu nekrotické zranění 2k8."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': 'Elf, Temný elf',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 164}
    },
    {
        'api_index': 'relentless-hex',
        'name_cz': 'Neúprosná kletba',
        'name_en': 'Relentless Hex',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 bonusová akce',
        'range': '9 metrů (30 stop)',
        'components': 'V',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Teleportace',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Starší vzývání z Xanatharova průvodce vším (od 7. úrovně černokněžníka):\n"
            "Tvá kletba vytváří dočasné pouto mezi tebou a tvým cílem. Jako bonusovou akci se můžeš magicky teleportovat "
            "až o 9 metrů (30 stop) na volné místo, které vidíš do 1,5 metru od cíle prokletého tvým kouzlem Uřknutí (Hex) "
            "nebo schopností Kletba čepelníka (Hexblade's Curse).\n\n"
            "Abys se mohl tímto způsobem teleportovat, musíš prokletý cíl vidět."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 57, 'feature_type': 'Eldritch Invocation'}
    },
    {
        'api_index': 'sickening-radiance',
        'name_cz': 'Chorobná záře',
        'name_en': 'Sickening Radiance',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': '36 metrů (120 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 10 minut',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Zářivé',
        'damage_dice': '4k10',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Z bodu, který zvolíš v dosahu, se šíří nazelenalé slabé světlo a vyplní kouli o poloměru 9 metrů (30 stop). "
            "Když se tvor poprvé v tahu přesune do oblasti kouzla nebo tam začne svůj tah, musí uspět v záchranném hodu na Odolnost, "
            "jinak utrpí zářivé zranění 4k10, utrpí 1 stupeň vyčerpání (exhaustion) a vyzařuje slabé zelené světlo v okruhu 1,5 metru, "
            "které znemožňuje neviditelnost."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 164}
    },
    {
        'api_index': 'charm-monster',
        'name_cz': 'Okouzli nestvůru',
        'name_en': 'Charm Monster',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 akce',
        'range': '9 metrů (30 stop)',
        'components': 'V, S',
        'material': '',
        'duration': '1 hodina',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Pokusíš se zmámit jednoho tvora jakéhokoliv typu, kterého vidíš v dosahu. Cíl musí provést záchranný hod na Moudrost "
            "(s výhodou, pokud s ním ty nebo tví společníci bojujete). Pokud neuspěje, je tebou zmámený (charmed), dokud kouzlo neskončí "
            "nebo dokud mu ty či tví společníci neublížíte. Zmámený tvor tě považuje za přátelského známého."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 5. nebo vyšší úrovně, můžeš zacílit jednoho tvora navíc za každou úroveň pozice nad 4."
        ),
        'classes': 'Černokněžník, Bard, Druid, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 151}
    },
    {
        'api_index': 'elemental-bane',
        'name_cz': 'Živelná zhouba',
        'name_en': 'Elemental Bane',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Proměny',
        'school_en': 'Transmutation',
        'casting_time': '1 akce',
        'range': '27 metrů (90 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Kyselinové / Chladové / Ohnivé / Bleskové / Hromové',
        'damage_dice': '2k6',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Zvol jednoho tvora, kterého vidíš v dosahu, a zvol jeden z typů zranění: kyselinové, chladové, ohnivé, bleskové nebo hromové. "
            "Cíl musí uspět v záchranném hodu na Odolnost, jinak je ovlivněn kouzlem po dobu jeho trvání.\n\n"
            "Poprvé v každém tahu, kdy zasažený cíl utrpí zranění zvoleného typu, utrpí dodatečné zranění 2k6 téhož typu. "
            "Cíl navíc ztrácí jakoukoliv odolnost vůči tomuto typu zranění, dokud kouzlo neskončí."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 5. nebo vyšší úrovně, můžeš zacílit jednoho tvora navíc za každou úroveň pozice nad 4."
        ),
        'classes': 'Černokněžník, Druid, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 155}
    },
    {
        'api_index': 'summon-greater-demon',
        'name_cz': 'Vyvolej vyššího démona',
        'name_en': 'Summon Greater Demon',
        'level': 4,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, S, M',
        'material': 'Lahvička krve z humanoida zabitého během posledních 24 hodin',
        'duration': 'Soustředění, až 1 hodina',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Vyvolávání',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': 'Charisma (CHA)',
        'heal_dice': '',
        'description': (
            "Vyslovíš rouhavá slova a povoláš jednoho démona z Propasti s nebezpečností (CR) 5 nebo nižší. "
            "Démon se objeví na volném místě, které vidíš v dosahu, a poslouchá tvé příkazy.\n\n"
            "Na konci každého ze svých tahů provede démon záchranný hod na Charisma (s nevýhodou, pokud znáš jeho pravé jméno). "
            "Při úspěchu se vymaní z tvé kontroly a útočí na nejbližší nedémonické tvory."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 5. nebo vyšší úrovně, maximální CR démona se zvýší o 1 za každou úroveň pozice nad 4."
        ),
        'classes': 'Černokněžník, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 166}
    },

    # =========================================================================
    # 5. ÚROVEŇ — HEXBLADE ROZŠÍŘENÁ KOUZLA, ZBROJ KLETEB & XGtE 5. KRUH
    # =========================================================================
    {
        'api_index': 'banishing-smite',
        'name_cz': 'Vyhošťující úder',
        'name_en': 'Banishing Smite',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vymítání',
        'school_en': 'Abjuration',
        'casting_time': '1 bonusová akce',
        'range': 'Sám sebe',
        'components': 'V',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na blízko',
        'damage_type': 'Silové',
        'damage_dice': '5k10',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Až v průběhu trvání tohoto kouzla příště zasáhneš tvora útokem zbraní, tvá zbraň zapraská silou "
            "a tvůj útok způsobí cíli dodatečné silové zranění 5k10.\n\n"
            "Navíc pokud tento útok sníží životy cíle na 50 nebo méně, vyhostíš ho. Pokud cíl pochází z jiné sféry existence, "
            "vrátí se do své domovské sféry; jinak je přenesen do neškodné polosféry, kde je vyřazený z boje, dokud kouzlo neskončí."
        ),
        'higher_levels': '',
        'classes': 'Paladin, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'cone-of-cold',
        'name_cz': 'Kužel mrazu',
        'name_en': 'Cone of Cold',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': 'Sám sebe (kužel 18 m)',
        'components': 'V, S, M',
        'material': 'Malý křišťálový nebo skleněný kužel',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Chladové',
        'damage_dice': '8k8',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Z tvých rukou vytryskne závan ledového vzduchu v kuželu o délce 18 metrů (60 stop). "
            "Každý tvor v této oblasti musí provést záchranný hod na Odolnost.\n\n"
            "Při neúspěchu utrpí chladové zranění 8k8, při úspěchu poloviční. Tvor zabitý tímto kouzlem se promění v zamrzlou sochu, "
            "dokud neroztaje."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 6. nebo vyšší úrovně, zranění se zvýší o 1k8 za každou úroveň pozice nad 5."
        ),
        'classes': 'Čaroděj, Kouzelník, Druid, Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything (The Hexblade Expanded Spell List)", 'page': 55}
    },
    {
        'api_index': 'armor-of-hexes',
        'name_cz': 'Zbroj kleteb',
        'name_en': 'Armor of Hexes',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vymítání',
        'school_en': 'Abjuration',
        'casting_time': '1 reakce (při zásahu od prokletého cíle)',
        'range': 'Sám sebe',
        'components': 'Žádné',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Obranné',
        'damage_type': '',
        'damage_dice': 'Hod k6 (4–6 = minutí)',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Schopnost Čepelníka (od 10. úrovně černokněžníka): Tvá kletba sílí. "
            "Pokud tě tvor prokletý tvou Kletbou čepelníka (Hexblade's Curse) zasáhne hodem na útok, můžeš jako reakci hodit k6.\n\n"
            "Při hodu 4 nebo více tě tento útok namísto zásahu automaticky mine, bez ohledu na to, kolik útočník hodil na kostce."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 56, 'feature_type': 'Patron Feature (10th level)'}
    },
    {
        'api_index': 'far-step',
        'name_cz': 'Daleký krok',
        'name_en': 'Far Step',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 bonusová akce',
        'range': 'Sám sebe',
        'components': 'V',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Teleportace',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Teleportuješ se až o 18 metrů (60 stop) na volné místo, které vidíš. "
            "V každém svém tahu před skončením kouzla můžeš použít bonusovou akci a teleportovat se tímto způsobem znovu."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 155}
    },
    {
        'api_index': 'synaptic-static',
        'name_cz': 'Synaptický šum',
        'name_en': 'Synaptic Static',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 akce',
        'range': '36 metrů (120 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Psychické',
        'damage_dice': '8k6',
        'saving_throw': 'Inteligence (INT)',
        'heal_dice': '',
        'description': (
            "Zvol bod v dosahu a způsobíš výbuch psychické energie v kouli o poloměru 6 metrů (20 stop). "
            "Každý tvor v oblasti musí provést záchranný hod na Inteligenci. Při neúspěchu utrpí psychické zranění 8k6, při úspěchu poloviční.\n\n"
            "Po neúspěšném záchranném hodu má cíl zmatené myšlenky po dobu 1 minuty: během této doby si musí odečíst 1k6 od všech svých "
            "hodů na útok, ověření vlastností a záchranných hodů na Odolnost pro udržení soustředění."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Bard, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 167}
    },
    {
        'api_index': 'negative-energy-flood',
        'name_cz': 'Příval negativní energie',
        'name_en': 'Negative Energy Flood',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, M',
        'material': 'Zlomená kost a čtvereček černého hedvábí',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Nekrotické',
        'damage_dice': '5k12',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Vyšleš stuhy negativní energie na jednoho tvora, kterého vidíš v dosahu. Pokud cíl není nemrtvý, musí provést záchranný hod "
            "na Odolnost. Při neúspěchu utrpí nekrotické zranění 5k12, při úspěchu poloviční. Tvor zabitý tímto zraněním povstane jako zombie "
            "na začátku tvého příštího tahu.\n\n"
            "Pokud zacílíš nemrtvého, neutrpí zranění a místo toho získá dočasné životy ve výši poloviny hodu 5k12."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 163}
    },
    {
        'api_index': 'enervation',
        'name_cz': 'Vysílení',
        'name_en': 'Enervation',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Nekrotické',
        'damage_dice': '4k8',
        'saving_throw': 'Obratnost (DEX)',
        'heal_dice': 'Polovina způsobeného zranění',
        'description': (
            "Úponek inkoustové temnoty vystřelí z tebe a dotkne se jednoho tvora, kterého vidíš v dosahu, aby z něj vysál život. "
            "Cíl musí provést záchranný hod na Obratnost. Při úspěchu utrpí nekrotické zranění 2k8 a kouzlo skončí.\n\n"
            "Při neúspěchu utrpí cíl nekrotické zranění 4k8 a až do skončení kouzla můžeš v každém svém tahu jako akci automaticky způsobit "
            "cíli nekrotické zranění 4k8. Kdykoliv kouzlo způsobí cíli zranění, obnovíš si životy ve výši poloviny způsobeného nekrotického zranění."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 6. nebo vyšší úrovně, zranění se zvýší o 1k8 za každou úroveň pozice nad 5."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 155}
    },
    {
        'api_index': 'danse-macabre',
        'name_cz': 'Tanec smrti',
        'name_en': 'Danse Macabre',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V, S',
        'material': '',
        'duration': 'Soustředění, až 1 hodina',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Vyvolávání nemrtvých',
        'damage_type': '',
        'damage_dice': '+CHA k útoku a zranění nemrtvých',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Vlákna temné moci vytrysknou z tvých prstů a probudí až pět Malých nebo Středních mrtvol, které vidíš v dosahu. "
            "Každá mrtvola okamžitě povstane a stane se nemrtvým (Kostlivec nebo Zombie) pod tvou kontrolou.\n\n"
            "Jako bonusovou akci jim můžeš v každém svém tahu udělit příkaz. Vyvolaní nemrtví si přičítají tvou opravu sesílací vlastnosti (CHA) "
            "ke svým hodům na útok a na zranění."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 6. nebo vyšší úrovně, můžeš oživit až dvě mrtvoly navíc za každou úroveň pozice nad 5."
        ),
        'classes': 'Černokněžník, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 153}
    },
    {
        'api_index': 'wall-of-light',
        'name_cz': 'Zeď světla',
        'name_en': 'Wall of Light',
        'level': 5,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': '36 metrů (120 stop)',
        'components': 'V, S, M',
        'material': 'Ruční zrcátko',
        'duration': 'Soustředění, až 10 minut',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Plošný efekt / Na dálku',
        'damage_type': 'Zářivé',
        'damage_dice': '4k8',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Třpytivá zeď jasného světla se objeví v bodě v dosahu (až 18 m dlouhá, 3 m vysoká a 1,5 m silná). "
            "Když se zeď objeví, každý tvor v její oblasti musí provést záchranný hod na Odolnost. Při neúspěchu utrpí zářivé zranění 4k8 "
            "a je na 1 minutu slepý (blinded). Tvor, který skončí svůj tah ve zdi, utrpí zářivé zranění 4k8.\n\n"
            "Dokud kouzlo trvá, můžeš jako akci vystřelit ze zdi paprsek světla na jednoho tvora do 18 metrů od ní (útok kouzlem na dálku, "
            "při zásahu zářivé zranění 4k8)."
        ),
        'higher_levels': (
            "Když sešleš toto kouzlo pomocí pozice kouzla 6. nebo vyšší úrovně, zranění se zvýší o 1k8 za každou úroveň pozice nad 5."
        ),
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 170}
    },

    # =========================================================================
    # 6. AŽ 9. ÚROVEŇ — MYSTIC ARCANUM, PIJÁK ŽIVOTA & MISTR KLETEB (XGtE)
    # =========================================================================
    {
        'api_index': 'lifedrinker',
        'name_cz': 'Piják života',
        'name_en': 'Lifedrinker',
        'level': 6,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': 'Pasivní (při zásahu zbraní paktu)',
        'range': 'Sám sebe',
        'components': 'Zbraň paktu',
        'material': '',
        'duration': 'Trvalé',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na blízko / Na dálku',
        'damage_type': 'Nekrotické',
        'damage_dice': '+Oprava CHA (min. +1)',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Starší vzývání Paktu čepele (od 12. úrovně černokněžníka):\n"
            "Když zasáhneš tvora svou zbraní paktu, tvor utrpí dodatečné nekrotické zranění rovné tvé opravě Charismatu (minimálně 1)."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Player's Handbook 5e & Hexblade Core", 'page': 111, 'feature_type': 'Eldritch Invocation'}
    },
    {
        'api_index': 'soul-cage',
        'name_cz': 'Klec duší',
        'name_en': 'Soul Cage',
        'level': 6,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Nekromancie',
        'school_en': 'Necromancy',
        'casting_time': '1 reakce (když humanoid do 18 m zemře)',
        'range': '18 metrů (60 stop)',
        'components': 'V, S, M',
        'material': 'Drobná stříbrná klec v hodnotě 100 zl',
        'duration': '8 hodin',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Zvláštní',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '2k8',
        'description': (
            "Toto kouzlo polapí duši humanoida v okamžiku jeho smrti a uvězní ji v drobné stříbrné kleci. "
            "Uvězněnou duši můžeš využít až šestkrát před skončením kouzla (jako bonusovou akci):\n"
            "• Ukrást život: Obnovíš si 2k8 životů.\n"
            "• Vyzvídat duši: Položíš duši otázku a ona musí pravdivě odpovědět.\n"
            "• Půjčit si zkušenost: Získáš výhodu k příštímu hodu na útok, ověření vlastnosti nebo záchrannému hodu.\n"
            "• Oči mrtvého: Vidíš očima uvězněné duše na libovolné místo, které za života znala."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 165}
    },
    {
        'api_index': 'mental-prison',
        'name_cz': 'Mentální vězení',
        'name_en': 'Mental Prison',
        'level': 6,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Iluze',
        'school_en': 'Illusion',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'S',
        'material': '',
        'duration': 'Soustředění, až 1 minuta',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': 'Psychické',
        'damage_dice': '5k10 (+10k10)',
        'saving_throw': 'Inteligence (INT)',
        'heal_dice': '',
        'description': (
            "Pokusíš se uvěznit tvora v iluzorní cele, kterou vnímá pouze on. Cíl musí provést záchranný hod na Inteligenci. "
            "Utrpí psychické zranění 5k10 bez ohledu na výsledek hodu, při úspěchu kouzlo skončí.\n\n"
            "Při neúspěchu je oblast kolem cíle zdánlivě obklopena nebezpečím (oheň, čepele, tlamy). Cíl je zadržený (restrained) "
            "a nevidí ani neslyší nic mimo svou celu. Pokud se pohne z místa nebo provede útok skrze iluzi, utrpí další psychické zranění 10k10 a kouzlo skončí."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 161}
    },
    {
        'api_index': 'scatter',
        'name_cz': 'Rozptýlení',
        'name_en': 'Scatter',
        'level': 6,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Vyvolávání',
        'school_en': 'Conjuration',
        'casting_time': '1 akce',
        'range': '9 metrů (30 stop)',
        'components': 'V',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Teleportace',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Vzduch kolem až pěti tvorů dle tvé volby, které vidíš v dosahu, se zachvěje. Nedobrovolný tvor musí uspět "
            "v záchranném hodu na Moudrost, aby odolal. Každého zasaženého tvora teleportuješ na volné místo, které vidíš "
            "do 36 metrů (120 stop) od sebe (místo musí být na zemi nebo na podlaze)."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 164}
    },
    {
        'api_index': 'master-of-hexes',
        'name_cz': 'Mistr kleteb',
        'name_en': 'Master of Hexes',
        'level': 7,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': 'Bez akce (při smrti prokletého cíle)',
        'range': '9 metrů (30 stop)',
        'components': 'Žádné',
        'material': '',
        'duration': 'Po zbytek trvání Kletby čepelníka',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Zvláštní',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Schopnost Čepelníka (od 14. úrovně černokněžníka): Můžeš snadno šířit svou Kletbu čepelníka z jednoho padlého nepřítele na druhého.\n\n"
            "Když zemře tvor prokletý tvou Kletbou čepelníka (Hexblade's Curse), můžeš kletbu okamžitě uvalit na jiného tvora, "
            "kterého vidíš do 9 metrů (30 stop) od sebe, pokud nejsi vyřazený z boje. Když kletbu tímto způsobem přeneseš, "
            "neobnovíš si životy ze smrti předchozího prokletého tvora."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 56, 'feature_type': 'Patron Feature (14th level)'}
    },
    {
        'api_index': 'crown-of-stars',
        'name_cz': 'Koruna hvězd',
        'name_en': 'Crown of Stars',
        'level': 7,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': 'Sám sebe',
        'components': 'V, S',
        'material': '',
        'duration': '1 hodina',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku (bonusová akce)',
        'damage_type': 'Zářivé',
        'damage_dice': '4k12 (7 hvězd)',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Sedm hvězdám podobných motelek světla se objeví a obíhá kolem tvé hlavy, dokud kouzlo neskončí. "
            "Jako bonusovou akci můžeš vyslat jednu z hvězd na jednoho tvora nebo předmět do 36 metrů (120 stop) od tebe.\n\n"
            "Proveď útok kouzlem na dálku. Při zásahu utrpí cíl zářivé zranění 4k12. Po vypálení sedmé hvězdy kouzlo skončí."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 152}
    },
    {
        'api_index': 'power-word-pain',
        'name_cz': 'Slovo moci: Bolest',
        'name_en': 'Power Word Pain',
        'level': 7,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 akce',
        'range': '18 metrů (60 stop)',
        'components': 'V',
        'material': '',
        'duration': 'Ihned / Do úspěšné záchrany',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Na dálku',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': 'Odolnost (CON)',
        'heal_dice': '',
        'description': (
            "Vyslovíš slovo moci, které způsobí, že vlny intenzivní bolesti zaplaví jednoho tvora, kterého vidíš v dosahu. "
            "Pokud má cíl 100 životů nebo méně, podléhá ochromující bolesti: jeho rychlost klesne na 3 metry, má nevýhodu "
            "na hody na útok, ověření vlastností a záchranné hody (kromě Odolnosti), a pokud se pokusí seslat kouzlo, musí nejprve uspět v záchraně na Odolnost."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 163}
    },
    {
        'api_index': 'maddening-darkness',
        'name_cz': 'Šílená temnota',
        'name_en': 'Maddening Darkness',
        'level': 8,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Evokace',
        'school_en': 'Evocation',
        'casting_time': '1 akce',
        'range': '45 metrů (150 stop)',
        'components': 'V, M',
        'material': 'Kapka dehtu a kousek pavoukovce',
        'duration': 'Soustředění, až 10 minut',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Plošný efekt',
        'damage_type': 'Psychické',
        'damage_dice': '8k8',
        'saving_throw': 'Moudrost (WIS)',
        'heal_dice': '',
        'description': (
            "Magická temnota se rozlije z bodu, který zvolíš v dosahu, a vyplní kouli o poloměru 18 metrů (60 stop). "
            "V této prostoru znějí výkřiky, blábolení a šílený smích. Tvory s viděním ve tmě touto temnotou nevidí.\n\n"
            "Každý tvor, který v této kouli začne svůj tah, musí provést záchranný hod na Moudrost. Při neúspěchu utrpí psychické zranění 8k8, "
            "při úspěchu poloviční."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Kouzelník',
        'races': 'Elf, Temný elf',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 160}
    },
    {
        'api_index': 'psychic-scream',
        'name_cz': 'Psychický výkřik',
        'name_en': 'Psychic Scream',
        'level': 9,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Očarování',
        'school_en': 'Enchantment',
        'casting_time': '1 akce',
        'range': '27 metrů (90 stop)',
        'components': 'S',
        'material': '',
        'duration': 'Ihned',
        'concentration': False,
        'ritual': False,
        'attack_type': 'Více cílů (až 10)',
        'damage_type': 'Psychické',
        'damage_dice': '14k6',
        'saving_throw': 'Inteligence (INT)',
        'heal_dice': '',
        'description': (
            "Uvolníš sílu své mysli a rozdrtíš intelekt až deseti tvorů dle tvé volby, které vidíš v dosahu. "
            "Každý cíl musí provést záchranný hod na Inteligenci.\n\n"
            "Při neúspěchu utrpí cíl psychické zranění 14k6 a je ochromený (stunned). Při úspěchu utrpí poloviční zranění a není ochromený. "
            "Pokud je cíl tímto zraněním zabit, jeho hlava exploduje."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník, Bard, Čaroděj, Kouzelník',
        'races': '',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 163}
    },

    # =========================================================================
    # RASOVÁ MAGIE TEMNÉHO ELFA (DROW) Z XANATHAROVA PRŮVODCE VŠÍM
    # =========================================================================
    {
        'api_index': 'drow-high-magic',
        'name_cz': 'Vysoká magie drowů',
        'name_en': 'Drow High Magic',
        'level': 2,
        'is_cantrip': False,
        'is_xhantar': True,
        'school': 'Věštění',
        'school_en': 'Divination',
        'casting_time': '1 akce',
        'range': 'Sám sebe / 36 m',
        'components': 'V, S',
        'material': '',
        'duration': 'Proměnlivé',
        'concentration': True,
        'ritual': False,
        'attack_type': 'Rasová schopnost Temného elfa',
        'damage_type': '',
        'damage_dice': '',
        'saving_throw': '',
        'heal_dice': '',
        'description': (
            "Rasová odbornost Temného elfa (Drow) z Xanatharova průvodce vším:\n"
            "Naučíš se více z vrozené magie drowů:\n"
            "• Naučíš se kouzlo Odhal magii (Detect Magic) a můžeš ho sesílat libovolně (at will), aniž bys utratil kouzelnou pozici.\n"
            "• Naučíš se také kouzla Levitace (Levitate) a Rozptyl magii (Dispel Magic). Každé z nich můžeš seslat jednou "
            "bez utracení kouzelné pozice; schopnost seslat je tímto způsobem se ti obnoví po dokončení dlouhého odpočinku.\n"
            "• Tvou sesílací vlastností pro všechna tato kouzla je Charisma."
        ),
        'higher_levels': '',
        'classes': 'Černokněžník',
        'races': 'Elf, Temný elf, Drow',
        'backgrounds': '',
        'icon': 'spells/default_spell.jpg',
        'icon_url': '/static/img/spells/spell_icon.svg',
        'raw_data': {'source': "Xanathar's Guide to Everything", 'page': 74, 'feature_type': 'Racial Feat (Drow)'}
    }
]
