$(document).ready(function () {

    star_table = $('#datatable').DataTable({
        dom: 'l<"toolbar">frtip',
        serverSide: true,
        ajax: {
            url: '/api/systems/stars/?format=datatables&keep=nphot,nspec,nlc,ra_hms,dec_dms,observing_status_display',  //adding "&keep=id,rank" will force return of id and rank fields
            data: get_filter_keywords,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
        },
        searching: false,
        orderMulti: false, //Can only order on one column at a time
        order: [2],
        columns: [
            {
                orderable: false,
                className: 'select-control',
                data: null,
                render: selection_render,
                width: '10',
                searchable: false,
            },
            {data: 'name', render: name_render},
            {data: 'ra', searchable: false, render: ra_render},
            {data: 'dec', searchable: false, render: dec_render},
            {data: 'classification', render: classification_render, searchable: false},
            {data: 'vmag', searchable: false, orderable: false},
            {data: 'nphot', render: nobs_render, searchable: false, orderable: false},
            {data: 'datasets', render: dataset_render, searchable: false, orderable: false},
            {data: 'tags', render: tag_render, searchable: false, orderable: false},
            {
                data: 'observing_status', render: status_render,
                width: '70',
                className: "dt-center",
                searchable: false
            },
        ],
        paging: true,
        pageLength: 50,
        lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
        scrollY: $(window).height() - $('header').outerHeight(true) - 196,
        scrollCollapse: true,
        autoWidth: true,
    });

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

    // Event listener to the two range filtering inputs to redraw on input
    $('#filter-form').submit(function (event) {
        event.preventDefault();
        star_table.draw();
    });

    // Hide all photometry not belonging to the selected Instrument
    let initialselected = $('#system-form-instrument-select:first-child').find(":selected").val();

    $('#form-photometry tr').each(function () {
        if ($(this).attr('id') === initialselected) {
            $(this).show()
        } else {
            $(this).hide()
        }
    });

    // Event listener to only show photometry Fields for the selected Instrument
    $('#system-form-instrument-select:first-child').change(function () {
        let selected = $(this).find(":selected").val();
        $('#form-photometry tr').each(function () {
            if ($(this).attr('id') === selected) {
                $(this).show()
            } else {
                $(this).hide()
            }
        })
    })


    // event listeners for edit buttons
    $("#status-button").click(openStatusEditWindow);

});