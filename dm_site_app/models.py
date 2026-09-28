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


class CompendiumItem(models.Model):
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