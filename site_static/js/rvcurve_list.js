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
            {data: 'logp', render: logp_render},
            {data: 'star', render: star_render},
            {data: 'time_spanned', render: timespan_render},
            {data: 'N_samples', render: nsamples_render},
            {data: 'average_rv', render: averagerv_render},
            {data: 'half_amplitude', render: halfamplitude_render},
            {data: 'solved', render: solved_render},
        ];
    } else {
        columns = [
            {data: 'logp', render: logp_render},
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
            url: '/api/analysis/rvcurves/?format=datatables&keep=href,delta_rv,delta_rv_err,average_rv_err',
            data: get_filter_keywords
        }
    } else {
        ajax_kw = {
            url: '/api/analysis/rvcurves/?format=datatables&keep=href,delta_rv,delta_rv_err,average_rv_err',
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
            "<button id='upload-button' class='tb-button'><i class='material-icons button' title='Add System(s)'>add</i>Upload RV curve(s)</button>" +
            '<progress hidden id="progress-bar" value="0" max="100" class="progress-bar"></progress>'
        );
        $("#delete-button").click(delete_all_selected_rvcurves);
        $("#dl-button").click(download_rvcurves);
        $("#upload-button").click(openAddUploadRVCurvesWindow);
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

    upload_rvcurves_window = $("#uploadRVcurves").dialog({
        autoOpen: false,
        width: '875',
        modal: true,
    });
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
        return "<a href='" + data['href'] + "' >" + data['name'] + "</a>"
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
        return Math.round(data * 100) / 100 // Round to 2 decimal places

    }
}

function averagerv_render(data, type, full, meta) {
    if (data === 0) {
        return "-"
    } else {
        return Math.round(data * 100) / 100 + " ± " + Math.round(full["average_rv_err"] * 100) / 100  // Round to 2 decimal places
    }
}

function halfamplitude_render(data, type, full, meta) {
    if (data === 0) {
        if (full["delta_rv"] !== 0) {
            return Math.round(full["delta_rv"] * 100) / 100 + " ± " + Math.round(full["delta_rv_err"] * 100) / 100
        }
        else{
            return "-"
        }
    } else {
        return Math.round(data * 100) / 100 // Round to 2 decimal places
    }
}


function logp_render(data, type, full, meta) {
    if (data === 0) {
        return "-"
    } else {
        if (data < -4) {
            return "<a href='" + full['href'] + "' >" + Math.round(data * 10000) / 10000 + " (Detection)</a> "
        }
        if (-4 < data && data < -1){
            return "<a href='" + full['href'] + "' >" + Math.round(data * 10000) / 10000 + " (Candidate)</a> "
        }
        if (-1 < data){
            return "<a href='" + full['href'] + "' >" + Math.round(data * 10000) / 10000 + " (No Detection)</a> "
        }
    }
}


function solved_render(data, type, full, meta) {
    console.log(full)
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
    if (RVcurves_table.rows('.selected').data().length === 0) {
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

//  Delete spectra
function delete_all_selected_rvcurves() {
    if (confirm('Are you sure you want to delete these RV curves? This can NOT be undone!') === true) {
        let rows = [];
        //   Get list of selected spectra
        RVcurves_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            rows.push(this);
        });

        //   Set Promise -> evaluates to a resolved Promise
        let p = $.when()

        // Loop over selected spectra
        $.each(rows, function (index, row) {
            let pk = row.data()["href"].split('/')[5];
            //  Delete each individual specfile or the spectrum if it is not associated
            //  with any specfile, although the latter should never happen
            //    Promise chaining using .then() + async function definition
            //    to allow the use of await
            p = p.then(async function () {
                //  Ajax call to remove spec files
                await $.ajax({
                    url: "/api/analysis/rvcurves/" + pk + '/',
                    type: "DELETE",
                    success: function (json) {
                        //  Remove the whole spectrum from table
                       RVcurves_table.row(row).remove().draw('full-hold');
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

        //   Reset check boxes
        RVcurves_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    }
}

//  Download RV Curves
function download_rvcurves() {
    //   Prevent impatient users from clicking again.
    $('#dl-button').prop('disabled', true);
    showProgress("Be Patient...");
    //   Prepare file list
    let rvcurvelist = [];
    //   Get list of selected spectra
    RVcurves_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        let rvfilepk = this.data()["href"].split('/')[5];
        //    Get file path
        $.getJSON(
            "/api/analysis/rvcurves/" + rvfilepk + "/path/",
            function (path) {
                //    Add to file list
                rvcurvelist.push(path);
            });
    });

    console.log(rvcurvelist)

    //   Load Filesaver and jszip libs to facilitate download
    $.getScript("/static/js/JsZip/FileSaver.js").done(function () {
        $.getScript("/static/js/JsZip/jszip.js").done(async function () {
            $.getScript("/static/js/JsZip/jszip-utils.js").done(async function () {

                //  Create zip file
                let zip = new JSZip();

                //  Set time string for zip file name
                let dt = new Date();
                let timecode = dt.getHours() + "" + dt.getMinutes() + dt.getSeconds();

                //  Get file using promises so that file assembly can wait until
                //  download has finished
                const getPromises = rvcurvelist.map(async path => {
                    let file = path.split('/').slice(-1);
                    return new Promise(function (resolve, reject) {
                        JSZipUtils.getBinaryContent(path, function (err, data) {
                            if (err) {
                                reject("ERROR: File not found");
                            } else {
                                resolve([file, data]);
                            }
                        })
                    });
                });

                //  Fill zip file
                for (const promise of getPromises) {
                    try {
                        const content = await promise;
                        zip.file(content[0], content[1]);
                    } catch (err) {
                        showError(err);
                        return
                    }
                }

                //  Generate zip file
                zip.generateAsync({type: "blob"}, function updateCallback(metadata) {
                    //  Update download progress
                    let msg = "            " + metadata.percent.toFixed(2) + " %           ";
                    showProgress(msg);
                    updatePercent(metadata.percent | 0);
                })
                    .then(function callback(blob) {
                        //  Save zip file
                        saveAs(blob, "RVcurve_" + timecode + ".zip");
                        //  Reset download button
                        $('#dl-button').prop('disabled', false);
                        showProgress("Download RV Curves");
                        $("#progress-bar").hide();
                    }, function (e) {
                        showError(e);
                    });
            });
        });
    });
}

function upload_rvcurves() {

}

function openAddUploadRVCurvesWindow() {
    upload_rvcurves_window = $("#uploadRVcurves").dialog({
        autoOpen: false,
        title: "Upload RV Curve(s)",
        close: function () {
            upload_rvcurves_window.dialog("close");
        },
    });

    upload_rvcurves_window.dialog("open");
}
