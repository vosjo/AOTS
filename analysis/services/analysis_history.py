from astropy.time import Time


def history_record(analysis, which):
    try:
        return getattr(analysis.history, which)()
    except analysis.history.model.DoesNotExist:
        return None


def earliest_iso(analysis):
    record = history_record(analysis, 'earliest')
    if record is None:
        return None
    return Time(record.history_date, precision=0).iso


def latest_iso(analysis):
    record = history_record(analysis, 'latest')
    if record is None:
        return None
    return Time(record.history_date, precision=0).iso


def added_by_display(analysis):
    record = history_record(analysis, 'earliest')
    if record is None or record.history_user is None:
        return '—'
    user = record.history_user
    full_name = f'{user.first_name} {user.last_name}'.strip()
    return full_name or user.username


def modified_by_username(analysis):
    record = history_record(analysis, 'latest')
    if record is None or record.history_user is None:
        return '—'
    return record.history_user.username
