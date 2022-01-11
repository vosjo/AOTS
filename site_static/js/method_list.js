
var method_table = null;

$(document).ready(function () {

   // Table functionality
   method_table = $('#methodtable').DataTable({
   serverSide: true,
   autoWidth: false,
   paging: false,
   ajax: {
      url: '/api/analysis/methods/?format=datatables',
      data: function ( d ) {
        d.project = $('#project-pk').attr('project');
      },
   },
   columns: [
      { data: 'name' },
      { data: 'description' },
      { data: 'slug' },
      { data: 'color', render : color_render},
      { data: 'derived_parameters' },
      { data: 'data_type_display', width: '100' },
      { data: 'pk', render: action_render, width: '100',
        className: 'dt-center', visible: user_authenticated},
   ]
   });

   function color_render( data, type, full, meta ) {
      // Render the tags as a list of divs with the correct color.
      return "<div class='circle block' style='background:"+data+"'></div>" + data
   }

   function action_render( data, type, full, meta ) {
      // Add edit and delete buttons
      return "<i class='material-icons button delete' id='delete-method-"+data+
               "' title='Delete method'>delete</i>" +
               "<i class='material-icons button edit' id='edit-method-"+data+
               "' title='Edit method'>edit</i>"
   }

   // Initializing the dialog window
   var method_add_window = $("#addEditMethod").dialog({autoOpen: false,
            width: 'auto',
            modal: true});

   // add event listeners
   $( ".methodAddButton").click( openMethodAddBox );
   $("#methodtable").on('click', 'i[id^=edit-method-]', function() {
      var closestRow = $(this).closest('tr');
      var data = method_table.row(closestRow).data();
      openMethodEditBox(closestRow, data);
   });
   $("#methodtable").on('click', 'i[id^=delete-method-]', function() {
      var closestRow = $(this).closest('tr');
      var data = method_table.row(closestRow).data();
      deleteMethod(closestRow, data);
   });

});

// Add new method
function openMethodAddBox() {

   method_add_window = $("#addEditMethod").dialog({
      title: 'Add new method',
      buttons: { "Add": addMethod },
      close: function() { method_add_window.dialog( "close" ); }
   });

   method_add_window.dialog( "open" );
};

function addMethod() {
   $.ajax({
      url : "/api/analysis/methods/",
      type : "POST",
      data : { name : $('#method-name').val(),
               description : $('#method-description').val(),
               slug : $('#method-slug').val(),
               color : $('#method-color').val(),
               data_type : $('#method-dataType').val(),
               project: $('#project-pk').attr('project'),
               },

      success : function(json) {
            method_add_window.dialog( "close" );
            method_table.row.add( json ).draw();
      },

      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });

};

// Edit method
function openMethodEditBox(tabelrow, method_data) {
   method_add_window = $("#addEditMethod").dialog({
      title: 'Edit method',
      buttons: { "Update": function () { editMethod(tabelrow, method_data); } },
      close: function() { method_add_window.dialog( "close" ); }
   });

   method_add_window.dialog( "open" );
   $("#method-name").val( method_data['name'] );
   $("#method-description").val( method_data['description'] );
   $('#method-slug').val( method_data['slug'] );
   $("#method-color").val( method_data['color'] );
   $('#method-dataType').val( method_data['data_type'] );
   $('#method-parameters').val( method_data['derived_parameters'] );
};

function editMethod(tabelrow, method_data) {
   console.log($('#method-dataType').val());
   $.ajax({
      url : "/api/analysis/methods/"+method_data['pk']+'/',
      type : "PATCH",
      data : { name :        $('#method-name').val(),
               description : $('#method-description').val(),
               slug :        $('#method-slug').val(),
               color :       $('#method-color').val(),
               data_type :   $('#method-dataType').val(),
               derived_parameters : $('#method-parameters').val(),
               },

      success : function(json) {
            method_add_window.dialog( "close" );
            method_table.row(tabelrow).data(json).draw();
      },

      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};

// Delete method
function deleteMethod(tabelrow, method_data) {
   if (confirm('Are you sure you want to remove this Method? This will delete all datasets with this method!')==true){
      $.ajax({
            url : "/api/analysis/methods/"+method_data['pk']+'/',
            type : "DELETE",
            success : function(json) {
               // remove the row from the table
               method_table.row(tabelrow).remove().draw();
            },

            error : function(xhr,errmsg,err) {
               console.log(xhr.status + ": " + xhr.responseText);
            }
      });
   };
};
