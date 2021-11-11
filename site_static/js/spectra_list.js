
var spectra_table = null;

$(document).ready(function () {
   let columns;
   if (user_authenticated) {
//    console.log()
   columns = [
          {
            orderable:      false,
            className:      'select-control',
            data:           null,
            render: selection_render,
            width:          '10',
         },
         { data: 'hjd', render : hjd_render },
         { data: 'star', render : star_render },
         { data: 'instrument', render : instrument_render },
         { data: 'resolution', render : resolution_render },
         { data: 'airmass', render : airmass_render },
         { data: 'exptime' },
      ];
   }
   else {
   columns = [
         { data: 'hjd', render : hjd_render },
         { data: 'star', render : star_render },
         { data: 'instrument', render : instrument_render },
         { data: 'resolution', render : resolution_render },
         { data: 'airmass', render : airmass_render },
         { data: 'exptime' },
      ];
   }
   // Table functionality
   spectra_table = $('#spectratable').DataTable({
   dom: 'l<"toolbar">frtip',
   autoWidth: false,
   serverSide: true,
   ajax: {
      url: '/api/observations/spectra/?format=datatables&keep=specfiles,telescope,href',
      data: get_filter_keywords,
   },
   searching: false,
   orderMulti: false, //Can only order on one column at a time
   order: [1],
   columns: columns,
   paging: true,
   pageLength: 20,
   lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
   scrollY: $(window).height() - $('header').outerHeight(true) - 196,
   scrollCollapse: true,
   });

   // Event listener to the two range filtering inputs to redraw on input
   $('#filter-form').submit( function(event) {
      event.preventDefault();
      spectra_table.draw();
   } );

   // check and uncheck tables rows
   $('#spectratable tbody').on( 'click', 'td.select-control', function () {
      var tr = $(this).closest('tr');
      var row = spectra_table.row( tr );
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

         spectra_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            deselect_row(this); // Open this row
         });
      } else {
         // close all rows
         $(this).text('check_box');

         spectra_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
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
      if (text === "filter_list"){
            $('#filter-dashboard-button').text("close");
      } else {
            $('#filter-dashboard-button').text("filter_list");
      }
   }

  //Add toolbar to table
   if (user_authenticated){
      $("div.toolbar").html(
          "<input id='dl-button'  class='tb-button' value='Download Spectra' type='button' disabled>" +
          '<progress id="progress-bar" value="0" max="100" class="progress-bar"></progress>' +
          "<input id='delete-button'  class='tb-button' value='Delete Spectrum' type='button' disabled>" +
          "<p class='hide' id='result'></p>"
      );
      $("#dl-button").click( DlSpectra );
      $("#delete-button").click( delete_all_selected_specfiles );
   }
});



// Table filter functionality

function get_filter_keywords( d ) {

   d = $.extend( {}, d, {
      "project": $('#project-pk').attr('project'),
      "target": $('#filter_target').val(),
      "telescope": $('#filter_telescope').val(),
      "instrument": $('#filter_instrument').val(),
   } );

   if ($('#filter_hjd').val() !== '') {
      d = $.extend( {}, d, {
         "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] | 0 ),
         "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] | 1000000000),
      } );
   }

   if ($('#filter_exptime').val() !== '') {
      d = $.extend( {}, d, {
         "exptime_min": parseFloat( $('#filter_exptime').val().split(':')[0] | 0 ),
         "exptime_max": parseFloat( $('#filter_exptime').val().split(':')[1] | 1000000000),
      } );
   }

   if ($('#id_fluxcal_yes').is(':checked')) {
      d = $.extend( {}, d, {
         "fluxcal": true
      } );
   }
   if ($('#id_fluxcal_no').is(':checked')) {
      d = $.extend( {}, d, {
         "fluxcal": false
      } );
   }

   return d
}

// Table renderers
function selection_render( data, type, full, meta ) {
   if ( $(spectra_table.row(meta['row']).node()).hasClass('selected') ){
      return '<i class="material-icons button select" title="Select">check_box</i>';
   } else {
      return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
   }
}


function hjd_render( data, type, full, meta ) {
   return "<a href='" + full['href'] + "' >" + data + "</a>"
}

function star_render( data, type, full, meta ) {
   try {
      return "<a href='" + data['href'] + "' >" + data['name'] + "</a>" + " (" + data['ra'].toFixed(5) + " " + data['dec'].toFixed(5) + ")"
   } catch(err) {
      return ''
   }
}

function instrument_render( data, type, full, meta ) {
   return data + " @ " + full['telescope']
}

function airmass_render( data, type, full, meta ){
   if (data === -1){
      return "-"
   }
   else {
      return data
   }
}

function resolution_render( data, type, full, meta ) {
   if (data === -1){
      return "-"
   }
   else {
      return data
   }
}

function delete_all_selected_specfiles(){
    if (confirm('Are you sure you want to delete this spectrum? This can NOT be undone!')===true){
        let rows = [];
        //   Get list of selected spectra
        spectra_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            rows.push(this);
        });
        // Loop over selected spectra
        $.each(rows, function (index, row) {
            //  Loop over all spec files
            $.each(row.data()["specfiles"], function(ind) {
                let pk = row.data()["specfiles"][ind]['pk'];
                //  Ajax call to remove spec files
                $.ajax({
                    url : "/api/observations/specfiles/"+pk+'/',
                    type : "DELETE",
                    success : function(json) {
                        //  Remove the whole spectrum from table
                        spectra_table.row(row).remove().draw('full-hold');
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
        })
    }
}


// Selection and Deselection of rows

function select_row(row) {
   $(row.node()).find("i[class*=select]").text('check_box');
   $(row.node()).addClass('selected');
   if ( spectra_table.rows('.selected').data().length < spectra_table.rows().data().length ) {
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
   if ( spectra_table.rows('.selected').data().length === 0 ) {
      $('#select-all').text('check_box_outline_blank');
      $('#dl-button').prop('disabled', true);
      $('#rm-button').prop('disabled', true);
      $('#delete-button').prop('disabled', true);
   } else {
      $('#select-all').text('indeterminate_check_box');
   }
}

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

function DlSpectra() {
   //   Prepare file list
   let spfilelist = [];
   //   Get list of selected spectra
   spectra_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        let specfiles = this.data()["specfiles"]
        //  Loop over all associated files
        $.each(specfiles, function(ind) {
            //  Identify files
            let sfilepk = specfiles[ind]['pk'];

            //    Get file path
            $.getJSON("/api/observations/specfiles/"+sfilepk+"/path/", function(path) {
                //    Add to file list
                spfilelist.push(path);
            });
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
            const getPromises = spfilelist.map (async path => {
                let file = path.split('/')[3];
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
                saveAs(blob, "Spectra"+timecode+".zip");
                //  Reset download button
                showProgress("Download Spectra");
            }, function (e) {
                showError(e);
            });


      });
   });
}
