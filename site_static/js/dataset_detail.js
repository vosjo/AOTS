var fullscreen_figure_window = null;

$(document).ready(function () {

    // Initialize dialog windows
    var edit_note_window = $("#noteEdit").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });

    var edit_name_window = $("#nameEdit").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });

    // Add event listeners
    $("#noteEditButton").click(openNoteEditBox);
    $("#nameEditButton").click(openNameEditBox);
});

function openNoteEditBox() {
    edit_note_window = $("#noteEdit").dialog({
        title: "Edit Notes",
        buttons: {"Update": updateNote},
        close: function () {
            edit_note_window.dialog("close");
        }
    });

    edit_note_window.dialog("open");
    $("#edit-note").val($("#noteField").text().trim());
};

function updateNote() {
    var dataset_id = $('#noteEditButton').attr('dataset_id');
    $.ajax({
        url: "/api/analysis/datasets/" + dataset_id + '/',
        type: "PATCH",
        data: {note: $("#edit-note").val().trim()},

        success: function (json) {
            edit_note_window.dialog("close");
            $("#noteField").text(json.note);
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
};

function openNameEditBox() {
    edit_name_window = $("#nameEdit").dialog({
        title: "Edit Dataset Name",
        buttons: {"Update": updateName},
        close: function () {
            edit_name_window.dialog("close");
        }
    });

    edit_name_window.dialog("open");
    $("#edit-name").val($("#nameField").text().trim());
};

function updateName() {
    var dataset_id = $('#nameEditButton').attr('dataset_id');
    $.ajax({
        url: "/api/analysis/datasets/" + dataset_id + '/',
        type: "PATCH",
        data: {name: $("#edit-name").val().trim()},

        success: function (json) {
            edit_name_window.dialog("close");
            $("#nameField").text(json.name);
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
};

function toggleParameterValid(cb) {
    var parameter_id = cb.getAttribute('parameter_id');
    var valid = cb.checked

    updateParameterValid(parameter_id, valid)
};

function updateParameterValid(parameter_id, valid) {
    $.ajax({
        url: "/api/analysis/parameters/" + parameter_id + '/',
        type: "PATCH",
        data: {valid: valid},

        success: function (json) {
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
            $('#cb-parameter-valid-' + parameter_id).checked = !valid
        }
    });
}

function toggleDatasetValid(cb) {
    var dataset_id = cb.getAttribute('dataset_id');
    var valid = cb.checked

    updateDatasetValid(dataset_id, valid)
};

function updateDatasetValid(dataset_id, valid) {
    $.ajax({
        url: "/api/analysis/datasets/" + dataset_id + '/',
        type: "PATCH",
        data: {valid: valid},

        success: function (json) {
            console.log(json);
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
            $('#dataset-valid-' + dataset_id).checked = !valid
        }
    });
};