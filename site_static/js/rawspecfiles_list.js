
var rawspecfile_table = null;

$(document).ready(function () {
   let columns;
   if (user_authenticated) {
   columns = [
        {
            orderable:      false,
            className:      'select-control',
            data:           null,
            render:         selection_render,
            width:          '10',
         },
         { data: 'hjd' },
         { data: 'instrument' },
         { data: 'filetype' },
         { data: 'exptime' },
         { data: 'filename' },
         { data: 'added_on' },
         { data: 'stars', orderable: false, render: stars_render },
//          { data: 'specfiles', orderable: false, render: processed_render },
      ];
   }
   else {
   columns = [
         { data: 'hjd' },
         { data: 'instrument' },
         { data: 'filetype' },
         { data: 'exptime' },
         { data: 'filename' },
         { data: 'added_on' },
         { data: 'stars', orderable: false, render: stars_render },
//          { data: 'specfiles', orderable: false, render: processed_render },
      ];
   };

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
   $('#filter-form').submit( function(event) {
      event.preventDefault();
      rawspecfile_table.draw();
   } );

   // Check and uncheck tables rows
   $('#rawspecfiletable tbody').on( 'click', 'td.select-control', function () {
      var tr = $(this).closest('tr');
      var row = rawspecfile_table.row( tr );
      if ( $(row.node()).hasClass('selected') ) {
         deselect_row(row);
      } else {
         select_row(row);
      }
   } );

   $('#select-all').on('click', function () {
      if ( $(this).text() === 'check_box' || $(this).text() === 'indeterminate_check_box') {
         // deselect all
         $(this).text('check_box_outline_blank');

         rawspecfile_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            deselect_row(this); // Open this row
         });
      } else {
         // close all rows
         $(this).text('check_box');

         rawspecfile_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
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
      if (text == "filter_list"){
            $('#filter-dashboard-button').text("close");
      } else {
            $('#filter-dashboard-button').text("filter_list");
      }
   };

   // Add toolbar to table
   if (user_authenticated){
      $("div.toolbar").html(
          "<input id='dl-button'  class='tb-button' value='Download raw data' type='button' disabled>" +
          '<progress id="progress-bar" value="0" max="100" class="progress-bar"></progress>' +
          "<input id='delete-button'  class='tb-button' value='Delete raw data' type='button' disabled>" +
          "<p class='hide' id='result'></p>"
      );
      $("#dl-button").click( download_rawfiles );
      $("#delete-button").click( delete_all_selected_rawspecfiles );
   }

    //  Adjust form drop dropdown content - First read System drop down
    $("#id_system").change(function() {
        //  Find system pk/ID
        let pk = $(this).val();
        if (pk != '') {
            //  Clear Specfile drop down
            clear_drop_down();

            //  Get Specfile info as JASON
            $.getJSON("/api/systems/stars/"+pk+'/specfiles/', function(data){
                //  Refilling Specfile drop down
                for (let key in data){
                    if (data.hasOwnProperty(key)){
                        let value=data[key];
                        $("#id_specfile").append("<option value = \"" + key + "\">" + value + "</option>");
                    }
                };
            });
        } else {
            //  Clear Specfile drop down
            clear_drop_down();
        }
    });

    //   Reset check boxes when changing number of displayed objects in table
    $('#rawspecfiletable_length').change(function() {
        rawspecfile_table.rows().every( function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
         });
    });

    //   Reset check boxes when switching to the next table page
    $('#rawspecfiletable_paginate').click(function() {
        rawspecfile_table.rows().every( function (rowIdx, tableLoop, rowLoop) {
            deselect_row(this);
         });
    });
});

//  Clear Specfile drop down
function clear_drop_down(){
    document.getElementById("id_specfile").length = 0;
    $("#id_specfile").val([]);
//     $("#id_specfile").append("<option value=\"\" selected=\"selected\">---------</option>");
    $("#id_specfile").append("<option value=\"\" selected=\"selected\">JD@Instrument - Filetype</option>");
}


// Table filter functionality

function get_filter_keywords( d ) {

   d = $.extend( {}, d, {
      "project": $('#project-pk').attr('project'),
      "instrument": $('#filter_instrument').val(),
      "filename": $('#filter_filename').val(),
      "filetype": $('#filter_filetype').val(),
      "systems": $('#filter_systems').val(),
   } );

   if ($('#filter_hjd').val() != '') {
      d = $.extend( {}, d, {
//          "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] | 0 ),
//          "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] | 1000000000),
         "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] ),
         "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] ),
      } );
   };

   if ($('#filter_expo_time').val() != '') {
      d = $.extend( {}, d, {
         "expo_min": parseFloat( $('#filter_expo_time').val().split(':')[0] ),
         "expo_max": parseFloat( $('#filter_expo_time').val().split(':')[1] ),
      } );
   };

   return d
}


