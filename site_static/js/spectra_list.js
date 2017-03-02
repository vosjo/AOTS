
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
   
   // Table functionality
   spectra_table = $('#spectratable').DataTable({
   autoWidth: false,
   ajax: {
      url: '/api/spectra/spectra/',
      dataSrc: '' 
   },
   columns: [
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
      { data: 'pk', render: action_render, width: '100', className: 'dt-center'},
   ]
   });
   
   function hjd_render( data, type, full, meta ) {
      return "<a href='/spectra/spectra/" + full['pk'] + "' >" + data + "</a>"
   }
   
   function star_render( data, type, full, meta ) {
      return "<a href='/stars/stars/" + data['pk'] + "' >" + data['name'] + "</a>"
   }
   
   function instrument_render( data, type, full, meta ) {
      return data + " @ " + full['telescope']
   }
   
   function action_render( data, type, full, meta ) {
      return "<i class='material-icons button delete' id='delete-spectrum-"+data+"'>delete</i>"
   }
   
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
      if ( $(this).text() == 'visibility' ) {
         // open all rows
         $(this).text('visibility_off')
         
         spectra_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            open_details(this); // Open this row
         });
      } else {
         // close all rows
         $(this).text('visibility')
         
         spectra_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            close_details(this); // close the row
         });
      };
   });
   
   // Delete spectrum completely event listener
   $("#spectratable").on('click', 'i[id^=delete-spectrum-]', function(){
      var thisrow = $(this).closest('tr');
      var data = spectra_table.row(thisrow).data();
      delete_spectrum(thisrow, data);
   });
   
});

function open_details(row) {
   row.child( format(row.data()) ).show();
   $(row.node()).find("i[class*=show]").text('visibility_off')
   row.child().addClass('expansion');
   // add event listeners
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

function remove_specfile(spec_elem, row) {
   var pk = spec_elem.attr('id').split('-')[2]
   if (confirm('Are you sure you want to remove this File from the spectrum?')==true){
      $.ajax({
            url : "/api/spectra/specfiles/"+pk+'/',
            type : "PATCH",
            data : { spectrum : null},
            success : function(json) {
               // remove the specfile from DOM
               spec_elem.closest('li')[0].remove() 
               
               // remove the whole spectrum, is all specfiles are gone
               if (row.child().find('li').length == 0) {
                  spectra_table.row(row).remove().draw('full-hold');
               }
               
               //remove item from the dataset
               var data = remove_specfile_from_data(spectra_table.row(row).data(), pk);
               spectra_table.row(row).data( data );
            },

            error : function(xhr,errmsg,err) {
               console.log(xhr.status + ": " + xhr.responseText);
            }
      });
   }
   
}

function delete_specfile(spec_elem, row) {
   var pk = spec_elem.attr('id').split('-')[2]
   if (confirm('Are you sure you want to delete this File from the spectrum? This can NOT be undone! If you want to remove it from this spectrum, but keep it in the database, use the remove button.')==true){
      $.ajax({
            url : "/api/spectra/specfiles/"+pk+'/',
            type : "DELETE",
            success : function(json) {
               // remove the specfile from DOM
               spec_elem.closest('li')[0].remove() 
               
               // remove the whole spectrum, is all specfiles are gone
               if (row.child().find('li').length == 0) {
                  spectra_table.row(row).remove().draw('full-hold');
               }
               
               //remove item from the dataset
               var data = remove_specfile_from_data(spectra_table.row(row).data(), pk);
               spectra_table.row(row).data( data );
            },

            error : function(xhr,errmsg,err) {
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
         url : "/api/spectra/spectra/"+data['pk']+"/",
         type : "DELETE", // http method
         success : function(json) {
            // delete the spectrum from the table
            spectra_table.row(row).remove().draw('full-hold');
         },

         error : function(xhr,errmsg,err) {
               console.log(xhr.status + ": " + xhr.responseText);
         }
      });
   }
}