var star_table = null;
var edit_status_window = null;
var edit_tags_window = null;
var all_tags = null;
var add_systems_window = null;


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
        pageLength: 20,
        lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
        scrollY: $(window).height() - $('.nav_bar').outerHeight(true)  - $('footer').outerHeight(true) - 196,
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
    });

    // make the filter button open the filter menu
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

    // check and uncheck tables rows
    $('#datatable tbody').on('click', 'td.select-control', function () {
        var tr = $(this).closest('tr');
        var row = star_table.row(tr);
        if ($(row.node()).hasClass('selected')) {
            deselect_row(row);
        } else {
            select_row(row);
        }
    });

    $('#select-all').on('click', function () {
        if ($(this).text() == 'check_box' | $(this).text() == 'indeterminate_check_box') {
            // deselect all
            $(this).text('check_box_outline_blank')

            star_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                deselect_row(this); // Open this row
            });
        } else {
            // close all rows
            $(this).text('check_box')

            star_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
                select_row(this); // close the row
            });
        }
    });

    // Load the tags and add them to the tag selection list, and the tag edit window
    load_tags();

    // initialize edit windows
    edit_status_window = $("#editStatus").dialog({
        autoOpen: false,
        width: '150',
        modal: true,
    });

    edit_tags_window = $("#editTags").dialog({
        autoOpen: false,
        width: '250',
        modal: true,
    });

    add_systems_window = $("#addSystems").dialog({
        autoOpen: false,
        width: '875',
        modal: true,
    });

    // event listeners for edit buttons
    $("#status-button").click(openStatusEditWindow);
    $("#tag-button").click(openTagEditWindow);
    $("#delete-button").click(deleteSystems);
    $("#addsystem-button").click(openAddSystemsWindow);
    $("#tospectra-button").click(toSpecta);
    $("#tolightcurve-button").click(toLightcurve);


    //   Reset check boxes when changing number of displayed objects in table
    $('#datatable_length').change(function () {
        star_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    //   Reset check boxes when switching to the next table page
    $('#datatable_paginate').click(function () {
        star_table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
        });
    });

    //  Change form status depending on Simbad status
    $('#id_get_simbad').change(
        function () {
            if ($(this).is(':checked')) {
                $('#id_ra').attr('readonly', true);
                $('#id_dec').attr('readonly', true);
                $('#id_sp_type').attr('readonly', true);
                $('#id_classification_type').attr('readonly', true);
                $('#id_classification_type').addClass('gray');
                $('#id_parallax').attr('readonly', true);
                $('#id_parallax_error').attr('readonly', true);
                $('#id_pmra_x').attr('readonly', true);
                $('#id_pmra_error').attr('readonly', true);
                $('#id_pmdec_x').attr('readonly', true);
                $('#id_pmdec_error').attr('readonly', true);
                $('#id_phot_g_mean_mag').attr('readonly', true);
                $('#id_phot_bp_mean_mag').attr('readonly', true);
                $('#id_phot_rp_mean_mag').attr('readonly', true);
                $('#id_phot_g_mean_magerr').attr('readonly', true);
                $('#id_phot_bp_mean_magerr').attr('readonly', true);
                $('#id_phot_rp_mean_magerr').attr('readonly', true);
                $('#id_Jmag').attr('readonly', true);
                $('#id_Hmag').attr('readonly', true);
                $('#id_Kmag').attr('readonly', true);
                $('#id_Jmagerr').attr('readonly', true);
                $('#id_Hmagerr').attr('readonly', true);
                $('#id_Kmagerr').attr('readonly', true);
                $('#id_W1mag').attr('readonly', true);
                $('#id_W2mag').attr('readonly', true);
                $('#id_W3mag').attr('readonly', true);
                $('#id_W4mag').attr('readonly', true);
                $('#id_W1magerr').attr('readonly', true);
                $('#id_W2magerr').attr('readonly', true);
                $('#id_W3magerr').attr('readonly', true);
                $('#id_W4magerr').attr('readonly', true);
                $('#id_FUV').attr('readonly', true);
                $('#id_NUV').attr('readonly', true);
                $('#id_FUVerr').attr('readonly', true);
                $('#id_NUVerr').attr('readonly', true);
                $('#id_Umag').attr('readonly', true);
                $('#id_Vmag').attr('readonly', true);
                $('#id_Gmag').attr('readonly', true);
                $('#id_Rmag').attr('readonly', true);
                $('#id_Imag').attr('readonly', true);
                $('#id_Zmag').attr('readonly', true);
                $('#id_Umagerr').attr('readonly', true);
                $('#id_Vmagerr').attr('readonly', true);
                $('#id_Gmagerr').attr('readonly', true);
                $('#id_Rmagerr').attr('readonly', true);
                $('#id_Imagerr').attr('readonly', true);
                $('#id_Zmagerr').attr('readonly', true);
                $('#id_APBmag').attr('readonly', true);
                $('#id_APVmag').attr('readonly', true);
                $('#id_APGmag').attr('readonly', true);
                $('#id_APRmag').attr('readonly', true);
                $('#id_APImag').attr('readonly', true);
                $('#id_APBmagerr').attr('readonly', true);
                $('#id_APVmagerr').attr('readonly', true);
                $('#id_APGmagerr').attr('readonly', true);
                $('#id_APRmagerr').attr('readonly', true);
                $('#id_APImagerr').attr('readonly', true);
                $('#id_SDSSUmag').attr('readonly', true);
                $('#id_SDSSGmag').attr('readonly', true);
                $('#id_SDSSRmag').attr('readonly', true);
                $('#id_SDSSImag').attr('readonly', true);
                $('#id_SDSSZmag').attr('readonly', true);
                $('#id_SDSSUmagerr').attr('readonly', true);
                $('#id_SDSSGmagerr').attr('readonly', true);
                $('#id_SDSSRmagerr').attr('readonly', true);
                $('#id_SDSSImagerr').attr('readonly', true);
                $('#id_SDSSZmagerr').attr('readonly', true);
                $('#id_PANGmag').attr('readonly', true);
                $('#id_PANRmag').attr('readonly', true);
                $('#id_PANImag').attr('readonly', true);
                $('#id_PANZmag').attr('readonly', true);
                $('#id_PANYmag').attr('readonly', true);
                $('#id_PANGmagerr').attr('readonly', true);
                $('#id_PANRmagerr').attr('readonly', true);
                $('#id_PANImagerr').attr('readonly', true);
                $('#id_PANZmagerr').attr('readonly', true);
                $('#id_PANYmagerr').attr('readonly', true);
                $('#id_tags').attr('readonly', true);
                $('#id_instrument').attr('readonly', true);
                $('#id_instrument').addClass('gray');
                $("td[id='label']").addClass('gray');
            } else {
                $('#id_ra').removeAttr('disabled');
                $('#id_dec').removeAttr('disabled');
                $('#id_sp_type').removeAttr('disabled');
                $('#id_classification_type').removeAttr('disabled');
                $('#id_parallax').removeAttr('disabled');
                $('#id_parallax_error').removeAttr('disabled');
                $('#id_pmra_x').removeAttr('disabled');
                $('#id_pmra_error').removeAttr('disabled');
                $('#id_pmdec_x').removeAttr('disabled');
                $('#id_pmdec_error').removeAttr('disabled');
                $('#id_phot_g_mean_mag').removeAttr('disabled');
                $('#id_phot_bp_mean_mag').removeAttr('disabled');
                $('#id_phot_rp_mean_mag').removeAttr('disabled');
                $('#id_phot_g_mean_magerr').removeAttr('disabled');
                $('#id_phot_bp_mean_magerr').removeAttr('disabled');
                $('#id_phot_rp_mean_magerr').removeAttr('disabled');
                $('#id_Jmag').removeAttr('disabled');
                $('#id_Hmag').removeAttr('disabled');
                $('#id_Kmag').removeAttr('disabled');
                $('#id_Jmagerr').removeAttr('disabled');
                $('#id_Hmagerr').removeAttr('disabled');
                $('#id_Kmagerr').removeAttr('disabled');
                $('#id_W1mag').removeAttr('disabled');
                $('#id_W2mag').removeAttr('disabled');
                $('#id_W3mag').removeAttr('disabled');
                $('#id_W4mag').removeAttr('disabled');
                $('#id_W1magerr').removeAttr('disabled');
                $('#id_W2magerr').removeAttr('disabled');
                $('#id_W3magerr').removeAttr('disabled');
                $('#id_W4magerr').removeAttr('disabled');
                $('#id_FUV').removeAttr('disabled');
                $('#id_NUV').removeAttr('disabled');
                $('#id_FUVerr').removeAttr('disabled');
                $('#id_NUVerr').removeAttr('disabled');
                $('#id_Umag').removeAttr('disabled');
                $('#id_Vmag').removeAttr('disabled');
                $('#id_Gmag').removeAttr('disabled');
                $('#id_Rmag').removeAttr('disabled');
                $('#id_Imag').removeAttr('disabled');
                $('#id_Zmag').removeAttr('disabled');
                $('#id_Umagerr').removeAttr('disabled');
                $('#id_Vmagerr').removeAttr('disabled');
                $('#id_Gmagerr').removeAttr('disabled');
                $('#id_Rmagerr').removeAttr('disabled');
                $('#id_Imagerr').removeAttr('disabled');
                $('#id_Zmagerr').removeAttr('disabled');
                $('#id_APBmag').removeAttr('disabled');
                $('#id_APVmag').removeAttr('disabled');
                $('#id_APGmag').removeAttr('disabled');
                $('#id_APRmag').removeAttr('disabled');
                $('#id_APImag').removeAttr('disabled');
                $('#id_APBmagerr').removeAttr('disabled');
                $('#id_APVmagerr').removeAttr('disabled');
                $('#id_APGmagerr').removeAttr('disabled');
                $('#id_APRmagerr').removeAttr('disabled');
                $('#id_APImagerr').removeAttr('disabled');
                $('#id_SDSSUmag').removeAttr('disabled');
                $('#id_SDSSGmag').removeAttr('disabled');
                $('#id_SDSSRmag').removeAttr('disabled');
                $('#id_SDSSImag').removeAttr('disabled');
                $('#id_SDSSZmag').removeAttr('disabled');
                $('#id_SDSSUmagerr').removeAttr('disabled');
                $('#id_SDSSGmagerr').removeAttr('disabled');
                $('#id_SDSSRmagerr').removeAttr('disabled');
                $('#id_SDSSImagerr').removeAttr('disabled');
                $('#id_SDSSZmagerr').removeAttr('disabled');
                $('#id_PANGmag').removeAttr('disabled');
                $('#id_PANRmag').removeAttr('disabled');
                $('#id_PANImag').removeAttr('disabled');
                $('#id_PANZmag').removeAttr('disabled');
                $('#id_PANYmag').removeAttr('disabled');
                $('#id_PANGmagerr').removeAttr('disabled');
                $('#id_PANRmagerr').removeAttr('disabled');
                $('#id_PANImagerr').removeAttr('disabled');
                $('#id_PANZmagerr').removeAttr('disabled');
                $('#id_PANYmagerr').removeAttr('disabled');
                $('#id_tags').removeAttr('disabled');
                $('#id_instrument').removeAttr('disabled');
                $("td[id='label']").removeClass('gray');
            }
        });

    // Adjust nav bar highlight
    adjust_nav_bar_active("#system_dropdown")
});


