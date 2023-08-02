var RVcurves_table = null;

$(document).ready(function () {
    let columns;
    if (user_authenticated) {
        columns = [
            {
                orderable: false,
                className: 'select-control',
                data: null,
                render: selection_render,
                width: '10',
            },
            {data: 'star', render: star_render},
            {data: 'time_spanned', render: timespan_render},
            {data: 'N_samples', render: nsamples_render},
            {data: 'average_rv', render: averagerv_render},
            {data: 'half_amplitude', render: halfamplitude_render},
            {data: 'solved', render: solved_render},
        ];
    } else {
        columns = [
            {data: 'star', render: star_render},
            {data: 'time_spanned', render: timespan_render},
            {data: 'N_samples', render: nsamples_render},
            {data: 'average_rv', render: averagerv_render},
            {data: 'half_amplitude', render: halfamplitude_render},
            {data: 'solved', render: solved_render},
        ];
    }

    let ajax_kw;
    if (sessionStorage.getItem("selectedpks") === null) {
        ajax_kw = {
            url: '/api/analysis/rvcurves/?format=datatables&keep=href',
            data: get_filter_keywords
        }
    } else {
        ajax_kw = {
            url: '/api/analysis/rvcurves/?format=datatables&keep=href',
            data: carryover
        }
    }

    // Table functionality
    RVcurves_table = $('#RVcurvestable').DataTable({
        dom: 'l<"toolbar">frtip',
        autoWidth: false,
        serverSide: true,
        ajax: ajax_kw,
        searching: false,
        orderMulti: false, //Can only order on one column at a time
        order: [1],
        columns: columns,
        paging: true,
        pageLength: 20,
        lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
        scrollY: $(window).height() - $('.nav_bar').outerHeight(true) - $('footer').outerHeight(true) - 196,
        scrollCollapse: true,
    });

    // Event listener to the two range filtering inputs to redraw on input
    $('#filter-form').submit(function (event) {
        event.preventDefault();
        RVcurves_table.draw();
    });

    // check and uncheck tables rows
    $('#RVcurvestable tbody').on('click', 'td.select-control', function () {
        var tr = $(this).closest('tr');
        var row = RVcurves_table.row(tr);
        if ($(row.node()).hasClass('selected')) {
            deselect_row(row);
        } else {
            select_row(row);
        }
    });

    $('#select-all').on('click', function () {
        if ($(this).text() === 'check_box' || $(this).text() === 'indeterminate_check_box') {
            // deselect all
            $(this).text('check_box_outline_blank');

            RVcurves_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                deselect_row(this); // Open this row
            });
        } else {
            // close all rows
            $(this).text('check_box');

            RVcurves_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                select_row(this); // close the row
            });
        }
    });

    // Make the filter button open the filter menu
    $('#filter-dashboard-button').on('click', openNav);

    function openNav() {
        $("#filter-dashboard").toggleClass('visible');
        $("#filter-dashboard-button").toggleClass('open');

        var text = $('#filter-dashboard-button').text();
        if (text === "filter_list") {
            $('#filter-dashboard-button').text("close");
        } else {
            $('#filter-dashboard-button').text("filter_list");
        }
    }

    //Add toolbar to table
    if (user_authenticated) {
        $("div.toolbar").html(
            "<div class='dropdown-container'>" +
            "<button onclick='Toggleeditdropdown()' class='dropbtn' id='editselected'><i class='material-icons button' title='Edit selected'>edit_note</i>Edit selected</button>" +
            "<div id='editdropdown' class='dropdown-content'>" +
            "<a id='delete-button' class='tb-button disabled'><i class='material-icons button dropdownbtn'>delete</i>Delete RV curves</a>" +
            "</div>" +
            "</div>" +
            "<div class='dropdown-container'>" +
            "<button onclick='Toggledownloaddropdown()' class='dropbtn' id='download'><i class='material-icons button' title='Carry over selection'>download</i>Download Files</button>" +
            "<div id='downloaddropdown' class='dropdown-content'>" +
            "<a id='dl-button'  class='tb-button disabled' ><i class='material-icons button dropdownbtn'>download_for_offline</i>Download RV curves</a>" +
            "</div>" +
            "</div>" +
            '<progress hidden id="progress-bar" value="0" max="100" class="progress-bar"></progress>'
      );
    }

    //   Reset check boxes when changing number of displayed objects in table
    $('#RVcurvestable_length').change(function () {
        RVcurves_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    //   Reset check boxes when switching to the next table page
    $('#RVcurvestable_paginate').click(function () {
        RVcurves_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    // Adjust nav bar highlight
    adjust_nav_bar_active("#analysis_dropdown")
});


// Table filter functionality

function get_filter_keywords(d) {

    d = $.extend({}, d, {
        "project": $('#project-pk').attr('project'),
        "target": $('#filter_target').val(),
    });

    return d
}

// Table renderers
function selection_render(data, type, full, meta) {
    if ($(RVcurves_table.row(meta['row']).node()).hasClass('selected')) {
        return '<i class="material-icons button select" title="Select">check_box</i>';
    } else {
        return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
    }
}

function star_render(data, type, full, meta) {
    try {
        return "<a href='" + data['href'] + "' >" + data['name'] + "</a>" + " (" + data['ra'].toFixed(5) + " " + data['dec'].toFixed(5) + ")"
    } catch (err) {
        return ''
    }
}

function nsamples_render(data, type, full, meta) {
    if (data === 0) {
        return "-"
    } else {
        return data
    }
}

function timespan_render(data, type, full, meta) {
    if (data === 0) {
        return "-"
    } else {
        return data
    }
}

function averagerv_render(data, type, full, meta) {
    if (data === 0) {
        return "-"
    } else {
        return data
    }
}

function halfamplitude_render(data, type, full, meta) {
    if (data === 0) {
        return "-"
    } else {
        return data
    }
}

function solved_render(data, type, full, meta) {
    if (data) {
        return "yes"
    } else {
        return "no"
    }
}


// Selection and Deselection of rows

function select_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box');
    $(row.node()).addClass('selected');
    if (RVcurves_table.rows('.selected').data().length < RVcurves_table.rows().data().length) {
        $('#select-all').text('indeterminate_check_box');
    } else {
        $('#select-all').text('check_box');
    }
    $('#dl-button').removeClass("disabled");
    $('#dl-raw-button').removeClass("disabled");
    $('#rm-button').removeClass("disabled");
    $('#delete-button').removeClass("disabled");
}

function deselect_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box_outline_blank');
    $(row.node()).removeClass('selected');
    if (RVcurveRVcurves_table.rows('.selected').data().length === 0) {
        $('#select-all').text('check_box_outline_blank');
        $('#dl-button').addClass("disabled");
        $('#dl-raw-button').addClass("disabled");
        $('#rm-button').addClass("disabled");
        $('#delete-button').addClass("disabled");
    } else {
        $('#select-all').text('indeterminate_check_box');
    }
}



