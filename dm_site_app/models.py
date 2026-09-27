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