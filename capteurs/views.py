import csv

from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Avg, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Capteur, Mesure


def _filtrer(request):
    qs = Mesure.objects.select_related("capteur").all()
    q = request.GET.get("q", "").strip()
    debut = request.GET.get("debut", "").strip()
    fin = request.GET.get("fin", "").strip()
    if q:
        qs = qs.filter(Q(capteur__id__icontains=q) | Q(capteur__nom__icontains=q))
    if debut:
        qs = qs.filter(date_heure__date__gte=debut)
    if fin:
        qs = qs.filter(date_heure__date__lte=fin)
    return qs.order_by("-date_heure"), q, debut, fin


def liste_capteurs(request):
    """Page d'accueil : liste des capteurs avec actions Détail / Graphique / Supprimer."""
    capteurs = Capteur.objects.order_by("nom")
    return render(request, "capteurs/liste_capteurs.html", {"capteurs": capteurs})


def liste_mesures(request):
    qs, q, debut, fin = _filtrer(request)
    moyenne = qs.aggregate(m=Avg("temperature"))["m"]
    moyennes_capteur = (
        qs.values("capteur__id", "capteur__nom")
        .annotate(moy=Avg("temperature"))
        .order_by("capteur__nom")
    )
    return render(
        request,
        "capteurs/liste.html",
        {
            "mesures": qs[:200],
            "moyenne": moyenne,
            "moyennes_capteur": moyennes_capteur,
            "total": qs.count(),
            "q": q,
            "debut": debut,
            "fin": fin,
            "refresh": request.GET.get("refresh", "").strip(),
        },
    )


def capteur_detail(request, capteur_id):
    capteur = get_object_or_404(Capteur, pk=capteur_id)

    if request.method == "POST":
        capteur.nom = request.POST.get("nom", capteur.nom).strip()
        capteur.emplacement = request.POST.get("emplacement", capteur.emplacement).strip()
        try:
            capteur.save()
            messages.success(request, "Capteur mis à jour.")
        except IntegrityError:
            messages.error(request, "Ce nom est déjà utilisé (il doit être unique).")
        return redirect("capteur_detail", capteur_id=capteur.id)

    mesures = capteur.mesures.order_by("-date_heure")[:50]
    return render(request, "capteurs/detail.html", {"capteur": capteur, "mesures": mesures})


def capteur_graphique(request, capteur_id):
    """Page d'un capteur affichant uniquement la courbe de ses températures."""
    capteur = get_object_or_404(Capteur, pk=capteur_id)
    points = list(
        capteur.mesures.order_by("-date_heure").values_list("date_heure", "temperature")[:200]
    )
    points.reverse()
    return render(
        request,
        "capteurs/graphique.html",
        {
            "capteur": capteur,
            "labels": [d.strftime("%Y-%m-%d %H:%M:%S") for d, _ in points],
            "valeurs": [float(t) for _, t in points],
        },
    )


@require_POST
def capteur_supprimer(request, capteur_id):
    capteur = get_object_or_404(Capteur, pk=capteur_id)
    nom = capteur.nom
    capteur.delete()
    messages.success(request, f"Capteur « {nom} » supprimé.")
    return redirect("liste")


def export_csv(request):
    qs, *_ = _filtrer(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="mesures.csv"'
    w = csv.writer(response)
    w.writerow(["id_capteur", "nom", "piece", "date_heure", "temperature"])
    for m in qs[:5000]:
        w.writerow([
            m.capteur.id, m.capteur.nom, m.capteur.piece,
            m.date_heure.strftime("%Y-%m-%d %H:%M:%S"), m.temperature,
        ])
    return response