// Table filter functionality

function get_filter_keywords(d) {

    var selected_class = $("#classification_options input:checked").map(function () {
        return this.value;
    }).get();
    var selected_status = $("#status_options input:checked").map(function () {
        return this.value;
    }).get();
    var selected_tags = $("#tag_filter_options input:checked").map(function () {
        return parseInt(this.value);
    }).get();

    d = $.extend({}, d, {
        "project": $('#project-pk').attr('project'),
        "name": $('#filter_name').val(),
        "coordinates": $('#filter_co').val(),
        "classification": $('#filter_class').val(),
        "ra": $('#filter_ra').val(),
        "dec": $('#filter_dec').val(),
        "status": selected_status[0],
        "tags": selected_tags[0],

    });

//     if ($('#filter_ra').val() != '') {
//         d = $.extend({}, d, {
//             "ra_min": parseFloat($('#filter_ra').val().split(':')[0]) / 24 * 360 || 0,
//             "ra_max": parseFloat($('#filter_ra').val().split(':')[1]) / 24 * 360 || 360,
//         });
//     }

//     if ($('#filter_dec').val() != '') {
//         var min = parseFloat($('#filter_dec').val().split(':')[0]);
//         var max = parseFloat($('#filter_dec').val().split(':')[1]);
//
//         if (min == NaN) {
//             min = -90
//         }
//         if (max == NaN) {
//             max = 90
//         }
//
//         d = $.extend({}, d, {
//             "dec_min": min,
//             "dec_max": max,
//         });
//     }

    if ($('#filter_mag').val() != '') {
        d = $.extend({}, d, {
            "mag_min": parseFloat($('#filter_mag').val().split(':')[0]) || '',
            "mag_max": parseFloat($('#filter_mag').val().split(':')[1]) || '',
        });
    }

    if ($('#filter_nspec').val() != '') {
        d = $.extend({}, d, {
            "nspec_min": parseFloat($('#filter_nspec').val().split(':')[0]) || '',
            "nspec_max": parseFloat($('#filter_nspec').val().split(':')[1]) || '',
        });
    }

    if ($('#filter_nphot').val() != '') {
        d = $.extend({}, d, {
            "nphot_min": parseFloat($('#filter_nphot').val().split(':')[0]) || '',
            "nphot_max": parseFloat($('#filter_nphot').val().split(':')[1]) || '',
        });
    }

    if ($('#filter_nlc').val() != '') {
        d = $.extend({}, d, {
            "nlc_min": parseFloat($('#filter_nlc').val().split(':')[0]) || '',
            "nlc_max": parseFloat($('#filter_nlc').val().split(':')[1]) || '',
        });
    }

    return d
}


