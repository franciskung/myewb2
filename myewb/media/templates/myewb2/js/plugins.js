
// usage: log('inside coolFunc', this, arguments);
window.log = function(){
  log.history = log.history || [];   // store logs to an array for reference
  log.history.push(arguments);
  if(this.console) {
      arguments.callee = arguments.callee.caller;
      console.log( Array.prototype.slice.call(arguments) );
  }
};
(function(b){function c(){}for(var d="assert,count,debug,dir,dirxml,error,exception,group,groupCollapsed,groupEnd,info,log,markTimeline,profile,profileEnd,time,timeEnd,trace,warn".split(","),a;a=d.pop();)b[a]=b[a]||c})(window.console=window.console||{});






/*

// jQuery available Plugin 1.6.1 (20101220)
// By John Terenzio | http://plugins.jquery.com/project/available | MIT License
(function($){var queue=[],interval,check=function(){for(var i=0;i<queue.length;i++){if($(queue[i][0])[0]&&(queue[i][2]||$(queue[i][0]).next()[0]||$.isReady)){try{queue[i][1].apply($(queue[i][0]).eq(0));}catch(e){if(typeof console!='undefined'){console.log(e);}}queue.splice(i,1);i--;}}if(!queue.length||$.isReady){interval=clearInterval(interval);}};$.fn.available=function(fn,turbo){turbo=turbo||false;queue.push([this.selector,fn,turbo]);if(!interval){interval=setInterval(check,1);}return this;};})(jQuery);


*/