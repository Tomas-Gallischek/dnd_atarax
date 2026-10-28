from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import random


class Player(models.Model):     
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='player',
        verbose_name="Uživatelský účet",
        blank=True,
        null=True
    )
    nickname = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Přezdívka hráče"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name="O hráči"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Datum registrace"
    )

    temna_esence = models.IntegerField(default=0, verbose_name="Temná esence", blank=True, null=True)
    pin_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="PIN kód")

    active_ramecek = models.ForeignKey(
        "Esence_Items_Owners",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_in_players',
        verbose_name="Aktivní rámeček"
    )

    active_icon = models.ForeignKey(
        "Esence_Items_Owners",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_in_players_icon',
        verbose_name="Aktivní ikonka"
    )

    admin = models.BooleanField(default=False, verbose_name="Jsi administrátor", blank=True, null=True)

    class Meta:
        verbose_name = "Hráč"
        verbose_name_plural = "Hráči"

    def clean(self):
        super().clean()
        if self.active_ramecek and self.active_ramecek.player_id != self.id:
            raise ValidationError({'active_ramecek': "Vybraný rámeček nevlastní tento hráč!"})
        if self.active_icon and self.active_icon.player_id != self.id:
            raise ValidationError({'active_icon': "Vybranou ikonku nevlastní tento hráč!"})

    def save(self, *args, **kwargs):
        if not self.user_id:
            import re
            base_name = self.nickname or (f"hrac_{self.pin_code}" if self.pin_code else "hrac")
            clean_username = re.sub(r'[^\w.@+-]', '_', base_name) or "hrac"
            candidate = clean_username
            idx = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{clean_username}_{idx}"
                idx += 1
            self.user = User.objects.create_user(username=candidate)

        if self.user:
            self.admin = bool(self.user.is_staff)
        super().save(*args, **kwargs)

    @property
    def active_frame_url(self):
        """Vrátí URL aktivního rámečku hráče (nebo None)."""
        if self.active_ramecek and self.active_ramecek.item and self.active_ramecek.item.image:
            try:
                return self.active_ramecek.item.image.url
            except Exception:
                return None
        return None

    @property
    def active_icon_url(self):
        """Vrátí URL aktivní ikonky hráče (nebo None)."""
        if self.active_icon and self.active_icon.item and self.active_icon.item.image:
            try:
                return self.active_icon.item.image.url
            except Exception:
                return None
        return None

    @property
    def owned_avatar_icons(self):
        """Vrátí unikátní položky ikonek, které hráč vlastní."""
        records = self.esence_items.filter(item__category='icons').select_related('item').order_by('item__rarity', 'item__name')
        seen = set()
        result = []
        for r in records:
            if r.item_id not in seen:
                seen.add(r.item_id)
                result.append(r)
        return result

    @property
    def is_dm(self):
        """Určí, zda má hráč status Dungeon Mastera (administrátor nebo is_staff)."""
        return bool(self.admin or (self.user and self.user.is_staff))

    def __str__(self):
        return self.nickname or self.user.username


