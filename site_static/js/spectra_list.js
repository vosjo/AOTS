
var spectra_table = null;

function format ( data ) {
   var res = "<ul>";
   for (var i=0; i < data['specfiles'].length; i++ ) {
      var sp = data['specfiles'][i];
      res = res + "<li>"
      res = res + sp['hjd'] + " - " + sp['instrument'] + " - " + sp['filetype'];
      res = res + "<i class='material-icons button delete' id='remove-specfile-" + sp['pk'] + "' title='Remove from spectrum'>close</i>";
      res = res + "<i class='material-icons button delete' id='delete-specfile-" + sp['pk'] + "' title='Remove from spectrum'>delete</i>";
      res = res + "</li>"

   }
   res = res + "</ul>";
   return res;
}



$(document).ready(function () {
   let columns;
   if (user_authenticated) {
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
         /*{ data: 'pk', render: action_render, width: '100',
           className: 'dt-center', visible: user_authenticated, orderable: false},*/
      ];
   }
   else {
   columns = [
        {
             className:      'details-control',
             orderable:      false,
             data:           null,
             defaultContent: '<i class="material-icons button show" title="Expand/hide">visibility</i>',
             width:          '10',
          },
         { data: 'hjd', render : hjd_render },
         { data: 'star', render : star_render },
         { data: 'instrument', render : instrument_render },
         { data: 'exptime' },
         /*{ data: 'pk', render: action_render, width: '100',
           className: 'dt-center', visible: user_authenticated, orderable: false}*/
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
      if (text == "filter_list"){
            $('#filter-dashboard-button').text("close");
      } else {
            $('#filter-dashboard-button').text("filter_list");
      }
   };


   // Add event listener for opening and closing details
   $('#spectratable tbody').on('click', 'td.details-control', function () {
      var tr = $(this).closest('tr');
      var row = spectra_table.row( tr );

      if ( row.child.isShown() ) {
         close_details(row); // This row is already open - close it
      }
      else {
         open_details(row); // Open this row
      }
   } );

   // Add event listener for opening and closing all details
   $('#expand-all').on('click', function () {
      if ( $(this).text() === 'visibility' ) {
         // Open all rows
         $(this).text('visibility_off');

         spectra_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            open_details(this); // Open this row
         });
      } else {
         // Close all rows
         $(this).text('visibility');

         spectra_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            close_details(this); // close the row
         });
      }
   });

   // Delete spectrum completely event listener
   $("#spectratable").on('click', 'i[id^=delete-spectrum-]', function(){
      var thisrow = $(this).closest('tr');
      var data = spectra_table.row(thisrow).data();
      delete_spectrum(thisrow, data);
   });

  //Add toolbar to table
   if (user_authenticated){
      $("div.toolbar").html("<input id='dl-button'  class='tb-button' value='Download Spectra' type='button' disabled>" +
          "<input id='rm-button'  class='tb-button' value='Remove Spectrum from Star' type='button' disabled>" +
          "<input id='delete-button'  class='tb-button' value='Delete Spectrum' type='button' disabled>");
      $("#dl-button").click( DlSpectra );
      $("#rm-button").click( remove_selected_specfiles );
      $("#delete-button").click( delete_selected_specfiles );
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

   if ($('#filter_hjd').val() != '') {
      d = $.extend( {}, d, {
         "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] | 0 ),
         "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] | 1000000000),
      } );
   }

   if ($('#filter_exptime').val() != '') {
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

function action_render( data, type, full, meta ) {
   return "<i class='material-icons button delete' id='delete-spectrum-"+data+"'>delete</i>"
}


function open_details(row) {
   row.child( format(row.data()) ).show();
   $(row.node()).find("i[class*=show]").text('visibility_off');
   row.child().addClass('expansion');
   // Add event listeners
   row.child().on('click', 'i[id^=remove-specfile-]', function (event) {
         remove_specfile($(this), row);
      }
   );
   row.child().on('click', 'i[id^=delete-specfile-]', function (event) {
         delete_specfile($(this), row);
      }
   );
}

function close_details(row) {
   row.child.hide();
   $(row.node()).find("i[class*=show]").text('visibility');
}

function remove_selected_specfiles(){
   if (confirm('Are you sure you want to remove this File from the spectrum?')===true){
   var rows = [];
   // get list of files
   spectra_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
      var row = this;
      rows.push(row);
   });
   $.each(rows, function (index, row) {
      var pk = row.data()["specfiles"][0]["pk"];
         $.ajax({
               url : "/api/observations/specfiles/"+pk+'/',
               type : "PATCH",
               data : { spectrum : null},
               success : function(json) {
                  // Not necessary anymore?
                  /*!// Remove the specfile from DOM
                  spec_elem.closest('li')[0].remove();*/

                  // Remove the whole spectrum, if all specfiles are gone
                  if (row.data()["specfiles"]["length"]-1 === 0) {
                     spectra_table.row(row).remove().draw('full-hold');
                  }

                  // Remove item from the dataset
                  var data = remove_specfile_from_data(row.data(), pk);
                  spectra_table.row(row).data( data );
               },

               error : function(xhr,errmsg,err) {
                   if (xhr.status === 403){
                       alert('You have to be logged in to remove this spectrum.');
                   }else{
                       alert(xhr.status + ": " + xhr.responseText);
                   }
                   console.log(xhr.status + ": " + xhr.responseText);
               }
         });
      })
   }
}

