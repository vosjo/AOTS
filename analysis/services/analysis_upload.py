from analysis.auxil import process_analyses
from analysis.models import Analysis


def upload_analysis_files(project, files):
    """Upload HDF5 analysis files and run processing. Returns [[success, message], ...]."""
    message_list = []
    for f in files:
        new_analysis = Analysis(
            datafile=f,
            project=project,
        )
        new_analysis.save()

        success, message = process_analyses.process_analysis_file(new_analysis.id)
        message = str(f) + ': ' + message

        if not success:
            new_analysis.delete()

        message_list.append([success, message])
    return message_list
