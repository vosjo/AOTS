$(document).ready(function () {

    //Add toolbar to table
    if (user_authenticated) {
        $("div.toolbar").html(
            "<div class='dropdown-container'>" +
            "<button onclick='Toggleeditdropdown()' class='dropbtn' id='editselected'><i class='material-icons button' title='Edit selected'>edit_note</i>Edit selected</button>" +
            "<div id='editdropdown' class='dropdown-content'>" +
            "<a id='tag-button'  class='tb-button disabled' ><i class='material-icons button dropdownbtn'>style</i>Edit Tags</a>" +
            "<a id='status-button' class='tb-button disabled'><i class='material-icons button dropdownbtn'>autorenew</i>Change Status</a>" +
            "<a id='delete-button' class='tb-button disabled'><i class='material-icons button dropdownbtn'>delete</i>Delete System(s)</a>" +
            "</div>" +
            "</div>" +
            "<button id='addsystem-button' class='tb-button'><i class='material-icons button' title='Add System(s)'>add</i>Add System(s)</button>" +
            "<div class='dropdown-container'>" +
            "<button onclick='Togglecarryoverdropdown()' class='dropbtn' id='carryover'><i class='material-icons button' title='Carry over selection'>arrow_forward</i>Carry over selection   </button>" +
            "<div id='carryoverdropdown' class='dropdown-content'>" +
            "<a id='tospectra-button'  class='tb-button disabled' ><i class='material-icons button dropdownbtn'>star</i>To Spectra</a>" +
            "<a id='tolightcurve-button' class='tb-button disabled'><i class='material-icons button dropdownbtn'>flare</i>To Lightcurves</a>" +
            "</div>" +
            "</div>"
        )
    }

});