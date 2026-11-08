from django.db import models

class Locations(models.Model):

    type_choices = (
        ('continent','Kontinent'),
        ('kingdom','Království'),
        ('region','Region'),
        ('city','Město'),
        ('location','Lokace'),
        ('dungeon','Dungeon'),
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=100,choices=type_choices, null=True, blank=True)
    layer_up = models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True,related_name='locations_below',verbose_name='Vrstva nad')
    layer_down = models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True,related_name='locations_above',verbose_name='Vrstva pod')
    image = models.FileField(upload_to='locations/', blank=True, null=True, verbose_name="Mapa / Obrázek lokace")
    image_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="Externí URL mapy")

    class Meta:
        verbose_name = "Lokace"
        verbose_name_plural = "Lokace"

    def __str__(self):
        return self.name

    @property
    def display_image_url(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        if self.image_url and self.image_url.strip():
            return self.image_url.strip()
        return '/static/img/default_location.svg'

    @property
    def has_custom_image(self):
        return bool((self.image and self.image.name) or (self.image_url and self.image_url.strip()))

class Npc(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Jméno")
    race = models.CharField(max_length=100, null=True, blank=True, verbose_name="Rasa")
    occupation = models.CharField(max_length=100, null=True, blank=True, verbose_name="Povolání")
    title = models.CharField(max_length=100, null=True, blank=True, verbose_name="Titul")
    location = models.ForeignKey(Locations, on_delete=models.SET_NULL, null=True, blank=True, related_name='npcs', verbose_name="Lokace")
    description = models.TextField(null=True, blank=True, verbose_name="Popis")
    gender = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('male', 'Muž'),
        ('female', 'Žena'),
        ('other', 'Jiné'),
    ], verbose_name="Pohlaví")
    image = models.FileField(upload_to='npcs/', blank=True, null=True, verbose_name="Obrázek NPC")
    image_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="Externí URL obrázku")

    loot_gold = models.IntegerField(default=0, verbose_name="Zlaté mince (GP)", blank=True, null=True)
    loot_silver = models.IntegerField(default=0, verbose_name="Stříbrné mince (SP)", blank=True, null=True)
    loot_able = models.BooleanField(default=False, verbose_name="možnost lootit")

    is_dead = models.BooleanField(default=False, verbose_name="Je mrtvý")
    in_fight = models.BooleanField(default=False, verbose_name="V boji")

    class Meta:
        verbose_name = "Npc"
        verbose_name_plural = "Npc"

    def __str__(self):
        return self.name or "Neznámé NPC"

    @property
    def display_image_url(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        if self.image_url and self.image_url.strip():
            return self.image_url.strip()
        return '/static/img/default_npc.svg'

    @property
    def has_custom_image(self):
        return bool((self.image and self.image.name) or (self.image_url and self.image_url.strip()))


class DmNote(models.Model):
    title = models.CharField(max_length=200, verbose_name="Název poznámky")
    content = models.TextField(verbose_name="Obsah poznámky")
    category = models.CharField(max_length=100, blank=True, null=True, default="Kampaň", verbose_name="Kategorie / Značka")
    is_current = models.BooleanField(default=False, verbose_name="Aktuální (připnuto nahoře)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Datum vytvoření")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Datum úpravy")

    class Meta:
        verbose_name = "Poznámka DM"
        verbose_name_plural = "Poznámky DM"
        ordering = ['-is_current', '-updated_at']

    def __str__(self):
        return self.title


def _parse_ac_value(val):
    """Bezpečně převede hodnotu AC (int, float nebo string jako '+2', '12') na celé číslo nebo None."""
    if val is None or val == "" or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return int(val)
    import re
    m = re.search(r'-?\d+', str(val))
    return int(m.group(0)) if m else None


def infer_equip_able(category=None, damage=None, armor_class=None, name_cz=None, name_en=None):
    """
    Určí, zda je předmět z logiky věci nasaditelný (zbraň, zbroj, štít, prsten, hůl apod.).
    """
    if damage and str(damage).strip() and str(damage).strip() not in ("—", "-"):
        return True
    ac_int = _parse_ac_value(armor_class)
    if ac_int is not None and ac_int > 0:
        return True
    cat_low = (category or "").strip().lower()
    equip_keywords = (
        "zbraň", "zbran", "zbraně", "zbrane", "weapon",
        "zbroj", "brnění", "brneni", "armor",
        "štít", "stit", "štíty", "stity", "shield",
        "prsten", "ring", "amulet", "plášť", "plast", "cloak",
        "hůl", "hul", "hole", "staff", "wand", "žezl", "zezl", "rod",
    )
    if any(kw in cat_low for kw in equip_keywords):
        return True
    n_cz = (name_cz or "").strip().lower()
    n_en = (name_en or "").strip().lower()
    if n_cz in ("štít", "stit") or n_en == "shield":
        return True
    return False


class Items_All_db(models.Model):
    # Identifikátory
    api_index = models.CharField(max_length=100, unique=True, verbose_name="API Index")
    name_cz = models.CharField(max_length=150, verbose_name="Český název")
    name_en = models.CharField(max_length=150, verbose_name="Anglický název")
    
    # Kategorizace a nákup
    category = models.CharField(max_length=100, verbose_name="Kategorie")
    cost_gold = models.IntegerField(default=0, verbose_name="Cena (Zlaťáky)")
    cost_silver = models.IntegerField(default=0, verbose_name="Cena (Stříbrňáky)")
    weight = models.FloatField(default=0.0, verbose_name="Váha (libry)")
    
    # Bojové statistiky (zploštěné do textu pro maximální jednoduchost)
    damage = models.CharField(max_length=100, blank=True, null=True, verbose_name="Poškození (Kostky a typ)")
    armor_class = models.IntegerField(blank=True, null=True, verbose_name="Obranné číslo (AC)")
    properties = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vlastnosti zbraně")
    equip_able = models.BooleanField(default=False, verbose_name="Lze nasadit (Equipable)")
    
    # Dodatečné informace
    description = models.TextField(blank=True, null=True, verbose_name="Popis")

    class Meta:
        verbose_name = "Předmět z Kompendia"
        verbose_name_plural = "Předměty z Kompendia"
        ordering = ['name_cz']

    def save(self, *args, **kwargs):
        self.armor_class = _parse_ac_value(self.armor_class)
        if not self.equip_able and not getattr(self, '_explicit_equip_able', False) and self.pk is None:
            self.equip_able = infer_equip_able(
                category=self.category,
                damage=self.damage,
                armor_class=self.armor_class,
                name_cz=self.name_cz,
                name_en=self.name_en,
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name_cz} ({self.category})"

class Items_Active(models.Model):
    char_own = models.ForeignKey(
        'player_site_app.Char_info',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Vlastník (Postava)",
        null=True,
        blank=True
    )
    api_index = models.CharField(max_length=100, verbose_name="API Index", blank=True, null=True)
    name_cz = models.CharField(max_length=150, verbose_name="Český název", blank=True, null=True)
    name_en = models.CharField(max_length=150, verbose_name="Anglický název", blank=True, null=True)
    quantity = models.IntegerField(default=1, verbose_name="Množství (ks)")
    
    # Kategorizace a nákup
    category = models.CharField(max_length=100, verbose_name="Kategorie", blank=True, null=True)
    cost_gold = models.IntegerField(default=0, verbose_name="Cena (Zlaťáky)", blank=True, null=True)
    cost_silver = models.IntegerField(default=0, verbose_name="Cena (Stříbrňáky)", blank=True, null=True)
    weight = models.FloatField(default=0.0, verbose_name="Váha (libry)", blank=True, null=True)
    
    # Bojové statistiky (zploštěné do textu pro maximální jednoduchost)
    damage = models.CharField(max_length=100, blank=True, null=True, verbose_name="Poškození (Kostky a typ)")
    armor_class = models.IntegerField(blank=True, null=True, verbose_name="Obranné číslo (AC)")
    properties = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vlastnosti zbraně")
    equip_able = models.BooleanField(default=False, verbose_name="Lze nasadit (Equipable)")
    is_equipped = models.BooleanField(default=False, verbose_name="Nasazeno (Equipped)")
    
    # Dodatečné informace
    description = models.TextField(blank=True, null=True, verbose_name="Popis")

    class Meta:
        verbose_name = "Aktivní předmět"
        verbose_name_plural = "Aktivní předměty"
        ordering = ['-is_equipped', 'name_cz']

    def __str__(self):
        qty_str = f" ({self.quantity}×)" if (self.quantity or 1) > 1 else ""
        eq_str = " [Nasazeno]" if self.is_equipped else ""
        return f"{self.name_cz}{qty_str}{eq_str} ({self.category})"

    @property
    def damage_dice_only(self):
        """
        Vrátí samotný zápis kostky poškození (např. '1d8' z '1d8 Sečné', nebo '2d4' z '2d4 bodné').
        """
        if not self.damage:
            return ""
        raw = str(self.damage).strip()
        if not raw or raw in ("—", "-"):
            return ""
        import re
        matches = re.findall(r'\d+\s*[dDkK]\s*\d+(?:\s*[+-]\s*\d+)?', raw)
        if matches:
            return "+".join(re.sub(r'\s+', '', m).lower().replace('k', 'd') for m in matches)
        return raw.split()[0] if raw else ""

    @property
    def total_weight(self):
        qty = max(1, self.quantity or 1)
        return round((self.weight or 0.0) * qty, 2)

    @property
    def total_cost_gold(self):
        qty = max(1, self.quantity or 1)
        total_silver = ((self.cost_gold or 0) * 10 + (self.cost_silver or 0)) * qty
        return total_silver // 10

    @property
    def total_cost_silver(self):
        qty = max(1, self.quantity or 1)
        total_silver = ((self.cost_gold or 0) * 10 + (self.cost_silver or 0)) * qty
        return total_silver % 10

    def stack_signature(self):
        """Klíč pro rozpoznání totožného předmětu v inventáři jedné postavy."""
        return (
            (self.api_index or '').strip().lower(),
            (self.name_cz or '').strip().lower(),
            (self.name_en or '').strip().lower(),
            (self.category or '').strip().lower(),
            int(self.cost_gold or 0),
            int(self.cost_silver or 0),
            round(float(self.weight or 0.0), 3),
            (self.damage or '').strip().lower(),
            _parse_ac_value(self.armor_class),
            (self.properties or '').strip().lower(),
        )

    @classmethod
    def add_or_stack(cls, character, item_template=None, quantity=1, skip_auto_log=False, **fields):
        """
        Přidá předmět do inventáře postavy se stackováním:
        Pokud postava již vlastní totožný předmět, navýší jeho `quantity` o `quantity`.
        Jinak vytvoří 1 nový záznam s daným `quantity`.
        """
        qty = max(1, int(quantity or 1))
        if item_template is not None:
            is_eq_able = bool(
                getattr(item_template, 'equip_able', False)
                or infer_equip_able(
                    item_template.category,
                    item_template.damage,
                    item_template.armor_class,
                    item_template.name_cz,
                    item_template.name_en,
                )
            )
            data = {
                'api_index': item_template.api_index,
                'name_cz': item_template.name_cz,
                'name_en': item_template.name_en,
                'category': item_template.category,
                'cost_gold': item_template.cost_gold,
                'cost_silver': item_template.cost_silver,
                'weight': item_template.weight,
                'damage': item_template.damage,
                'armor_class': _parse_ac_value(item_template.armor_class),
                'properties': item_template.properties,
                'description': item_template.description,
                'equip_able': is_eq_able,
            }
        else:
            data = dict(fields)
            if 'armor_class' in data:
                data['armor_class'] = _parse_ac_value(data['armor_class'])
            if 'equip_able' not in data:
                data['equip_able'] = infer_equip_able(
                    data.get('category'),
                    data.get('damage'),
                    data.get('armor_class'),
                    data.get('name_cz'),
                    data.get('name_en'),
                )

        candidate = cls(char_own=character, quantity=qty, **data)
        target_sig = candidate.stack_signature()

        if character and character.pk:
            existing_items = list(cls.objects.filter(char_own=character).order_by('id'))
            for existing in existing_items:
                if existing.stack_signature() == target_sig:
                    existing.quantity = max(1, existing.quantity or 1) + qty
                    if candidate.equip_able and not existing.equip_able:
                        existing.equip_able = True
                    if skip_auto_log:
                        existing._skip_auto_log = True
                    existing.save()
                    return existing, False

        if skip_auto_log:
            candidate._skip_auto_log = True
        candidate.save()
        return candidate, True

    @classmethod
    def consolidate_for_character(cls, character):
        """
        Sloučí případné duplicitní záznamy totožných předmětů u dané postavy do jednoho stacku
        a zároveň automaticky doplní `equip_able=True` u zbraní a zbrojí.
        """
        if not character or not character.pk:
            return
        items = list(cls.objects.filter(char_own=character).order_by('id'))
        if not items:
            return
        seen = {}
        any_equipped = False
        for item in items:
            inferred_eq = infer_equip_able(
                item.category, item.damage, item.armor_class, item.name_cz, item.name_en
            )
            needs_save_fields = []
            if inferred_eq and not item.equip_able:
                item.equip_able = True
                needs_save_fields.append('equip_able')
            if item.is_equipped:
                any_equipped = True
                if not item.equip_able:
                    item.equip_able = True
                    if 'equip_able' not in needs_save_fields:
                        needs_save_fields.append('equip_able')

            sig = item.stack_signature()
            if sig not in seen:
                if (item.quantity or 0) < 1:
                    item.quantity = 1
                    needs_save_fields.append('quantity')
                if needs_save_fields:
                    item._skip_auto_log = True
                    item.save(update_fields=needs_save_fields)
                seen[sig] = item
            else:
                primary = seen[sig]
                primary.quantity = max(1, primary.quantity or 1) + max(1, item.quantity or 1)
                update_cols = ['quantity']
                if item.equip_able and not primary.equip_able:
                    primary.equip_able = True
                    update_cols.append('equip_able')
                if item.is_equipped and not primary.is_equipped:
                    primary.is_equipped = True
                    update_cols.append('is_equipped')
                primary._skip_auto_log = True
                primary.save(update_fields=update_cols)
                item._skip_auto_log = True
                item.delete()

        if any_equipped and hasattr(character, 'recalculate_ac_from_equipment'):
            character.recalculate_ac_from_equipment(force_reset_if_empty=False, skip_auto_log=True)

    def save(self, *args, **kwargs):
        from player_site_app.models import create_db_log, Char_info
        if not self.quantity or self.quantity < 1:
            self.quantity = 1
        self.armor_class = _parse_ac_value(self.armor_class)
        if not self.equip_able and not getattr(self, '_explicit_equip_able', False) and self.pk is None:
            self.equip_able = infer_equip_able(
                self.category, self.damage, self.armor_class, self.name_cz, self.name_en
            )
        if self.is_equipped and not self.equip_able:
            self.equip_able = True

        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_new = self.pk is None
        old_item = None
        old_char_own_id = None
        if not is_new:
            old_item = Items_Active.objects.filter(pk=self.pk).first()
            if old_item:
                old_char_own_id = old_item.char_own_id
        super().save(*args, **kwargs)
        qty_increased = bool(old_item and (self.quantity or 1) > (old_item.quantity or 1))
        if self.char_own_id and (is_new or old_char_own_id != self.char_own_id or qty_increased):
            Char_info.objects.filter(pk=self.char_own_id).update(has_new_inv=True)
            if self.char_own:
                self.char_own.has_new_inv = True

        # Přepočet AC postavy při změně nasazení nebo hodnoty AC předmětu
        if self.char_own and hasattr(self.char_own, 'recalculate_ac_from_equipment'):
            was_equipped_ac = bool(old_item and old_item.is_equipped and (old_item.armor_class or 0) > 0)
            now_equipped_ac = bool(self.is_equipped and (self.armor_class or 0) > 0)
            ac_changed = bool(old_item and old_item.armor_class != self.armor_class and self.is_equipped)
            if now_equipped_ac or was_equipped_ac or ac_changed:
                self.char_own.recalculate_ac_from_equipment(
                    force_reset_if_empty=(was_equipped_ac and not now_equipped_ac),
                    skip_auto_log=skip_auto_log,
                )

        if not skip_auto_log and self.char_own:
            unit_val = (self.cost_gold or 0) + ((self.cost_silver or 0) / 10.0)
            if is_new or (old_item and old_item.char_own_id != self.char_own_id):
                qty_prefix = f"{self.quantity}× " if (self.quantity or 1) > 1 else ""
                create_db_log(
                    character=self.char_own,
                    player=self.char_own.player,
                    message=f"Postava {self.char_own.name} získala předmět do inventáře: {qty_prefix}'{self.name_cz}' ({self.category or 'Ostatní'})",
                    value=float(round(unit_val * (self.quantity or 1), 2))
                )
            elif old_item and old_item.is_equipped != self.is_equipped:
                state_txt = "nasadila" if self.is_equipped else "sundala"
                create_db_log(
                    character=self.char_own,
                    player=self.char_own.player,
                    message=f"Postava {self.char_own.name} si {state_txt} předmět '{self.name_cz}'",
                    value=1.0 if self.is_equipped else 0.0
                )
            elif old_item and (old_item.quantity or 1) != (self.quantity or 1):
                delta_q = (self.quantity or 1) - (old_item.quantity or 1)
                create_db_log(
                    character=self.char_own,
                    player=self.char_own.player,
                    message=f"Změna počtu kusů předmětu '{self.name_cz}' u postavy {self.char_own.name}: {old_item.quantity or 1}× -> {self.quantity}×",
                    value=float(round(unit_val * delta_q, 2))
                )
            elif old_item and (
                old_item.name_cz != self.name_cz
                or old_item.damage != self.damage
                or old_item.armor_class != self.armor_class
                or old_item.cost_gold != self.cost_gold
                or old_item.cost_silver != self.cost_silver
            ):
                create_db_log(
                    character=self.char_own,
                    player=self.char_own.player,
                    message=f"Upraven předmět v inventáři postavy {self.char_own.name}: '{self.name_cz}'",
                    value=float(unit_val)
                )
        self._skip_auto_log = False

    def delete(self, *args, **kwargs):
        from player_site_app.models import create_db_log
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        char = self.char_own
        name_cz = self.name_cz
        qty = max(1, self.quantity or 1)
        was_equipped_ac = bool(self.is_equipped and (self.armor_class or 0) > 0)
        unit_val = (self.cost_gold or 0) + ((self.cost_silver or 0) / 10.0)
        res = super().delete(*args, **kwargs)
        if char and was_equipped_ac and hasattr(char, 'recalculate_ac_from_equipment'):
            char.recalculate_ac_from_equipment(force_reset_if_empty=True, skip_auto_log=skip_auto_log)
        if not skip_auto_log and char:
            qty_prefix = f"{qty}× " if qty > 1 else ""
            create_db_log(
                character=char,
                player=char.player,
                message=f"Předmět {qty_prefix}'{name_cz}' byl odebrán z inventáře postavy {char.name}",
                value=float(-round(unit_val * qty, 2))
            )
        return res


class Monsters_All_db(models.Model):
    # Identifikace
    api_index = models.CharField(max_length=100, unique=True, verbose_name="API Index")
    name_cz = models.CharField(max_length=150, verbose_name="Český název")
    name_en = models.CharField(max_length=150, verbose_name="Anglický název")

    # Typologie a zařazení
    size = models.CharField(max_length=50, verbose_name="Velikost")
    monster_type = models.CharField(max_length=100, verbose_name="Typ nestvůry")
    subtype = models.CharField(max_length=100, blank=True, null=True, verbose_name="Podtyp")
    alignment = models.CharField(max_length=100, blank=True, null=True, verbose_name="Přesvědčení")

    # Bojové statistiky a životy
    armor_class = models.IntegerField(verbose_name="Třída zbroje (AC)")
    armor_desc = models.CharField(max_length=150, blank=True, null=True, verbose_name="Typ zbroje")
    hit_points = models.IntegerField(verbose_name="Životy (HP)")
    hit_dice = models.CharField(max_length=50, blank=True, null=True, verbose_name="Kostky životů")
    speed = models.CharField(max_length=200, verbose_name="Rychlost")

    # Základní vlastnosti (Ability Scores)
    strength = models.IntegerField(default=10, verbose_name="Síla (STR)")
    dexterity = models.IntegerField(default=10, verbose_name="Obratnost (DEX)")
    constitution = models.IntegerField(default=10, verbose_name="Odolnost (CON)")
    intelligence = models.IntegerField(default=10, verbose_name="Inteligence (INT)")
    wisdom = models.IntegerField(default=10, verbose_name="Moudrost (WIS)")
    charisma = models.IntegerField(default=10, verbose_name="Charisma (CHA)")

    # Záchrany, dovednosti, obrana a smysly
    saving_throws = models.CharField(max_length=255, blank=True, null=True, verbose_name="Záchranné hody")
    skills = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dovednosti")
    damage_vulnerabilities = models.CharField(max_length=255, blank=True, null=True, verbose_name="Zranitelnosti")
    damage_resistances = models.CharField(max_length=255, blank=True, null=True, verbose_name="Odolnosti")
    damage_immunities = models.CharField(max_length=255, blank=True, null=True, verbose_name="Imunity vůči poškození")
    condition_immunities = models.CharField(max_length=255, blank=True, null=True, verbose_name="Stavové imunity")
    senses = models.CharField(max_length=255, blank=True, null=True, verbose_name="Smysly")
    languages = models.CharField(max_length=255, blank=True, null=True, verbose_name="Jazyky")

    # Nebezpečnost a postup
    challenge_rating = models.FloatField(verbose_name="Nebezpečnost (CR)")
    xp = models.IntegerField(default=0, verbose_name="Zkušenosti (XP)")
    proficiency_bonus = models.IntegerField(default=2, verbose_name="Zdatnostní bonus")

    # Schopnosti a akce
    special_abilities = models.TextField(blank=True, null=True, verbose_name="Zvláštní schopnosti")
    actions = models.TextField(blank=True, null=True, verbose_name="Akce")
    legendary_actions = models.TextField(blank=True, null=True, verbose_name="Legendární akce")
    reactions = models.TextField(blank=True, null=True, verbose_name="Reakce")

    # Popis, obrázek a surová data
    description = models.TextField(blank=True, null=True, verbose_name="Popis")
    image_url = models.CharField(max_length=255, blank=True, null=True, verbose_name="URL obrázku")
    raw_data = models.JSONField(blank=True, null=True, verbose_name="Původní JSON data")
    
    # pracovní
    in_fight = models.BooleanField(default=False, verbose_name="V boji")

    class Meta:
        verbose_name = "Nestvůra z Kompendia"
        verbose_name_plural = "Nestvůry z Kompendia"
        ordering = ['challenge_rating', 'name_cz']

    def __str__(self):
        return f"{self.name_cz} (CR {self.formatted_cr})"

    @property
    def formatted_cr(self):
        if self.challenge_rating == 0.125:
            return "1/8"
        elif self.challenge_rating == 0.25:
            return "1/4"
        elif self.challenge_rating == 0.5:
            return "1/2"
        elif self.challenge_rating.is_integer():
            return str(int(self.challenge_rating))
        return str(self.challenge_rating)

    @staticmethod
    def _calc_mod(score):
        m = (score - 10) // 2
        return f"+{m}" if m >= 0 else str(m)

    @property
    def str_mod(self):
        return self._calc_mod(self.strength)

    @property
    def dex_mod(self):
        return self._calc_mod(self.dexterity)

    @property
    def con_mod(self):
        return self._calc_mod(self.constitution)

    @property
    def int_mod(self):
        return self._calc_mod(self.intelligence)

    @property
    def wis_mod(self):
        return self._calc_mod(self.wisdom)

    @property
    def cha_mod(self):
        return self._calc_mod(self.charisma)


class Monsters_Active(models.Model):
    # Identifikace
    api_index = models.CharField(max_length=100, verbose_name="API Index", blank=True, null=True)
    name_cz = models.CharField(max_length=150, verbose_name="Český název", blank=True, null=True)
    name_en = models.CharField(max_length=150, verbose_name="Anglický název", blank=True, null=True)

    # Typologie a zařazení
    size = models.CharField(max_length=50, verbose_name="Velikost", blank=True, null=True)
    monster_type = models.CharField(max_length=100, verbose_name="Typ nestvůry", blank=True, null=True)
    subtype = models.CharField(max_length=100, blank=True, null=True, verbose_name="Podtyp")
    alignment = models.CharField(max_length=100, blank=True, null=True, verbose_name="Přesvědčení")

    # Bojové statistiky a životy
    armor_class = models.IntegerField(verbose_name="Třída zbroje (AC)", blank=True, null=True)
    armor_desc = models.CharField(max_length=150, blank=True, null=True, verbose_name="Typ zbroje")
    hit_points = models.IntegerField(verbose_name="Životy (HP)", blank=True, null=True)
    current_hp = models.IntegerField(verbose_name="Aktuální životy (HP)", blank=True, null=True)
    hit_dice = models.CharField(max_length=50, blank=True, null=True, verbose_name="Kostky životů")
    speed = models.CharField(max_length=200, verbose_name="Rychlost", blank=True, null=True)

    # Základní vlastnosti (Ability Scores)
    strength = models.IntegerField(default=10, verbose_name="Síla (STR)", blank=True, null=True)
    dexterity = models.IntegerField(default=10, verbose_name="Obratnost (DEX)", blank=True, null=True)
    constitution = models.IntegerField(default=10, verbose_name="Odolnost (CON)", blank=True, null=True)
    intelligence = models.IntegerField(default=10, verbose_name="Inteligence (INT)", blank=True, null=True)
    wisdom = models.IntegerField(default=10, verbose_name="Moudrost (WIS)", blank=True, null=True)
    charisma = models.IntegerField(default=10, verbose_name="Charisma (CHA)", blank=True, null=True)

    # Záchrany, dovednosti, obrana a smysly
    saving_throws = models.CharField(max_length=255, blank=True, null=True, verbose_name="Záchranné hody")
    skills = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dovednosti")
    damage_vulnerabilities = models.CharField(max_length=255, blank=True, null=True, verbose_name="Zranitelnosti")
    damage_resistances = models.CharField(max_length=255, blank=True, null=True, verbose_name="Odolnosti")
    damage_immunities = models.CharField(max_length=255, blank=True, null=True, verbose_name="Imunity vůči poškození")
    condition_immunities = models.CharField(max_length=255, blank=True, null=True, verbose_name="Stavové imunity")
    senses = models.CharField(max_length=255, blank=True, null=True, verbose_name="Smysly")
    languages = models.CharField(max_length=255, blank=True, null=True, verbose_name="Jazyky")

    # Nebezpečnost a postup
    challenge_rating = models.FloatField(verbose_name="Nebezpečnost (CR)", blank=True, null=True)
    xp = models.IntegerField(default=0, verbose_name="Zkušenosti (XP)", blank=True, null=True)
    proficiency_bonus = models.IntegerField(default=2, verbose_name="Zdatnostní bonus", blank=True, null=True)

    # Schopnosti a akce
    special_abilities = models.TextField(blank=True, null=True, verbose_name="Zvláštní schopnosti")
    actions = models.TextField(blank=True, null=True, verbose_name="Akce")
    legendary_actions = models.TextField(blank=True, null=True, verbose_name="Legendární akce")
    reactions = models.TextField(blank=True, null=True, verbose_name="Reakce")

    # Popis, obrázek a surová data
    description = models.TextField(blank=True, null=True, verbose_name="Popis")
    image_url = models.CharField(max_length=255, blank=True, null=True, verbose_name="URL obrázku")
    raw_data = models.JSONField(blank=True, null=True, verbose_name="Původní JSON data")

    # pracovní
    in_fight = models.BooleanField(default=False, verbose_name="V boji")
    combat_initiative = models.IntegerField(default=0, verbose_name="Iniciativa v boji")
    is_dead = models.BooleanField(default=False, verbose_name="Je mrtvý")

    # loot
    loot_gold = models.IntegerField(default=0, verbose_name="Zlaté mince (GP)", blank=True, null=True)
    loot_silver = models.IntegerField(default=0, verbose_name="Stříbrné mince (SP)", blank=True, null=True)
    loot_able = models.BooleanField(default=False, verbose_name="možnost lootit")
    

    class Meta:
        verbose_name = "Aktivní nestvůra"
        verbose_name_plural = "Aktivní nestvůry"
        ordering = ['is_dead', 'challenge_rating', 'name_cz']

    def __str__(self):
        return f"({'Mrtvý' if self.is_dead else 'Živý'}) - {self.name_cz} (CR {self.formatted_cr})"

    @property
    def formatted_cr(self):
        if self.challenge_rating == 0.125:
            return "1/8"
        elif self.challenge_rating == 0.25:
            return "1/4"
        elif self.challenge_rating == 0.5:
            return "1/2"
        elif self.challenge_rating.is_integer():
            return str(int(self.challenge_rating))
        return str(self.challenge_rating)

    @staticmethod
    def _calc_mod(score):
        m = (score - 10) // 2
        return f"+{m}" if m >= 0 else str(m)

    @property
    def str_mod(self):
        return self._calc_mod(self.strength)

    @property
    def dex_mod(self):
        return self._calc_mod(self.dexterity)

    @property
    def con_mod(self):
        return self._calc_mod(self.constitution)

    @property
    def int_mod(self):
        return self._calc_mod(self.intelligence)

    @property
    def wis_mod(self):
        return self._calc_mod(self.wisdom)

    @property
    def cha_mod(self):
        return self._calc_mod(self.charisma)

    @property
    def max_hp(self):
        return self.hit_points or 10

    @property
    def current_hp_val(self):
        if self.current_hp is not None:
            return self.current_hp
        return self.max_hp


class OverAllSettings(models.Model):
    loging_active = models.BooleanField(default=True, verbose_name="Přihlašování aktivní")
    editing_active = models.BooleanField(default=True, verbose_name="Editace aktivní")

    class Meta:
        verbose_name = "Globální nastavení"
        verbose_name_plural = "Globální nastavení"

    def __str__(self):
        return f"Globální nastavení (Přihlašování: {'Zapnuto' if self.loging_active else 'Vypnuto'})"


class Kronika(models.Model):
    CATEGORY_CHOICES = [
        ('info', 'Info'),
        ('lore', 'Příběh'),
    ]

    nazev = models.CharField(max_length=200, verbose_name="Název")
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='info',
        verbose_name="Kategorie"
    )
    popis = models.TextField(verbose_name="Popis")
    odkryto_hracum = models.BooleanField(
        default=False,
        verbose_name="Odkrýt hráčům"
    )
    datum_vytvoreni = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Datum vytvoření"
    )
    datum_aktualizace = models.DateTimeField(
        auto_now=True,
        verbose_name="Datum aktualizace"
    )

    class Meta:
        verbose_name = "Kronika"
        verbose_name_plural = "Kronika"
        ordering = ['-datum_vytvoreni']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.nazev} ({'Odkryto' if self.odkryto_hracum else 'Skryto'})"

    def save(self, *args, **kwargs):
        from player_site_app.models import Player
        is_new = self.pk is None
        old_odkryto = False
        if not is_new:
            old_odkryto = bool(Kronika.objects.filter(pk=self.pk).values_list('odkryto_hracum', flat=True).first())
        super().save(*args, **kwargs)
        if self.odkryto_hracum and (is_new or not old_odkryto):
            Player.objects.all().update(has_new_kronika=True)