// Table renderers

function selection_render( data, type, full, meta ) {
   if ( $(rawspecfile_table.row(meta['row']).node()).hasClass('selected') ){
      return '<i class="material-icons button select" title="Select">check_box</i>';
   } else {
      return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
   }
}

function stars_render( data, type, full, meta ) {
    let systems = [];
    for(let key in data){
        if (data.hasOwnProperty(key)){
            let value=data[key];
            systems.push("<a href='" + value + "' > " + key + "</a>");
        }
    }
    return systems
}


// Selection and Deselection of rows

function select_row(row) {
   $(row.node()).find("i[class*=select]").text('check_box');
   $(row.node()).addClass('selected');
   if ( rawspecfile_table.rows('.selected').data().length < rawspecfile_table.rows().data().length ) {
      $('#select-all').text('indeterminate_check_box');
   } else {
      $('#select-all').text('check_box');
   }
    $('#dl-button').prop('disabled', false);
    $('#rm-button').prop('disabled', false);
    $('#delete-button').prop('disabled', false);
}

function deselect_row(row) {
   $(row.node()).find("i[class*=select]").text('check_box_outline_blank');
   $(row.node()).removeClass('selected');
   if ( rawspecfile_table.rows('.selected').data().length === 0 ) {
      $('#select-all').text('check_box_outline_blank');
      $('#dl-button').prop('disabled', true);
      $('#rm-button').prop('disabled', true);
      $('#delete-button').prop('disabled', true);
   } else {
      $('#select-all').text('indeterminate_check_box');
   }
}

//  Delete raw data
function delete_all_selected_rawspecfiles(){
    if (confirm('Are you sure you want to delete this spectrum? This can NOT be undone!')===true){
        let rows = [];
        //   Get list of selected files
        rawspecfile_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            //  Determine ID/PK
            let pk = this.data()['pk'];
            //  Ajax call to remove spec files
            $.ajax({
                url : "/api/observations/rawspecfiles/"+pk+'/',
                type : "DELETE",
                success : function(json) {
                    //  Remove the whole spectrum from table
                    rawspecfile_table.row(this).remove().draw('full-hold');
                },
                error : function(xhr,errmsg,err) {
                    if (xhr.status === 403){
                        alert('You have to be logged in to delete this spectrum.');
                    }else{
                        alert(xhr.status + ": " + xhr.responseText);
                    }
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        })

    //   Reset check boxes
    rawspecfile_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
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
            "/api/observations/rawspecfiles/"+pk+"/path/",
            function(path) {
                //    Add to file list
                rawlist.push(path);
            });
    });

    //   Load Filesaver and jszip libs to facilitate download
    $.getScript("/static/js/JsZip/FileSaver.js").done( function () {
        $.getScript("/static/js/JsZip/jszip.js").done( async function () {

            //  Create zip file
            let zip = new JSZip();

            //  Set time string for zip file name
            let dt  = new Date();
            let timecode = dt.getHours()+""+dt.getMinutes()+dt.getSeconds();

            //  Get file using promises so that file assembly can wait until
            //  download has finished
            const getPromises = rawlist.map (async path => {
                let file = path.split('/').slice(-1);
                return new Promise(function(resolve, reject) {
                    $.get(path)
                    .done(function(data) {
                        resolve([file, data]);
                    })
                    .fail(function() {
                        reject("ERROR: File not found");
                    })
                });
            });

            //  Fill zip file
            for (const getPromise of getPromises) {
                try {
                    const content = await getPromise;
                    zip.file(content[0], content[1]);
                }
                catch (err) {
                    showError(err);
                    return
                }
            }

            //  Generate zip file
            zip.generateAsync({type: "blob"}, function updateCallback(metadata) {
                //  Update download progress
                let msg = "            " + metadata.percent.toFixed(2) + " %           ";
                showProgress(msg);
                updatePercent(metadata.percent|0);
            })
            .then(function callback(blob) {
                //  Save zip file
                saveAs(blob, "Raw_data_"+timecode+".zip");
                //  Reset download button
                showProgress("Download raw data");
            }, function (e) {
                showError(e);
            });


        });
    });
}
