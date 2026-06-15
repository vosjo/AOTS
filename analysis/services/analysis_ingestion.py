from dataclasses import dataclass

from django.db.models import F, ExpressionWrapper, FloatField

from analysis.auxil import process_analyses, read_analyses
from analysis.categories import CategorySource, category_derived_parameters, resolve_category, valid_category_codes
from analysis.models import Analysis
from stars.models import Star
from stars.services import star_io


@dataclass
class IngestResult:
    success: bool
    message: str


def ingest_analysis_file(analysis_id, category_override=None) -> IngestResult:
    """Validate HDF5, match star, create parameters and category-derived parameters."""
    try:
        analfile = Analysis.objects.get(pk=analysis_id)
    except Analysis.DoesNotExist:
        return IngestResult(False, 'Analysis not found')

    try:
        data = analfile.get_data()
    except Exception:
        return IngestResult(False, 'Not added, file has wrong format / file is unreadable')

    try:
        systemname, ra, dec, name, note, reference, atype = read_analyses.get_basic_info(data)
    except Exception as e:
        print(e)
        return IngestResult(False, 'Not added, basic info unreadable')

    category_override = (category_override or '').strip() or None
    if category_override:
        if category_override not in valid_category_codes():
            return IngestResult(False, f'Unknown category: {category_override}')
        category = category_override
        category_source = CategorySource.USER
    else:
        category, category_source = resolve_category(atype)
    analfile.category = category
    analfile.category_source = category_source
    analfile.file_type = atype or ''
    analfile.name = name
    analfile.note = note
    analfile.reference = reference
    analfile.save()

    message = 'Validated the analysis file'

    if ra != 0.0 and dec != 0.0:
        star = Star.objects.filter(
            ra__range=(ra - 0.01, ra + 0.01),
            dec__range=(dec - 0.01, dec + 0.01),
            project__exact=analfile.project.pk,
        )
    else:
        star = Star.objects.filter(
            name__iexact=systemname,
            project__exact=analfile.project.pk,
        )
        if not star:
            return IngestResult(False, 'Not added, no system information present')

    if star:
        star = star.annotate(
            distance=ExpressionWrapper(
                ((F('ra') - ra) ** 2 + (F('dec') - dec) ** 2) ** (1. / 2.),
                output_field=FloatField(),
            )
        ).order_by('distance')[0]
        analfile.star = star
        analfile.save()
        message += f", added to existing System {star} (_r = {star.distance})"
    else:
        star = star_io.create_star(
            name=systemname,
            project=analfile.project,
            ra=ra,
            dec=dec,
            classification='',
        )
        analfile.star = star
        analfile.save()
        message += f", created new System {star}"

    try:
        npars = process_analyses.create_parameters(analfile, data)
        if npars == 0:
            analfile.fit = False
            analfile.save()
            message += ', (No parameters included, no fit)'
        else:
            message += f', ({npars} parameters)'
            if category_derived_parameters(analfile.category).strip():
                nderived = process_analyses.create_derived_parameters(analfile)
                if nderived:
                    message += f', ({nderived} derived parameters)'
    except Exception:
        raise

    return IngestResult(True, message)


def process_analysis_file(file_id):
    """Backward-compatible wrapper returning (success, message) tuple."""
    result = ingest_analysis_file(file_id)
    return result.success, result.message
