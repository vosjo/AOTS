
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
      ];
   };

   // Table functionality
   rawspecfile_table = $('#rawspecfiletable').DataTable({
   dom: 'l<"toolbar">frtip',
   autoWidth: false,
   serverSide: true,
   ajax: {
      url: '/api/observations/rawspecfiles/?format=datatables',
      data: get_filter_keywords,
   },
   searching: false,
   orderMulti: false, //Can only order on one column at a time
   order: [1],
   columns: columns,
//    columns: [
//       { data: 'hjd' },
//       { data: 'instrument' },
//       { data: 'filetype' },
//       { data: 'exptime' },
//       { data: 'filename' },
//       { data: 'added_on' },
//       { data: 'stars', orderable: false, render: stars_render },
//       { data: 'pk', render: action_render, width: '100',
//         className: 'dt-center', visible: user_authenticated, orderable: false},
//    ],
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
      $("#dl-button").click( DlSpectra );
      $("#delete-button").click( delete_all_selected_rawspecfiles );
   }

//    // Event listeners
//    $("#rawspecfiletable").on('click', 'i[id^=process-specfile-]', function() {
//       var thisrow = $(this).closest('tr');
//       var data = rawspecfile_table.row(thisrow).data();
//       processRawSpecfile(thisrow, data);
//    });
//    $("#rawspecfiletable").on('click', 'i[id^=delete-specfile-]', function() {
//       var thisrow = $(this).closest('tr');
//       var data = rawspecfile_table.row(thisrow).data();
//       deleteRawSpecfile(thisrow, data);
//    });

});

// Table filter functionality

function get_filter_keywords( d ) {

   d = $.extend( {}, d, {
      "project": $('#project-pk').attr('project'),
//       "target": $('#filter_target').val(),
      "instrument": $('#filter_instrument').val(),
   } );

   if ($('#filter_hjd').val() != '') {
      d = $.extend( {}, d, {
         "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] | 0 ),
         "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] | 1000000000),
      } );
   }

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
//     console.log(data);
//     let obj = JSON.parse(data);
//     let obj = data;
    let systems = [];
    for(let key in data){
        if (data.hasOwnProperty(key)){
            let value=data[key];
            systems.push("<a href='" + value + "' > " + key + "</a>");
        }
//         else {
//             return '';
//         }
    }
    return systems

//    return 'Test';
//    if ( data ){
//       console.log(data);
//       return "<a href='" + data + "' >" + 'Yes' + "</a>";
//    } else {
//       return 'No';
//    }
//       if ( data ){ return 'Yes'; } else { return 'No'; }
}

// function action_render( data, type, full, meta ) {
//    var res = "<i class='material-icons button delete' id='delete-specfile-"+data+"'>delete</i>"
//    if ( !full['stars'] ) {
//       res = res + "<i class='material-icons button process' id='process-specfile-"+data+"' title='Process'>build</i>"
//    }
//    return res
// }

function delete_all_selected_rawspecfiles(){
    if (confirm('Are you sure you want to delete this spectrum? This can NOT be undone!')===true){
        let rows = [];
        //   Get list of selected spectra
        rawspecfile_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
            rows.push(this);
        });
        // Loop over selected spectra
        $.each(rows, function (index, row) {
            //  Loop over all spec files
            $.each(row.data()["specfiles"], function(ind) {
                let pk = row.data()["specfiles"][ind]['pk'];
                //  Ajax call to remove spec files
                $.ajax({
                    url : "/api/observations/rawspecfiles/"+pk+'/',
                    type : "DELETE",
                    success : function(json) {
                        //  Remove the whole spectrum from table
                        rawspecfile_table.row(row).remove().draw('full-hold');
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
   rawspecfile_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
       spfilelist.push('/media/raw_spectra/'.concat(this.data()['filename']));
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
                saveAs(blob, "Raw_data_"+timecode+".zip");
                //  Reset download button
                showProgress("Download raw data");
            }, function (e) {
                showError(e);
            });


      });
   });
}

// function processRawSpecfile(row, data) {
//    $.ajax({
//       url : "/api/observations/rawspecfiles/"+data['pk']+'/process/',
//       type : "POST",
//       success : function(json) {
//          // remove the row from the table
//          rawspecfile_table.row(row).data(json).draw('full-hold');
//       },
//
//       error : function(xhr,errmsg,err) {
//          console.log(xhr.status + ": " + xhr.responseText);
//       }
//    });
// };

// function deleteRawSpecfile(row, data) {
//    if (confirm('Are you sure you want to remove this raw spectrum file?')==true){
//       $.ajax({
//          url : "/api/observations/rawspecfiles/"+data['pk']+'/',
//          type : "DELETE",
//          success : function(json) {
//             // remove the row from the table
//             rawspecfile_table.row(row).remove().draw('full-hold');
//          },
//
//          error : function(xhr,errmsg,err) {
//             console.log(xhr.status + ": " + xhr.responseText);
//          }
//       });
//    };
// };
