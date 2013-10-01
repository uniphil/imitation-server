
(function() {
  var streamer = $("#streamer");

  var reset = function() {
    streamer.html('nothing streaming...');
  }; reset()

  var state = {};
  var get_state = function() {
    $.getJSON('/stream', function(data) {
      state = data;
      console.log(state);
      start_stream();
    });
  };

  get_state();

  var start_stream = function() {
    var im_path = '/frame/' + state.stream + '/0';
    streamer.css({background: "url('" + im_path + "')",
                  "background-size": "cover"});
    streamer.html('');
  };

})();
