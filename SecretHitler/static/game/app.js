if(typeof(EventSource) !== "undefined") {
  var source = new EventSource("stream/");
  source.onmessage = function(event) {
    console.log(event.data);
  };
} else {
  console.log("Sorry, your browser does not support server-sent events...");
}