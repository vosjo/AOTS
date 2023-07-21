$(document).ready(function () {
    $("#detailedStarmap").dialog({
        autoOpen: false,
        title: 'Change Profile Picture',
        width: 'auto',
        height: 'auto',
        modal: true
    });

    // Adjust nav bar highlight
    adjust_nav_bar_active("#user_dropdown")
});


function openChangeProfilePicWindow() {
    let change_propic_window = $("#changepropic").dialog({
        close: function () {
            change_propic_window.dialog("close");
        }
    });

    change_propic_window.dialog("open");
}