function remove_specfile(spec_elem, row) {
   var pk = spec_elem.attr('id').split('-')[2];
   if (confirm('Are you sure you want to remove this File from the spectrum?')===true){
      $.ajax({
            url : "/api/observations/specfiles/"+pk+'/',
            type : "PATCH",
            data : { spectrum : null},
            success : function(json) {
               // Remove the specfile from DOM
               spec_elem.closest('li')[0].remove();

               // Remove the whole spectrum, if all specfiles are gone
               if (row.child().find('li').length === 0) {
                  spectra_table.row(row).remove().draw('full-hold');
               }

               // Remove item from the dataset
               var data = remove_specfile_from_data(spectra_table.row(row).data(), pk);
               spectra_table.row(row).data( data );
            },

            error : function(xhr,errmsg,err) {
                if (xhr.status === 403){
                    alert('You have to be logged in to remove this spectrum.');
                }else{
                    alert(xhr.status + ": " + xhr.responseText);
                }
                console.log(xhr.status + ": " + xhr.responseText);
            }
      });
   }

}

function delete_selected_specfiles(){
   if (confirm('Are you sure you want to delete these Files from these spectra? This can NOT be undone! If you want to remove them from these spectra, but keep them in the database, use the remove button.')===true){
   var rows = [];
   // get list of files
   spectra_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
      var row = this;
      rows.push(row);
   });
   $.each(rows, function (index, row) {
      var pk = row.data()["specfiles"][0]["pk"];
               $.ajax({
               url : "/api/observations/specfiles/"+pk+'/',
               type : "DELETE",
               success : function(json) {
                  /*// Remove the specfile from DOM
                  spec_elem.closest('li')[0].remove()*/

                  // Remove the whole spectrum, if all specfiles are gone
                  if (row.data()["specfiles"]["length"]-1 === 0) {
                     spectra_table.row(row).remove().draw('full-hold');
                  }

                  // Remove item from the dataset
                  var data = remove_specfile_from_data(row.data(), pk);
                  spectra_table.row(row).data( data );
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
   }
}

function delete_specfile(spec_elem, row) {
   var pk = spec_elem.attr('id').split('-')[2]
   if (confirm('Are you sure you want to delete this File from the spectrum? This can NOT be undone! If you want to remove it from this spectrum, but keep it in the database, use the remove button.')==true){
      $.ajax({
            url : "/api/observations/specfiles/"+pk+'/',
            type : "DELETE",
            success : function(json) {
               // Remove the specfile from DOM
               spec_elem.closest('li')[0].remove()

               // Remove the whole spectrum, if all specfiles are gone
               if (row.child().find('li').length == 0) {
                  spectra_table.row(row).remove().draw('full-hold');
               }

               // Remove item from the dataset
               var data = remove_specfile_from_data(spectra_table.row(row).data(), pk);
               spectra_table.row(row).data( data );
            },

            error : function(xhr,errmsg,err) {
                if (xhr.status == 403){
                    alert('You have to be logged in to delete this spectrum.');
                }else{
                    alert(xhr.status + ": " + xhr.responseText);
                }
                console.log(xhr.status + ": " + xhr.responseText);
            }
      });
   }
}

function remove_specfile_from_data(data, pk) {
   for (var i=0; i < data['specfiles'].length; i++) {
      if (data['specfiles'][i]['pk'] == pk) {
         data['specfiles'].splice(i,1)
         break;
      }
   }
}

function delete_spectrum(row, data) {
   if (confirm('Are you sure you want to delete this Spectrum? The individual files will be kept.')==true){
      $.ajax({
         url : "/api/observations/spectra/"+data['pk']+"/",
         type : "DELETE", // http method
         success : function(json) {
            // Delete the spectrum from the table
            spectra_table.row(row).remove().draw('full-hold');
         },

         error : function(xhr,errmsg,err) {
                if (xhr.status == 403){
                    alert('You have to be logged in to delete this spectrum.');
                }else{
                    alert(xhr.status + ": " + xhr.responseText);
                }
               console.log(xhr.status + ": " + xhr.responseText);
         }
      });
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


function DlSpectra() {
   var spfilelist = [];
   // get list of files
   spectra_table.rows('.selected').every(function (rowIdx, tableLoop, rowLoop) {
      var specid = this.data()['pk'];
      $.getJSON("/api/observations/spectra/" + specid + "/", function (spectrum) {
         var sfilepk = spectrum.specfiles[0].pk;
         $.getJSON("/api/observations/specfiles/" + sfilepk + "/", function (sfile) {
            spfilelist.push(sfile.filename);
         })
      });
   });

   $.getScript("/static/js/JsZip/FileSaver.js").done( function () {
      $.getScript("/static/js/JsZip/jszip.js").done( function () {
         let zip = new JSZip();
         window.setTimeout(function () {
            $.each(spfilelist, function (inx, filepath) {
               $.get("/media/spectra/" + filepath, function (content) {
                  zip.file(filepath, content);
               });
            });
            window.setTimeout(function () {
               let dt = new Date();
               let timecode = dt.getHours()+""+dt.getMinutes()+dt.getSeconds();
               zip.generateAsync({type: "blob"}).then(function (content) {
                              saveAs(content, "Spectra"+timecode+".zip");
                           });
            }, 250);
         },100);
      })
   });
}
