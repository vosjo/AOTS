var dataset_table = null;
var add_dataset_window = null;

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
            {data: 'name', render: name_render},
            {data: 'note', render: note_render},
            {data: 'method', render: method_render},
            {data: 'added_on'},
        ];
    } else {
        columns = [
            {data: 'star', render: star_render},
            {data: 'name', render: name_render},
            {data: 'note', render: note_render},
            {data: 'method', render: method_render},
            {data: 'added_on'},
        ];
    }

    dataset_table = $('#datasettable').DataTable({
        dom: 'l<"toolbar">frtip',
        autoWidth: false,
        serverSide: true,
        ajax: {
            url: '/api/analysis/datasets/?format=datatables&keep=href,file_url',
            data: get_filter_keywords
        },
        searching: false,
        orderMulti: false, //Can only order on one column at a time
        order: [1],
        columns: columns,
        paging: true,
        pageLength: 20,
        lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
        // scrollY: $(window).height() - $('header').outerHeight(true) - $('.upload').outerHeight(true) - $('#messages').outerHeight(true) - 186,
        scrollY: $(window).height() - $('header').outerHeight(true) - 196,
        scrollCollapse: true,
    });

    //  Initialize add dataset window
    add_dataset_window = $("#addDataset").dialog({
        autoOpen: false,
        width: '875',
        modal: true,
    });

    //Add toolbar to table
    if (user_authenticated) {
        $("div.toolbar").html(
            "<div class='dropdown-container'>" +
            "<button onclick='Toggleeditdropdown()' class='dropbtn' id='editselected'><i class='material-icons button' title='Edit selected'>edit_note</i>Edit selected</button>"+
            "<div id='editdropdown' class='dropdown-content'>" +
            "<a id='delete-button' class='tb-button disabled'><i class='material-icons button dropdownbtn'>delete</i>Delete Dataset</a>" +
            "</div>" +
            "</div>" +
            "<div class='dropdown-container'>" +
            "<button onclick='Toggledownloaddropdown()' class='dropbtn' id='download'><i class='material-icons button' title='Carry over selection'>download</i>Download Files</button>"+
            "<div id='downloaddropdown' class='dropdown-content'>" +
            "<a id='dl-button'  class='tb-button disabled' ><i class='material-icons button dropdownbtn'>download_for_offline</i>Download Dataset</a>" +
            "</div>" +
            "</div>" +
            "<button id='adddataset-button' class='tb-button'><i class='material-icons button' title='Add Datasets(s)'>add</i>Add Datasets(s)</button>" +
            "<div class='dropdown-container'>" +
            '<progress hidden id="progress-bar" value="0" max="100" class="progress-bar"></progress>' +
            '<progress hidden id="progress-bar-raw" value="0" max="100" class="progress-bar"></progress>'
        );
        $("#dl-button").click(download_dataset);
        $("#delete-button").click(delete_dataset);
        $("#adddataset-button").click(openAddDatasetWindow);
    }

    //  Check and uncheck tables rows
    $('#datasettable tbody').on('click', 'td.select-control', function () {
        var tr = $(this).closest('tr');
        var row = dataset_table.row(tr);
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

            dataset_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                deselect_row(this); // Open this row
            });
        } else {
            // close all rows
            $(this).text('check_box');

            dataset_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                select_row(this); // close the row
            });
        }
    });

    //   Reset check boxes when changing number of displayed objects in table
    $('#datasettable_length').change(function () {
        dataset_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    //   Reset check boxes when switching to the next table page
    $('#datasettable_paginate').click(function () {
        dataset_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    // Event listener to the two range filtering inputs to redraw on input
    $('#filter-form').submit(function (event) {
        event.preventDefault();
        dataset_table.draw();
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
});


// Table filter functionality
function get_filter_keywords(d) {

    d = $.extend({}, d, {
        "project": $('#project-pk').attr('project'),
        "system": $('#filter_system').val(),
        "name": $('#filter_name').val(),
        "method": $('#filter_method').val(),
    });

    return d
}


//  Table renderers
function selection_render(data, type, full, meta) {
    if ($(dataset_table.row(meta['row']).node()).hasClass('selected')) {
        return '<i class="material-icons button select" title="Select">check_box</i>';
    } else {
        return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
    }
}

function star_render(data, type, full, meta) {
    return "<a href='" + data['href'] + "' >" + data['name'] + "</a>";
}

function name_render(data, type, full, meta) {
    return "<a href='" + full['href'] + "' >" + data + "</a>";
}

function note_render(data, type, full, meta) {
    if (data.length > 30) return data.substring(0, 30) + '...';
    return data
}

function method_render(data, type, full, meta) {
    return "<div title='" + data.description + "'>" + data.name + "</div>";
}


// Selection and Deselection of rows
function select_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box');
    $(row.node()).addClass('selected');
    if (dataset_table.rows('.selected').data().length < dataset_table.rows().data().length) {
        $('#select-all').text('indeterminate_check_box');
    } else {
        $('#select-all').text('check_box');
    }
    $('#dl-button').removeClass("disabled");
    $('#rm-button').removeClass("disabled");
    $('#delete-button').removeClass("disabled");
}

function deselect_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box_outline_blank');
    $(row.node()).removeClass('selected');
    if (dataset_table.rows('.selected').data().length === 0) {
        $('#select-all').text('check_box_outline_blank');
        $('#dl-button').addClass("disabled");
        $('#rm-button').addClass("disabled");
        $('#delete-button').addClass("disabled");
    } else {
        $('#select-all').text('indeterminate_check_box');
    }
}


/*
//  Process dataset
function process_dataset(row, data) {
    $.ajax({
        url: "/api/analysis/datasets/" + data['pk'] + "/process/",
        type: "POST",
        success: function (json) {
            // remove the row from the table
            dataset_table.row(row).data(json).draw('full-hold');
            // show success message for 5 sec.
            var li = $("<li class='success'>Processed dataset " + json['name'] + "</li>");
            $("#messages").append(li);
            li.delay(5000).fadeOut()
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}*/


//  Delete dataset
function delete_dataset(row, data) {
    if (confirm('Are you sure you want to remove these DataSets?') == true) {
        let rows = [];
        //   Get list of selected spectra
        dataset_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            rows.push(this);
        });

        //   Set Promise -> evaluates to a resolved Promise
        let p = $.when()

        $.each(rows, function (index, row) {
            let pk = row.data()["href"].split('/')[5];
            console.log('pk', pk)
            //    Promise chaining using .then() + async function definition
            //    to allow the use of await
            p = p.then(async function () {
                //  Ajax call to remove spec files
                await $.ajax({
                    url: "/api/analysis/datasets/" + pk + '/',
                    type: "DELETE",
                    success: function (json) {
                        //  Remove the whole spectrum from table
                        dataset_table.row(row).remove().draw('full-hold');
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
}



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


//  Download functions
function download_dataset() {
    //   Prevent impatient users from clicking again.
    $('#dl-button').prop('disabled', true);
    showProgress("Be Patient...");
    //   Prepare file list
    let url_list = [];
    //   Get list of selected spectra
    dataset_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        let url = this.data()["file_url"];
        url_list.push(url);
    });

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
            const getPromises = url_list.map(async url => {
                let file = url.split('/').slice(-1);
                return new Promise(function (resolve, reject) {
                    JSZipUtils.getBinaryContent(url, function(err, data) {
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
                    saveAs(blob, "Dataset_" + timecode + ".zip");
                    //  Reset download button
                    $('#dl-button').prop('disabled', false);
                    showProgress("Download Dataset");
                    $("#progress-bar").hide();
                }, function (e) {
                    showError(e);
                });
            });
        });
    });
}


// Open add dataset window
function openAddDatasetWindow() {
    add_dataset_window = $("#addDataset").dialog({
        autoOpen: false,
        title: "Add Dataset(s)",
        close: function () {
            add_dataset_window.dialog("close");
        },
    });

    add_dataset_window.dialog("open");
}


//  Close the dropdown menu if the user clicks outside of it
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
