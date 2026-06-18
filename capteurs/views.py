import csv

from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Avg, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Capteur, Mesure


def _filtrer(request):
    """Applique les filtres GET communs (q, debut, fin) et renvoie le queryset."""
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
        action = request.POST.get("action")
        if action == "supprimer":
            capteur.delete()
            messages.success(request, "Capteur et mesures supprimés.")
            return redirect("liste")
        if action == "modifier":
            capteur.nom = request.POST.get("nom", capteur.nom).strip()
            capteur.emplacement = request.POST.get(
                "emplacement", capteur.emplacement
            ).strip()
            try:
                capteur.save()
                messages.success(request, "Capteur mis à jour.")
            except IntegrityError:
                messages.error(
                    request, "Ce nom est déjà utilisé (il doit être unique)."
                )
            return redirect("capteur_detail", capteur_id=capteur.id)

    mesures = capteur.mesures.order_by("-date_heure")[:200]
    moyenne = capteur.mesures.aggregate(m=Avg("temperature"))["m"]
    points = list(
        capteur.mesures.order_by("date_heure").values_list("date_heure", "temperature")[
            :200
        ]
    )
    return render(
        request,
        "capteurs/detail.html",
        {
            "capteur": capteur,
            "mesures": mesures,
            "moyenne": moyenne,
            "labels": [d.strftime("%d/%m %H:%M") for d, _ in points],
            "valeurs": [float(t) for _, t in points],
        },
    )


def export_csv(request):
    qs, *_ = _filtrer(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="mesures.csv"'
    w = csv.writer(response)
    w.writerow(["id_capteur", "nom", "piece", "date_heure", "temperature"])
    for m in qs[:5000]:
        w.writerow(
            [
                m.capteur.id,
                m.capteur.nom,
                m.capteur.piece,
                m.date_heure.strftime("%Y-%m-%d %H:%M:%S"),
                m.temperature,
            ]
        )
    return response
