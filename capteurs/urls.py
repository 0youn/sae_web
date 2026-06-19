from django.urls import path

from . import views

urlpatterns = [
    path("", views.liste_capteurs, name="liste"),
    path("donnees/", views.liste_mesures, name="donnees"),
    path("export.csv", views.export_csv, name="export_csv"),
    path("capteur/<str:capteur_id>/", views.capteur_detail, name="capteur_detail"),
    path("capteur/<str:capteur_id>/graphique/", views.capteur_graphique, name="capteur_graphique"),
    path("capteur/<str:capteur_id>/supprimer/", views.capteur_supprimer, name="capteur_supprimer"),
]