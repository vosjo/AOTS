
var header_window = null;

$(document).ready(function() {

   // Initializing all dialog windows
   header_window = $("#headerWindow").dialog({autoOpen: false, 
         close: function() { header_window.dialog( "close" ); },
         title: "File Header",
         width: 'auto',
         modal: true});
   
   var update_note_window = $("#noteEdit").dialog({autoOpen: false, 
            width: 'auto',
            modal: true});
   
   var edit_spectrum_window = $("#spectrumEdit").dialog({autoOpen: false, 
            width: 'auto',
            modal: true});

   
   // add event listeners
   $( "#noteEditButton").click( openNoteUpdateBox );
   $( "#spectrumEditButton").click( openSpectrumEditBox );
   
   $(".showheader").click(function( event ){
      event.preventDefault();
      // get the header information
      $.ajax({
            url : $(this).attr('href'),
            type : "GET", 
            success : function(json) {
               $('#headerList').empty() //remove all header items
               for (var key in json) {  //add new header items
                  $('#headerList').append("<li> <span class='header-key'>"+key+"</span> : <span class='header-value'>"+json[key]+"</span></li>")
               }
               console.log(json);
            },

            error : function(xhr,errmsg,err) {
               console.log(xhr.status + ": " + xhr.responseText); 
            }
      });
      
      header_window = $("#headerWindow").dialog({
         maxHeight:$(window).height()*0.98,
         title: $(this).attr('name'),
         position: { my: "center top", at: "center top", of: window },
      });
      
      header_window.dialog( "open" );
      
   });

});


// Functionality to open the edit/update windows
function openNoteUpdateBox() {
   update_note_window = $("#noteEdit").dialog({
      buttons: { "Update": updateNote },
      close: function() { update_note_window.dialog( "close" ); }
   });
      
   update_note_window.dialog( "open" );
   $("#edit-message").val( $("#noteField").text().trim() ); 
};


function openSpectrumEditBox() {
   edit_spectrum_window = $("#spectrumEdit").dialog({
      buttons: { "Update": editSpectrum },
      close: function() { edit_spectrum_window.dialog( "close" ); }
   });
      
   edit_spectrum_window.dialog( "open" );
   $("#spectrum-valid").val( true ); 
   $("#spectrum-fluxcal").val( false ); 
   $("#spectrum-fluxunits").val( 'test' ); 
};


// Update the note of the spectrum
function updateNote() {
   var spectrum_id = $('#noteEditButton').attr('spectrum_id')
   $.ajax({
      url : "/api/observations/spectra/"+spectrum_id+'/', 
      type : "PATCH",
      data : { note: $("#edit-message").val().trim() },
      
      success : function(json) {
            update_note_window.dialog( "close" );
            $("#noteField").text(json.note);
//             star.note = json.note;
      },

      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};


function editSpectrum() {
   var spectrum_id = $('#spectrumEditButton').attr('spectrum_id')
   
   $.ajax({
      url : "/api/observations/spectra/"+spectrum_id+'/',
      type : "PATCH",
      data : { valid: $("#spectrum-valid").is(':checked'),
               fluxcal: $("#spectrum-fluxcal").is(':checked'),
               flux_units: $("#spectrum-fluxunits").val().trim()
             },
      
      success : function(json) {
            edit_spectrum_window.dialog( "close" );
            
            if (json.valid) {
               $("#spectrum-valid-icon").removeClass("invalid")
               $("#spectrum-valid-icon").addClass("valid")
            } else {
               $("#spectrum-valid-icon").addClass("invalid")
               $("#spectrum-valid-icon").removeClass("valid")
            };
            
            if (json.fluxcal) {
               $("#spectrum-fluxcal-icon").removeClass("invalid")
               $("#spectrum-fluxcal-icon").addClass("valid")
            } else {
               $("#spectrum-fluxcal-icon").addClass("invalid")
               $("#spectrum-fluxcal-icon").removeClass("valid")
            };
      },

      error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
      }
   });
};
