
from django.contrib import admin
from django.db import models
from django.forms.models import ModelForm


class Periodico(models.Model):
    TIPOS = (
                  ('PAIS','PAIS'),
                  ('HOY','HOY'),
                  ('MUNDO','MUNDO'),
                  ('ABC','ABC'),
                  )
    periodico = models.CharField(default= 0 , choices = TIPOS, max_length = 30)
    def __str__(self):
        return unicode(self.periodico)
 
class Usuario(models.Model):
    nombre = models.CharField(max_length = 30)
    email = models.EmailField()
    contrasena = models.CharField(max_length = 30)
    periodico =  models.ManyToManyField(Periodico)
    def __str__(self):
        return self.nombre
    

class IngresoForm(ModelForm):
    class Meta:
        model = Usuario      
    
    

admin.site.register(Usuario)
    
admin.site.register(Periodico)
    
    