class Spells_All_db(models.Model):
    # Identifikace
    api_index = models.CharField(max_length=100, unique=True, verbose_name="API Index")
    name_cz = models.CharField(max_length=150, verbose_name="Český název")
    name_en = models.CharField(max_length=150, verbose_name="Anglický název")

    # Magické zařazení
    level = models.IntegerField(default=0, verbose_name="Úroveň kouzla")  # 0 = Trik, 1-9 = Level 1-9
    is_cantrip = models.BooleanField(default=False, verbose_name="Je trik")
    school = models.CharField(max_length=100, blank=True, null=True, verbose_name="Magická škola (CZ)")
    school_en = models.CharField(max_length=100, blank=True, null=True, verbose_name="Magická škola (EN)")

    # Sesílání a parametry
    casting_time = models.CharField(max_length=100, blank=True, null=True, verbose_name="Doba vyvolání")
    range = models.CharField(max_length=100, blank=True, null=True, verbose_name="Dosah")
    components = models.CharField(max_length=100, blank=True, null=True, verbose_name="Složky (V, S, M)")
    material = models.TextField(blank=True, null=True, verbose_name="Materiální složka")
    duration = models.CharField(max_length=150, blank=True, null=True, verbose_name="Trvání")
    concentration = models.BooleanField(default=False, verbose_name="Soustředění")
    ritual = models.BooleanField(default=False, verbose_name="Rituál")

    # Bojové a mechanické parametry
    attack_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Typ útoku")
    damage_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Typ zranění")
    damage_dice = models.CharField(max_length=150, blank=True, null=True, verbose_name="Kostky poškození")
    saving_throw = models.CharField(max_length=100, blank=True, null=True, verbose_name="Záchranný hod")
    heal_dice = models.CharField(max_length=150, blank=True, null=True, verbose_name="Léčení")

    # Popis
    description = models.TextField(blank=True, null=True, verbose_name="Popis")
    higher_levels = models.TextField(blank=True, null=True, verbose_name="Na vyšších úrovních")

    # Filtrování pro postavy (povolání, rasy, zázemí)
    classes = models.CharField(max_length=255, blank=True, null=True, verbose_name="Povolání (CZ)")
    races = models.CharField(max_length=255, blank=True, null=True, verbose_name="Rasy (CZ)")
    backgrounds = models.CharField(max_length=255, blank=True, null=True, verbose_name="Zázemí (CZ)")
    is_xhantar = models.BooleanField(default=False, verbose_name="Xanatharův průvodce (Rozšíření)")

    # Ikonka a vizuál
    icon = models.FileField(
        upload_to='spells/icons/',
        blank=True,
        null=True,
        default='spells/default_spell.jpg',
        verbose_name="Ikonka soubor"
    )
    icon_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default='/static/img/spells/default_spell.jpg',
        verbose_name="URL ikonky"
    )
    raw_data = models.JSONField(blank=True, null=True, verbose_name="Původní JSON data")

    class Meta:
        verbose_name = "Kouzlo z Kompendia"
        verbose_name_plural = "Kouzla z Kompendia"
        ordering = ['level', 'name_cz']

    def __str__(self):
        typ = "Trik" if self.is_cantrip or self.level == 0 else f"Level {self.level}"
        return f"{self.name_cz} ({typ})"

    @property
    def display_icon_url(self):
        return '/static/img/spells/cantrip_icon.svg' if self.is_trick else '/static/img/spells/spell_icon.svg'

    @property
    def is_trick(self):
        return self.level == 0 or self.is_cantrip