// Table renderers

function selection_render(data, type, full, meta) {
    if ($(star_table.row(meta['row']).node()).hasClass('selected')) {
        return '<i class="material-icons button select" title="Select">check_box</i>';
    } else {
        return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
    }
}

function name_render(data, type, full, meta) {
    // Create a link to the detail for the star name
    return "<a href='" + full['href'] + "'>" + data + "</a>";
}

function ra_render(data, type, full, meta) {
    return full['ra_hms'];
}

function dec_render(data, type, full, meta) {
    return full['dec_dms'];
}

function dataset_render(data, type, full, meta) {
    // Render the tags as a list of divs with the correct color.
    var result = ""
    var ds = data[0];
    for (i = 0; i < data.length; i++) {
        ds = data[i];
        result += "<div class='dataset' style='background-color:" + ds.color + "' title='" + ds.name + "'>" + "<a href='" + ds.href + "'>" + ds.name.charAt(0) + "</a></div>";
    }
    return result;
}

function tag_render(data, type, full, meta) {
    // Render the tags as a list of divs with the correct color.
    var result = ""
    var tag = data[0];
    for (i = 0; i < data.length; i++) {
        tag = data[i];
        result += "<div class='small-tag' style='border-color:" + tag.color + "' title='" + tag.description + "'>" + tag.name + "</div>";
    }
    return result;
}

