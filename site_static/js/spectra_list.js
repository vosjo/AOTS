var spectra_table = null;

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
            {data: 'hjd', render: hjd_render},
            {data: 'star', render: star_render},
            {data: 'instrument', render: instrument_render},
            {data: 'resolution', render: resolution_render},
            {data: 'airmass', render: airmass_render},
            {data: 'exptime'},
        ];
    } else {
        columns = [
            {data: 'hjd', render: hjd_render},
            {data: 'star', render: star_render},
            {data: 'instrument', render: instrument_render},
            {data: 'resolution', render: resolution_render},
            {data: 'airmass', render: airmass_render},
            {data: 'exptime'},
        ];
    }

    let ajax_kw;
    if (sessionStorage.getItem("selectedpks") === null) {
        ajax_kw = {
            url: '/api/observations/spectra/?format=datatables&keep=pk,specfiles,telescope,href',
            data: get_filter_keywords
        }
    } else {
        ajax_kw = {
            url: '/api/observations/spectra/?format=datatables&keep=pk,specfiles,telescope,href',
            data: carryover
        }
    }

    // Table functionality
    spectra_table = $('#spectratable').DataTable({
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
        spectra_table.draw();
    });

    // check and uncheck tables rows
    $('#spectratable tbody').on('click', 'td.select-control', function () {
        var tr = $(this).closest('tr');
        var row = spectra_table.row(tr);
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

            spectra_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                deselect_row(this); // Open this row
            });
        } else {
            // close all rows
            $(this).text('check_box');

            spectra_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
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
            "<a id='delete-button' class='tb-button disabled'><i class='material-icons button dropdownbtn'>delete</i>Delete Spectra</a>" +
            "</div>" +
            "</div>" +
            "<div class='dropdown-container'>" +
            "<button onclick='Toggledownloaddropdown()' class='dropbtn' id='download'><i class='material-icons button' title='Download Files'>download</i>Download Files</button>" +
            "<div id='downloaddropdown' class='dropdown-content'>" +
            "<a id='dl-button'  class='tb-button disabled' ><i class='material-icons button dropdownbtn'>download_for_offline</i><span class='dl-btn-text'>Download Spectra</span></a>" +
            "<a id='dl-button-raw' class='tb-button disabled'><i class='material-icons button dropdownbtn'>raw_on</i><span class='dl-btn-text'>Download Raw Data</span></a>" +
            "</div>" +
            "</div>" +
            '<progress hidden id="progress-bar" value="0" max="100" class="progress-bar"></progress>' +
            '<progress hidden id="progress-bar-raw" value="0" max="100" class="progress-bar"></progress>'
        );
        $("#dl-button").click(download_specfiles);
        $("#delete-button").click(delete_all_selected_specfiles);
        $("#dl-button-raw").click(download_rawfiles);
    }

    //   Reset check boxes when changing number of displayed objects in table
    $('#spectratable_length').change(function () {
        spectra_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    //   Reset check boxes when switching to the next table page
    $('#spectratable_paginate').click(function () {
        spectra_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    // Adjust nav bar highlight
    adjust_nav_bar_active("#observation_dropdown")
});


// Table filter functionality

function get_filter_keywords(d) {

    d = $.extend({}, d, {
        "project": $('#project-pk').attr('project'),
        "target": $('#filter_target').val(),
        "telescope": $('#filter_telescope').val(),
        "instrument": $('#filter_instrument').val(),
    });

    if ($('#filter_hjd').val() !== '') {
        let hjd_min = $('#filter_hjd').val().split(':')[0];
        if (hjd_min == '') {
            hjd_min = 0.;
        }
        let hjd_max = $('#filter_hjd').val().split(':')[1];
        if (hjd_max == '') {
            hjd_max = 1000000000.;
        }
        d = $.extend({}, d, {
//          "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] | 0 ),
//          "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] | 1000000000),
            "hjd_min": parseFloat(hjd_min),
            "hjd_max": parseFloat(hjd_max),
        });
    }

    if ($('#filter_exptime').val() !== '') {
        d = $.extend({}, d, {
            "exptime_min": parseFloat($('#filter_exptime').val().split(':')[0] | 0),
            "exptime_max": parseFloat($('#filter_exptime').val().split(':')[1] | 1000000000),
        });
    }

    if ($('#id_fluxcal_yes').is(':checked')) {
        d = $.extend({}, d, {
            "fluxcal": true
        });
    }
    if ($('#id_fluxcal_no').is(':checked')) {
        d = $.extend({}, d, {
            "fluxcal": false
        });
    }

    return d
}

// Table renderers
function selection_render(data, type, full, meta) {
    if ($(spectra_table.row(meta['row']).node()).hasClass('selected')) {
        return '<i class="material-icons button select" title="Select">check_box</i>';
    } else {
        return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
    }
}


function hjd_render(data, type, full, meta) {
    return "<a href='" + full['href'] + "' >" + data + "</a>"
}

function star_render(data, type, full, meta) {
    try {
        return "<a href='" + data['href'] + "' >" + data['name'] + "</a>" + " (" + data['ra'].toFixed(5) + " " + data['dec'].toFixed(5) + ")"
    } catch (err) {
        return ''
    }
}

function instrument_render(data, type, full, meta) {
    return data + " @ " + full['telescope']
}

function airmass_render(data, type, full, meta) {
    if (data === -1) {
        return "-"
    } else {
        return data
    }
}

function resolution_render(data, type, full, meta) {
    if (data === -1) {
        return "-"
    } else {
        return data
    }
}

// Selection and Deselection of rows

function select_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box');
    $(row.node()).addClass('selected');
    if (spectra_table.rows('.selected').data().length < spectra_table.rows().data().length) {
        $('#select-all').text('indeterminate_check_box');
    } else {
        $('#select-all').text('check_box');
    }
    $('#dl-button').removeClass("disabled");
    $('#dl-button-raw').removeClass("disabled");
    $('#rm-button').removeClass("disabled");
    $('#delete-button').removeClass("disabled");
}

function deselect_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box_outline_blank');
    $(row.node()).removeClass('selected');
    if (spectra_table.rows('.selected').data().length === 0) {
        $('#select-all').text('check_box_outline_blank');
        $('#dl-button').addClass("disabled");
        $('#dl-button-raw').addClass("disabled");
        $('#rm-button').addClass("disabled");
        $('#delete-button').addClass("disabled");
    } else {
        $('#select-all').text('indeterminate_check_box');
    }
}


