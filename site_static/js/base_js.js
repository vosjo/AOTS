/*
 Code part to take care of the csrf token 
*/

let opacityInterval = null;

$(function () {
    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    /*
    The functions below will create a header with csrftoken
    */

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

});


function msg_fade_out(messages){
    setTimeout(function() {
        opacityInterval = setInterval(function () {
            let currentOpacity = parseFloat(messages.style.opacity);

            let newOpacity = currentOpacity - 0.01;

            // Set the new opacity of the list
            messages.style.opacity = newOpacity;

            // Stop the interval when the opacity reaches 0
            if (newOpacity <= 0.1) {
                clearInterval(opacityInterval);
            }
        }, 100);
    }, 5000);
}


// Adjust nav bar highlight
function adjust_nav_bar_active(id_class, drop_down=true) {
    $(".float_right").find('.active').each(function (i) {
        $(this).removeClass('active');
    })

    if (drop_down) {
        $(id_class).find('.drop_button').addClass('active');
    } else {
        $(id_class).addClass('active');
    }
}

$(document).ready(function () {
    // Get the 1st and 2nd level path names
    var firstLevel = window.location.pathname.split('/')[1]
    var secondLevel = window.location.pathname

    // Copy the correct navigation subdivision into the 2nd level navigation bar
//    $('a[href*="'+secondLevel+'"]').siblings('ul').clone().appendTo("#subtoolbar");

    // toggle the active class for the 1st and 2nd level navigation bar
//    $('#toolbar a[href*="/' + secondLevel + '"]').parent('li').toggleClass('active');
//    $('#subtoolbar a[href*="'+secondLevel+'"]').parent('li').toggleClass('active');

    const messages = document.getElementById("messages");

    if ( messages ){
        const listItems = messages.getElementsByTagName("li");

        for (let i = listItems.length - 1; i >= 0; i--) {
            const btn = document.createElement("button");

            btn.appendChild(document.createTextNode("\u{00d7}"));

            btn.classList.add("remove-msg-btn");

            listItems[i].insertBefore(btn, listItems[i].childNodes[0]);

            btn.addEventListener("click", function() {
                const listItem = this.parentNode;
                listItem.parentNode.removeChild(listItem);
            });
        }

        messages.style.opacity = 1;

        msg_fade_out(messages);

        // Add a mouseenter event listener to the list
        messages.addEventListener("mouseenter", function() {
          // Set the opacity of the list to 1
          messages.style.opacity = 1;

          // Stop the opacity interval
          clearInterval(opacityInterval);
        });

        // Add a mouseleave event listener to the list
        messages.addEventListener("mouseleave", function() {
          msg_fade_out(messages)
        });
    }

    // Open/close the navigation menu in "responsive mode"
    $("#menu_icon").click(function (e) {
      var x = document.getElementById("mainNavBar");
      if (x.className === "nav_bar") {
        x.className += " responsive";
      } else {
        x.className = "nav_bar";
      }

      var caret_right = document.getElementById("caretRight");
      if (caret_right.className === "fa fa-caret-right") {
        caret_right.className = "fa fa-caret-down";
      } else {
        caret_right.className = "fa fa-caret-right";
      }
    })

    // Open/close the submenu if the user clicks on it
    $(".drop_button").click(function (e) {
        $(this).parent().find(".nav_dropdown-content").each(function (i) {
            if ($(this).hasClass('show')) {
                $(this).removeClass('show');
            } else {
                $(this).addClass('show');
            }
        })
    })

    // Open/close the subsubmenu if the user clicks on it
    $(".unfold_button").click(function (e) {
        if (document.documentElement.clientWidth < 1100) {
            $(this).parent().find(".unfold-content").each(function (i) {
                if ($(this).hasClass('show_right')) {
                    $(this).removeClass('show_right');
                } else {
                    $(this).addClass('show_right');
                }
            })
        }
    })

    // Close the dropdown menu of the nav bar if the user clicks outside of it
    $(window).click(function (e) {
        if (!e.target.matches('.drop_button') && !e.target.matches('.unfold_button')) {
    //       openNavMenu();
            $(".nav_dropdown-content").each(function (i) {
                if ($(this).hasClass('show')) {
                    $(this).removeClass('show');
                }
            })
        }
    })

});
