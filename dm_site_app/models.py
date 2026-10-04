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

    class Meta:
        verbose_name = "Lokace"
        verbose_name_plural = "Lokace"

    def __str__(self):
        return self.name

class Npc(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Jméno")
    location = models.ForeignKey(Locations, on_delete=models.SET_NULL, null=True, blank=True, related_name='npcs', verbose_name="Lokace")
    description = models.TextField(null=True, blank=True, verbose_name="Popis")
    gender = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('male', 'Muž'),
        ('female', 'Žena'),
        ('other', 'Jiné'),
    ], verbose_name="Pohlaví")

    class Meta:
        verbose_name = "Npc"
        verbose_name_plural = "Npc"

    def __str__(self):
        return self.name or "Neznámé NPC"

class NpcLoot(models.Model):
    npc = models.ForeignKey(Npc, on_delete=models.CASCADE, related_name='loot_items')
    item_name = models.CharField(max_length=100, verbose_name="Předmět")
    quantity = models.IntegerField(default=1, verbose_name="Počet")
    
    class Meta:
        verbose_name = "Loot"
        verbose_name_plural = "Loot"

    def __str__(self):
        return f"{self.quantity}x {self.item_name}"


class Items_All_db(models.Model):
    # Identifikátory
    api_index = models.CharField(max_length=100, unique=True, verbose_name="API Index")
    name_cz = models.CharField(max_length=150, verbose_name="Český název")
    name_en = models.CharField(max_length=150, verbose_name="Anglický název")
    
# Kategorizace a nákup
    category = models.CharField(max_length=100, verbose_name="Kategorie")
    cost_gold = models.IntegerField(default=0, verbose_name="Cena (Zlaťáky)")
    cost_silver = models.IntegerField(default=0, verbose_name="Cena (Stříbrňáky)") # NOVÝ ŘÁDEK
    weight = models.FloatField(default=0.0, verbose_name="Váha (libry)")
    
    # Bojové statistiky (zploštěné do textu pro maximální jednoduchost)
    damage = models.CharField(max_length=100, blank=True, null=True, verbose_name="Poškození (Kostky a typ)")
    armor_class = models.IntegerField(blank=True, null=True, verbose_name="Obranné číslo (AC)")
    properties = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vlastnosti zbraně")
    
    # Dodatečné informace
    description = models.TextField(blank=True, null=True, verbose_name="Popis")

    class Meta:
        verbose_name = "Předmět z Kompendia"
        verbose_name_plural = "Předměty z Kompendia"
        ordering = ['name_cz']

    def __str__(self):
        return f"{self.name_cz} ({self.category})"

class Items_Active(models.Model):
    # Identifikátory
    api_index = models.CharField(max_length=100, unique=True, verbose_name="API Index", blank=True, null=True)
    name_cz = models.CharField(max_length=150, verbose_name="Český název", blank=True, null=True)
    name_en = models.CharField(max_length=150, verbose_name="Anglický název", blank=True, null=True)
    
    # Kategorizace a nákup
    category = models.CharField(max_length=100, verbose_name="Kategorie", blank=True, null=True)
    cost_gold = models.IntegerField(default=0, verbose_name="Cena (Zlaťáky)", blank=True, null=True)
    cost_silver = models.IntegerField(default=0, verbose_name="Cena (Stříbrňáky)", blank=True, null=True) # NOVÝ ŘÁDEK
    weight = models.FloatField(default=0.0, verbose_name="Váha (libry)", blank=True, null=True)
    
    # Bojové statistiky (zploštěné do textu pro maximální jednoduchost)
    damage = models.CharField(max_length=100, blank=True, null=True, verbose_name="Poškození (Kostky a typ)")
    armor_class = models.IntegerField(blank=True, null=True, verbose_name="Obranné číslo (AC)")
    properties = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vlastnosti zbraně")
    
    # Dodatečné informace
    description = models.TextField(blank=True, null=True, verbose_name="Popis")

    class Meta:
        verbose_name = "Aktivní předmět"
        verbose_name_plural = "Aktivní předměty"
        ordering = ['name_cz']

    def __str__(self):
        return f"{self.name_cz} ({self.category})"


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
    api_index = models.CharField(max_length=100, unique=True, verbose_name="API Index", blank=True, null=True)
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

    class Meta:
        verbose_name = "Aktivní nestvůra"
        verbose_name_plural = "Aktivní nestvůry"
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