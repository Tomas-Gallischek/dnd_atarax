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