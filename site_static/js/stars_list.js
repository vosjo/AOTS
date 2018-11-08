
var star_table = null;
var edit_status_window = null;
var edit_tags_window = null;
var all_tags = null;


$(document).ready(function () {

   star_table = $('#datatable').DataTable({
   dom: 'l<"toolbar">frtip',
   serverSide: true, 
   ajax: {
      url: '/api/stars/stars/?format=datatables',
      data: get_filter_keywords,
   },
   columns: [
      { orderable:      false,
         className:      'select-control',
         data:           null,
         render: selection_render,
         width:          '10',
      },
      { data: 'name', render: name_render },
      { data: 'ra_hms' },
      { data: 'dec_dms' },
      { data: 'classification', render: classification_render },
      { data: 'vmag' },
      { data: 'tags', render: tag_render },
      { data: 'observing_status', render: status_render, 
         width: '70', 
         className: "dt-center" },
   ],
   paging: true,
   pageLength: 50,
   lengthMenu: [[10, 25, 50, 100, 1000], [10, 25, 50, 100, 1000]], // Use -1 for all. 
   scrollY: '900px',
   scrollCollapse: true,
   autoWidth: true,
   });
   
   //Add toolbar to table
   $("div.toolbar").html("<input id='tag-button'  class='tb-button' value='Edit Tags' type='button' disabled>" +
                           "<input id='status-button' class='tb-button' value='Change Status' type='button' disabled>");
   
   // Event listener to the two range filtering inputs to redraw on input
   $('#filter-form').submit( function(event) {
      event.preventDefault();
      star_table.draw();
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
   
   // check and uncheck tables rows
   $('#datatable tbody').on( 'click', 'td.select-control', function () {
      var tr = $(this).closest('tr');
      var row = star_table.row( tr );
      if ( $(row.node()).hasClass('selected') ) {
         deselect_row(row);
      } else {
         select_row(row);
      }
   } );
   
   $('#select-all').on('click', function () {
      if ( $(this).text() == 'check_box' | $(this).text() == 'indeterminate_check_box') {
         // deselect all
         $(this).text('check_box_outline_blank')
         
         star_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            deselect_row(this); // Open this row
         });
      } else {
         // close all rows
         $(this).text('check_box')
         
         star_table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            select_row(this); // close the row
         });
      };
   });
   
   // Load the tags and add them to the tag selection list, and the tag edit window
   load_tags ();
   
   // initialize edit windows
   edit_status_window = $("#editStatus").dialog({autoOpen: false, 
         width: '150',
         modal: true});
   
   edit_tags_window = $("#editTags").dialog({autoOpen: false, 
         width: '250',
         modal: true});
   
   // event listeners for edit buttons
   $( "#status-button").click( openStatusEditWindow );
   $( "#tag-button").click( openTagEditWindow );
   
});


// Table filter functionality

function get_filter_keywords( d ) {
   
      var selected_class = $("#classification_options input:checked").map( function () { return this.value; }).get();
      
      console.log(selected_class)
      console.log(d)
   
      d = $.extend( {}, d, {
        "project": $('#project-pk').attr('project'),
        "min_ra": parseFloat( $('#filter_ra').val().split(':')[0] ) / 24 * 360 || 0,
        "max_ra": parseFloat( $('#filter_ra').val().split(':')[1] ) / 24 * 360 || 360,
        "min_dec": parseFloat( $('#filter_dec').val().split(':')[0] ) || -90,
        "max_dec": parseFloat( $('#filter_dec').val().split(':')[1] ) || 90,
        "classification": selected_class,
      } );
      
      console.log(d)
      
      return d
}


// Table renderers

function selection_render( data, type, full, meta ) {
   if ( $(star_table.row(meta['row']).node()).hasClass('selected') ){
      return '<i class="material-icons button select" title="Select">check_box</i>';
   } else {
      return '<i class="material-icons button select" title="Select">check_box_outline_blank</i>';
   }
}

