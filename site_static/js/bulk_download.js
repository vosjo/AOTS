/**
 * Celery bulk ZIP download (spectra, raw files, light curves, datasets).
 */
function aotsStartBulkDownload(options) {
    const projectId = options.projectId;
    const idList = options.idList;
    const kind = options.kind || 'processed';
    const onProgress = options.onProgress || function () {};
    const onError = options.onError || function () {};
    const onComplete = options.onComplete || function () {};

    if (!projectId) {
        onError('Missing project context.');
        return;
    }
    if (!idList || idList.length === 0) {
        onError('No items selected.');
        return;
    }

    onProgress('Preparing download…');

    $.ajax({
        url: '/api/observations/bulk-download/start/?kind=' + encodeURIComponent(kind),
        method: 'POST',
        headers: {
            'Projectid': projectId,
            'Staridlist': idList.join(';'),
        },
    }).done(function (data) {
        aotsPollBulkDownloadTask(data.task_id, onProgress, onError, onComplete);
    }).fail(function (xhr) {
        const detail = xhr.responseJSON && xhr.responseJSON.detail;
        onError(detail || 'Bulk download failed');
    });
}

function aotsPollBulkDownloadTask(taskId, onProgress, onError, onComplete) {
    $.ajax({
        url: '/api/observations/tasks/' + taskId + '/',
        dataType: 'json',
        xhrFields: {withCredentials: true},
    }).done(function (status) {
        if (!status.ready) {
            onProgress('Building ZIP… ' + status.status);
            setTimeout(function () {
                aotsPollBulkDownloadTask(taskId, onProgress, onError, onComplete);
            }, 2000);
            return;
        }
        if (status.status === 'SUCCESS') {
            if (status.result && status.result.error) {
                onError(status.result.error);
                return;
            }
            window.location = '/api/observations/bulk-download/' + taskId + '/file/';
            onComplete();
            return;
        }
        onError(status.error || 'Bulk download failed');
    }).fail(function (xhr) {
        const detail = xhr.responseJSON && xhr.responseJSON.detail;
        onError(detail || 'Bulk download status failed');
    });
}
