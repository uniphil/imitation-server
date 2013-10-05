#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    imitate
    ~~~~~~~

    a simple web server for pushing scheduled images to clients
    built for the film project "Imitation" by Matthieu and Phil

    folders for frames are constructed based on the video filename
        video/blah123.mov -> frames/blah123/frame{0..n}.jpg
"""


import os
import pickle
from datetime import datetime
from flask import (Flask, request, render_template, stream_with_context,
                   Response, url_for, send_file, redirect, jsonify)
app = Flask(__name__)


js_redirect = lambda endpoint: '<script>window.location="{}"</script>'\
                                .format(url_for(endpoint))


if 'video' not in os.listdir('.'):
    os.makedirs('video')
if 'frames' not in os.listdir('.'):
    os.makedirs('frames')


@app.route('/controller')
def controller():
    # 0. get the current status
    try:
        with open('state.pickle', 'rb') as p:
            state = pickle.load(p)
    except IOError:
        state = {'stream': None, 'start': None, 'interval': None, 'frames': 0}
        with open('state.pickle', 'wb') as p:
            pickle.dump(state, p)
    # 1. get available video files
    videos = os.listdir('video')
    try:
        video_names = set(n.rsplit('.', 1)[0] for n in videos)
    except IndexError:
        return 'one or more videos lacked a file extension', 400
    # 2. get available frames folders
    frame_sources = set(os.listdir('frames'))
    # 3. get videos to export
    unchopped = video_names - frame_sources
    unchopped_videos = ([v for v in videos if v.startswith(f)][0] for f in unchopped)
    # 4. wrap it all up nicely
    return render_template('controller.html', state=state,
                           frames=frame_sources, unchopped=unchopped_videos)


@app.route('/chop')
def chop():
    import time
    import subprocess

    vid = request.args.get('video')
    if vid is None:
        return 'missing parameter: video', 400
    try:
        stream_folder = vid.rsplit('.', 1)[0]
        stream_dir = 'frames/{}'.format(stream_folder)
    except IndexError:
        return 'the video seems to be missing a file extension?', 400
    try:
        assert vid in os.listdir('video')
    except AssertionError:
        return 'could not find video {}'.format(vid), 404
    try:
        os.makedirs(stream_dir)
    except FileExistsError:
        return 'frames already exist in {}'.format(stream_dir)

    vid_dir = 'video/{}'.format(vid)
    frame_path = '{}/frame%04d.jpg'.format(stream_dir)

    splitter_cmd = ['avconv', '-i', vid_dir, '-s', '1280x720', frame_path]
    splitter = subprocess.Popen(splitter_cmd)

    def split():
        yield '<pre>'
        n = 0
        while splitter.poll() is None:
            n += 1
            stuff = len(os.listdir(stream_dir))
            yield '{} '.format(stuff)
            if not n % 18:
                yield '<br/>'
            time.sleep(0.5)
        yield '<br/>Done!</pre>'
        yield js_redirect('controller')
    return Response(stream_with_context(split()))


@app.route('/clean')
def clean():
    import shutil
    vid = request.args.get('video')
    if vid is None:
        return 'missing parameter: video', 400
    try:
        stream_folder = vid.rsplit('.', 1)[0]
        stream_dir = 'frames/{}'.format(stream_folder)
    except IndexError:
        return 'the video seems to be missing a file extension?', 400
    try:
        assert stream_folder in os.listdir('frames')
    except AssertionError:
        return 'frames not found', 404
    try:
        assert any(v.startswith(vid) for v in os.listdir('video'))
    except AssertionError:
        return 'there is no video to fall back on {}'.format(vid), 404
    try:
        shutil.rmtree(stream_dir)
    except OSError as e:
        return '<pre>some kind of oserror -- {}</pre>'.format(e)

    return js_redirect('controller')


@app.route('/stream/<frames>')
def stream(frames):
    stream_dir = 'frames/{}'.format(frames)
    try:
        assert frames in os.listdir('frames')
    except AssertionError:
        return 'frames not found', 404
    period=request.args.get('period')
    if period is None:
        with open('state.pickle', 'rb') as p:
            s = pickle.load(p)
            pperiod=s.get('interval') or 3
        return render_template('stream-setup.html', stream=frames, pp=pperiod)
    try:
        period = int(period)
    except ValueError:
        return 'invalid period {}'.format(period)

    with open('state.pickle', 'wb') as p:
        # stamp = datetime.now().timestamp()
        num_frames = len(os.listdir(stream_dir))
        state = {'stream': frames, 'start': None, 'interval': period,
                 'frames': num_frames}
        pickle.dump(state, p)

    return redirect(url_for('controller'))


@app.route('/stream/stop')
def stop():
    with open('state.pickle', 'rb') as p:
        state = pickle.load(p)
    state['start'] = None
    with open('state.pickle', 'wb') as p:
        pickle.dump(state, p)
    return jsonify(state)


@app.route('/stream/start')
def start():
    try:
        assert 'timestamp' in request.args
    except AssertionError:
        return 'missing timestamp to start', 400
    with open('state.pickle', 'rb') as p:
        state = pickle.load(p)
    try:
        state['start'] = int(request.args['timestamp'])
    except ValueError:
        return 'timestamp must be an int', 400
    with open('state.pickle', 'wb') as p:
        pickle.dump(state, p)
    return jsonify(state)


@app.route('/stream')
def client_stream():
    with open('state.pickle', 'rb') as p:
        state = pickle.load(p)
    return jsonify(state)


@app.route('/frame/<stream>/<int:n>')
def frame(stream, n):
    try:
        f = sorted(os.listdir('frames/{}'.format(stream)))[n]
    except IndexError:
        return 'frame {} not found for {}'.format(n, stream), 404
    img_path = 'frames/{}/{}'.format(stream, f)
    return send_file(img_path, mimetype='image/jpeg')


@app.route('/')
def client():
    return render_template('client.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
