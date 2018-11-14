
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
      ajax: {
         url: '/api/observations/observatories/?format=datatables&keep=url',
      },
      columns: [
         { data: 'name', render: name_render },
         { data: 'latitude'},
         { data: 'longitude'},
         { data: 'altitude' },
         { data: 'note' },
         { data: 'pk', render: action_render, width: '100', 
         className: 'dt-center', visible: user_authenticated},
      ]
   });
   
   function name_render( data, type, full, meta ) {
      return "<a href='" + full['url'] + "' >" + data + "</a>"
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
   
   var obs_url = $('#observatoryEditUrl').val()
   if (obs_url.substring(0, 8) != "http://") { obs_url = "http://" + obs_url };
   
   $.ajax({
      url : "/api/observations/observatories/", 
      type : "POST",
      data : { name :        $('#observatoryEditName').val(), 
               latitude :    $('#observatoryEditLatitude').val(),
               longitude :   $('#observatoryEditLongitude').val(),
               altitude :    $('#observatoryEditAltitude').val(),
               note :        $('#observatoryEditNote').val(),
               url :         obs_url,
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
   
   console.log(data);
   
   observatory_window.dialog( "open" );
   $("#observatoryEditName").val( data['name'] );
   $("#observatoryEditLatitude").val( data['latitude'] );
   $("#observatoryEditLongitude").val( data['longitude'] );
   $("#observatoryEditAltitude").val( data['altitude'] );
   $("#observatoryEditNote").val( data['note'] );
   $("#observatoryEditUrl").val( data['url'] );
};

function editObservatory(tabelrow, data) {
   
   var obs_url = $('#observatoryEditUrl').val()
   if (obs_url.substring(0, 8) != "http://") { obs_url = "http://" + obs_url };
   
   $.ajax({
      url : "/api/observations/observatories/"+data['pk']+'/', 
      type : "PATCH",
      data : { name :        $('#observatoryEditName').val(), 
               latitude :    $('#observatoryEditLatitude').val(),
               longitude :   $('#observatoryEditLongitude').val(),
               altitude :    $('#observatoryEditAltitude').val(),
               note :        $('#observatoryEditNote').val(),
               url :         obs_url,
               },
      
      success : function(json) {
            observatory_window.dialog( "close" );
            observatory_table.row(tabelrow).data(json).draw();
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
