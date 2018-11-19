
var dataset_table = null;

$(document).ready(function () {
   
   dataset_table = $('#datasettable').DataTable({
   ajax: {
      url: '/api/analysis/datasets/?format=datatables',
      data: function ( d ) {
        d.project = $('#project-pk').attr('project');
      },
   },
   columns: [
      { data: 'star', render: star_render },
      { data: 'name', render: name_render },
      { data: 'note', render: note_render },
      { data: 'method', render: method_render },
      { data: 'added_on' },
      { data: 'pk', render: action_render, width: '30', visible: user_authenticated},
   ]
   });
   
   // Delete a dataset
   $("#datasettable").on('click', 'i[id^=delete-dataset-]', function(){
      var thisrow = $(this).closest('tr');
      var data = dataset_table.row(thisrow).data();
      delete_dataset(thisrow, data)
   });
   
   // Process a dataset
   $("#datasettable").on('click', 'i[id^=process-dataset-]', function(){
      var thisrow = $(this).closest('tr');
      var data = dataset_table.row(thisrow).data();
      process_dataset(thisrow, data);
   });
   
});

function star_render( data, type, full, meta ) {
   return "<a href='/systems/stars/"+full['star_pk']+"/'>"+data+"</a>";
}

function name_render( data, type, full, meta ) {
   return "<a href='/analysis/datasets/"+full['pk']+"/'>"+data+"</a>";
}

function note_render( data, type, full, meta ) {
   if (data.length > 30) return data.substring(0,30) + '...';
   return data
}

function method_render( data, type, full, meta ) {
   return "<div title='"+data.description+"'>"+data.name+"</div>";
}

function action_render( data, type, full, meta ) {
   // Add deleta tag icon
   return "<i class='material-icons button delete' id='delete-dataset-"+data+
            "' title='Delete'>delete</i>" + 
            "<i class='material-icons button process' id='process-dataset-"+data+
            "' title='(Re)Process'>build</i>"
}

function process_dataset(row, data) {
   $.ajax({
      url : "/api/analysis/datasets/"+data['pk']+"/process/",
      type : "POST",
      success : function(json) {
         // remove the row from the table
         dataset_table.row(row).data(json).draw('full-hold');
         // show success message for 5 sec.
         var li = $("<li class='success'>Processed dataset " + json['name'] + "</li>");
         $("#messages").append(li);
         li.delay(5000).fadeOut()
      },

      error : function(xhr,errmsg,err) {
         console.log(xhr.status + ": " + xhr.responseText);
      }
   });
}

function delete_dataset(row, data) {
   if (confirm('Are you sure you want to remove this DataSet?')==true){
      $.ajax({
         url : "/api/analysis/datasets/"+data['pk']+'/',
         type : "DELETE",
         success : function(json) {
            // remove the row from the table
            dataset_table.row(row).remove().draw('full-hold');
         },

         error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
         }
      });
   }
}
