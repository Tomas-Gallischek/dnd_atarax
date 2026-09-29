from datetime import timezone
from django.db import models
from django.contrib.auth.models import User


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

    class Meta:
        verbose_name = "Hráč"
        verbose_name_plural = "Hráči"

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
    name = models.CharField(max_length=50, verbose_name="Jméno úspěchu")
    description = models.CharField(max_length=200, verbose_name="Popis úspěchu")

    bronze_value = models.FloatField(default=0, verbose_name="hodnota pro bronze", null=True, blank=True)
    silver_value = models.FloatField(default=0, verbose_name="hodnota pro silver", null=True, blank=True)
    gold_value = models.FloatField(default=0, verbose_name="hodnota pro gold", null=True, blank=True)
    platinum_value = models.FloatField(default=0, verbose_name="hodnota pro platinum", null=True, blank=True)
    emerald_value = models.FloatField(default=0, verbose_name="hodnota pro emerald", null=True, blank=True)
    diamond_value = models.FloatField(default=0, verbose_name="hodnota pro diamond", null=True, blank=True)


# Databáze existujících achivementů
class Achivements_players(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='achivements',
        verbose_name="Hráč"
    )
    Achivement = models.ForeignKey(
        Achivements_database,
        on_delete=models.CASCADE,
        related_name='achivements',
        verbose_name="Achivement"
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
    
    def update_achivement_status(self):
        if self.current_value >= self.Achivement.diamond_value and self.current_status != 'diamond':
            self.current_status = 'diamond'
            self.diamond_obtained_date = timezone.now()
        elif self.current_value >= self.Achivement.emerald_value and self.current_status != 'emerald':
            self.current_status = 'emerald'
            self.emerald_obtained_date = timezone.now()
        elif self.current_value >= self.Achivement.platinum_value and self.current_status != 'platinum':
            self.current_status = 'platinum'
            self.platinum_obtained_date = timezone.now()
        elif self.current_value >= self.Achivement.gold_value and self.current_status != 'gold':
            self.current_status = 'gold'
            self.gold_obtained_date = timezone.now()
        elif self.current_value >= self.Achivement.silver_value and self.current_status != 'silver':
            self.current_status = 'silver'
            self.silver_obtained_date = timezone.now()
        elif self.current_value >= self.Achivement.bronze_value and self.current_status != 'bronze':
            self.current_status = 'bronze'
            self.bronze_obtained_date = timezone.now()
        else:
            self.current_status = None
            self.bronze_obtained_date = None
            self.silver_obtained_date = None
            self.gold_obtained_date = None
            self.platinum_obtained_date = None
            self.emerald_obtained_date = None
            self.diamond_obtained_date = None


        self.save()