class Char_info(models.Model):

    race_choices = (
        ("Člověk", "Člověk"),
        ("Elf", "Elf"),
        ("Hobit", "Hobit"),
        ("Trpaslík", "Trpaslík"),
        ("Drakorozený", "Drakorozený"),
        ("Gnom", "Gnom"),
        ("Půlelf", "Půlelf"),
        ("Půlork", "Půlork"),
        ("Tiefling", "Tiefling"),
        ("Ostatní", "Ostatní"),
    )

    class_choices = (
        ("Barbar", "Barbar"),
        ("Bard", "Bard"),
        ("Bojovník", "Bojovník"),
        ("Čaroděj", "Čaroděj"),
        ("Černokněžník", "Černokněžník"),
        ("Druid", "Druid"),
        ("Hraničář", "Hraničář"),
        ("Klerik", "Klerik"),
        ("Kouzelník", "Kouzelník"),
        ("Mnich", "Mnich"),
        ("Paladin", "Paladin"),
        ("Tulák", "Tulák"),
        ("Ostatní", "Ostatní")
    )

    background_choices = (
        ("Akolyta", "Akolyta"),
        ("Bavič", "Bavič"),
        ("Cechovní řemeslník", "Cechovní řemeslník"),
        ("Hlídkař", "Hlídkař"),
        ("Lidový hrdina", "Lidový hrdina"),
        ("Mudrc", "Mudrc"),
        ("Námořník", "námořník"),
        ("Poustevník", "poustevník"),
        ("Šlechtic", "Šlechtic"),
        ("Šarlatán", "šarlatán"),
        ("Uličník", "uličník"),
        ("Voják", "Voják"),
        ("Zločinec", "Zločinec"),
        ("Ostatní", "ostatní")
    )

    alignment_choices = (
        ("Zákonně dobrý", "Zákonně dobrý"),
        ("Chaoticky dobrý", "Chaoticky dobrý"),
        ("Neutrální dobrý", "Neutrální dobrý"),
        ("Zákonně neutrální", "Zákonně neutrální"),
        ("Neutrální", "Neutrální"),
        ("Chaoticky neutrální", "Chaoticky neutrální"),
        ("Zákonně zlý", "Zákonně zlý"),
        ("Neutrálně zlý", "Neutrálně zlý"),
        ("Chaoticky zlý", "Chaoticky zlý"),
        ("Ostatní", "Ostatní"),
    )

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='characters',
        verbose_name="Hráč"
    )

    # Základní identita
    name = models.CharField(max_length=100, verbose_name="Jméno postavy")
    image = models.FileField(
        upload_to='characters/',
        blank=True,
        null=True,
        verbose_name="Profilový obrázek"
    )
    image_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Externí URL profilového obrázku"
    )
    active_icon = models.ForeignKey(
        "Esence_Items_Owners",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_in_characters',
        verbose_name="Aktivní ikonka z Dungeon Shopu"
    )
    race = models.CharField(max_length=50, blank=True, null=True, verbose_name="Rasa", default="Ostatní", choices=race_choices)
    character_class = models.CharField(max_length=50, blank=True, null=True, verbose_name="Povolání", default="Ostatní", choices=class_choices)
    level = models.IntegerField(default=1, verbose_name="Úroveň")
    background = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zázemí", choices=background_choices)
    alignment = models.CharField(max_length=50, blank=True, null=True, verbose_name="Přesvědčení", choices=alignment_choices)
    experience_points = models.IntegerField(default=0, verbose_name="Zkušenosti (XP)")
    gold = models.IntegerField(default=0, verbose_name="Zlaťáky", blank=True, null=True)
    silver = models.IntegerField(default=0, verbose_name="Stříbráky", blank=True, null=True)
    total_golds = models.FloatField(default=0, verbose_name="Celkové zlaťáky - EVER", blank=True, null=True)
    

    # Bojové statistiky & Životy
    armor_class = models.IntegerField(default=10, verbose_name="Třída zbroje (AC)")
    hit_points_max = models.IntegerField(default=10, verbose_name="Maximální životy")
    hit_points_current = models.IntegerField(default=10, verbose_name="Současné životy")
    speed = models.IntegerField(default=30, verbose_name="Rychlost (stopy)")

    # Základní vlastnosti (Ability Scores)
    strength = models.IntegerField(default=10, verbose_name="Síla (STR)")
    dexterity = models.IntegerField(default=10, verbose_name="Obratnost (DEX)")
    constitution = models.IntegerField(default=10, verbose_name="Odolnost (CON)")
    intelligence = models.IntegerField(default=10, verbose_name="Inteligence (INT)")
    wisdom = models.IntegerField(default=10, verbose_name="Moudrost (WIS)")
    charisma = models.IntegerField(default=10, verbose_name="Charisma (CHA)")

    # Časová razítka
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Poslední úprava")

    # pracovní
    in_fight = models.BooleanField(default=False, verbose_name="V boji")

    # Viditelnost pro ostatní hráče (DM kontrola)
    is_public = models.BooleanField(
        default=True,
        verbose_name="Veřejná postava (viditelná pro ostatní hráče)",
        help_text="Pokud je vypnuto, postava je skrytá a vidí ji pouze Dungeon Master."
    )

    class Meta:
        verbose_name = "Postava hráče"
        verbose_name_plural = "Postavy hráče"
        ordering = ['-level', 'name']

    def save(self, *args, **kwargs):
        while self.silver >= 10:
            self.gold += 1
            self.silver -= 10
        while self.silver < 0:
            self.gold -= 1
            self.silver += 10

        if self.gold < 0:
            self.gold = 0
        if self.silver < 0:
            self.silver = 0

        super().save(*args, **kwargs)

    @property
    def has_custom_image(self):
        """Vrátí True, pokud má postava nahraný vlastní obrázek nebo aktivní ikonku."""
        if self.active_icon_id:
            return True
        if self.image:
            name = getattr(self.image, 'name', '') or ''
            if name and name != 'characters/default_avatar.jpg':
                return True
        if self.image_url and self.image_url.strip():
            if 'default_avatar' not in self.image_url:
                return True
        return False

    @property
    def default_class_image_url(self):
        """Vrátí URL unikátního výchozího profilového obrázku podle povolání postavy."""
        class_key = (self.character_class or "").strip().lower()
        mapping = {
            'barbar': '/static/img/classes/barbar.svg',
            'bard': '/static/img/classes/bard.svg',
            'bojovník': '/static/img/classes/bojovnik.svg',
            'bojovnik': '/static/img/classes/bojovnik.svg',
            'fighter': '/static/img/classes/bojovnik.svg',
            'čaroděj': '/static/img/classes/carodej.svg',
            'carodej': '/static/img/classes/carodej.svg',
            'sorcerer': '/static/img/classes/carodej.svg',
            'černokněžník': '/static/img/classes/cernokneznik.svg',
            'cernokneznik': '/static/img/classes/cernokneznik.svg',
            'warlock': '/static/img/classes/cernokneznik.svg',
            'druid': '/static/img/classes/druid.svg',
            'hraničář': '/static/img/classes/hranicar.svg',
            'hranicar': '/static/img/classes/hranicar.svg',
            'ranger': '/static/img/classes/hranicar.svg',
            'klerik': '/static/img/classes/klerik.svg',
            'cleric': '/static/img/classes/klerik.svg',
            'kouzelník': '/static/img/classes/kouzelnik.svg',
            'kouzelnik': '/static/img/classes/kouzelnik.svg',
            'wizard': '/static/img/classes/kouzelnik.svg',
            'mnich': '/static/img/classes/mnich.svg',
            'monk': '/static/img/classes/mnich.svg',
            'paladin': '/static/img/classes/paladin.svg',
            'tulák': '/static/img/classes/tulak.svg',
            'tulak': '/static/img/classes/tulak.svg',
            'rogue': '/static/img/classes/tulak.svg',
        }
        for key, url in mapping.items():
            if key in class_key:
                return url
        return '/static/img/classes/ostatni.svg'

    @property
    def profile_image_url(self):
        """Vrátí URL aktivní ikonky z Esence Shopu, vlastního profilového obrázku, nebo výchozí obrázek podle povolání postavy."""
        if self.active_icon and self.active_icon.item and self.active_icon.item.image:
            try:
                return self.active_icon.item.image.url
            except Exception:
                pass
        if self.has_custom_image:
            if self.image:
                try:
                    return self.image.url
                except Exception:
                    pass
            if self.image_url:
                return self.image_url
        if self.player and getattr(self.player, 'active_icon', None) and self.player.active_icon.item and self.player.active_icon.item.image:
            try:
                return self.player.active_icon.item.image.url
            except Exception:
                pass
        return self.default_class_image_url

    @property
    def frame_url(self):
        """Vrátí URL aktivního rámečku hráče pro tuto postavu (nebo None)."""
        if self.player:
            return self.player.active_frame_url
        return None

    @property
    def active_frame_url(self):
        return self.frame_url

    def __str__(self):
        cls_str = f" ({self.character_class})" if self.character_class else ""
        return f"{self.name} - Úr. {self.level}{cls_str} [{self.player}]"

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
        return self.hit_points_max or 10

    @property
    def current_hp_val(self):
        if self.hit_points_current is not None:
            return self.hit_points_current
        return self.max_hp