function name_render( data, type, full, meta ) {
   // Create a link to the detail for the star name
   return "<a href='/stars/stars/"+full['pk']+"/'>"+data+"</a>";
}

function tag_render( data, type, full, meta ) {
   // Render the tags as a list of divs with the correct color.
   var result = ""
   var tag = data[0];
   for (i = 0; i < data.length; i++) {
      tag = data[i];
      result += "<div class='small-tag' style='border-color:"+tag.color+"' title='"+tag.description+"'>"+tag.name+"</div>";
   }
   return result;
}

function classification_render( data, type, full, meta ) {
   // add the classification type to the table
   return "<span class='classification-" + full['classification_type'] + 
          "' title='"+full['classification_type_display']+"'>" + 
          data + " </span>"
   
//    return "<span title='"+full['classification_type_display']+"'>"+data+"</span>";
}

function status_render( data, type, full, meta ) {
   return '<i class="material-icons status-icon ' + data +  '" title="' +
          full['observing_status_display'] +'"></i>'
}


// Selection and Deselection of rows

function select_row(row) {
   $(row.node()).find("i[class*=select]").text('check_box')
   $(row.node()).addClass('selected');
   if ( star_table.rows('.selected').data().length < star_table.rows().data().length ) {
      $('#select-all').text('indeterminate_check_box');
   } else {
      $('#select-all').text('check_box');
   }
   $('#tag-button').prop('disabled', false)
   $('#status-button').prop('disabled', false)
};

function deselect_row(row) {
   $(row.node()).find("i[class*=select]").text('check_box_outline_blank')
   $(row.node()).removeClass('selected');
   if ( star_table.rows('.selected').data().length == 0 ) {
      $('#select-all').text('check_box_outline_blank');
      $('#tag-button').prop('disabled', true)
      $('#status-button').prop('disabled', true)
   } else {
      $('#select-all').text('indeterminate_check_box');
   }
};

// Edit status and tags functionality

function load_tags () {
   // load all tags and add them to the window
   $.ajax({
      url : "/api/stars/tags/", 
      type : "GET",
      success : function(json) {
         all_tags = json;
//             console.log(all_tags);
         for (var i=0; i<all_tags.length; i++) {
            tag = all_tags[i];
            $('#tagOptions').prepend("<li title='" + tag['description'] + 
            "'><input class='tristate' name='tags' type='checkbox' value='" 
            + tag['pk'] + "' />" + tag['name'] + "</li>" );
            
            $('#tag_filter_options').prepend(
            "<li><label><input id='id_status_" + i + "' name='tags' type='checkbox' value='" + 
            tag['pk'] + "' />" + tag['name'] + "</label></li>");
            
         }
         $('#tagOptions').on('change', ':checkbox', function(event){ cylceTristate(event, this); });
      },
      error : function(xhr,errmsg,err) {
         console.log(xhr.status + ": " + xhr.responseText);
         all_tags = [];
      }
   }); 
};

// ------------

function openStatusEditWindow() {
   edit_status_window = $("#editStatus").dialog({
      title: "Change Status",
      buttons: { "Update": updateStatus },
      close: function() { edit_status_window.dialog( "close" ); }
   });
   
   $("input[name='new-status']").prop('checked', false);
   edit_status_window.dialog( "open" );
}

function updateStatus() {
   var new_status = $("input[name='new-status']");
   if ( new_status.filter(':checked').length == 0 ) {
      $('#status-error').text('You need to select a status option!');
   } else {
      $('#status-error').text('');
      
      star_table.rows('.selected').every( function ( rowIdx, tableLoop, rowLoop ) {
         updateStarStatus(this, new_status.filter(':checked').val());
      });
      
   }
}

function updateStarStatus(row, status) {
   $.ajax({
      url : "/api/stars/stars/"+row.data()['pk']+'/', 
      type : "PATCH",
      data : { observing_status: status },
      
      success : function(json) {
         edit_status_window.dialog( "close" );
         row.data(json).draw('page');
      },

      error : function(xhr,errmsg,err) {
         if (xhr.status == 403){
            $('#status-error').text('You have to be logged in to edit');
         }else{
            $('#status-error').text(xhr.status + ": " + xhr.responseText);
         }
         console.log(xhr.status + ": " + xhr.responseText);
      }
   });
}

