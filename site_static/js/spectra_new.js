
$(document).ready(function() {
   
   $('#id_flux_units').attr('disabled', 'disabled');
   
   $('#id_fluxcal').change(
      function(){
         if ($(this).is(':checked')) {
            $('#id_flux_units').removeAttr('disabled');
         } else {
            $('#id_flux_units').attr('disabled', 'disabled');
         }
   });
   
   $('#id_observatory_is_spacecraft').change(
      function(){
         if ($(this).is(':checked')) {
            $('#id_observatory_latitude').attr('disabled', 'disabled');
            $('#id_observatory_longitude').attr('disabled', 'disabled');
            $('#id_observatory_altitude').attr('disabled', 'disabled');
         } else {
            $('#id_observatory_latitude').removeAttr('disabled');
            $('#id_observatory_longitude').removeAttr('disabled');
            $('#id_observatory_altitude').removeAttr('disabled');
         }
   });
   
   $('#id_observatory').change(
      function(){
         if ($(this).val() == '') {
            $('#id_observatory_name').removeAttr('disabled');
            $('#id_observatory_is_spacecraft').removeAttr('disabled');
            if (!$('#id_observatory_is_spacecraft').is(':checked')) {
               $('#id_observatory_latitude').removeAttr('disabled');
               $('#id_observatory_longitude').removeAttr('disabled');
               $('#id_observatory_altitude').removeAttr('disabled');
            }
         } else {
            $('#id_observatory_name').attr('disabled', 'disabled');
            $('#id_observatory_is_spacecraft').attr('disabled', 'disabled');
            $('#id_observatory_latitude').attr('disabled', 'disabled');
            $('#id_observatory_longitude').attr('disabled', 'disabled');
            $('#id_observatory_altitude').attr('disabled', 'disabled');
            
         };
   });
   
});


