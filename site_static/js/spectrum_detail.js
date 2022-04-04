var header_window = null;

$(document).ready(function () {

    // Initializing all dialog windows
    header_window = $("#headerWindow").dialog({
        autoOpen: false,
        close: function () {
            header_window.dialog("close");
        },
        title: "File Header",
        width: 'auto',
        modal: true
    });

    var update_note_window = $("#noteEdit").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });

    var edit_spectrum_window = $("#spectrumEdit").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });


    //   Add event listeners
    $("#noteEditButton").click(openNoteUpdateBox);
    $("#spectrumEditButton").click(openSpectrumEditBox);
    $("#id_normalize").click(statusNorm);

    //   Set initial status of the spectrum plot form
    statusNorm();

    $(".showheader").click(function (event) {
        event.preventDefault();
        // get the header information
        $.ajax({
            url: $(this).attr('href'),
            type: "GET",
            success: function (json) {
                $('#headerList').empty() //remove all header items
                for (var key in json) {  //add new header items
                    $('#headerList').append("<li> <span class='header-key'>" + key + "</span> : <span class='header-value'>" + json[key] + "</span></li>")
                }
            },

            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });

        header_window = $("#headerWindow").dialog({
            maxHeight: $(window).height() * 0.98,
            title: $(this).attr('name'),
            position: {my: "center top", at: "center top", of: window},
        });

        header_window.dialog("open");

    });

});


// Functionality to open the edit/update windows
function openNoteUpdateBox() {
    update_note_window = $("#noteEdit").dialog({
        buttons: {"Update": updateNote},
        close: function () {
            update_note_window.dialog("close");
        }
    });

    update_note_window.dialog("open");
    $("#edit-message").val($("#noteField").text().trim());
};


function openSpectrumEditBox() {
    edit_spectrum_window = $("#spectrumEdit").dialog({
        buttons: {"Update": editSpectrum},
        close: function () {
            edit_spectrum_window.dialog("close");
        }
    });

    edit_spectrum_window.dialog("open");

    //   Get the flux unit from the database
    var spectrum_id = $('#spectrumEditButton').attr('spectrum_id');
    $.ajax({
        url: "/api/observations/spectra/" + spectrum_id + '/',
        type: "GET",
        success: function (json) {
            $("#spectrum-fluxunits").val(json['flux_units']);
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
};


function statusNorm() {
    //  Check if plot is already normalized (dirty hack)
    let checkNorm = $("script")[7].text.search('normalized');
    //  Set normalization option to True accordingly
    if (checkNorm != -1) {
        $("#id_normalize").attr('checked', true);
    }

    //  Activate/deactivate polynomial order field
    let checked = $("#id_normalize").prop('checked');
    if (!checked) {
        $('#id_order').attr('disabled', true);
        $('#id_order').attr('value', 3);
        $('#div-order').attr('class', 'Wrapper_gray');
    } else {
        $('#id_order').attr('disabled', false);
        $('#div-order').attr('class', 'Wrapper');
    }

    //  Check if spectrum is already normalized -> no normalization necessary
    let normSensible = $("#normalized").attr('normalized');

    //  Get and set binning value
    let binValue = $("#rebin").attr('rebin');
    $('#id_binning').attr('value', binValue);

    //  Disable normalization if true
    if (normSensible == 'true') {
        $('#id_normalize').attr('disabled', true);
        $('#div-norm').attr('class', 'Wrapper_gray');

        $('#id_order').attr('disabled', true);
        $('#div-order').attr('class', 'Wrapper_gray');
    }
};


// Update the note of the spectrum
function updateNote() {
    var spectrum_id = $('#noteEditButton').attr('spectrum_id')
    $.ajax({
        url: "/api/observations/spectra/" + spectrum_id + '/',
        type: "PATCH",
        data: {note: $("#edit-message").val().trim()},

        success: function (json) {
            update_note_window.dialog("close");
            $("#noteField").text(json.note);
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
};


function editSpectrum() {
    var spectrum_id = $('#spectrumEditButton').attr('spectrum_id')

    $.ajax({
        url: "/api/observations/spectra/" + spectrum_id + '/',
        type: "PATCH",
        data: {
            valid: $("#spectrum-valid").is(':checked'),
            fluxcal: $("#spectrum-fluxcal").is(':checked'),
            flux_units: $("#spectrum-fluxunits").val().trim()
        },

        success: function (json) {
            edit_spectrum_window.dialog("close");
            console.log($("#spectrum-valid").is(':checked'));
            console.log($("#spectrum-fluxcal").is(':checked'));

            if (json.valid) {
                $("#spectrum-valid-icon").removeClass("invalid")
                $("#spectrum-valid-icon").addClass("valid")
            } else {
                $("#spectrum-valid-icon").addClass("invalid")
                $("#spectrum-valid-icon").removeClass("valid")
            }
            ;

            if (json.fluxcal) {
                $("#spectrum-fluxcal-icon").removeClass("invalid")
                $("#spectrum-fluxcal-icon").addClass("valid")
            } else {
                $("#spectrum-fluxcal-icon").addClass("invalid")
                $("#spectrum-fluxcal-icon").removeClass("valid")
            }
            ;
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
};
