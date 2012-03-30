

var timeout_id = 0;
var cheers_timeout_id = 0;

// this goes into the external javascript file later
function install_cheers(cheersUrl) {
    $('.cheers').unbind('click');
    $('.cheers_detail').unbind('click');
    $('.cheers_remove').unbind('click');

    /*    
    $('.cheers').click(function() {
        var cheerslink = $(this);
        $.get($(this).attr('href'), function(data) {
            $('.cheerscount', cheerslink.parent()).html(data);
            cheerslink.hide();
        });
        return false;
    });
    */
    
    $('.cheers').colorbox({opacity: '0.5', width: '600px', height: '50%'});
    $('.cheers_detail').colorbox({opacity: '0.5', width: '600px', height: '50%'});
    
    $('.cheers_remove').click(function() {
        if (confirm("Are you sure you want to remove this?"))
        {
            $.get($(this).attr('href'),
                  function() {
                    refresh_cheerslist(cheersUrl);
                  });
        }
        return false;
    });
}

// so does this
function install_watchlists() {
    $('.watchlist-toggle').unbind('click');
    
    $('.watchlist-toggle').click(function() {
        var my_id = $(this).attr('id').substr(17);

        if($(this).hasClass('toggle-remove')) {
            // remove it from the watchlist when clicked
            var my_obj = $(this);
            $.get($(this).attr('href') + my_id + '/',
                function() {
                    my_obj.removeClass('toggle-remove');
                    my_obj.addClass('toggle-add');
                    my_obj.addClass('faded');
                });
        } else {
            var my_obj = $(this);
            $.get($(this).attr('href') + my_id + '/',
                function() {
                    my_obj.removeClass('toggle-add');
                    my_obj.addClass('toggle-remove');
                    my_obj.removeClass('faded');
                });
        }
        return false;
    });

	$('.topic_views').colorbox({iframe: true, width: "80%", height: "80%"});
}

function load_homepage_posts()   // now, this'll be a behind-the-scenes function that's only called by hashchanges.
{
  clearTimeout(timeout_id);

  fetchUrl = "/?ajax=1";

  $.ajax({
    url: fetchUrl,
    success: function(data) {
    
      $(document).ready(function() {
        $('#topiclisting').html(data);
        
        runDelayedAvatarLoad();

        install_watchlists();
        install_cheers();
      });
    }
    
  });

  // and set a timer to auto-refresh... every half hour, let's say?
  timeout_id = setTimeout('load_homepage_posts()', 30 * 60 * 1000, true);
}



function chapter_dashboard(fetchUrl)
{
    $.ajax({
        url: fetchUrl,
        success: function(data) {
            $(document).ready(function() {
                  $('#chapter_dashboard').html(data);
      
		          $('#dashboard_links a').mouseover(function() {
					var myname = $(this).attr('id').substr(10);
					$('.dashboard-detail').hide();
					$('#' + myname).show();

					$('#dashboard_links a').removeClass('current');
					$(this).addClass('current');
				  });
            });
        }
    });
}

