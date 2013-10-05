
var StreamPlay = function(view_el) {

  this.endpoint = '/stream';
  this.state = {};
  this.mode = 'idle';
  this.endpoint_check_freq = 2000;  // ms
  this.bump = 200;  // ms
  // this.preload = 3;
  this.message_el = $('<span></span>');
  this.preload_el = $('<img class="preloader" src="" />');
  view_el.append(this.message_el);
  view_el.append(this.preload_el);


  this.setTimeout = function(callback, delay) {
    var othis = this,
        args = Array.prototype.slice.call(arguments, 2);
    return setTimeout(callback instanceof Function ?
      function() { callback.apply(othis, args); } :
      callback, delay);
  };


  this.setInterval = function(callback, delay) {
    var othis = this,
        args = Array.prototype.slice.call(arguments, 2);
    return setInterval(callback instanceof Function ?
      function() { callback.apply(othis, args); } :
      callback, delay);
  };


  this.check_state = function() {
    $this = this;
    $.ajax({
      type: 'GET',
      url: this.endpoint,
      success: function() { $this.update_state.apply($this, arguments); },
      error: function() { $this.notify_error.apply($this, arguments); },
    });
  };


  this.update_state = function(server_state) {
    this.state = server_state;

    if (this.state.start === null) {
      if (this.state.stream !== null && this.mode !== 'paused') {
        this.pause_stream();
      }
      return;
    }

    // where are we in the current stream?
    var stream_start = new Date(this.state.start),
        now = new Date();
    var current_frame = (now - stream_start) / (this.state.interval * 1000);

    // has the stream expired yet?
    if (current_frame > this.state.frames) {
      console.log('all frames are done (' + current_frame + ')');
      this.stop_stream();
      return;
    }

    if (this.mode !== 'streaming'){
      this.start_stream();
    }

  };


  this.notify_error = function() {
    console.log('connection error');
    this.message_el.text('connection error.');
    view_el.css({background: 'black'});
    this.mode = 'idle';
  };


  this.stop_stream = function() {
    if (this.mode !== 'idle') {
      console.log('stop_stream: going to idle');
      this.message_el.text('nothing streaming...');
      view_el.css({background: 'black'});
      this.mode = 'idle';
    }
  };


  this.start_stream = function() {
    console.log('start_stream: starting up');
    this.message_el.text('');
    this.mode = 'streaming';
    this.show_frame();
  };


  this.pause_stream = function() {
    console.log('pause_stream: pausing');
    this.message_el.text('paused');
    this.mode = 'paused';
    var bg_path = '/frame/' + this.state.stream + '/0';
    view_el.css({'background': "url('" + bg_path + "') 50% no-repeat",
                 'background-size': 'contain'});
  }


  this.show_frame = function() {
    if (this.state.start === null) {
      return;
    }
    // where are we in the current stream?
    var stream_start = new Date(this.state.start),
        now = new Date();
    var frame_time = (now - stream_start) / (this.state.interval * 1000);
    var this_frame = Math.round(frame_time);
    var next_frame = this_frame + 1;
    var next_time = +stream_start + (this.state.interval*1000 * next_frame);

    console.log('showing frame ' + this_frame);
    var bg_path = '/frame/' + this.state.stream + '/' + this_frame;
    view_el.css({'background': "url('" + bg_path + "') 50% no-repeat",
                 'background-size': 'contain'});

    if (this.mode === 'streaming') {
      var time_to_next = (next_time - new Date());
      this.setTimeout(this.show_frame, time_to_next);
      this.preload_frame(next_frame);
    }
  };


  this.preload_frame = function(frame_num) {
    var preload_path = '/frame/' + this.state.stream + '/' + frame_num;
    this.preload_el.attr('src', preload_path);
  };


  this.startstop = function() {
    console.log('startstop');
    if (this.state.start === null) {
      $.ajax({
        type: 'GET',
        url: this.endpoint + '/start?timestamp=' + +new Date(),
        // args: {timestamp: +(new Date())},
      });
      return 'started';
    } else {
      $.ajax({
        type: 'GET',
        url: this.endpoint + '/stop',
      });
      return 'stopped';
    }
  };


  this.bump_back = function() {
    console.log('bumping back');
    $.ajax({
      type: 'GET',
      url: this.endpoint + '/start?timestamp=' + (this.state.start + this.bump)
    });
  };


  this.bump_forward = function() {
    console.log('bump forward');
    $.ajax({
      type: 'GET',
      url: this.endpoint + '/start?timestamp=' + (this.state.start - this.bump)
    });
  };
 

  this.set_controls = function(ctl) {
    $this = this;
    $('.startstop', ctl).click(function() {
      $(this).text($this.startstop() === 'started' ? 'stop' : 'start');
    });
    $('.bump.back', ctl).click(function() { $this.bump_back(); });
    $('.bump.forward', ctl).click(function() { $this.bump_forward(); });
  };


  this.init = function() {
    this.setInterval(this.check_state, this.endpoint_check_freq);
  };
};


var streamer_el = $("#streamer");
var controls = $(".control-block");
var streamer = null;

if (streamer_el.length > 0) {
  streamer = new StreamPlay(streamer_el);
  streamer.init();
}
if (streamer && controls.length > 0) {
  streamer.set_controls(controls);
}
