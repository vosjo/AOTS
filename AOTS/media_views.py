"""Serve private media via signed tokens (capability URLs)."""

from __future__ import annotations

import mimetypes
import os

from django.conf import settings
from django.core import signing
from django.http import FileResponse, Http404, HttpResponse
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET

from AOTS.media_signing import safe_download_basename, unsign_media_token


@require_GET
def media_download(request, token: str):
    try:
        data = unsign_media_token(token)
    except signing.SignatureExpired:
        return HttpResponse('Signed URL expired.', status=410)
    except signing.BadSignature:
        return HttpResponse('Invalid signed URL.', status=403)

    relative = data['p']
    absolute = os.path.normpath(os.path.join(settings.MEDIA_ROOT, relative))
    media_root = os.path.normpath(str(settings.MEDIA_ROOT))
    if not absolute.startswith(media_root + os.sep) and absolute != media_root:
        raise Http404()
    if not os.path.isfile(absolute):
        raise Http404()

    download_name = safe_download_basename(data.get('n') or '', fallback=os.path.basename(relative))
    content_type = 'application/octet-stream'
    disposition = content_disposition_header(as_attachment=True, filename=download_name)

    use_x_accel = getattr(settings, 'MEDIA_USE_X_ACCEL', False)
    if use_x_accel:
        response = HttpResponse(content_type=content_type)
        response['X-Accel-Redirect'] = f'/protected-media/{relative}'
        response['Content-Disposition'] = disposition
        response['X-Content-Type-Options'] = 'nosniff'
        return response

    guessed, _ = mimetypes.guess_type(download_name)
    response = FileResponse(
        open(absolute, 'rb'),
        as_attachment=True,
        filename=download_name,
        content_type=guessed or content_type,
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response