//  Download options:

//  Update progress bar
function updatePercent(percent) {
    $("#progress-bar")
        .val(percent);
}

//  Change download button text
function showProgress(text) {
    $("#progress-bar").show()
    $("#dl-button")
        .val(text);
}

//  Show Error message
function showError(text) {
    $("#dl-button")
        .removeClass()
        .addClass("alert")
        .val(text);
}

function carryover(d) {
    if (sessionStorage.getItem("selectedpks") === null) {
        return get_filter_keywords(d)
    }
    let pks = sessionStorage.getItem('selectedpks');
    sessionStorage.removeItem("selectedpks");

    d = $.extend({}, d, {
        "project": $('#project-pk').attr('project'),
        "pk": pks
    });

    return d;
}


// Close the dropdown menu if the user clicks outside of it
$(window).click(function (e) {
    if (!e.target.matches('.dropbtn')) {
        $(".dropdown-content").each(function (i) {
            if ($(this).hasClass('show')) {
                $(this).removeClass('show');
            }
        })
    }
})


function Toggleeditdropdown() {
    $("#editdropdown").toggle();
    let otherdd = $("#downloaddropdown");
    if (otherdd.is(":visible")) {
        otherdd.toggle();
    }
}


function Toggledownloaddropdown() {
    $("#downloaddropdown").toggle("show");
    let otherdd = $("#editdropdown")
    if (otherdd.is(":visible")) {
        otherdd.toggle("show");
    }
}
