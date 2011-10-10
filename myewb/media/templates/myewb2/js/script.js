/* Author:
Francis & Sean & friends
October 2011
*/



// delay-load of avatar images
// with many props to http://24ways.org/2010/speed-up-your-site-with-delayed-content

function runDelayedAvatarLoad() {

  $('[data-background-src]').css("background-image", function(index){
    console.log($(this).attr('data-background-src'));
    return "url(" + $(this).attr('data-background-src') + ")";

  });  


}





$(document).ready(function() {

  runDelayedAvatarLoad();
  // this is also run again by the frontpage's Ajax post loader

});