# DATABÁZE EXISTUJÍCÍCH ACHIVEMENTŮ
class Achivements_database(models.Model):
    image = models.FileField(upload_to='achievements/', blank=True, null=True, verbose_name="Ikona úspěchu")
    name = models.CharField(max_length=50, verbose_name="Jméno úspěchu")
    description = models.CharField(max_length=200, verbose_name="Popis úspěchu")

    bronze_value = models.FloatField(default=0, verbose_name="hodnota pro bronze", null=True, blank=True)
    silver_value = models.FloatField(default=0, verbose_name="hodnota pro silver", null=True, blank=True)
    gold_value = models.FloatField(default=0, verbose_name="hodnota pro gold", null=True, blank=True)
    platinum_value = models.FloatField(default=0, verbose_name="hodnota pro platinum", null=True, blank=True)
    emerald_value = models.FloatField(default=0, verbose_name="hodnota pro emerald", null=True, blank=True)
    diamond_value = models.FloatField(default=0, verbose_name="hodnota pro diamond", null=True, blank=True)

    class Meta:
        verbose_name = "Úspěch (šablona)"
        verbose_name_plural = "Úspěchy (šablony)"

    def __str__(self):
        return self.name

    @property
    def display_icon_url(self):
        """Vrátí URL nahraného obrázku nebo výchozí předpřipravenou SVG ikonu."""
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        slug_map = {
            'cesta hrdiny': 'cesta_hrdiny.svg',
            'esencionik': 'esencionik.svg',
            'gambler': 'gambler.svg',
            'sladke mameni': 'sladke_mameni.svg',
            'sladké mámení': 'sladke_mameni.svg',
            'smolar': 'smolar.svg',
            'smolař': 'smolar.svg',
            'smrtici stroj': 'smrtici_stroj.svg',
            'smrtící stroj': 'smrtici_stroj.svg',
            'stvoritel': 'stvoritel.svg',
            'stvořitel': 'stvoritel.svg',
            'vsechno je jednou poprve': 'vsechno_je_jednou_poprve.svg',
            'všechno je jednou poprvé': 'vsechno_je_jednou_poprve.svg',
            'zbohatlik': 'zbohatlik.svg',
            'zbohatlík': 'zbohatlik.svg',
            'stistko': 'stistko.svg',
            'štístko': 'stistko.svg',
        }
        clean_name = self.name.strip().lower() if self.name else ""
        if clean_name in slug_map:
            return f'/static/img/achievements/{slug_map[clean_name]}'
        return '/static/img/achievements/default.svg'