//  Delete spectra
function delete_all_selected_specfiles() {
    if (confirm('Are you sure you want to delete this spectrum? This can NOT be undone!') === true) {
        let rows = [];
        //   Get list of selected spectra
        spectra_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            rows.push(this);
        });

        //   Set Promise -> evaluates to a resolved Promise
        let p = $.when()

        // Loop over selected spectra
        $.each(rows, function (index, row) {
            //  Delete each individual specfile or the spectrum if it is not associated
            //  with any specfile, although the latter should never happen
            if (row.data()["specfiles"].length === 0) {
                let pk = row.data()["href"].split('/')[5];
                //    Promise chaining using .then() + async function definition
                //    to allow the use of await
                p = p.then(async function () {
                    //  Ajax call to remove spec files
                    await $.ajax({
                        url: "/api/observations/spectra/" + pk + '/',
                        type: "DELETE",
                        success: function (json) {
                            //  Remove the whole spectrum from table
                            spectra_table.row(row).remove().draw('full-hold');
                        },
                        error: function (xhr, errmsg, err) {
                            if (xhr.status === 403) {
                                alert('You have to be logged in to delete this spectrum.');
                            } else {
                                alert(xhr.status + ": " + xhr.responseText);
                            }
                            console.log(xhr.status + ": " + xhr.responseText);
                        }
                    });
                });
            } else {
                //  Loop over all spec files
                $.each(row.data()["specfiles"], function (ind) {
                    let pk = row.data()["specfiles"][ind]['pk'];
                    //    Promise chaining using .then() + async function definition
                    //    to allow the use of await
                    p = p.then(async function () {

                        //  Ajax call to remove spec files
                        await $.ajax({
                            url: "/api/observations/specfiles/" + pk + '/',
                            type: "DELETE",
                            success: function (json) {
                                //  Remove the whole spectrum from table
                                spectra_table.row(row).remove().draw('full-hold');
                            },
                            error: function (xhr, errmsg, err) {
                                if (xhr.status === 403) {
                                    alert('You have to be logged in to delete this spectrum.');
                                } else {
                                    alert(xhr.status + ": " + xhr.responseText);
                                }
                                console.log(xhr.status + ": " + xhr.responseText);
                            }
                        });
                    });
                })
            }
        })

        //   Reset check boxes
        spectra_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    }
}


