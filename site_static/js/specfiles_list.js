
var specfile_table = null;

$(document).ready(function () {
   
   // Table functionality
   specfile_table = $('#specfiletable').DataTable({
   autoWidth: false,
   ajax: {
      url: '/api/observations/specfiles/?format=datatables',
      data: function ( d ) {
        d.project = $('#project-pk').attr('project');
      },
   },
   columns: [
      { data: 'hjd' },
      { data: 'instrument' },
      { data: 'filetype' },
      { data: 'added_on' },
      { data: 'star' },
      { data: 'spectrum', render : processed_render },
      { data: 'pk', render: action_render, width: '100', 
        className: 'dt-center', visible: user_authenticated},
   ]
   });
   
   function processed_render( data, type, full, meta ) {
      if ( data ){
         return "<a href='" + data + "' >" + 'Yes' + "</a>";
      } else {
         return 'No';
      }
//       if ( data ){ return 'Yes'; } else { return 'No'; }
   }
   
   function action_render( data, type, full, meta ) {
      var res = "<i class='material-icons button delete' id='delete-specfile-"+data+"'>delete</i>"
      if ( !full['spectrum'] ) { 
         res = res + "<i class='material-icons button process' id='process-specfile-"+data+"' title='Process'>build</i>"
      }
      return res
   }
   
   // Event listeners
   $("#specfiletable").on('click', 'i[id^=process-specfile-]', function() {
      var thisrow = $(this).closest('tr');
      var data = specfile_table.row(thisrow).data();
      processSpecfile(thisrow, data);
   });
   $("#specfiletable").on('click', 'i[id^=delete-specfile-]', function() {
      var thisrow = $(this).closest('tr');
      var data = specfile_table.row(thisrow).data();
      deleteSpecfile(thisrow, data);
   });
   
});

function processSpecfile(row, data) {
   $.ajax({
      url : "/api/observations/specfiles/"+data['pk']+'/process/',
      type : "POST",
      success : function(json) {
         // remove the row from the table
         specfile_table.row(row).data(json).draw('full-hold');
      },

      error : function(xhr,errmsg,err) {
         console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};

function deleteSpecfile(row, data) {
   if (confirm('Are you sure you want to remove this spectrum file?')==true){
      $.ajax({
         url : "/api/observations/specfiles/"+data['pk']+'/',
         type : "DELETE",
         success : function(json) {
            // remove the row from the table
            specfile_table.row(row).remove().draw('full-hold');
         },

         error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
         }
      });
   };
};