function nobs_render(data, type, full, meta) {
    return full['nphot'] + " / " + full['nspec'] + " / " + full['nlc'];
}

function classification_render(data, type, full, meta) {
    // add the classification type to the table
    return "<span class='classification-" + full['classification_type'] +
        "' title='" + full['classification_type_display'] + "'>" +
        data + " </span>"

//    return "<span title='"+full['classification_type_display']+"'>"+data+"</span>";
}

function status_render(data, type, full, meta) {
    return '<i class="material-icons status-icon ' + data + '" title="' +
        full['observing_status_display'] + '"></i>'
}


// Selection and Deselection of rows

function select_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box')
    $(row.node()).addClass('selected');
    if (star_table.rows('.selected').data().length < star_table.rows().data().length) {
        $('#select-all').text('indeterminate_check_box');
    } else {
        $('#select-all').text('check_box');
    }
    $('#tag-button').removeClass("disabled");
    $('#status-button').removeClass("disabled");
    $('#delete-button').removeClass("disabled");
    $('#tospectra-button').removeClass("disabled");
    $('#tolightcurve-button').removeClass("disabled");
}

function deselect_row(row) {
    $(row.node()).find("i[class*=select]").text('check_box_outline_blank')
    $(row.node()).removeClass('selected');
    if (star_table.rows('.selected').data().length === 0) {
        $('#select-all').text('check_box_outline_blank');
        $('#tag-button').addClass("disabled");
        $('#status-button').addClass("disabled");
        $('#delete-button').addClass("disabled");
        $('#tospectra-button').addClass("disabled");
        $('#tolightcurve-button').addClass("disabled");
    } else {
        $('#select-all').text('indeterminate_check_box');
    }
}

// Edit status and tags functionality

