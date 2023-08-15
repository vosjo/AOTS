$(document).ready(function () {
    $('#switchToggle').change(function () {
        if ($(this).is(":checked")) {
            $('#fluxBlock').hide();
            $('#fluxOcBlock').hide();
            $('#magBlock').show();
            $('#magOcBlock').show();
        } else {
            $('#fluxBlock').show();
            $('#fluxOcBlock').show();
            $('#magBlock').hide();
            $('#magOcBlock').hide();
        }
    });
});

