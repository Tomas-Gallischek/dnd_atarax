from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
import random


class Player(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='player',
        verbose_name="Uživatelský účet"
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
    pin_code = models.IntegerField(default=0, verbose_name="Pin kod", blank=True, null=True)

    admin = models.BooleanField(default=False, verbose_name="Jsi administrátor", blank=True, null=True)

    class Meta:
        verbose_name = "Hráč"
        verbose_name_plural = "Hráči"

    def save(self, *args, **kwargs):
        if self.user.is_staff == True:
            self.admin = True
        else:
            self.admin = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nickname or self.user.username


class Char_info(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='characters',
        verbose_name="Hráč"
    )

    # Základní identita
    name = models.CharField(max_length=100, verbose_name="Jméno postavy")
    race = models.CharField(max_length=50, blank=True, null=True, verbose_name="Rasa")
    character_class = models.CharField(max_length=50, blank=True, null=True, verbose_name="Povolání")
    level = models.IntegerField(default=1, verbose_name="Úroveň")
    background = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zázemí")
    alignment = models.CharField(max_length=50, blank=True, null=True, verbose_name="Přesvědčení")
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

    # Příběh, poznámky a časová razítka
    backstory = models.TextField(blank=True, null=True, verbose_name="Příběh postavy")
    notes = models.TextField(blank=True, null=True, verbose_name="Poznámky")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Poslední úprava")

    # pracovní
    in_fight = models.BooleanField(default=False, verbose_name="V boji")
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

# DATABÁZE EXISTUJÍCÍCH ACHIVEMENTŮ
class Achivements_database(models.Model):
    img_ozn = models.CharField(max_length=50, verbose_name="Označení ikonky", default = "PRÁZDNO", null = True, blank = True)
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

        d_val = self.Achivement.diamond_value
        e_val = self.Achivement.emerald_value
        p_val = self.Achivement.platinum_value
        g_val = self.Achivement.gold_value
        s_val = self.Achivement.silver_value
        b_val = self.Achivement.bronze_value

        if d_val is not None and d_val > 0 and self.current_value >= d_val:
            if self.current_status != 'diamond':
                self.current_status = 'diamond'
            if not self.diamond_obtained_date:
                self.diamond_obtained_date = timezone.now()
        elif e_val is not None and e_val > 0 and self.current_value >= e_val:
            if self.current_status != 'emerald':
                self.current_status = 'emerald'
            if not self.emerald_obtained_date:
                self.emerald_obtained_date = timezone.now()
        elif p_val is not None and p_val > 0 and self.current_value >= p_val:
            if self.current_status != 'platinum':
                self.current_status = 'platinum'
            if not self.platinum_obtained_date:
                self.platinum_obtained_date = timezone.now()
        elif g_val is not None and g_val > 0 and self.current_value >= g_val:
            if self.current_status != 'gold':
                self.current_status = 'gold'
            if not self.gold_obtained_date:
                self.gold_obtained_date = timezone.now()
        elif s_val is not None and s_val > 0 and self.current_value >= s_val:
            if self.current_status != 'silver':
                self.current_status = 'silver'
            if not self.silver_obtained_date:
                self.silver_obtained_date = timezone.now()
        elif b_val is not None and self.current_value >= b_val and (b_val > 0 or self.current_value > 0):
            if self.current_status != 'bronze':
                self.current_status = 'bronze'
            if not self.bronze_obtained_date:
                self.bronze_obtained_date = timezone.now()
        else:
            self.current_status = None


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