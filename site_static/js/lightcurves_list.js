
var lightcurve_table = null;

$(document).ready(function () {
   let columns;
   if(user_authenticated){
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
      { data: 'exptime' },
      { data: 'cadence' },
      { data: 'pk', render: action_render, width: '100',
        className: 'dt-center', visible: user_authenticated, orderable: false},
   ]}
   else{
   columns = [
      { data: 'hjd', render : hjd_render },
      { data: 'star', render : star_render },
      { data: 'instrument', render : instrument_render },
      { data: 'exptime' },
      { data: 'cadence' },
      { data: 'pk', render: action_render, width: '100',
        className: 'dt-center', visible: user_authenticated, orderable: false},
   ]}
   // Table functionality
   lightcurve_table = $('#lightcurvetable').DataTable({
   dom: 'l<"toolbar">frtip',
   autoWidth: false,
   serverSide: true,
   ajax: {
      url: '/api/observations/lightcurves/?format=datatables&keep=telescope,href',
      data: get_filter_keywords,
   },
   searching: false,
   orderMulti: false, //Can only order on one column at a time
   order: [1],
   columns : columns,
   paging: true,
   pageLength: 20,
   lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
   scrollY: $(window).height() - $('header').outerHeight(true) - 196,
   scrollCollapse: true,
   });
    
   // check and uncheck tables rows
   $('#lightcurvetable tbody').on( 'click', 'td.select-control', function () {
      var tr = $(this).closest('tr');
      var row = lightcurve_table.row( tr );
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

         lightcurve_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            deselect_row(this); // Open this row
         });
      } else {
         // close all rows
         $(this).text('check_box');

         lightcurve_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            select_row(this); // close the row
         });
      }
   });
   
   // Event listener to the two range filtering inputs to redraw on input
   $('#filter-form').submit( function(event) {
      event.preventDefault();
      lightcurve_table.draw();
   } );

   // make the filter button open the filter menu
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
   }


   // Delete lightcurve completely event listener
   $("#lightcurvetable").on('click', 'i[id^=delete-lightcurve-]', function(){
      var thisrow = $(this).closest('tr');
      var data = lightcurve_table.row(thisrow).data();
      delete_lightcurve(thisrow, data);
   });

   if (user_authenticated){
      $("div.toolbar").html(
          "<input id='dl-button'  class='tb-button' value='Download Lightcurve(s)' type='button' disabled>" +
          "<input id='delete-button'  class='tb-button' value='Delete Lightcurve(s)' type='button' disabled>" +
          '<progress id="progress-bar" value="0" max="100" class="progress-bar"></progress>'
      );
      $("#dl-button").click( download_lightcurves );
      $("#delete-button").click( delete_lightcurves );
   }
   $('#lightcurvetable_length').change(function() {
       lightcurve_table.rows().every( function (rowIdx, tableLoop, rowLoop) {
           deselect_row(this);
        });
   });

   //   Reset check boxes when switching to the next table page
   $('#lightcurvetable_paginate').click(function() {
       lightcurve_table.rows().every( function (rowIdx, tableLoop, rowLoop) {
           deselect_row(this);
        });
});
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
      let hjd_min = $('#filter_hjd').val().split(':')[0];
      if (hjd_min === '') {
          hjd_min = 0.;
      }
      let hjd_max = $('#filter_hjd').val().split(':')[1];
      if (hjd_max === '') {
          hjd_max = 1000000000.;
      }
      d = $.extend( {}, d, {
//          "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] | 0 ),
//          "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] | 1000000000),
         "hjd_min": parseFloat( hjd_min ),
         "hjd_max": parseFloat( hjd_max ),
      } );
   }

   if ($('#filter_exptime').val() != '') {
      d = $.extend( {}, d, {
         "exptime_min": parseFloat( $('#filter_exptime').val().split(':')[0] | 0 ),
         "exptime_max": parseFloat( $('#filter_exptime').val().split(':')[1] | 1000000000),
      } );
   }

   return d
}

// Selection and Deselection of rows

function select_row(row) {
   $(row.node()).find("i[class*=select]").text('check_box');
   $(row.node()).addClass('selected');
   if ( lightcurve_table.rows('.selected').data().length < lightcurve_table.rows().data().length ) {
      $('#select-all').text('indeterminate_check_box');
   } else {
      $('#select-all').text('check_box');
   }
    $('#dl-button').prop('disabled', false);
    $('#delete-button').prop('disabled', false);
}

