let rawspecfile_table = null;
let edit_linkage_window = null;
let add_spectra_window = null;

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
            {data: 'obs_date'},
//          { data: 'hjd' },
            {data: 'instrument'},
            {data: 'filetype'},
            {data: 'exptime'},
            {data: 'filename', orderable: false},
            {data: 'added_on'},
            {data: 'specfile', render: reduced_render},
            {data: 'stars', orderable: false, render: stars_render},
//          { data: 'specfiles', orderable: false, render: processed_render },
        ];
    } else {
        columns = [
            {data: 'obs_date'},
//          { data: 'hjd' },
            {data: 'instrument'},
            {data: 'filetype'},
            {data: 'exptime'},
            {data: 'filename'},
            {data: 'added_on'},
            {data: 'specfile', render: reduced_render},
            {data: 'stars', orderable: false, render: stars_render},
//          { data: 'specfiles', orderable: false, render: processed_render },
        ];
    }
    ;

    // Table functionality
    rawspecfile_table = $('#rawspecfiletable').DataTable({
        dom: 'l<"toolbar">frtip',
        autoWidth: false,
        serverSide: true,
        ajax: {
            url: '/api/observations/rawspecfiles/?format=datatables&keep=pk',
            data: get_filter_keywords,
        },
        searching: false,
        orderMulti: false, //Can only order on one column at a time
        order: [1],
        columns: columns,
        paging: true,
        pageLength: 20,
        lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
        scrollY: $(window).height() - $('header').outerHeight(true) - $('.upload').outerHeight(true) - $('#messages').outerHeight(true) - 186,
        scrollCollapse: true,
    });

    // Event listener to the two range filtering inputs to redraw on input
    $('#filter-form').submit(function (event) {
        event.preventDefault();
        rawspecfile_table.draw();
    });

    // Check and uncheck tables rows
    $('#rawspecfiletable tbody').on('click', 'td.select-control', function () {
        var tr = $(this).closest('tr');
        var row = rawspecfile_table.row(tr);
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

            rawspecfile_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                deselect_row(this); // Open this row
            });
        } else {
            // close all rows
            $(this).text('check_box');

            rawspecfile_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
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
        if (text == "filter_list") {
            $('#filter-dashboard-button').text("close");
        } else {
            $('#filter-dashboard-button').text("filter_list");
        }
    };

    // Add toolbar to table
    if (user_authenticated) {
        $("div.toolbar").html(
            "<input id='dl-button'  class='tb-button' value='Download raw data' type='button' disabled>" +
            '<progress id="progress-bar" value="0" max="100" class="progress-bar"></progress>' +
            "<input id='add-button' class='tb-button' value='Add Raw spectra' type='button'>" +
            '<progress id="progress-bar-upload" value="0" max="100" class="progress-bar"></progress>' +
            "<input id='change-button'  class='tb-button' value='Change file allocations' type='button' disabled>" +
            "<input id='delete-button'  class='tb-button' value='Delete raw data' type='button' disabled>" +
            "<p class='hide' id='result'></p>"
        );
        $("#dl-button").click(download_rawfiles);
        $("#delete-button").click(delete_all_selected_rawspecfiles);
        $("#change-button").click(openLinkageEditWindow);
        $("#add-button").click(openAddSpectraWindow);
    }

    //  Save content of system and specfile form fields to allow their reset
    let saved_system = $("#id_system")[0]['innerHTML'];
    let saved_specfile = $("#id_specfile")[0]['innerHTML'];


    //  Add spectra form:
    //  Adjust form drop dropdown content I: read system name
    $("#id_system_name").on("keyup", function () {
        let name = $(this).val().toLowerCase();
        $("#id_system option").filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(name) > -1)
        });
    });

    //  Add spectra form:
    //  Adjust form drop dropdown content II: read observation date
    $("#id_specfile_date").on("keyup", function () {
        var date = $(this).val().toLowerCase();
        $("#id_specfile option").filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(date) > -1)
        });
    });

    //  Add spectra form:
    //  Adjust form drop dropdown content III: evaluate system drop down
    $("#id_system").change(function () {
        //  Set pk list
        let pk_list = $(this).val();

        //  Clear Specfile drop down
        document.getElementById("id_specfile").length = 0;
        $("#id_specfile").val([]);

        //  Loop over pks
        $.each(pk_list, function (index, pk) {
            //  Get Specfile info as JASON
            $.getJSON("/api/systems/stars/" + pk + '/specfiles/', function (data) {
                //  Refilling Specfile drop down
                for (let key in data) {
                    if (data.hasOwnProperty(key)) {
                        let value = data[key];
                        $("#id_specfile").append("<option value = \"" + key + "\">" + value + "</option>");
                    }
                }
                ;
            });
        });
    });

    //  Add spectra form:
    //  Adjust form drop dropdown content IV: evaluate spectra drop down
    $("#id_specfile").change(function () {
        //  Set pk list
        let pk_list = $(this).val();

        //  Clear Specfile drop down
        document.getElementById("id_system").length = 0;
        $("#id_system").val([]);

        //  Loop over pks
        $.each(pk_list, function (index, pk) {
            //  Get Specfile info as JASON
            $.getJSON("/api/observations/specfiles/" + pk + '/', function (data) {
                data = data['star_pk']
                //  Refilling System drop down
                for (let key in data) {
                    let value = data[key];
                    if (data.hasOwnProperty(key)) {
                        let value = data[key];
                        $("#id_system").append("<option value = \"" + key + "\">" + value + "</option>");
                    }
                }
                ;
            });
        });
    });

    //  Add spectra form:
    //  Reset system and specfile form fields by means of double click
    $("#id_system").on("dblclick", function () {
        document.getElementById("id_system").length = 0;
        $("#id_system").val([]);
        $("#id_system").append(saved_system);
    });

    $("#id_specfile").on("dblclick", function () {
        document.getElementById("id_specfile").length = 0;
        $("#id_specfile").val([]);
        $("#id_specfile").append(saved_specfile);
    });

    //  Edit linkage form:
    //  Adjust form drop dropdown content I: read system name
    $("#id_system_name_patch").on("keyup", function () {
        let name = $(this).val().toLowerCase();
        $("#id_system_patch option").filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(name) > -1)
        });
    });

    //  Edit linkage form:
    //  Adjust form drop dropdown content II: read observation date
    $("#id_specfile_date_patch").on("keyup", function () {
        var date = $(this).val().toLowerCase();
        $("#id_specfile_patch option").filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(date) > -1)
        });
    });

    //  Edit linkage form:
    //  Adjust form drop dropdown content III: evaluate system drop down
    $("#id_system_patch").change(function (index) {
        //  Set pk list
        let pk_list = $(this).val();

        //  Clear Specfile drop down
        document.getElementById("id_specfile_patch").length = 0;
        $("#id_specfile_patch").val([]);

        //  Loop over pks
        $.each(pk_list, function (index, pk) {
            //  Get Specfile info as JASON
            $.getJSON("/api/systems/stars/" + pk + '/specfiles/', function (data) {
                //  Refilling Specfile drop down
                for (let key in data) {
                    if (data.hasOwnProperty(key)) {
                        let value = data[key];
                        $("#id_specfile_patch").append("<option value = \"" + key + "\">" + value + "</option>");
                    }
                }
                ;
            });
        });
    });

    //  Edit linkage form:
    //  Adjust form drop dropdown content IV: evaluate spectra drop down
    $("#id_specfile_patch").change(function () {
        //  Set pk list
        let pk_list = $(this).val();

        //  Clear Specfile drop down
        document.getElementById("id_system_patch").length = 0;
        $("#id_system_patch").val([]);

        //  Loop over pks
        $.each(pk_list, function (index, pk) {
            //  Get Specfile info as JASON
            $.getJSON("/api/observations/specfiles/" + pk + '/', function (data) {
                data = data['star_pk']
                //  Refilling System drop down
                for (let key in data) {
                    let value = data[key];
                    if (data.hasOwnProperty(key)) {
                        let value = data[key];
                        $("#id_system_patch").append("<option value = \"" + key + "\">" + value + "</option>");
                    }
                }
                ;
            });
        });
    });

    //  Edit linkage form:
    //  Reset system and specfile form fields by means of double click
    $("#id_system_patch").on("dblclick", function () {
        document.getElementById("id_system_patch").length = 0;
        $("#id_system_patch").val([]);
        $("#id_system_patch").append(saved_system);
    });

    $("#id_specfile_patch").on("dblclick", function () {
        document.getElementById("id_specfile_patch").length = 0;
        $("#id_specfile_patch").val([]);
        $("#id_specfile_patch").append(saved_specfile);
    });


    //  Add progress bar for raw data file upload
    $("#raw-upload-form").submit(function (e) {
        //  Prevent normal behaviour
        e.preventDefault();
        //  Get form
        $form = $(this);
        //  Create new form
        let formData = new FormData(this);
        //  Get files
        const rawfiles = document.getElementById('id_rawfile');
        const data = rawfiles.files[0];
        //  Display progress bar
        if (data != null) {
            $("#progress-bar-upload").removeClass("hidden");
        }
        ;
        //  Get project
        let project = $('#project-pk').attr('project_slug')
        //  Ajax call to make it happen
        $.ajax({
            type: 'POST',
            url: '/w/' + project + '/observations/rawspecfiles/',
            data: formData,
            dataType: 'json',
            xhr: function () {
                //  Handel progress bar updates
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e => {
                    if (e.lengthComputable) {
                        const percentProgress = (e.loaded / e.total) * 100;
                        $("#progress-bar-upload").val(percentProgress);
                    }
                });
                return xhr
            },
            success: function (response) {
                //  Set extract and set message
                $.each(response.messages, function (id, message_list) {
                    let success = message_list[0];
                    let message = message_list[1];

                    if (success == true) {
                        $("#messages").append(
                            "<li class=\"success\">" + message + "</li>"
                        );
                    } else if (success == false) {
                        $("#messages").append(
                            "<li class=\"error\">" + message + "</li>"
                        );
                    } else {
                        $("#messages").append(
                            "<li class=\"error\">An undefined error has occurred.</li>"
                        );
                    }
                    ;
                });

                //  Redraw table
                rawspecfile_table.draw('full-hold');

                //  Reset form fields
                $("#raw-upload-form")[0].reset();

                //  Reset Specfile dropdown that is not reset by the line above
                $("#id_system>option").map(function () {
                    //  Set pk
                    let pk = $(this).val();
                    //  Get Specfile info as JASON
                    $.getJSON("/api/systems/stars/" + pk + '/specfiles/', function (data) {
                        //  Refilling Specfile drop down
                        for (let key in data) {
                            if (data.hasOwnProperty(key)) {
                                let value = data[key];
                                $("#id_specfile").append(
                                    "<option value = \"" + key + "\">" + value
                                    + "</option>");
                            }
                        }
                        ;
                    });
                });

                //  Remove progress bar
//                 $("#progress-bar-upload").addClass("not-visible");
            },
            error: function (err) {
                console.log('error', err);
                alert(err.statusText);
            },
            cache: false,
            contentType: false,
            processData: false,
        });
    });


    //   Reset check boxes when changing number of displayed objects in table
    $('#rawspecfiletable_length').change(function () {
        rawspecfile_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    //   Reset check boxes when switching to the next table page
    $('#rawspecfiletable_paginate').click(function () {
        rawspecfile_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    //   Initialize edit windows
    edit_linkage_window = $("#editLinkage").dialog({
        autoOpen: false,
//         width: '40%',
        width: '975',
//         minwidth: '350',
        modal: true,
        title: "Adjust file allocations",
        buttons: {"Update": updateLinkage},
        close: function () {
            edit_linkage_window.dialog("close");
        }
    });

//    initialize_add_spectra_window();
    add_spectra_window = $("#addRawSpec").dialog({
        autoOpen: false,
        width: '975',
        modal: true,
        autoOpen: false,
        title: "Add raw data",
//         cache: false,
        close: function () {
            add_spectra_window.dialog("close");
        },
//         close: function() { add_spectra_window.dialog( "destroy" ); },
    });
});


// function initialize_add_spectra_window() {
//     add_spectra_window = $("#addRawSpec").dialog({
//         autoOpen: false,
//         width: '975',
//         modal: true,
//         title: "Add raw data",
// //         cache: false,
//         close: function() { add_spectra_window.dialog( "close" ); },
// //         buttons: {
// //             "Refresh": function () {
// //                 add_spectra_window.dialog( "destroy" );
// //                 initialize_add_spectra_window();
// // //                 window.location.reload();
// //                 add_spectra_window.dialog( "open" );
// //             }
// //         },
//    });
// }

// Table filter functionality

function get_filter_keywords(d) {

    d = $.extend({}, d, {
        "project": $('#project-pk').attr('project'),
        "instrument": $('#filter_instrument').val(),
        "filename": $('#filter_filename').val(),
        "filetype": $('#filter_filetype').val(),
        "systems": $('#filter_systems').val(),
        "obs_date": $('#filter_obs_date').val(),
    });

    if ($('#filter_hjd').val() != '') {
        let hjd_min = $('#filter_hjd').val().split(':')[0];
        if (hjd_min == '') {
            hjd_min = 0.;
        }
        let hjd_max = $('#filter_hjd').val().split(':')[1];
        if (hjd_max == '') {
            hjd_max = 1000000000.;
        }
        d = $.extend({}, d, {
            "hjd_min": parseFloat(hjd_min),
            "hjd_max": parseFloat(hjd_max),
        });
    }
    ;

    if ($('#filter_expo_time').val() != '') {
        d = $.extend({}, d, {
            "expo_min": parseFloat($('#filter_expo_time').val().split(':')[0]),
            "expo_max": parseFloat($('#filter_expo_time').val().split(':')[1]),
        });
    }
    ;

    return d
}


// Table renderers

function selection_render(data, type, full, meta) {
    if ($(rawspecfile_table.row(meta['row']).node()).hasClass('selected')) {
        return '<i class="material-icons button select" title="Select">check_box</i>';
    } else {
        return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
    }
}

function stars_render(data, type, full, meta) {
    let systems = [];
    for (let key in data) {
        if (data.hasOwnProperty(key)) {
            let value = data[key];
            systems.push("<a href='" + value + "' > " + key + "</a>");
        }
    }
    return systems
}

function reduced_render(data, type, full, meta) {
    let nspecfiles = data.length;
//     console.log(nspecfiles);
    if (nspecfiles === 0) {
        return '<i class="material-icons status-icon invalid" title="Not allocated to a reduced Spectrum."></i>'
    } else {
        return '<i class="material-icons status-icon valid" title="Allocated to a reduced Spectrum."></i>'
    }
}


// Selection and Deselection of rows

function select_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box');
    $(row.node()).addClass('selected');
    if (rawspecfile_table.rows('.selected').data().length < rawspecfile_table.rows().data().length) {
        $('#select-all').text('indeterminate_check_box');
    } else {
        $('#select-all').text('check_box');
    }
    $('#dl-button').prop('disabled', false);
    $('#rm-button').prop('disabled', false);
    $('#delete-button').prop('disabled', false);
    $('#change-button').prop('disabled', false);
}

function deselect_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box_outline_blank');
    $(row.node()).removeClass('selected');
    if (rawspecfile_table.rows('.selected').data().length === 0) {
        $('#select-all').text('check_box_outline_blank');
        $('#dl-button').prop('disabled', true);
        $('#rm-button').prop('disabled', true);
        $('#delete-button').prop('disabled', true);
        $('#change-button').prop('disabled', true);
    } else {
        $('#select-all').text('indeterminate_check_box');
    }
}