function load_tags() {
    //   Clear tag options of the add-system form
    $("#id_tags").empty();

    //   Load all tags and add them to the window
    $.ajax({
        url: "/api/systems/tags/?project=" + $('#project-pk').attr('project'),
        type: "GET",
        success: function (json) {
            all_tags = json.results;

            for (var i = 0; i < all_tags.length; i++) {
                tag = all_tags[i];

                $('#tagOptions').append("<li title='" + tag['description'] +
                    "'><input name='tags' type='checkbox' value='"
                    + tag['pk'] + "' /> " + tag['name'] + "</li>");

                $('#tag_filter_options').append(
                    "<li><label><input id='id_status_" + i + "' name='tags' type='radio' value='" +
                    tag['pk'] + "' /> " + tag['name'] + "</label></li>");

                //  Add tag options to add-system form
                $('#id_tags').append('<li><label for="id_tags_' + i + '"><input id="id_tags_' + i + '" type="checkbox" name="tags" value="' + tag['pk'] + '"> ' + tag['name'].replace(/\_/g, ' ') + '</label></li>')

            }
/*
            $('#tagOptions').on('change', ':checkbox', function (event) {
                cylceTristate(event, this);
            });*/

            $('input[type=radio]').click(allow_unselect);

        },
        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
            all_tags = [];
        }
    });
}

// ------------

function openStatusEditWindow() {
    edit_status_window = $("#editStatus").dialog({
        title: "Change Status",
        buttons: {"Update": updateStatus},
        close: function () {
            edit_status_window.dialog("close");
        }
    });

    $("input[name='new-status']").prop('checked', false);
    edit_status_window.dialog("open");
}

function updateStatus() {
    var new_status = $("input[name='new-status']");
    if (new_status.filter(':checked').length == 0) {
        $('#status-error').text('You need to select a status option!');
    } else {
        $('#status-error').text('');

        star_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            updateStarStatus(this, new_status.filter(':checked').val());
        });

    }
}

