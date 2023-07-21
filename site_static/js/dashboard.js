$(document).ready(function () {
    const detailed_starmap_window = $("#detailedStarmap").dialog({
        autoOpen: false,
        title: 'Full Overview of Sky Positions',
        width: 'auto',
        height: 'auto',
        modal: true
    });

    const tr1 = document.getElementById('tr_1');
    const tr2 = document.getElementById('tr_2');
    const tr3 = document.getElementById('tr_3');
    const tr4 = document.getElementById('tr_4');

    tr1.innerHTML += tr3.innerHTML;
    tr2.innerHTML += tr4.innerHTML;

    tr3.parentNode.removeChild(tr3);
    tr4.parentNode.removeChild(tr4);

    // Adjust nav bar highlight
    adjust_nav_bar_active("#dashboard_a", drop_down=false)
});


function openDetailedStarmap() {
    let detailed_starmap_window = $("#detailedStarmap").dialog({
        close: function () {
            detailed_starmap_window.dialog("close");
        }
    });

    detailed_starmap_window.dialog("open");
}