
var header_window = null;

$(document).ready(function() {

   // Initializing all dialog windows
   header_window = $("#headerWindow").dialog({autoOpen: false, 
         close: function() { header_window.dialog( "close" ); },
         title: "File Header",
         width: 'auto',
         modal: true});

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