function updateStarStatus(row, status) {
    $.ajax({
        url: "/api/systems/stars/" + row.data()['pk'] + '/',
        type: "PATCH",
        data: {observing_status: status},

        success: function (json) {
            edit_status_window.dialog("close");
            $(".fullwidth.dataTable").DataTable().draw('page');
        },

        error: function (xhr, errmsg, err) {
            if (xhr.status == 403) {
                $('#status-error').text('You have to be logged in to edit');
            } else {
                $('#status-error').text(xhr.status + ": " + xhr.responseText);
            }
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

// -------------

function openTagEditWindow() {
    edit_tags_window = $("#editTags").dialog({
        title: "Add/Remove Tags",
        buttons: {"Update": updateTags},
        close: function () {
            edit_tags_window.dialog("close");
        }
    });
/*
    // Reset the counts per tag
    var all_tag_counts = {}
    for (tag in all_tags) {
        all_tag_counts[all_tags[tag]['pk']] = 0
    }

    // count how many objects each tag has
    star_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        var tags = this.data()['tags'];
        for (tag in tags) {
            all_tag_counts[tags[tag]['pk']]++;
        }
    });

    // Set the checkbox states depending on the number of objects
    var selected_stars = star_table.rows('.selected').data().length
    for (tag in all_tag_counts) {
        // Standard unchecked state, no object has this tag
        $(".tristate[value='" + tag + "']").prop("checked", false);
        $(".tristate[value='" + tag + "']").prop("indeterminate", false);
        $(".tristate[value='" + tag + "']").removeClass("indeterminate");

        if (all_tag_counts[tag] == selected_stars) {
            // checked state, all objects have this tag
            $(".tristate[value='" + tag + "']").prop("checked", true);
        } else if (all_tag_counts[tag] > 0) {
            // indeterminate state, some objects have this tag
            $(".tristate[value='" + tag + "']").prop("indeterminate", true);
            $(".tristate[value='" + tag + "']").addClass("indeterminate");
        }
    }*/
    edit_tags_window.dialog("open");
}

function updateTags() {
    // Get the checked tags
    let new_tags = $("input[name='tags']").filter(':checked');
    new_tags = new_tags.map(
        function () { return parseInt(this.value); }
        ).get()
/*
    // Get the checked and indeterminate tags
    var checked_tags = $(".tristate:checked:not(.indeterminate)").map(
        function () {
            return parseInt(this.value);
        }).get();
    var indeterminate_tags = $(".tristate.indeterminate").map(
        function () {
            return parseInt(this.value);
        }).get();*/

    // Update the tags for each selected star
    star_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        // var new_tags = checked_tags;
        // var current_tags = this.data()['tags'].map(function (x) {
        //     return x.pk;
        // });
        //
        // for (tag in indeterminate_tags) {
        //     if (current_tags.indexOf(indeterminate_tags[tag]) > -1) {
        //         new_tags.push(indeterminate_tags[tag])
        //     }
        // }
        update_star_tags(this, new_tags);
    });

}

function update_star_tags(row, new_tags) {
    var star_pk = row.data()['pk']
//    console.log(row.data());
    $.ajax({
        url: "/api/systems/stars/" + star_pk + '/',
        type: "PATCH",
        contentType: "application/json; charset=utf-8",

        data: JSON.stringify({"tag_ids": new_tags}),

        success: function (json) {
            // update the table and close the edit window
            $(".fullwidth.dataTable").DataTable().draw('page');
            edit_tags_window.dialog("close");
        },

        error: function (xhr, errmsg, err) {
            if (xhr.status == 403) {
                $('#tag-error').text('You have to be logged in to edit');
            } else {
                $('#tag-error').text(xhr.status + ": " + xhr.responseText);
            }
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

// -----

function deleteSystems() {
    if (confirm('Are you sure you want to delete these Systems? This can NOT be undone!') === true) {
        var rows = [];
        // get list of files
        star_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            var row = this;
            rows.push(row);
        });
        if ($('#progress-bar').length === 0) {
            $(".toolbar").append('<progress id="progress-bar" value="0" max="' + rows.length + '" class="progress-bar"></progress>')
        } else {
            $("#progress-bar").prop("max", rows.length)
            $("#progress-bar").val(0)
        }
        let n = 0;
        //   Set Promise -> evaluates to a resolved Promise
        let p = $.when()
        $.each(rows, function (index, row) {
            let pk = row.data()["pk"];
            //    Promise chaining using .then() + async function definition to allow
            //                                  the use of await
            p = p.then(async function () {
                await $.ajax({
                    url: "/api/systems/stars/" + pk + '/',
                    type: "DELETE",
                    success: function (json) {
                        n += 1;
                        star_table.row(row).remove().draw('full-hold');
                        $('#select-all').text('check_box_outline_blank');
                        $('#tag-button').addClass("disabled");
                        $('#status-button').addClass("disabled");
                        $('#delete-button').addClass("disabled");
                        $('#tospectra-button').addClass("disabled");
                        $('#tolightcurve-button').addClass("disabled");
                        $('#progress-bar').val(n)
                    },
                    error: function (xhr, errmsg, err) {
                        n += 1;
                        $('#progress-bar').val(n)
                        if (xhr.status === 403) {
                            alert('You have to be logged in to delete this system.');
                        } else {
                            alert(xhr.status + ": " + xhr.responseText);
                        }
                        console.log(xhr.status + ": " + xhr.responseText);
                    },
                });
            });
        })
    }
}

// -------------


function openAddSystemsWindow() {
    add_systems_window = $("#addSystems").dialog({
        autoOpen: false,
        title: "Add System(s)",
        close: function () {
            add_systems_window.dialog("close");
        },
    });

    add_systems_window.dialog("open");
}


// ----------------------------------------------------------------------
/*
// Tristate checkbox functionality
function cylceTristate(event, checkbox) {
    checkbox = $(checkbox);
    // Add extra indeterminate state inbetween unchecked and checked
    if (checkbox.prop("checked") & !checkbox.hasClass("indeterminate")) {
        checkbox.prop("checked", false);
        checkbox.prop("indeterminate", true);
        checkbox.addClass("indeterminate");
    } else if (checkbox.prop("checked") & checkbox.hasClass("indeterminate")) {
        checkbox.prop("indeterminate", false);
        checkbox.removeClass("indeterminate");
    }
}*/


// Allow unchecking of radio buttons in the filter window
$('input[type=radio]').click(allow_unselect);

function allow_unselect(e) {
    if (e.ctrlKey) {
        $(this).prop('checked', false);
    }
}

function Toggleeditdropdown() {
    $("#editdropdown").toggle();
    let otherdd = $("#carryoverdropdown");
    if (otherdd.is(":visible")) {
        otherdd.toggle();
    }
}

function Togglecarryoverdropdown() {
    $("#carryoverdropdown").toggle("show");
    let otherdd = $("#editdropdown")
    if (otherdd.is(":visible")) {
        otherdd.toggle("show");
    }
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

function toSpecta() {
    let pks = []
    star_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        let pk = this.data()["pk"];
        pks.push(pk);
    });
    sessionStorage.setItem("selectedpks", pks);
    window.location.href = "../../observations/spectra";
}

function toLightcurve() {
    let pks = []
    star_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        let pk = this.data()["pk"];
        pks.push(pk);
    });
    sessionStorage.setItem("selectedpks", pks);
    window.location.href = "../../observations/lightcurves";
}
