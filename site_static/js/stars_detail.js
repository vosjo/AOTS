var star = {}
let photeditenabled = false

$(document).ready(function () {

    // load the star info
    var star_id = $('#tag_list').attr('star_id')
    $.ajax({
        url: "/api/systems/stars/" + star_id + '/',
        type: "GET",
        success: function (json) {
            star = json;
            makepage();
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });

    // Initializing all dialog windows
    var update_note_window = $("#noteEdit").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });

    var add_identifier_window = $("#identifierAdd").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });

    var update_tag_window = $("#tadAdd").dialog({
        autoOpen: false,
        width: 'auto',
        modal: true
    });
    var all_parameters_window = $("#allParameters").dialog({
        autoOpen: false,
        title: 'Parameter Overview',
        width: 'auto',
        height: 'auto',
        modal: true
    });

    // add event listeners
    $("#noteEditButton").click(openNoteUpdateBox);
    $("#identifierAddButton").click(openIdentifierAddBox);
    $("#tagEditButton").click(openTagEditBox);
    $("#allParameterButton").click(openAllParameterBox);
    $("#photedit").click(enablephotedit);

    // Delete identifier on click
    $(".identifier").on('click', 'i[id^=delete-identifier-]', function () {
        var identifier_pk = $(this).attr('id').split('-')[2];
        delete_identifier(identifier_pk);
    });

    // toggle the observation section
    $('#toggle-obs').click(function () {
        $('#obs_summary').slideToggle();
        $('#obs_detail').slideToggle();

        if ($(this).text() == 'visibility') {
            $(this).text('visibility_off')
        } else {
            $(this).text('visibility')
        }

        $(".photvalconst").each(function () {
            let band = $(this).data("band")
            $(".dropdownlink").each(function () {
                if (band === $(this).data("band")) {
                    $(this).hide()
                }
            })
        });


    });
    $(".dropdownlink").click(function (e) {
        $(this).hide()
        let band = $(this).data("band")
        $(".phottablerow").each(function (i, row) {
            let rowband = $(row).find('td[class="mono"]').text()
            if (rowband === band) {
                console.log($(row).find('td[class="photvalconst"]'))
                if (!$(row).find('td[class="photvalconst"]').length) {
                    $(this).show()
                }
            }
        })
        let novaluesrow = $("#tr-novaluesyet")
        if (novaluesrow.is(":visible")){
            novaluesrow.hide()
        }
    })
    $(".rmband").click(function (e) {
        let band;
        $(this).parent().parent().children().each(function (){
            if (typeof $(this).attr("class") != "undefined") {
                if ($(this).attr("class") === "photvalinp") {
                    band = $(this).data("band")
                    let inp = $(this).children()[0]
                    $(inp).val("")
                }
                else {
                    if ($(this).attr("class") === "photerrinp"){
                        let err = $(this).children()[0]
                        $(err).val("")
                    }
                }
            }
            $(this).closest(".phottablerow").hide()
            $(".dropdownlink").each(function (i, row) {
                if ($(this).data("band") === band){
                    $(this).show()
                }
            })
        })
    })
});

// Create the page dynamicaly
function makepage() {
    show_tags() // handle the tags
}

function show_tags() {
    // Check which tags should be displayed in the tag window, and check the
    // included tags in the tag edit window.
    $('#tag_list').empty(); // remove all existing tags
    for (i = 0; i < star.tags.length; i++) {
        var tag = star.tags[i];
        $('#tag_pk_' + tag.pk).prop("checked", true);
        $('#tag_list').append(
            "<div class='tag' id='tag-" + tag.pk + "' style='border-color:" + tag.color + "' title='" + tag.info + "'>" + tag.name + "</div>"
        );
    }

}


// Functionality to open the edit/update windows
function openNoteUpdateBox() {
    update_note_window = $("#noteEdit").dialog({
        buttons: {"Update": updateNote},
        close: function () {
            update_note_window.dialog("close");
        }
    });

    update_note_window.dialog("open");
    $("#edit-message").val($("#noteField").text().trim());
}

function openIdentifierAddBox() {
    add_identifier_window = $("#identifierAdd").dialog({
        buttons: {"Add": create_identifier},
        close: function () {
            add_identifier_window.dialog("close");
        }
    });

    add_identifier_window.dialog("open");
}

function openTagEditBox() {
    update_tag_window = $("#tadAdd").dialog({
        buttons: {"Update": update_tags},
        close: function () {
            update_tag_window.dialog("close");
        }
    });

    update_tag_window.dialog("open");
}

