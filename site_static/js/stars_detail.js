
var star = {}

$(document).ready(function() {

   // load the star info
   var star_id = $('#tag_list').attr('star_id')
   $.ajax({
      url : "/api/systems/stars/"+star_id+'/',
      type : "GET",
      success : function(json) {
         star = json;
         makepage();
      },
      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });

   // Initializing all dialog windows
   var update_note_window = $("#noteEdit").dialog({autoOpen: false,
            width: 'auto',
            modal: true});

   var add_identifier_window = $("#identifierAdd").dialog({autoOpen: false,
            width: 'auto',
            modal: true});

   var update_tag_window = $("#tadAdd").dialog({autoOpen: false,
            width: 'auto',
            modal: true});
   var all_parameters_window = $("#allParameters").dialog({autoOpen: false,
            title: 'Parameter Overview',
            width: 'auto',
            height: 'auto',
            modal: true});

   // add event listeners
   $( "#noteEditButton").click( openNoteUpdateBox );
   $( "#identifierAddButton").click( openIdentifierAddBox );
   $( "#tagEditButton").click( openTagEditBox );
   $( "#allParameterButton").click( openAllParameterBox );

   // Delete identifier on click
   $(".identifier").on('click', 'i[id^=delete-identifier-]', function(){
      var identifier_pk = $(this).attr('id').split('-')[2];
      delete_identifier(identifier_pk);
   });

   // toggle the observation section
   $('#toggle-obs').click( function (){
      $('#obs_summary').slideToggle();
      $('#obs_detail').slideToggle();

      if ($(this).text() == 'visibility') {
         $(this).text('visibility_off')
      } else {
         $(this).text('visibility')
      }

   });

});

// Create the page dynamicaly
function makepage () {
   show_tags () // handle the tags
};

function show_tags () {
   // Check which tags should be displayed in the tag window, and check the
   // included tags in the tag edit window.
   $('#tag_list').empty(); // remove all existing tags
   for (i=0; i<star.tags.length; i++) {
      var tag = star.tags[i];
      $('#tag_pk_'+tag.pk).prop("checked", true);
      $('#tag_list').append(
      "<div class='tag' id='tag-"+tag.pk+"' style='border-color:"+tag.color+"' title='"+tag.info+"'>"+tag.name+"</div>"
      );
   };
}


// Functionality to open the edit/update windows
function openNoteUpdateBox() {
   update_note_window = $("#noteEdit").dialog({
      buttons: { "Update": updateNote },
      close: function() { update_note_window.dialog( "close" ); }
   });

   update_note_window.dialog( "open" );
   $("#edit-message").val( $("#noteField").text().trim() );
};

function openIdentifierAddBox() {
   add_identifier_window = $("#identifierAdd").dialog({
      buttons: { "Add": create_identifier },
      close: function() { add_identifier_window.dialog( "close" ); }
   });

   add_identifier_window.dialog( "open" );
};

function openTagEditBox() {
   update_tag_window = $("#tadAdd").dialog({
      buttons: { "Update": update_tags },
      close: function() { update_tag_window.dialog( "close" ); }
   });

   update_tag_window.dialog( "open" );
};

function openAllParameterBox() {
   all_parameters_window = $("#allParameters").dialog({
      close: function() { all_parameters_window.dialog( "close" ); }
   });

   all_parameters_window.dialog( "open" );
};

// Update the comment of the star
function updateNote() {
   var star_id = $('#noteEditButton').attr('star_id')
   $.ajax({
      url : "/api/systems/stars/"+star_id+'/',
      type : "PATCH",
      data : { note: $("#edit-message").val().trim() },

      success : function(json) {
            update_note_window.dialog( "close" );
            $("#noteField").text(json.note);
            star.note = json.note;
      },

      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });
}

// Create an identifier
function create_identifier(){
   $.ajax({
      url : "/api/systems/identifiers/",
      type : "POST",
      data : { star : $('#identifierAddButton').attr('star_id'),
               name : $('#identifierAddtext').val() ,
               href : $('#identifierAddhref').val(),
      },

      success : function(json) {
//          add identifier to the list and close the window on success
            add_identifier_window.dialog( "close" );
            if (json.href != ""){
               $("#identifier_list").prepend("<div class=\"identifier\" id=\"identifier-"+json.pk+"\"> <a href=\"" +
               json.href+"\" target=\"_blank\">"+json.name+
               "</a> <i class=\"material-icons button delete\" id=\"delete-identifier-"+
               json.pk+"\">delete</i></div>");
            } else {
               $("#identifier_list").prepend("<div class=\"identifier\" id=\"identifier-"+json.pk+"\">"+json.name+
               "<i class=\"material-icons button delete\" id=\"delete-identifier-"+
               json.pk+"\">delete</i></div>");
            }
      },

      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};

// Delete an identifier
function delete_identifier(identifier_pk){
    if (confirm('Are you sure you want to remove this Identifier?')==true){
        $.ajax({
            url : "/api/systems/identifiers/"+identifier_pk+'/',
            type : "DELETE",

            success : function(json) {
              $('#identifier-'+identifier_pk).hide();
            },

            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    } else {
        return false;
    }
};

// Update the tags attached to this star
function update_tags(){
   var new_tags = $("#tagOptions input:checked").map(
       function () { return this.value; } ).get();
   var star_pk = $('#tagEditButton').attr('star_id')
   $.ajax({
      url : "/api/systems/stars/"+star_pk+'/',
      type : "PATCH",
      contentType: "application/json; charset=utf-8",

      data : JSON.stringify({ "tag_ids": new_tags }),

      success : function(json) {
         // update the tags of the star variable, and update the page
         star.tags = json.tags;
         show_tags();
         update_tag_window.dialog( "close" );
      },

      error : function(xhr,errmsg,err) {
         console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};