//  Open add spectra window
function openAddSpectraWindow() {
//     add_spectra_window = $("#addRawSpec").dialog({
//         autoOpen: false,
//         title: "Add raw data",
//         close: function() {
//             add_spectra_window.dialog( "close" );
//     //           $(".upload-button").click();
//         },
//     });

    $("#raw-upload-form").submit(function () {
        $(this).closest(".ui-dialog-content").dialog("close");
    });

    add_spectra_window.dialog("open");
}

//  Delete raw data
function delete_all_selected_rawspecfiles() {
    if (confirm('Are you sure you want to delete this spectrum? This can NOT be undone!') === true) {
        let rows = [];
        //   Get list of selected files
        rawspecfile_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            //  Determine ID/PK
            let pk = this.data()['pk'];
            //  Ajax call to remove spec files
            $.ajax({
                url: "/api/observations/rawspecfiles/" + pk + '/',
                type: "DELETE",
                success: function (json) {
                    //  Remove the whole spectrum from table
                    rawspecfile_table.row(this).remove().draw('full-hold');
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
        })

        //   Reset check boxes
        rawspecfile_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    }
}


//  Open edit window for file linkage
function openLinkageEditWindow() {
    edit_linkage_window.dialog("open");
}

function updateLinkage() {
    //  Bind to selected spectra
    let spectra = $("#id_specfile_patch");
    let specfiles = spectra.children().filter(':checked')

    //  Check that spectra are selected
    if (specfiles.length == 0) {
        $('#linkage-error').text('You need to select a spectrum file!');
    } else {
        //  Loop over SpecFiles, get 'pk'
        let pk_list_spf = [];
        specfiles.map(function (index) {
            //  Get SpecFile 'pk'
            let pd_spf = $(this).val();
            pk_list_spf.push(pd_spf);
        });

        //   Get list of selected RawSpecfiles
        rawspecfile_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            //  Determine ID/PK
            let pk_raw = this.data()['pk'];

            //  Modify the linkage
            change_rawspecfiles_linkage(this, pk_raw, pk_list_spf);
        });

        //   Reset check boxes
        rawspecfile_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    }
}

