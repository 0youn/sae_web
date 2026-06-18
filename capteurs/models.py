from django.db import models


class Capteur(models.Model):
    id = models.CharField(max_length=32, primary_key=True, db_column="id")
    nom = models.CharField(max_length=64, unique=True)
    piece = models.CharField(max_length=64)
    emplacement = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = "capteur"

    def __str__(self):
        return self.nom


class Mesure(models.Model):
    id_mesure = models.AutoField(primary_key=True, db_column="id_mesure")
    capteur = models.ForeignKey(
        Capteur,
        on_delete=models.CASCADE,
        db_column="id_capteur",
        related_name="mesures",
    )
    date_heure = models.DateTimeField(db_column="date_heure")
    temperature = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = "mesure"
