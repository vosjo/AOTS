
var specfile_table = null;

$(document).ready(function () {

   // Table functionality
   specfile_table = $('#specfiletable').DataTable({
   autoWidth: false,
   serverSide: true,
   ajax: {
      url: '/api/observations/specfiles/?format=datatables',
      data: get_filter_keywords,
   },
   searching: false,
   orderMulti: false, //Can only order on one column at a time
   order: [0],
   columns: [
      { data: 'hjd' },
      { data: 'instrument' },
      { data: 'filetype' },
      { data: 'filename' },
      { data: 'added_on' },
      { data: 'star' , orderable: false, render: star_render},
      { data: 'spectrum', render : processed_render },
      { data: 'pk', render: action_render, width: '100',
        className: 'dt-center', visible: user_authenticated, orderable: false},
   ],
   paging: true,
   pageLength: 20,
   lengthMenu: [[10, 20, 50, 100, 1000], [10, 20, 50, 100, 1000]], // Use -1 for all.
   scrollY: $(window).height() - $('header').outerHeight(true) - $('.upload').outerHeight(true) - $('#messages').outerHeight(true) - 186,
   scrollCollapse: true,
   });

   // Event listener to the two range filtering inputs to redraw on input
   $('#filter-form').submit( function(event) {
      event.preventDefault();
      specfile_table.draw();
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

    //  Adjust form drop dropdown content - First read System drop down
    $("#id_system").change(function() {
        //  Set pk list
        let pk_list = $(this).val();

        //  Clear Specfile drop down
        document.getElementById("id_specfile").length = 0;
        $("#id_specfile").val([]);

        //  Loop over pks
        $.each(pk_list, function(index, pk) {
            //  Get Specfile info as JASON
            $.getJSON("/api/systems/stars/"+pk+'/specfiles/', function(data){
                //  Refilling Specfile drop down
                for (let key in data){
                    if (data.hasOwnProperty(key)){
                        let value=data[key];
                        $("#id_specfile").append("<option value = \"" + key + "\">" + value + "</option>");
                    }
                };
            });
        });
    });

    //  Add progress bar for raw data file upload
    $("#raw-upload-form").submit(function(e){
        //  Prevent normal behaviour
        e.preventDefault();
        //  Get form
        $form = $(this);
        //  Create new form
        let formData = new FormData(this);
        //  Get files
        const rawfiles = document.getElementById('id_rawfile');
        const data     = rawfiles.files[0];
        //  Display progress bar
        if(data != null){
            $("#progress-bar").removeClass("hidden");
        };
        //  Get project
        let project = $('#project-pk').attr('project_slug')
        //  Ajax call to make it happen
        $.ajax({
            type: 'POST',
            url:'/w/'+project+'/observations/rawspecfiles/',
            data: formData,
            dataType: 'json',
            xhr: function(){
                //  Handel progress bar updates
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e=>{
                    if(e.lengthComputable){
                        const percentProgress = (e.loaded/e.total)*100;
                        $("#progress-bar").val(percentProgress);
                    }
                });
                return xhr
            },
            success: function(response){
                //  Set extract and set message
                $.each(response.messages, function(id, message_list) {
                    let success = message_list[0];
                    let message = message_list[1];

                    if (success == true){
                        $("#messages").append(
                            "<li class=\"success\">"+message+"</li>"
                        );
                    } else if (success == false){
                        $("#messages").append(
                            "<li class=\"error\">"+message+"</li>"
                        );
                    } else {
                        $("#messages").append(
                            "<li class=\"error\">An undefined error has occurred.</li>"
                        );
                    };
                });

                //  Reset form fields
                $("#raw-upload-form")[0].reset();

                //  Reset Specfile dropdown that is not reset by the line above
                $("#id_system>option").map( function() {
                    //  Set pk
                    let pk = $(this).val();
                    //  Get Specfile info as JASON
                    $.getJSON("/api/systems/stars/"+pk+'/specfiles/', function(data){
                        //  Refilling Specfile drop down
                        for (let key in data){
                            if (data.hasOwnProperty(key)){
                                let value=data[key];
                                $("#id_specfile").append(
                                    "<option value = \"" + key + "\">" + value
                                    +"</option>");
                            }
                        };
                    });
                });

                //  Remove progress bar
//                 $("#progress-bar").addClass("not-visible");
            },
            error: function(err){
                console.log('error', err);
                alert(err.statusText);
            },
            cache: false,
            contentType: false,
            processData: false,
        });
    });
});


// Table filter functionality

function get_filter_keywords( d ) {

   d = $.extend( {}, d, {
      "project": $('#project-pk').attr('project'),
      "target": $('#filter_target').val(),
      "instrument": $('#filter_instrument').val(),
      "filename": $('#filter_filename').val(),
      "filetype": $('#filter_filetype').val(),
   } );

   if ($('#filter_hjd').val() != '') {
      d = $.extend( {}, d, {
//          "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] | 0 ),
//          "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] | 1000000000),
         "hjd_min": parseFloat( $('#filter_hjd').val().split(':')[0] ),
         "hjd_max": parseFloat( $('#filter_hjd').val().split(':')[1] ),
      } );
   }

   return d
}


//  Table renderers

function star_render( data, type, full, meta ) {
    let systems = [];
    for(let key in data){
        if (data.hasOwnProperty(key)){
            let value=data[key];
            systems.push("<a href='" + value + "' > " + key + "</a>");
        }
    };
    return systems
}

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

//  Further function
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
