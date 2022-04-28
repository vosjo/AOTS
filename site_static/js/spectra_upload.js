$(document).ready(function () {
    disabled_all();

    $('#id_flux_units').attr('disabled', 'disabled');

    $('#id_fluxcal').change(
        function () {
            if ($(this).is(':checked')) {
                $('#id_flux_units').removeAttr('disabled');
                $('#id_normalized').attr('disabled', 'disabled');
            } else {
                $('#id_flux_units').attr('disabled', 'disabled');
                $('#id_normalized').removeAttr('disabled');
            }
        }
    );

    $('#id_normalized').change(
        function () {
            if ($(this).is(':checked')) {
                $('#id_fluxcal').attr('disabled', 'disabled');
                $('#id_flux_units').attr('disabled', 'disabled');
            } else {
                $('#id_fluxcal').removeAttr('disabled');
                $('#id_flux_units').removeAttr('disabled');
            }
        }
    );

    $('#id_create_new_star').change(
        function () {
            if ($(this).is(':checked')) {
                $('#id_classification').removeAttr('disabled');
                $('#id_classification_type').removeAttr('disabled');
            } else {
                $('#id_classification').attr('disabled', 'disabled');
                $('#id_classification_type').attr('disabled', 'disabled');
            }
        });

    $('#id_observatory_is_spacecraft').change(
        function () {
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
        function () {
            if ($(this).val() == '') {
                $('#id_observatory_name').removeAttr('disabled');
                $('#id_observatory_is_spacecraft').removeAttr('disabled');
                if (!$('#id_observatory_is_spacecraft').is(':checked')) {
                    $('#id_observatory_latitude').removeAttr('disabled');
                    $('#id_observatory_longitude').removeAttr('disabled');
                    $('#id_observatory_altitude').removeAttr('disabled');
                }
                $('#th_observatory_name').addClass('underline');
                $('#th_observatory_is_spacecraft').addClass('underline');
                $('#th_observatory_latitude').addClass('underline');
                $('#th_observatory_longitude').addClass('underline');
                $('#th_observatory_altitude').addClass('underline');
                $('#th_observatory').removeClass('underline');
            } else {
                $('#id_observatory_name').attr('disabled', 'disabled');
                $('#id_observatory_is_spacecraft').attr('disabled', 'disabled');
                $('#id_observatory_latitude').attr('disabled', 'disabled');
                $('#id_observatory_longitude').attr('disabled', 'disabled');
                $('#id_observatory_altitude').attr('disabled', 'disabled');
                $('#th_observatory_name').removeClass('underline');
                $('#th_observatory_is_spacecraft').removeClass('underline');
                $('#th_observatory_latitude').removeClass('underline');
                $('#th_observatory_longitude').removeClass('underline');
                $('#th_observatory_altitude').removeClass('underline');
            }
            ;
        });

    $('#id_add_info').change(
        function () {
            if ($(this).is(':checked')) {
                $('#id_objectname').removeAttr('disabled');
                $('#id_ra').removeAttr('disabled');
                $('#id_dec').removeAttr('disabled');
                $('#id_create_new_star').removeAttr('disabled');
                $('#id_classification').removeAttr('disabled');
                $('#id_classification_type').removeAttr('disabled');
                $('#id_wind_speed').removeAttr('disabled');
                $('#id_wind_direction').removeAttr('disabled');
                $('#id_seeing').removeAttr('disabled');
                $('#id_airmass').removeAttr('disabled');
                $('#id_telescope').removeAttr('disabled');
                $('#id_instrument').removeAttr('disabled');
                $('#id_hjd').removeAttr('disabled');
                $('#id_exptime').removeAttr('disabled');
                $('#id_resolution').removeAttr('disabled');
                $('#id_snr').removeAttr('disabled');
                $('#id_observer').removeAttr('disabled');
                $('#id_observatory').removeAttr('disabled');
                $('#id_observatory_name').removeAttr('disabled');
                $('#id_observatory_is_spacecraft').removeAttr('disabled');
                $('#id_observatory_latitude').removeAttr('disabled');
                $('#id_observatory_longitude').removeAttr('disabled');
                $('#id_observatory_altitude').removeAttr('disabled');
                $('#id_normalized').removeAttr('disabled');
                $('#id_barycor_bool').removeAttr('disabled');
                $('#id_fluxcal').removeAttr('disabled');
                $('#id_flux_units').removeAttr('disabled');
                $('#id_note').removeAttr('disabled');
                $('#id_filetype').removeAttr('disabled');
                $('#user_info').removeClass('gray');
                $('h3').removeClass('gray');
            } else {
                disabled_all();
            }
            ;
        });
});

function disabled_all() {
    $('#id_objectname').attr('disabled', 'disabled');
    $('#id_ra').attr('disabled', 'disabled');
    $('#id_dec').attr('disabled', 'disabled');
    $('#id_create_new_star').attr('disabled', 'disabled');
    $('#id_classification').attr('disabled', 'disabled');
    $('#id_classification_type').attr('disabled', 'disabled');
    $('#id_wind_speed').attr('disabled', 'disabled');
    $('#id_wind_direction').attr('disabled', 'disabled');
    $('#id_seeing').attr('disabled', 'disabled');
    $('#id_airmass').attr('disabled', 'disabled');
    $('#id_telescope').attr('disabled', 'disabled');
    $('#id_instrument').attr('disabled', 'disabled');
    $('#id_hjd').attr('disabled', 'disabled');
    $('#id_exptime').attr('disabled', 'disabled');
    $('#id_resolution').attr('disabled', 'disabled');
    $('#id_snr').attr('disabled', 'disabled');
    $('#id_observer').attr('disabled', 'disabled');
    $('#id_observatory').attr('disabled', 'disabled');
    $('#id_observatory_name').attr('disabled', 'disabled');
    $('#id_observatory_is_spacecraft').attr('disabled', 'disabled');
    $('#id_observatory_latitude').attr('disabled', 'disabled');
    $('#id_observatory_longitude').attr('disabled', 'disabled');
    $('#id_observatory_altitude').attr('disabled', 'disabled');
    $('#id_normalized').attr('disabled', 'disabled');
    $('#id_barycor_bool').attr('disabled', 'disabled');
    $('#id_fluxcal').attr('disabled', 'disabled');
    $('#id_flux_units').attr('disabled', 'disabled');
    $('#id_note').attr('disabled', 'disabled');
    $('#id_filetype').attr('disabled', 'disabled');
    $('#user_info').addClass('gray');
    $('h3').addClass('gray');
}

