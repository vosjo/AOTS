$(document).ready(function () {

    var detailed_starmap_window = $("#detailedStarmap").dialog({
        autoOpen: false,
        title: 'Full Overview of Sky Positions',
        width: 'auto',
        height: 'auto',
        modal: true
    });

});


function openDetailedStarmap() {
    detailed_starmap_window = $("#detailedStarmap").dialog({
        close: function () {
            detailed_starmap_window.dialog("close");
        }
    });

    detailed_starmap_window.dialog("open");
}