function deselect_row(row) {
   $(row.node()).find("i[class*=select]").text('check_box_outline_blank');
   $(row.node()).removeClass('selected');
   if ( lightcurve_table.rows('.selected').data().length === 0 ) {
      $('#select-all').text('check_box_outline_blank');
      $('#dl-button').prop('disabled', true);
      $('#delete-button').prop('disabled', true);
   } else {
      $('#select-all').text('indeterminate_check_box');
   }
}

//  Update progress bar
function updatePercent(bar, percent) {
    bar.val(percent);
}

//  Change download button text
function showProgress(button, text) {
    button.val(text);
}

// Table renderers
function selection_render( data, type, full, meta ) {
   if ( $(lightcurve_table.row(meta['row']).node()).hasClass('selected') ){
      return '<i class="material-icons button select" title="Select">check_box</i>';
   } else {
      return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
   }
}

function hjd_render( data, type, full, meta ) {
   return "<a href='" + full['href'] + "' >" + data + "</a>"
}

function star_render( data, type, full, meta ) {
   return "<a href='" + data['href'] + "' >" + data['name'] + "</a>" + " (" + data['ra'].toFixed(5) + " " + data['dec'].toFixed(5) + ")"
}

function instrument_render( data, type, full, meta ) {
   return data + " @ " + full['telescope']
}

function action_render( data, type, full, meta ) {
   return "<i class='material-icons button delete' id='delete-lightcurve-"+data+"'>delete</i>"
}


function delete_lightcurve(row, data) {
   if (confirm('Are you sure you want to delete this light curve? This can NOT be undone.')===true){
      $.ajax({
         url : "/api/observations/lightcurves/"+data['pk']+"/",
         type : "DELETE", // http method
         success : function(json) {
            // delete the lightcurve from the table
            lightcurve_table.row(row).remove().draw('full-hold');
         },

         error : function(xhr,errmsg,err) {
               console.log(xhr.status + ": " + xhr.responseText);
         }
      });
   }
}

function delete_lightcurves() {
   if (confirm('Are you sure you want to delete these lightcuves? This can NOT be undone!')===true){
      let rows = [];
      //   Get list of selected lightcurves
      lightcurve_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
         rows.push(this);
      });

      //   Set Promise -> evaluates to a resolved Promise
      let p = $.when()

      // Loop over selected lightcurves
      $.each(rows, function (index, row) {
         let pk = row.data()['pk'];

         //    Promise chaining using .then() + async function definition
         //    to allow the use of await
         p = p.then( async function () {
             await $.ajax({
                 url : "/api/observations/lightcurves/"+pk+'/',
                 type : "DELETE",
                 success : function(json) {
                     //  Remove the lightcurve from table
                     lightcurve_table.row(row).remove().draw('full-hold');
                 },
                 error : function(xhr,errmsg,err) {
                     if (xhr.status === 403){
                         alert('You have to be logged in to delete this lightcurve.');
                     }else{
                         alert(xhr.status + ": " + xhr.responseText);
                     }
                     console.log(xhr.status + ": " + xhr.responseText);
                 }
             });
         });
      })

      //   Reset check boxes
      lightcurve_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
         deselect_row(this);
      });
      }
}

function download_lightcurves() {
   //   Prevent impatient users from clicking again.
   $('#dl-button').prop('disabled', true);
   showProgress($("#dl-button") ,"Be Patient...");
   //   Prepare file list
   let lcfilelist = [];
   //   Get list of selected lightcurves
   lightcurve_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
        let lcfilepk = this.data()["pk"];
        //    Get file path
        $.getJSON(
            "/api/observations/lightcurves/"+lcfilepk+"/path/",
            function(path) {
                //    Add to file list
                lcfilelist.push(path);
        });
   });
   console.log(lcfilelist);

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
            const getPromises = lcfilelist.map (async path => {
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
                showProgress($("#dl-button") ,msg);
                updatePercent($("#progress-bar"), metadata.percent|0);
            })
            .then(function callback(blob) {
                //  Save zip file
                saveAs(blob, "Lightcurves_"+timecode+".zip");
                //  Reset download button
                $('#dl-button').prop('disabled', false);
                showProgress($("#dl-button") ,"Download Lightcurves");
            }, function (e) {
                showError(e);
            });
      });
   });
}