//  Download options:

//  Update progress bar
function updatePercent(percent) {
    $("#progress-bar")
        .val(percent);
}

function updatePercent_raw(percent) {
    $("#progress-bar-raw")
        .val(percent);
}

//  Change download button text
function showProgress(text) {
    $("#progress-bar").show();
    $("#dl-button .dl-btn-text").text(text);
}

function showProgress_raw(text) {
    $("#progress-bar-raw").show();
    $("#dl-button-raw .dl-btn-text").text(text);
}

//  Show Error message
function showError(text) {
    $("#dl-button .dl-btn-text").text(text);
    $("#progress-bar").hide();
}

function showError_raw(text) {
    $("#dl-button-raw .dl-btn-text").text(text);
    $("#progress-bar-raw").hide();
}

function selected_spectrum_pks() {
    let spectrum_pks = [];
    spectra_table.rows('.selected').every(function () {
        let pk = this.data().pk;
        if (pk !== undefined && pk !== null) {
            spectrum_pks.push(String(pk));
        }
    });
    return spectrum_pks;
}

function download_specfiles() {
    if ($('#dl-button').hasClass('disabled')) {
        showError('Select spectra first (checkbox column).');
        return;
    }
    const spectrum_pks = selected_spectrum_pks();
    if (spectrum_pks.length === 0) {
        showError('No spectra selected.');
        return;
    }
    $('#dl-button').addClass('disabled');
    $("#progress-bar").show();
    aotsStartBulkDownload({
        projectId: $('#project-pk').attr('project'),
        idList: spectrum_pks,
        kind: 'processed',
        onProgress: showProgress,
        onError: function (msg) {
            showError(msg);
            $('#dl-button').removeClass('disabled');
        },
        onComplete: function () {
            $('#dl-button').removeClass('disabled');
            showProgress('Download Spectra');
        },
    });
}

function download_rawfiles() {
    if ($('#dl-button-raw').hasClass('disabled')) {
        showError_raw('Select spectra first (checkbox column).');
        return;
    }
    const spectrum_pks = selected_spectrum_pks();
    if (spectrum_pks.length === 0) {
        showError_raw('No spectra selected.');
        return;
    }
    $('#dl-button-raw').addClass('disabled');
    $("#progress-bar-raw").show();
    aotsStartBulkDownload({
        projectId: $('#project-pk').attr('project'),
        idList: spectrum_pks,
        kind: 'raw',
        onProgress: showProgress_raw,
        onError: function (msg) {
            showError_raw(msg);
            $('#dl-button-raw').removeClass('disabled');
        },
        onComplete: function () {
            $('#dl-button-raw').removeClass('disabled');
            showProgress_raw('Download Raw Data');
        },
    });
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
    $("#editdropdown").toggleClass("show");
    let otherdd = $("#downloaddropdown");
    if (otherdd.hasClass("show")) {
        otherdd.toggleClass("show");
    }
}


function Toggledownloaddropdown() {
    $("#downloaddropdown").toggleClass("show");
    let otherdd = $("#editdropdown")
    if (otherdd.hasClass("show")) {
        otherdd.toggleClass("show");
    }
}
