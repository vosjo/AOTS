$(document).ready(function () {
    $("#detailedStarmap").dialog({
        autoOpen: false,
        title: 'Change Profile Picture',
        width: 'auto',
        height: 'auto',
        modal: true
    });
});


function openChangeProfilePicWindow() {
    let change_propic_window = $("#changepropic").dialog({
        close: function () {
            change_propic_window.dialog("close");
        }
    });

    change_propic_window.dialog("open");
}