# Databáze existujících achivementů
class Achivements_players(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='achivements',
        verbose_name="Hráč",
        blank = True,
        null = True
    )
    Achivement = models.ForeignKey(
        Achivements_database,
        on_delete=models.CASCADE,
        related_name='achivements',
        verbose_name="Achivement",
        blank = True,
        null = True
    )
    char = models.ForeignKey(
        Char_info,
        on_delete=models.CASCADE,
        related_name='achivements',
        verbose_name="Postava",
        blank = True,
        null = True
    )

    STATUS_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('emerald', 'Emerald'),
        ('diamond', 'Diamond'),
    ]

    current_status = models.CharField(max_length=20, verbose_name="Aktuální status", choices=STATUS_CHOICES, null=True, blank=True)
    current_value = models.FloatField(default=0, verbose_name="Současná hodnota")

    bronze_obtained_date = models.DateTimeField(null=True, blank=True, verbose_name="Datum získání bronze")
    silver_obtained_date = models.DateTimeField(null=True, blank=True, verbose_name="Datum získání silver")
    gold_obtained_date = models.DateTimeField(null=True, blank=True, verbose_name="Datum získání gold")
    platinum_obtained_date = models.DateTimeField(null=True, blank=True, verbose_name="Datum získání platinum")
    emerald_obtained_date = models.DateTimeField(null=True, blank=True, verbose_name="Datum získání emerald")
    diamond_obtained_date = models.DateTimeField(null=True, blank=True, verbose_name="Datum získání diamond")

    class Meta:
        verbose_name = "Úspěch hráče"
        verbose_name_plural = "Úspěchy hráčů"
        ordering = ['-current_value', 'Achivement']

    def __str__(self):
        ach_name = self.Achivement.name if self.Achivement else "Neznámý úspěch"
        who = self.char.name if self.char else (str(self.player) if self.player else "Neznámý")
        status = f" ({self.get_current_status_display()})" if self.current_status else ""
        return f"{who} - {ach_name}{status}"

    @property
    def achivement(self):
        """Umožňuje přístup k FK přes malé písmeno achivement."""
        return self.Achivement
    
    def update_achivement_status(self):
        if not self.Achivement:
            return

        # Pokud není hráč přímo nastaven, zkusíme ho převzít z postavy
        if not self.player and self.char and self.char.player:
            self.player = self.char.player

        tier_ranks = {
            'bronze': 1,
            'silver': 2,
            'gold': 3,
            'platinum': 4,
            'emerald': 5,
            'diamond': 6,
        }

        old_status = None
        if self.pk:
            try:
                db_status = Achivements_players.objects.filter(pk=self.pk).values_list('current_status', flat=True).first()
                if db_status:
                    old_status = db_status
            except Exception:
                old_status = self.current_status
        old_rank = tier_ranks.get(old_status, 0)

        d_val = self.Achivement.diamond_value
        e_val = self.Achivement.emerald_value
        p_val = self.Achivement.platinum_value
        g_val = self.Achivement.gold_value
        s_val = self.Achivement.silver_value
        b_val = self.Achivement.bronze_value

        tiers = [
            ('bronze', b_val, 25, 'bronze_obtained_date', lambda v, b: b is not None and v >= b and (b > 0 or v > 0)),
            ('silver', s_val, 50, 'silver_obtained_date', lambda v, s: s is not None and s > 0 and v >= s),
            ('gold', g_val, 100, 'gold_obtained_date', lambda v, g: g is not None and g > 0 and v >= g),
            ('platinum', p_val, 250, 'platinum_obtained_date', lambda v, p: p is not None and p > 0 and v >= p),
            ('emerald', e_val, 500, 'emerald_obtained_date', lambda v, e: e is not None and e > 0 and v >= e),
            ('diamond', d_val, 1000, 'diamond_obtained_date', lambda v, d: d is not None and d > 0 and v >= d),
        ]

        highest_tier = None
        essence_added = 0
        now = timezone.now()

        for tier_name, threshold, reward, date_attr, cond_fn in tiers:
            if cond_fn(self.current_value, threshold):
                highest_tier = tier_name
                tier_rank = tier_ranks[tier_name]
                date_val = getattr(self, date_attr)
                if not date_val:
                    setattr(self, date_attr, now)
                    if old_rank < tier_rank:
                        essence_added += reward

        self.current_status = highest_tier

        if essence_added > 0 and self.player:
            if self.player.temna_esence is None:
                self.player.temna_esence = 0
            self.player.temna_esence += essence_added
            self.player.save()

            # Zamezení zacyklení: propsání temné esence do achievementu "Esencionik"
            # provádíme pouze tehdy, pokud aktuální achievement NENÍ "Esencionik".
            ach_name = self.Achivement.name.strip().lower() if self.Achivement and self.Achivement.name else ""
            if ach_name != "esencionik":
                target_char = self.char
                if not target_char and self.player:
                    target_char = self.player.characters.first()
                if target_char:
                    try:
                        esencionik_db = Achivements_database.objects.filter(name__iexact="Esencionik").first()
                        if esencionik_db:
                            es_ach, _ = Achivements_players.objects.get_or_create(
                                player=self.player,
                                char=target_char,
                                Achivement=esencionik_db,
                                defaults={'current_value': 0}
                            )
                            es_ach.current_value += essence_added
                            es_ach.save()
                    except Exception:
                        pass


    def save(self, *args, **kwargs):
        self.update_achivement_status() # Spuštění funkce pro kontrolu achivementu
        super().save(*args, **kwargs)

