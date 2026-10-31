from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import random


def create_db_log(character=None, player=None, message="", value=0.0):
    """Pomocná funkce pro bezpečný zápis podrobného záznamu do tabulky Logs."""
    try:
        if player is None and character is not None:
            player = getattr(character, 'player', None)
        if character is None and player is not None:
            try:
                character = player.characters.first()
            except Exception:
                character = None
        if player is None:
            return None
        clean_msg = str(message or "").strip()[:500]
        clean_val = float(value) if value is not None else 0.0
        return Logs.objects.create(
            player=player,
            character=character,
            message=clean_msg,
            value=clean_val
        )
    except Exception as exc:
        print(f"[Log Error] Nepodařilo se zapsat do Logs: {exc}")
        return None



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
    pin_code = models.TextField(blank=True, null=True, verbose_name="PIN kód")

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
    has_new_kronika = models.BooleanField(default=False, verbose_name="Nový záznam v Kronice")

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
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        old_player = None
        if self.pk and not skip_auto_log:
            try:
                old_player = Player.objects.filter(pk=self.pk).first()
            except Exception:
                old_player = None

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

        if old_player and not skip_auto_log:
            p_name = self.nickname or (self.user.username if self.user else f"Hráč #{self.pk}")
            if (old_player.temna_esence or 0) != (self.temna_esence or 0):
                old_te = old_player.temna_esence or 0
                new_te = self.temna_esence or 0
                delta = new_te - old_te
                sign = "+" if delta >= 0 else ""
                create_db_log(
                    player=self,
                    message=f"Změna Temné esence hráče {p_name}: {old_te} -> {new_te} TE ({sign}{delta} TE)",
                    value=float(delta)
                )
            if old_player.nickname != self.nickname:
                create_db_log(
                    player=self,
                    message=f"Změna přezdívky hráče z '{old_player.nickname}' na '{self.nickname}'",
                    value=0.0
                )
            if old_player.pin_code != self.pin_code:
                create_db_log(
                    player=self,
                    message=f"Hráči {p_name} byl změněn přihlašovací PIN kód",
                    value=0.0
                )
            if old_player.active_ramecek_id != self.active_ramecek_id:
                frame_name = self.active_ramecek.item.name if (self.active_ramecek and self.active_ramecek.item) else "Žádný"
                create_db_log(
                    player=self,
                    message=f"Změna aktivního rámečku hráče {p_name} na: '{frame_name}'",
                    value=0.0
                )
            if old_player.active_icon_id != self.active_icon_id:
                icon_name = self.active_icon.item.name if (self.active_icon and self.active_icon.item) else "Výchozí"
                create_db_log(
                    player=self,
                    message=f"Změna aktivní profilové ikonky hráče {p_name} na: '{icon_name}'",
                    value=0.0
                )
        self._skip_auto_log = False

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
    def owned_frames(self):
        """Vrátí unikátní položky rámečků (borders), které hráč vlastní."""
        records = self.esence_items.filter(item__category='borders').select_related('item').order_by('item__rarity', 'item__name')
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

    saving_throw_choices = (
        ("Síla", "Síla (STR)"),
        ("Obratnost", "Obratnost (DEX)"),
        ("Odolnost", "Odolnost (CON)"),
        ("Inteligence", "Inteligence (INT)"),
        ("Moudrost", "Moudrost (WIS)"),
        ("Charisma", "Charisma (CHA)"),
    )

    skill_choices = (
        ("Akrobacie", "Akrobacie (OBR)"),
        ("Atletika", "Atletika (SIL)"),
        ("Historie", "Historie (INT)"),
        ("Hbitost rukou", "Hbitost rukou (OBR)"),
        ("Klamání", "Klamání (CHA)"),
        ("Lékařství", "Lékařství (MDR)"),
        ("Mystika", "Mystika (INT)"),
        ("Náboženství", "Náboženství (INT)"),
        ("Nenápadnost", "Nenápadnost (OBR)"),
        ("Ovládání zvířat", "Ovládání zvířat (MDR)"),
        ("Pátrání", "Pátrání (INT)"),
        ("Přesvědčování", "Přesvědčování (CHA)"),
        ("Přežití", "Přežití (MDR)"),
        ("Příroda", "Příroda (INT)"),
        ("Vhled", "Vhled (MDR)"),
        ("Vnímání", "Vnímání (MDR)"),
        ("Vystupování", "Vystupování (CHA)"),
        ("Zastrašování", "Zastrašování (CHA)"),
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
    

    # Bojové statistiky & Životy (Deník hrdiny)
    armor_class = models.IntegerField(default=10, verbose_name="Třída zbroje (AC)")
    hit_points_max = models.IntegerField(default=10, verbose_name="Maximální životy")
    hit_points_current = models.IntegerField(default=10, verbose_name="Současné životy")
    speed = models.IntegerField(default=30, verbose_name="Rychlost (stopy)")
    initiative = models.IntegerField(default=0, verbose_name="Iniciativa")
    inspiration = models.BooleanField(default=False, verbose_name="Inspirace")
    proficiency_bonus = models.IntegerField(default=2, verbose_name="Zdatnostní bonus")
    passive_perception = models.IntegerField(default=10, verbose_name="Pasivní moudrost (vnímání)")
    hit_dice = models.CharField(max_length=50, default="1d8", blank=True, null=True, verbose_name="Kostka životů")
    saving_throws = models.JSONField(default=list, blank=True, verbose_name="Záchranné hody")
    skills = models.JSONField(default=list, blank=True, verbose_name="Dovednosti")

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
    has_new_inv = models.BooleanField(default=False, verbose_name="Nový předmět v inventáři")
    has_new_ach = models.BooleanField(default=False, verbose_name="Nový posun v úspěších")

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
        if self.silver is None:
            self.silver = 0
        if self.gold is None:
            self.gold = 0

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

        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_new = self.pk is None
        old_char = None
        if not is_new and not skip_auto_log:
            try:
                old_char = Char_info.objects.filter(pk=self.pk).first()
            except Exception:
                old_char = None

        super().save(*args, **kwargs)

        if not skip_auto_log:
            if is_new:
                create_db_log(
                    character=self,
                    player=self.player,
                    message=f"Vytvořena nová postava: {self.name} (Úroveň {self.level}, {self.character_class or 'Ostatní'})",
                    value=float(self.level or 1)
                )
            elif old_char:
                if old_char.name != self.name:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna jména postavy z '{old_char.name}' na '{self.name}'",
                        value=0.0
                    )
                if old_char.race != self.race:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna rasy postavy {self.name}: {old_char.race} -> {self.race}",
                        value=0.0
                    )
                if old_char.character_class != self.character_class:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna povolání postavy {self.name}: {old_char.character_class} -> {self.character_class}",
                        value=0.0
                    )
                if old_char.level != self.level:
                    delta_lvl = (self.level or 0) - (old_char.level or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna úrovně (Level) postavy {self.name}: {old_char.level} -> {self.level}",
                        value=float(delta_lvl)
                    )
                if (old_char.experience_points or 0) != (self.experience_points or 0):
                    delta_xp = (self.experience_points or 0) - (old_char.experience_points or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna zkušeností (XP) postavy {self.name}: {old_char.experience_points or 0} -> {self.experience_points or 0} XP",
                        value=float(delta_xp)
                    )
                if old_char.background != self.background:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna zázemí postavy {self.name}: {old_char.background} -> {self.background}",
                        value=0.0
                    )
                if old_char.alignment != self.alignment:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna přesvědčení postavy {self.name}: {old_char.alignment} -> {self.alignment}",
                        value=0.0
                    )
                if (old_char.gold or 0) != (self.gold or 0) or (old_char.silver or 0) != (self.silver or 0):
                    old_g_total = (old_char.gold or 0) + (old_char.silver or 0) / 10.0
                    new_g_total = (self.gold or 0) + (self.silver or 0) / 10.0
                    delta_gold = round(new_g_total - old_g_total, 2)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna financí postavy {self.name}: {old_char.gold or 0} zl {old_char.silver or 0} st -> {self.gold or 0} zl {self.silver or 0} st",
                        value=float(delta_gold)
                    )
                if old_char.hit_points_current != self.hit_points_current:
                    delta_hp = (self.hit_points_current or 0) - (old_char.hit_points_current or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna životů (HP) postavy {self.name}: {old_char.hit_points_current} -> {self.hit_points_current} / {self.hit_points_max} HP",
                        value=float(delta_hp)
                    )
                if old_char.hit_points_max != self.hit_points_max:
                    delta_max_hp = (self.hit_points_max or 0) - (old_char.hit_points_max or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna maximálních životů (Max HP) postavy {self.name}: {old_char.hit_points_max} -> {self.hit_points_max} HP",
                        value=float(delta_max_hp)
                    )
                if old_char.armor_class != self.armor_class:
                    delta_ac = (self.armor_class or 0) - (old_char.armor_class or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna třídy zbroje (AC) postavy {self.name}: {old_char.armor_class} -> {self.armor_class}",
                        value=float(delta_ac)
                    )
                if old_char.speed != self.speed:
                    delta_spd = (self.speed or 0) - (old_char.speed or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna rychlosti postavy {self.name}: {old_char.speed} -> {self.speed} stop",
                        value=float(delta_spd)
                    )
                if old_char.initiative != self.initiative:
                    delta_init = (self.initiative or 0) - (old_char.initiative or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna iniciativy postavy {self.name}: {old_char.initiative} -> {self.initiative}",
                        value=float(delta_init)
                    )
                if old_char.inspiration != self.inspiration:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna inspirace postavy {self.name}: {'Ano' if old_char.inspiration else 'Ne'} -> {'Ano' if self.inspiration else 'Ne'}",
                        value=1.0 if self.inspiration else 0.0
                    )
                if old_char.proficiency_bonus != self.proficiency_bonus:
                    delta_prof = (self.proficiency_bonus or 0) - (old_char.proficiency_bonus or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna zdatnostního bonusu postavy {self.name}: {old_char.proficiency_bonus} -> {self.proficiency_bonus}",
                        value=float(delta_prof)
                    )
                if old_char.passive_perception != self.passive_perception:
                    delta_pp = (self.passive_perception or 0) - (old_char.passive_perception or 0)
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna pasivního vnímání postavy {self.name}: {old_char.passive_perception} -> {self.passive_perception}",
                        value=float(delta_pp)
                    )
                if old_char.hit_dice != self.hit_dice:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna kostky životů postavy {self.name}: {old_char.hit_dice} -> {self.hit_dice}",
                        value=0.0
                    )
                ability_fields = [
                    ('strength', 'Síla (STR)'),
                    ('dexterity', 'Obratnost (DEX)'),
                    ('constitution', 'Odolnost (CON)'),
                    ('intelligence', 'Inteligence (INT)'),
                    ('wisdom', 'Moudrost (WIS)'),
                    ('charisma', 'Charisma (CHA)'),
                ]
                for field_attr, label in ability_fields:
                    old_v = getattr(old_char, field_attr, 10) or 0
                    new_v = getattr(self, field_attr, 10) or 0
                    if old_v != new_v:
                        create_db_log(
                            character=self,
                            player=self.player,
                            message=f"Změna atributu {label} postavy {self.name}: {old_v} -> {new_v}",
                            value=float(new_v - old_v)
                        )
                if old_char.saving_throws != self.saving_throws:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna záchranných hodů postavy {self.name}: {', '.join(self.saving_throws_list) or 'Žádné'}",
                        value=0.0
                    )
                if old_char.skills != self.skills:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna dovedností postavy {self.name}: {', '.join(self.skills_list) or 'Žádné'}",
                        value=0.0
                    )
                if old_char.in_fight != self.in_fight:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Postava {self.name} {'vstoupila do boje' if self.in_fight else 'opustila boj'}",
                        value=1.0 if self.in_fight else 0.0
                    )
                if old_char.is_public != self.is_public:
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna viditelnosti postavy {self.name}: {'Veřejná pro družinu' if self.is_public else 'Skrytá (pouze DM)'}",
                        value=1.0 if self.is_public else 0.0
                    )
                old_img_name = getattr(old_char.image, 'name', '') or ''
                new_img_name = getattr(self.image, 'name', '') or ''
                if (
                    old_char.active_icon_id != self.active_icon_id
                    or old_img_name != new_img_name
                    or (old_char.image_url or '') != (self.image_url or '')
                ):
                    create_db_log(
                        character=self,
                        player=self.player,
                        message=f"Změna profilového obrázku postavy {self.name}",
                        value=0.0
                    )

        self._skip_auto_log = False

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

    @property
    def initiative_display(self):
        return f"+{self.initiative}" if self.initiative >= 0 else str(self.initiative)

    @property
    def inspiration_display(self):
        return "Ano" if self.inspiration else "Ne"

    @property
    def proficiency_bonus_display(self):
        return f"+{self.proficiency_bonus}" if self.proficiency_bonus >= 0 else str(self.proficiency_bonus)

    @property
    def saving_throws_list(self):
        if isinstance(self.saving_throws, list):
            return self.saving_throws
        if isinstance(self.saving_throws, str) and self.saving_throws:
            return [s.strip() for s in self.saving_throws.split(',') if s.strip()]
        return []

    @property
    def skills_list(self):
        if isinstance(self.skills, list):
            return self.skills
        if isinstance(self.skills, str) and self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []

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
                if hasattr(self.image, 'storage') and self.image.storage.exists(self.image.name):
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
        newly_unlocked_tiers = []
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
                        newly_unlocked_tiers.append((tier_name, reward))

        self.current_status = highest_tier

        if essence_added > 0 and self.player:
            if self.player.temna_esence is None:
                self.player.temna_esence = 0
            self.player.temna_esence += essence_added
            self.player._skip_auto_log = True
            self.player.save()

            ach_title = self.Achivement.name if self.Achivement else "Úspěch"
            target_char = self.char
            if not target_char and self.player:
                target_char = self.player.characters.first()
            char_label = target_char.name if target_char else (self.player.nickname or "Hráč")
            tier_labels = ", ".join([f"{t.capitalize()} (+{r} TE)" for t, r in newly_unlocked_tiers])

            create_db_log(
                character=target_char,
                player=self.player,
                message=f"Postava {char_label} odemkla hodnost {tier_labels} v úspěchu '{ach_title}'! Získáno +{essence_added} Temné esence (celkem {self.player.temna_esence} TE)",
                value=float(essence_added)
            )

            # Zamezení zacyklení: propsání temné esence do achievementu "Esencionik"
            # provádíme pouze tehdy, pokud aktuální achievement NENÍ "Esencionik".
            ach_name = self.Achivement.name.strip().lower() if self.Achivement and self.Achivement.name else ""
            if ach_name != "esencionik":
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
                            old_es_val = es_ach.current_value or 0
                            es_ach.current_value = old_es_val + essence_added
                            es_ach._skip_auto_log = True
                            es_ach.save()
                            create_db_log(
                                character=target_char,
                                player=self.player,
                                message=f"Postup v úspěchu 'Esencionik' (z odměny za '{ach_title}'): {old_es_val} -> {es_ach.current_value} (+{essence_added} TE)",
                                value=float(essence_added)
                            )
                    except Exception:
                        pass


    def save(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_passive_gold_check = getattr(self, '_is_passive_gold_check', False)
        is_new = self.pk is None
        old_val = None
        old_status = None
        if not is_new:
            try:
                old_row = Achivements_players.objects.filter(pk=self.pk).values('current_value', 'current_status').first()
                if old_row:
                    old_val = old_row['current_value']
                    old_status = old_row['current_status']
            except Exception:
                old_val = None
                old_status = None

        self.update_achivement_status() # Spuštění funkce pro kontrolu achivementu
        super().save(*args, **kwargs)

        target_char = self.char or (self.player.characters.first() if self.player else None)
        if target_char:
            status_changed = (old_status != self.current_status and bool(self.current_status))
            value_progressed = (old_val is not None and (self.current_value or 0) > (old_val or 0))
            if status_changed or (not is_passive_gold_check and (is_new or value_progressed)):
                Char_info.objects.filter(pk=target_char.pk).update(has_new_ach=True)
                target_char.has_new_ach = True

        if not skip_auto_log:
            ach_title = self.Achivement.name if self.Achivement else "Úspěch"
            char_label = target_char.name if target_char else (self.player.nickname if self.player else "Hráč")
            if is_new:
                create_db_log(
                    character=target_char,
                    player=self.player,
                    message=f"Postavě {char_label} byl přiřazen úspěch '{ach_title}' (hodnota: {self.current_value})",
                    value=float(self.current_value or 0)
                )
            elif old_val is not None and old_val != self.current_value:
                delta = (self.current_value or 0) - (old_val or 0)
                create_db_log(
                    character=target_char,
                    player=self.player,
                    message=f"Změna hodnoty úspěchu '{ach_title}' u postavy {char_label}: {old_val} -> {self.current_value}",
                    value=float(delta)
                )
        self._skip_auto_log = False
        self._is_passive_gold_check = False

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
        verbose_name="Postava",
        null=True,
        blank=True
    )

    message = models.CharField(max_length=500, verbose_name="Zpráva")
    value = models.FloatField(default=0, verbose_name="Hodnota", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")

    class Meta:
        verbose_name = "Log změn"
        verbose_name_plural = "Logy změn"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.player_id and self.character_id and self.character and self.character.player_id:
            self.player = self.character.player
        if self.message and len(self.message) > 500:
            self.message = self.message[:500]
        super().save(*args, **kwargs)

    def __str__(self):
        char_str = str(self.character.name) if self.character else "Bez postavy"
        return f"{self.player} - {char_str} - {self.message} ({self.value})"


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
            'basic': 1,
            'rare': 5,
            'epic': 10,
            'legendary': 20,
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

    def save(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_new = self.pk is None
        old_note = None
        if not is_new and not skip_auto_log:
            old_note = CharNotes.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)
        if not skip_auto_log and self.character:
            if is_new:
                create_db_log(
                    character=self.character,
                    player=self.player,
                    message=f"Přidána poznámka postavy {self.character.name}: '{self.title}'",
                    value=0.0
                )
            elif old_note:
                if old_note.is_favorite != self.is_favorite:
                    fav_label = "označena jako oblíbená" if self.is_favorite else "odebrána z oblíbených"
                    create_db_log(
                        character=self.character,
                        player=self.player,
                        message=f"Poznámka '{self.title}' postavy {self.character.name} byla {fav_label}",
                        value=1.0 if self.is_favorite else 0.0
                    )
                elif old_note.title != self.title or old_note.note != self.note:
                    create_db_log(
                        character=self.character,
                        player=self.player,
                        message=f"Upravena poznámka postavy {self.character.name}: '{self.title}'",
                        value=0.0
                    )
        self._skip_auto_log = False

    def delete(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        char = self.character
        player = self.player
        title = self.title
        res = super().delete(*args, **kwargs)
        if not skip_auto_log and char:
            create_db_log(
                character=char,
                player=player,
                message=f"Smazána poznámka postavy {char.name}: '{title}'",
                value=0.0
            )
        return res


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

    def save(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_new = self.pk is None
        old_story = None
        if not is_new and not skip_auto_log:
            old_story = CharBackstory.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)
        if not skip_auto_log and self.character:
            vis_str = "Veřejná" if self.public else "Soukromá"
            if is_new:
                create_db_log(
                    character=self.character,
                    player=self.player,
                    message=f"Přidána kapitola příběhu postavy {self.character.name}: '{self.title}' ({vis_str})",
                    value=0.0
                )
            elif old_story:
                if old_story.public != self.public:
                    create_db_log(
                        character=self.character,
                        player=self.player,
                        message=f"Kapitola příběhu '{self.title}' postavy {self.character.name} byla nastavena jako {vis_str}",
                        value=1.0 if self.public else 0.0
                    )
                elif old_story.title != self.title or old_story.backstory != self.backstory:
                    create_db_log(
                        character=self.character,
                        player=self.player,
                        message=f"Upravena kapitola příběhu postavy {self.character.name}: '{self.title}'",
                        value=0.0
                    )
        self._skip_auto_log = False

    def delete(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        char = self.character
        player = self.player
        title = self.title
        res = super().delete(*args, **kwargs)
        if not skip_auto_log and char:
            create_db_log(
                character=char,
                player=player,
                message=f"Smazána kapitola příběhu postavy {char.name}: '{title}'",
                value=0.0
            )
        return res


class CharacterSpellSlot(models.Model):
    character = models.ForeignKey(
        Char_info,
        on_delete=models.CASCADE,
        related_name='spell_slots',
        verbose_name="Postava"
    )
    level = models.IntegerField(default=1, verbose_name="Úroveň kouzla (1–9)")
    current_slots = models.IntegerField(default=0, verbose_name="Volné pozice")
    max_slots = models.IntegerField(default=0, verbose_name="Maximální pozice")

    class Meta:
        verbose_name = "Pozice pro kouzla"
        verbose_name_plural = "Pozice pro kouzla"
        ordering = ['level']
        unique_together = ('character', 'level')

    def __str__(self):
        return f"{self.character.name} - Úroveň {self.level}: {self.current_slots}/{self.max_slots}"

    @property
    def used_slots(self):
        return max(0, self.max_slots - self.current_slots)

    def save(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_new = self.pk is None
        old_slot = None
        if not is_new and not skip_auto_log:
            old_slot = CharacterSpellSlot.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)
        if not skip_auto_log and self.character:
            if is_new:
                create_db_log(
                    character=self.character,
                    player=self.character.player,
                    message=f"Nastaveny pozice pro kouzla ({self.level}. úroveň) postavy {self.character.name}: {self.current_slots}/{self.max_slots}",
                    value=float(self.current_slots)
                )
            elif old_slot and (old_slot.current_slots != self.current_slots or old_slot.max_slots != self.max_slots):
                delta = (self.current_slots or 0) - (old_slot.current_slots or 0)
                create_db_log(
                    character=self.character,
                    player=self.character.player,
                    message=f"Změna pozic pro kouzla ({self.level}. úroveň) postavy {self.character.name}: {old_slot.current_slots}/{old_slot.max_slots} -> {self.current_slots}/{self.max_slots}",
                    value=float(delta)
                )
        self._skip_auto_log = False

    def delete(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        char = self.character
        lvl = self.level
        res = super().delete(*args, **kwargs)
        if not skip_auto_log and char:
            create_db_log(
                character=char,
                player=char.player,
                message=f"Odstraněny pozice pro kouzla ({lvl}. úroveň) postavy {char.name}",
                value=0.0
            )
        return res


class CharacterFeature(models.Model):
    character = models.ForeignKey(
        Char_info,
        on_delete=models.CASCADE,
        related_name='features',
        verbose_name="Postava"
    )
    title = models.CharField(max_length=200, verbose_name="Název schopnosti / rysu")
    description = models.TextField(verbose_name="Popis schopnosti nebo rysu")
    source = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zdroj (povolání, rasa, zázemí, apod.)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")

    class Meta:
        verbose_name = "Schopnost a rys postavy"
        verbose_name_plural = "Schopnosti a rysy postav"
        ordering = ['title']

    def __str__(self):
        return f"{self.character.name} - {self.title}"

    def save(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        is_new = self.pk is None
        old_feat = None
        if not is_new and not skip_auto_log:
            old_feat = CharacterFeature.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)
        if not skip_auto_log and self.character:
            src_info = f" ({self.source})" if self.source else ""
            if is_new:
                create_db_log(
                    character=self.character,
                    player=self.character.player,
                    message=f"Přidána schopnost/rys postavy {self.character.name}: '{self.title}'{src_info}",
                    value=0.0
                )
            elif old_feat and (old_feat.title != self.title or old_feat.description != self.description or old_feat.source != self.source):
                create_db_log(
                    character=self.character,
                    player=self.character.player,
                    message=f"Upravena schopnost/rys postavy {self.character.name}: '{self.title}'{src_info}",
                    value=0.0
                )
        self._skip_auto_log = False

    def delete(self, *args, **kwargs):
        skip_auto_log = getattr(self, '_skip_auto_log', False)
        char = self.character
        title = self.title
        res = super().delete(*args, **kwargs)
        if not skip_auto_log and char:
            create_db_log(
                character=char,
                player=char.player,
                message=f"Odebrána schopnost/rys postavy {char.name}: '{title}'",
                value=0.0
            )
        return res