
var lighcurve_table = null;

$(document).ready(function () {
   
   // Table functionality
   lighcurve_table = $('#lightcurvetable').DataTable({
   autoWidth: false,
   serverSide: true, 
   ajax: {
      url: '/api/observations/lightcurves/?format=datatables&keep=telescope,href',
      data: get_filter_keywords,
   },
   searching: false,
   orderMulti: false, //Can only order on one column at a time
   order: [1],
   columns: [
      { data: 'hjd', render : hjd_render },
      { data: 'star', render : star_render },
      { data: 'instrument', render : instrument_render },
      { data: 'exptime' },
      { data: 'cadence' },
      { data: 'pk', render: action_render, width: '100', 
        className: 'dt-center', visible: user_authenticated, orderable: false},
   ],
   paging: true,
   pageLength: 20,
   lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all. 
   scrollY: $(window).height() - $('header').outerHeight(true) - 196,
   scrollCollapse: true,
   });
   
   // Event listener to the two range filtering inputs to redraw on input
   $('#filter-form').submit( function(event) {
      event.preventDefault();
      lighcurve_table.draw();
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
   };
   
   
   // Delete spectrum completely event listener
   $("#lightcurvetable").on('click', 'i[id^=delete-spectrum-]', function(){
      var thisrow = $(this).closest('tr');
      var data = lighcurve_table.row(thisrow).data();
      delete_spectrum(thisrow, data);
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
   
   return d
}

// Table renderers
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
   return "<i class='material-icons button delete' id='delete-spectrum-"+data+"'>delete</i>"
}


function delete_spectrum(row, data) {
   if (confirm('Are you sure you want to delete this light curve? This can NOT be undone.')==true){
      $.ajax({
         url : "/api/observations/lightcurves/"+data['pk']+"/",
         type : "DELETE", // http method
         success : function(json) {
            // delete the spectrum from the table
            lighcurve_table.row(row).remove().draw('full-hold');
         },

         error : function(xhr,errmsg,err) {
               console.log(xhr.status + ": " + xhr.responseText);
         }
      });
   }
}