//  Delete raw data
function change_rawspecfiles_linkage(row, pk_raw, pk_spf) {
    //  Ajax call to patch SpecFile <-> RawFile association
    $.ajax({
        url: "/api/observations/rawspecfiles/" + pk_raw + '/',
        type: "PATCH",
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({'specfile': pk_spf}),
        success: function (json) {
            //  Close edit window
            edit_linkage_window.dialog("close");
            //  Redraw table row
            row.data(json).draw('page');
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
}

//  Download options:

//  Update progress bar
function updatePercent(percent) {
    $("#progress-bar")
        .val(percent);
}

//  Change download button text
function showProgress(text) {
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

//  Download Raw Data
function download_rawfiles() {
    //   Prepare file list
    let rawlist = [];
    //   Get list of selected spectra
    rawspecfile_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        //  Determine ID/PK
        let pk = this.data()['pk'];

        //    Get file path
        $.getJSON(
            "/api/observations/rawspecfiles/" + pk + "/path/",
            function (path) {
                //    Add to file list
                rawlist.push(path);
            });
    });

    //   Load Filesaver and jszip libs to facilitate download
    $.getScript("/static/js/JsZip/FileSaver.js").done(function () {
        $.getScript("/static/js/JsZip/jszip.js").done(async function () {

            //  Create zip file
            let zip = new JSZip();

            //  Set time string for zip file name
            let dt = new Date();
            let timecode = dt.getHours() + "" + dt.getMinutes() + dt.getSeconds();

            //  Get file using promises so that file assembly can wait until
            //  download has finished
            const getPromises = rawlist.map(async path => {
                let file = path.split('/').slice(-1);
                return new Promise(function (resolve, reject) {
                    $.get(path)
                        .done(function (data) {
                            resolve([file, data]);
                        })
                        .fail(function () {
                            reject("ERROR: File not found");
                        })
                });
            });

            //  Fill zip file
            for (const getPromise of getPromises) {
                try {
                    const content = await getPromise;
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
                    saveAs(blob, "Raw_data_" + timecode + ".zip");
                    //  Reset download button
                    showProgress("Download raw data");
                }, function (e) {
                    showError(e);
                });


        });
    });
}
