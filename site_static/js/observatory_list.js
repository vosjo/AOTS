
var observatory_table = null;
var observatory_window = null;

$(document).ready(function () {
   
   // Initializing all dialog windows
   var observatory_window = $("#observatoryEdit").dialog({autoOpen: false, 
            width: 'auto',
            modal: true});
   
   
   // Table functionality
   observatory_table = $('#observatorytable').DataTable({
      autoWidth: false,
      pageLength: 25,
      ajax: {
         url: '/api/observations/observatories/?format=datatables&keep=url&keep=short_name',
         data: function ( d ) {
           d.project = $('#project-pk').attr('project');
         },
      },
      columns: [
         { data: 'name', render: name_render },
         { data: 'telescopes'},
         { data: 'latitude'},
         { data: 'longitude'},
         { data: 'altitude' },
         { data: 'space_craft', render: spacecraft_render },
         { data: 'note' },
         { data: 'pk', render: action_render, width: '100', 
         className: 'dt-center', visible: user_authenticated},
      ]
   });
   
   function name_render( data, type, full, meta ) {
      return "<a href='" + full['url'] + "' >" + data + "</a>"
   }
   
   function spacecraft_render( data, type, full, meta ) {
      if ( data ) {
         return "<i class='material-icons status-icon valid'></i>"
      } else {
         return "<i class='material-icons status-icon invalid'></i>"
      }
   }
   
   function action_render( data, type, full, meta ) {
      return "<i class='material-icons button edit' id='edit-observatory-"+data+"'>edit</i>" + 
             "<i class='material-icons button delete' id='delete-observatory-"+data+"'>delete</i>"
   }
   
   // add observatory event listner
   $( ".observatoryAddButton").click( openObservatoryAddBox );
   
   // Delete observatory event listener
   $("#observatorytable").on('click', 'i[id^=delete-observatory-]', function(){
      var thisrow = $(this).closest('tr');
      var data = observatory_table.row(thisrow).data();
      deleteObservatory(thisrow, data);
   });
   
   // Delete observatory event listener
   $("#observatorytable").on('click', 'i[id^=edit-observatory-]', function(){
      var thisrow = $(this).closest('tr');
      var data = observatory_table.row(thisrow).data();
      openObservatoryEditBox(thisrow, data);
   });
   
});






// Add new observatory
function openObservatoryAddBox() {
   
   observatory_window = $("#observatoryEdit").dialog({
      title: 'Add a new Observatory',
      buttons: { "Add": addObservatory },
      close: function() { observatory_window.dialog( "close" ); }
   });
      
   observatory_window.dialog( "open" );
};


function addObservatory() {
   
   $.ajax({
      url : "/api/observations/observatories/", 
      type : "POST",
      data : { project:      $('#project-pk').attr('project'),
               name :        $('#observatoryEditName').val(), 
               short_name :  $('#observatoryEditShortName').val(), 
               telescopes :  $('#observatoryEditTelescopes').val(),
               latitude :    $('#observatoryEditLatitude').val(),
               longitude :   $('#observatoryEditLongitude').val(),
               altitude :    $('#observatoryEditAltitude').val(),
               space_craft:  $('#observatoryEditSpacecraft').is(':checked'),
               note :        $('#observatoryEditNote').val(),
               url :         $('#observatoryEditUrl').val(),
               weatherurl :  $('#observatoryEditWeatherUrl').val(),
               },
      
      success : function(json) {
            observatory_window.dialog( "close" );
            observatory_table.row.add( json ).draw();
      },
      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};


// Edit an exiting observatory
function openObservatoryEditBox(tabelrow, data) {
   observatory_window = $("#observatoryEdit").dialog({
      title: "Edit observatory data",
      buttons: { "Update": function () { editObservatory(tabelrow, data); } },
      close: function() { observatory_window.dialog( "close" ); }
   });
   
   observatory_window.dialog( "open" );
   $("#observatoryEditName").val( data['name'] );
   $("#observatoryEditShortName").val( data['short_name'] );
   $("#observatoryEditTelescopes").val( data['telescopes'] );
   $("#observatoryEditLatitude").val( data['latitude'] );
   $("#observatoryEditLongitude").val( data['longitude'] );
   $("#observatoryEditAltitude").val( data['altitude'] );
   $("#observatoryEditSpacecraft").prop('checked', data['space_craft'] );
   $("#observatoryEditNote").val( data['note'] );
   $("#observatoryEditUrl").val( data['url'] );
   $("#observatoryEditWeatherUrl").val( data['weatherurl'] );
};

function editObservatory(tabelrow, data) {
   
   $.ajax({
      url : "/api/observations/observatories/"+data['pk']+'/', 
      type : "PATCH",
      data : { name :        $('#observatoryEditName').val(), 
               short_name :  $('#observatoryEditShortName').val(), 
               telescopes :  $('#observatoryEditTelescopes').val(),
               latitude :    $('#observatoryEditLatitude').val(),
               longitude :   $('#observatoryEditLongitude').val(),
               altitude :    $('#observatoryEditAltitude').val(),
               space_craft:  $('#observatoryEditSpacecraft').is(':checked'),
               note :        $('#observatoryEditNote').val(),
               url :         $('#observatoryEditUrl').val(),
               weatherurl :  $('#observatoryEditWeatherUrl').val(), 
               },
      
      success : function(json) {
            observatory_window.dialog( "close" );
            observatory_table.row(tabelrow).data(json).draw();
            console.log(json);
      },

      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};


// Delete an observatory
function deleteObservatory(row, data) {
   if (confirm('Are you sure you want to delete this Observatory? This cannot be undone')==true){
      $.ajax({
         url : "/api/observations/observatories/"+data['pk']+"/",
         type : "DELETE", 
         success : function(json) {
            observatory_table.row(row).remove().draw('full-hold');
         },
         error : function(xhr,errmsg,err) {
               console.log(xhr.status + ": " + xhr.responseText);
         }
      });
   }
}