// -------------

function openTagEditWindow() {
   edit_tags_window = $("#editTags").dialog({
      title: "Add/Remove Tags",
      buttons: { "Update": updateTags},
      close: function() { edit_tags_window.dialog( "close" ); }
   });
   
   // Reset the counts per tag
   var all_tag_counts = {} 
   for ( tag in all_tags ) {
      all_tag_counts[all_tags[tag]['pk']] = 0
   };
   
   // count how many objects each tag has
   star_table.rows('.selected').every( function ( rowIdx, tableLoop, rowLoop ) {
      var tags = this.data()['tags'];
      for (tag in tags) {
         all_tag_counts[tags[tag]['pk']] ++;
      }
   });
   
   // Set the checkbox states depending on the number of objects
   var selected_stars = star_table.rows('.selected').data().length
   for (tag in all_tag_counts) {
      // Standard unchecked state, no object has this tag
      $(".tristate[value='"+tag+"']").prop("checked", false); 
      $(".tristate[value='"+tag+"']").prop("indeterminate",false);
      $(".tristate[value='"+tag+"']").removeClass("indeterminate");
      
      if ( all_tag_counts[tag] == selected_stars ){ 
         // checked state, all objects have this tag
         $(".tristate[value='"+tag+"']").prop("checked", true);
      } else if ( all_tag_counts[tag] > 0 ) {
         // indeterminate state, some objects have this tag
         $(".tristate[value='"+tag+"']").prop("indeterminate", true);
         $(".tristate[value='"+tag+"']").addClass("indeterminate");
      }
   }
   edit_tags_window.dialog( "open" );
}

function updateTags() {
   // Get the checked and indeterminate tags
   var checked_tags = $(".tristate:checked:not(.indeterminate)").map( 
      function () { return parseInt(this.value); } ).get();
   var indeterminate_tags = $(".tristate.indeterminate").map( 
      function () { return parseInt(this.value); } ).get();
   
   // Update the tags for each selected star
   star_table.rows('.selected').every( function ( rowIdx, tableLoop, rowLoop ) {
      var new_tags = checked_tags;
      var current_tags = this.data()['tags'].map( function (x) { return x.pk; } );
      
      for ( tag in indeterminate_tags ) {
         if ( current_tags.indexOf(indeterminate_tags[tag]) > -1 ) {
            new_tags.push(indeterminate_tags[tag])
         }
      }
      update_star_tags(this, new_tags);
      console.log(new_tags);
   });
   
}

function update_star_tags(row, new_tags){
   var star_pk = row.data()['pk']
   $.ajax({
      url : "/api/stars/stars/"+star_pk+'/', 
      type : "PATCH",
      contentType: "application/json; charset=utf-8",
      
      data : JSON.stringify({ "tag_ids": new_tags }),
      
      success : function(json) {
         // update the table and close the edit window
         row.data( json ).draw('page');
         edit_tags_window.dialog( "close" );
      },

      error : function(xhr,errmsg,err) {
         if (xhr.status == 403){
            $('#tag-error').text('You have to be logged in to edit');
         }else{
            $('#tag-error').text(xhr.status + ": " + xhr.responseText);
         }
         console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};


// Tristate checkbox functionality
function cylceTristate(event, checkbox) {
   checkbox = $(checkbox);
   // Add extra indeterminate state inbetween unchecked and checked
   if ( checkbox.prop("checked") & !checkbox.hasClass("indeterminate") ) {
      checkbox.prop("checked", false);
      checkbox.prop("indeterminate", true);
      checkbox.addClass("indeterminate");
   } else if ( checkbox.prop("checked") & checkbox.hasClass("indeterminate") ) {
      checkbox.prop("indeterminate", false);
      checkbox.removeClass("indeterminate");
   }
};
