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
