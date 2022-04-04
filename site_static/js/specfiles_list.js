var specfile_table = null;

$(document).ready(function () {

    // Table functionality
    specfile_table = $('#specfiletable').DataTable({
        autoWidth: false,
        serverSide: true,
        ajax: {
            url: '/api/observations/specfiles/?format=datatables',
            data: get_filter_keywords,
        },
        searching: false,
        orderMulti: false, //Can only order on one column at a time
        order: [0],
        columns: [
            {data: 'hjd'},
            {data: 'instrument'},
            {data: 'filetype'},
            {data: 'filename', orderable: false},
            {data: 'added_on'},
            {data: 'star', orderable: false, render: star_render},
            {data: 'spectrum', render: processed_render},
            {
                data: 'pk', render: action_render, width: '100',
                className: 'dt-center', visible: user_authenticated, orderable: false
            },
        ],
        paging: true,
        pageLength: 20,
        lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
        scrollY: $(window).height() - $('header').outerHeight(true) - $('.upload').outerHeight(true) - $('#messages').outerHeight(true) - 186,
        scrollCollapse: true,
    });

    // Event listener to the two range filtering inputs to redraw on input
    $('#filter-form').submit(function (event) {
        event.preventDefault();
        specfile_table.draw();
    });

    // make the filter button open the filter menu
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
    }

    // Event listeners
    $("#specfiletable").on('click', 'i[id^=process-specfile-]', function () {
        var thisrow = $(this).closest('tr');
        var data = specfile_table.row(thisrow).data();
        processSpecfile(thisrow, data);
    });
    $("#specfiletable").on('click', 'i[id^=delete-specfile-]', function () {
        var thisrow = $(this).closest('tr');
        var data = specfile_table.row(thisrow).data();
        deleteSpecfile(thisrow, data);
    });

    //  Adjust form drop dropdown content - First read System drop down
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

            });
        });
    });
});


// Table filter functionality

function get_filter_keywords(d) {

    d = $.extend({}, d, {
        "project": $('#project-pk').attr('project'),
        "target": $('#filter_target').val(),
        "instrument": $('#filter_instrument').val(),
        "filename": $('#filter_filename').val(),
        "filetype": $('#filter_filetype').val(),
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

    return d
}


//  Table renderers

function star_render(data, type, full, meta) {
    let systems = [];
    for (let key in data) {
        if (data.hasOwnProperty(key)) {
            let value = data[key];
            systems.push("<a href='" + value + "' > " + key + "</a>");
        }
    }

    return systems
}

function processed_render(data, type, full, meta) {
    if (data) {
        return "<a href='" + data + "' >" + 'Yes' + "</a>";
    } else {
        return 'No';
    }
//       if ( data ){ return 'Yes'; } else { return 'No'; }
}

function action_render(data, type, full, meta) {
    var res = "<i class='material-icons button delete' id='delete-specfile-" + data + "'>delete</i>"
    if (!full['spectrum']) {
        res = res + "<i class='material-icons button process' id='process-specfile-" + data + "' title='Process'>build</i>"
    }
    return res
}

//  Further function
function processSpecfile(row, data) {
    $.ajax({
        url: "/api/observations/specfiles/" + data['pk'] + '/process/',
        type: "POST",
        success: function (json) {
            // remove the row from the table
            specfile_table.row(row).data(json).draw('full-hold');
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

function deleteSpecfile(row, data) {
    if (confirm('Are you sure you want to remove this spectrum file?') == true) {
        $.ajax({
            url: "/api/observations/specfiles/" + data['pk'] + '/',
            type: "DELETE",
            success: function (json) {
                // remove the row from the table
                specfile_table.row(row).remove().draw('full-hold');
            },

            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

}
