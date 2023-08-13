from django.db.models import F, ExpressionWrapper, DecimalField
from stars.models import Star


def find_or_create_star(metadata, project, modelinstance, modeltype, update_star=True):
    message = "RV Curve successfully created"
    ra = metadata["RA"]
    dec = metadata["DEC"]

    star = Star.objects.filter(project__exact=project) \
        .filter(ra__range=(ra - 0.1, ra + 0.1)) \
        .filter(dec__range=(dec - 0.1, dec + 0.1))

    if len(star) > 0:
        #     If there is one or more stars returned, select the closest star
        star = star.annotate(
            distance=ExpressionWrapper(
                ((F('ra') - ra) ** 2 +
                 (F('dec') - dec) ** 2
                 ) ** (1. / 2.),
                output_field=DecimalField()
            )
        ).order_by('distance')[0]
        if modeltype == "RV":
            star.rvcurve_set.add(modelinstance)
        elif modeltype == "SED":
            star.sed_set.add(modelinstance)
            if update_star:
                # TODO: update star params
                pass
        message += ", and added to existing System {} (_r = {})".format(
            star,
            star.distance
        )
        return True, message, star
    else:
        if 'NAME' in metadata:
            stname = metadata["NAME"]
        elif "SID" in metadata:
            stname = "GAIA DR3 " + metadata["SID"]
        else:
            return False, "Insufficient Metadata!", None
        #     Need to make a new star
        star = Star(
            name=stname,
            ra=ra,
            dec=dec,
            project=project,
        )
        if 'SPCLASS' in metadata:
            star.classification = metadata['SPCLASS']
        star.save()

        if modeltype == "RV":
            star.rvcurve_set.add(modelinstance)
        elif modeltype == "SED":
            star.sed_set.add(modelinstance)
            if update_star:
                # TODO: update star params
                pass

        message += ", and added to new System {}".format(star)
        return True, message, star