function openAllParameterBox() {
    all_parameters_window = $("#allParameters").dialog({
        close: function () {
            all_parameters_window.dialog("close");
        }
    });

    all_parameters_window.dialog("open");
}

// Update the comment of the star
function updateNote() {
    var star_id = $('#noteEditButton').attr('star_id')
    $.ajax({
        url: "/api/systems/stars/" + star_id + '/',
        type: "PATCH",
        data: {note: $("#edit-message").val().trim()},

        success: function (json) {
            update_note_window.dialog("close");
            $("#noteField").text(json.note);
            star.note = json.note;
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

// Create an identifier
function create_identifier() {
    $.ajax({
        url: "/api/systems/identifiers/",
        type: "POST",
        data: {
            star: $('#identifierAddButton').attr('star_id'),
            name: $('#identifierAddtext').val(),
            href: $('#identifierAddhref').val(),
        },

        success: function (json) {
//          add identifier to the list and close the window on success
            add_identifier_window.dialog("close");
            if (json.href != "") {
                $("#identifier_list").prepend("<div class=\"identifier\" id=\"identifier-" + json.pk + "\"> <a href=\"" +
                    json.href + "\" target=\"_blank\">" + json.name +
                    "</a> <i class=\"material-icons button delete\" id=\"delete-identifier-" +
                    json.pk + "\">delete</i></div>");
            } else {
                $("#identifier_list").prepend("<div class=\"identifier\" id=\"identifier-" + json.pk + "\">" + json.name +
                    "<i class=\"material-icons button delete\" id=\"delete-identifier-" +
                    json.pk + "\">delete</i></div>");
            }
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

// Delete an identifier
function delete_identifier(identifier_pk) {
    if (confirm('Are you sure you want to remove this Identifier?') == true) {
        $.ajax({
            url: "/api/systems/identifiers/" + identifier_pk + '/',
            type: "DELETE",

            success: function (json) {
                $('#identifier-' + identifier_pk).hide();
            },

            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    } else {
        return false;
    }
}

// Update the tags attached to this star
function update_tags() {
    var new_tags = $("#tagOptions input:checked").map(
        function () {
            return this.value;
        }).get();
    var star_pk = $('#tagEditButton').attr('star_id')
    $.ajax({
        url: "/api/systems/stars/" + star_pk + '/',
        type: "PATCH",
        contentType: "application/json; charset=utf-8",

        data: JSON.stringify({"tag_ids": new_tags}),

        success: function (json) {
            // update the tags of the star variable, and update the page
            star.tags = json.tags;
            show_tags();
            update_tag_window.dialog("close");
        },

        error: function (xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

// Enable Editing Photometry on Button click
function enablephotedit() {
    photedit = $("#photedit");
    if (photeditenabled) {
        photedit.show();
        $("#phot-submit-btn").hide();
        $(".photval").each(function (ind, obj) {
        });
        $(".photerr").each(function (ind, obj) {
        });
        $("#submitrow").hide();
        $("#addband").hide();
        photeditenabled = false;
    } else {
        photedit.hide();
        $("#phot-submit-btn").show();
        let existingbands = [];
        let bandvalues = [];
        let banderrvalues = [];
        $(".photvalconst").each(function (ind, obj) {
            let band = $(this).data("band");
            existingbands.push(band);
            let magval = parseFloat($(this).text());
            bandvalues.push(magval);
            $(this).closest('tr').hide();
            $(".dropdownlink").each(function(){
                if ($(this).data("band") === band){
                    $(this).hide()
                }
            })
        });
        $(".photerrconst").each(function (ind, obj) {
            let magval = parseFloat($(this).text());
            banderrvalues.push(magval);
        });
        $(".photvalinp").each(function (ind, obj) {
            let band = $(this).data("band");
            let arrind = jQuery.inArray(band, existingbands);
            if (arrind > -1) {
                $(this).closest('tr').show();
                $(this).find('input[type=number]').val(bandvalues[arrind]);
                $(this).parent().find('td[class=photerrinp]').find('input[type=number]').val(banderrvalues[arrind]);
            }
        });
        $("#submitrow").show();
        $("#addband").show();
        $("#getvizier").show();
        photeditenabled = true;
    }
}


function Toggledropdown() {
    $("#addbanddropdown").toggleClass("show");
}


// Close the dropdown menu if the user clicks outside of it
$(window).click(function (e) {
    if (!e.target.matches('.dropbtn')) {
        $(".dropdown-content").each(function (i) {
            if ($(this).hasClass('show')) {
                $(this).removeClass('show');
            }
        })
    }
})

function GetVizier() {

}