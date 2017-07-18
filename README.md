youtube-dl-server
=================

Credits go out to [meanbearwiz](https://twitter.com/manbearwiz) who created the project.
Very spartan and opinionated Web / REST interface for downloading youtube videos onto a server. [`bottle`](https://github.com/bottlepy/bottle) + [`youtube-dl`](https://github.com/rg3/youtube-dl).

![screenshot][1]

How to use this image
---------------------

###Run on host networking

```
python3 youtube-dl-server.py
```

###Start a download remotely

Downloads can be triggured by supplying the `{{url}}` of the requested video through the Web UI or through the REST interface via curl, etc.

####HTML

Just navigate to `http://{{address}}:8080/` and enter the requested `{{url}}`.

####Curl

```
curl -X POST --data-urlencode "url={{url}}" http://{{address}}:8080/youtube-dl/q
```

Implementation
--------------

The server uses [`bottle`](https://github.com/bottlepy/bottle) for the web framework and [`youtube-dl`](https://github.com/rg3/youtube-dl) to handle the downloading. For better or worse, the calls to youtube-dl are made through the shell rather then through the python API.

[1]: https://raw.githubusercontent.com/sqozz/youtube-dl-server/master/youtube-dl-server.png
