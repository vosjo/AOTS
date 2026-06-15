from analysis.services.analysis_ingestion import ingest_analysis_file
from analysis.models import Analysis


def upload_analysis_files(project, files, category=None):
    """Upload HDF5 analysis files and run processing. Returns [[success, message], ...]."""
    category_override = (category or '').strip() or None
    message_list = []
    for f in files:
        new_analysis = Analysis(
            datafile=f,
            project=project,
        )
        new_analysis.save()

        result = ingest_analysis_file(new_analysis.id, category_override=category_override)
        success = result.success
        message = str(f) + ': ' + result.message

        if not success:
            new_analysis.delete()

        message_list.append([success, message])
    return message_list