class Spells_Active(models.Model):
    char_own = models.ForeignKey(
        'player_site_app.Char_info',
        on_delete=models.CASCADE,
        related_name='spells_active',
        verbose_name="Vlastník (Postava)",
        null=True,
        blank=True
    )
    template_spell = models.ForeignKey(
        Spells_All_db,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_instances',
        verbose_name="Šablona kouzla"
    )

    # Identifikace
    api_index = models.CharField(max_length=100, blank=True, null=True, verbose_name="API Index")
    name_cz = models.CharField(max_length=150, verbose_name="Český název")
    name_en = models.CharField(max_length=150, verbose_name="Anglický název")

    # Magické zařazení
    level = models.IntegerField(default=0, verbose_name="Úroveň kouzla")
    is_cantrip = models.BooleanField(default=False, verbose_name="Je trik")
    school = models.CharField(max_length=100, blank=True, null=True, verbose_name="Magická škola (CZ)")
    school_en = models.CharField(max_length=100, blank=True, null=True, verbose_name="Magická škola (EN)")

    # Sesílání a parametry
    casting_time = models.CharField(max_length=100, blank=True, null=True, verbose_name="Doba vyvolání")
    range = models.CharField(max_length=100, blank=True, null=True, verbose_name="Dosah")
    components = models.CharField(max_length=100, blank=True, null=True, verbose_name="Složky (V, S, M)")
    material = models.TextField(blank=True, null=True, verbose_name="Materiální složka")
    duration = models.CharField(max_length=150, blank=True, null=True, verbose_name="Trvání")
    concentration = models.BooleanField(default=False, verbose_name="Soustředění")
    ritual = models.BooleanField(default=False, verbose_name="Rituál")

    # Bojové a mechanické parametry
    attack_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Typ útoku")
    damage_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Typ zranění")
    damage_dice = models.CharField(max_length=150, blank=True, null=True, verbose_name="Kostky poškození")
    saving_throw = models.CharField(max_length=100, blank=True, null=True, verbose_name="Záchranný hod")
    heal_dice = models.CharField(max_length=150, blank=True, null=True, verbose_name="Léčení")

    # Popis
    description = models.TextField(blank=True, null=True, verbose_name="Popis")
    higher_levels = models.TextField(blank=True, null=True, verbose_name="Na vyšších úrovních")

    # Filtrování pro postavy (povolání, rasy, zázemí)
    classes = models.CharField(max_length=255, blank=True, null=True, verbose_name="Povolání (CZ)")
    races = models.CharField(max_length=255, blank=True, null=True, verbose_name="Rasy (CZ)")
    backgrounds = models.CharField(max_length=255, blank=True, null=True, verbose_name="Zázemí (CZ)")
    is_xhantar = models.BooleanField(default=False, verbose_name="Xanatharův průvodce (Rozšíření)")

    # Ikonka a vizuál
    icon = models.FileField(
        upload_to='spells/icons/',
        blank=True,
        null=True,
        default='spells/default_spell.jpg',
        verbose_name="Ikonka soubor"
    )
    icon_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default='/static/img/spells/default_spell.jpg',
        verbose_name="URL ikonky"
    )
    raw_data = models.JSONField(blank=True, null=True, verbose_name="Původní JSON data")

    # Stav u postavy
    nauceno = models.BooleanField(default=False, verbose_name="Naučeno")
    vybaveno = models.BooleanField(default=False, verbose_name="Vybaveno")

    class Meta:
        verbose_name = "Aktivní kouzlo postavy"
        verbose_name_plural = "Aktivní kouzla postav"
        ordering = ['level', 'name_cz']

    def __str__(self):
        char_name = self.char_own.name if self.char_own else "Bez postavy"
        stav = "Vybaveno" if self.vybaveno else ("Naučeno" if self.nauceno else "Nenaučeno")
        return f"{self.name_cz} [{char_name}] ({stav})"

    @property
    def display_icon_url(self):
        return '/static/img/spells/cantrip_icon.svg' if self.is_trick else '/static/img/spells/spell_icon.svg'

    @property
    def is_trick(self):
        return self.level == 0 or self.is_cantrip or (self.template_spell and (self.template_spell.level == 0 or self.template_spell.is_cantrip))

    def clean(self):
        super().clean()
        if self.is_trick or self.level == 0 or self.is_cantrip:
            self.vybaveno = False

    def save(self, *args, **kwargs):
        from player_site_app.models import create_db_log
        # Triky jsou trvale k dispozici a nelze je vybavovat do slotů připravených kouzel
        if self.is_trick or self.level == 0 or self.is_cantrip:
            self.vybaveno = False

        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_new = self.pk is None
        old_spell = None
        if not is_new and not skip_auto_log:
            old_spell = Spells_Active.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)
        if not skip_auto_log and self.char_own:
            typ_label = "trik" if self.is_trick else f"kouzlo ({self.level}. úroveň)"
            if is_new:
                if self.nauceno:
                    create_db_log(
                        character=self.char_own,
                        player=self.char_own.player,
                        message=f"Postava {self.char_own.name} se naučila {typ_label}: '{self.name_cz}'",
                        value=float(self.level or 0)
                    )
            elif old_spell:
                if old_spell.nauceno != self.nauceno:
                    action_str = "se naučila" if self.nauceno else "zapomněla"
                    create_db_log(
                        character=self.char_own,
                        player=self.char_own.player,
                        message=f"Postava {self.char_own.name} {action_str} {typ_label}: '{self.name_cz}'",
                        value=1.0 if self.nauceno else 0.0
                    )
                if old_spell.vybaveno != self.vybaveno and self.nauceno:
                    eq_str = "vybavila" if self.vybaveno else "odebrala z vybavených"
                    create_db_log(
                        character=self.char_own,
                        player=self.char_own.player,
                        message=f"Postava {self.char_own.name} {eq_str} {typ_label}: '{self.name_cz}'",
                        value=1.0 if self.vybaveno else 0.0
                    )
        self._skip_auto_log = False

    def delete(self, *args, **kwargs):
        from player_site_app.models import create_db_log
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        char = self.char_own
        name_cz = self.name_cz
        is_trick = self.is_trick
        lvl = self.level
        res = super().delete(*args, **kwargs)
        if not skip_auto_log and char:
            typ_label = "trik" if is_trick else f"kouzlo ({lvl}. úroveň)"
            create_db_log(
                character=char,
                player=char.player,
                message=f"Postavě {char.name} bylo odebráno {typ_label}: '{name_cz}'",
                value=0.0
            )
        return res