class Logs(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="Hráč"
    )

    character = models.ForeignKey(
        Char_info,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="Postava"
    )

    
    message = models.CharField(max_length=200, verbose_name="Zpráva")
    value = models.FloatField(default=0, verbose_name="Hodnota", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")

    def __str__(self):
        return f"{self.player} - {self.character} - {self.message} - {self.value}"


EsenceShopChoices = [
    ('borders', 'Rámečky'),
    ('icons', 'Ikonky profilu'),
    ('backgrounds', 'Pozadí'),
    ('treasures', 'Truhly'),
]   

Rarities = [
    ('basic', 'Běžná'),
    ('rare', 'Vzácná'),
    ('epic', 'Epická'),
    ('legendary', 'Legendární'),
]

class Esence_Items_Shop(models.Model):
    name = models.CharField(max_length=100, verbose_name="Jméno")
    category = models.CharField(max_length=100, verbose_name="Kategorie", choices=EsenceShopChoices)
    image = models.FileField(upload_to='esence_items', verbose_name="Obrázek")
    rarity = models.CharField(max_length=100, verbose_name="Rarita", choices=Rarities, default="basic")
    cost = models.IntegerField(default=0, verbose_name="Cena", blank=True, null=True) 

    @property
    def dismantle_value(self):
        """Vrátí počet temné esence získané za rozebrání předmětu podle rarity."""
        values = {
            'basic': 5,
            'rare': 25,
            'epic': 50,
            'legendary': 100,
        }
        return values.get(self.rarity, 0)

    def __str__(self):
        return f"{self.name} - {self.rarity} - {self.category}"

class Esence_Items_Owners(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='esence_items',
        verbose_name="Hráč"
    )
    item = models.ForeignKey(
        Esence_Items_Shop,
        on_delete=models.CASCADE,
        related_name='esence_items',
        verbose_name="Předmět"
    )

    class Meta:
        verbose_name = "Vlastněný předmět z Esence Shopu"
        verbose_name_plural = "Vlastněné předměty z Esence Shopu"

    def __str__(self):
        return f"{self.item.name} ({self.player})"
        
    
class CharNotes(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Hráč"
    )
    character = models.ForeignKey(
        Char_info,
        on_delete=models.CASCADE,
        related_name='char_notes',
        verbose_name="Postava"
    )
    title = models.CharField(max_length=200, default="Nová poznámka", verbose_name="Název poznámky")
    note = models.TextField(verbose_name="Text poznámky")
    is_favorite = models.BooleanField(default=False, verbose_name="Oblíbená poznámka")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualizováno")

    class Meta:
        verbose_name = "Poznámka hráče"
        verbose_name_plural = "Poznámky hráčů"
        ordering = ['-is_favorite', '-updated_at']

    def __str__(self):
        return f"{self.character.name} - {self.title} ({self.player})"


class CharBackstory(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='backstories',
        verbose_name="Hráč"
    )
    character = models.ForeignKey(
        Char_info,
        on_delete=models.CASCADE,
        related_name='char_backstories',
        verbose_name="Postava"
    )
    title = models.CharField(max_length=200, default="Kapitola příběhu", verbose_name="Název zápisu")
    backstory = models.TextField(verbose_name="Příběh postavy")
    public = models.BooleanField(default=False, verbose_name="Veřejné pro ostatní hráče")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualizováno")

    class Meta:
        verbose_name = "Příběh postavy"
        verbose_name_plural = "Příběhy postav"
        ordering = ['-created_at']

    def __str__(self):
        status = "Veřejné" if self.public else "Soukromé"
        return f"{self.character.name} - {self.title} [{status}] ({self.player})"


    
        