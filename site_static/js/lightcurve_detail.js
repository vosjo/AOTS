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

    var edit_lightcurve_window = $("#lightcurveEdit").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });


    // add event listeners
    $("#noteEditButton").click(openNoteUpdateBox);
    $("#lightcurveEditButton").click(openLichtCurveEditBox);

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
                console.log(json);
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

    // Adjust nav bar highlight
    adjust_nav_bar_active("#observation_dropdown")
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


function openLichtCurveEditBox() {
    edit_lightcurve_window = $("#lightcurveEdit").dialog({
        buttons: {"Update": editLichtCurve},
        close: function () {
            edit_lightcurve_window.dialog("close");
        }
    });

    edit_lightcurve_window.dialog("open");
    $("#lightcurve-valid").val(true);
    $("#lightcurve-fluxcal").val(false);
    $("#lightcurve-fluxunits").val('test');
};


// Update the note of the lightcurve
function updateNote() {
    var lightcurve_id = $('#noteEditButton').attr('lightcurve_id')
    $.ajax({
        url: "/api/observations/lightcurves/" + lightcurve_id + '/',
        type: "PATCH",
        data: {note: $("#edit-message").val().trim()},

        success: function (json) {
            update_note_window.dialog("close");
            $("#noteField").text(json.note);
//             star.note = json.note;
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
};


function editLichtCurve() {
    var lightcurve_id = $('#lightcurveEditButton').attr('lightcurve_id')

    $.ajax({
        url: "/api/observations/lightcurves/" + lightcurve_id + '/',
        type: "PATCH",
        data: {
            valid: $("#lightcurve-valid").is(':checked'),
            fluxcal: $("#lightcurve-fluxcal").is(':checked'),
            flux_units: $("#lightcurve-fluxunits").val().trim()
        },

        success: function (json) {
            edit_lightcurve_window.dialog("close");

            if (json.valid) {
                $("#lightcurve-valid-icon").removeClass("invalid")
                $("#lightcurve-valid-icon").addClass("valid")
            } else {
                $("#lightcurve-valid-icon").addClass("invalid")
                $("#lightcurve-valid-icon").removeClass("valid")
            }
            ;

            if (json.fluxcal) {
                $("#lightcurve-fluxcal-icon").removeClass("invalid")
                $("#lightcurve-fluxcal-icon").addClass("valid")
            } else {
                $("#lightcurve-fluxcal-icon").addClass("invalid")
                $("#lightcurve-fluxcal-icon").removeClass("valid")
            }
            ;
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
};
