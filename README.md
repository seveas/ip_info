ip\_info
=======

Really simple flask app that provides you info about where you're connecting
from. Similar to sites like whatismyip.com, but without all the clutter and
crap.

Dependencies
------------
You need the python libraries flask, whelk, publicsuffix and GeoIP. These can
be installed with your OS' package manager or with pip. You also need a working
`whois` program on your `$PATH`.

Ubuntu users can install these packages with:

    sudo add-apt-repository ppa:dennis/python
    sudo apt-get install python-whelk python-flask python-publicsuffix python-geoip whois

Usage
-----
Using the built-in flask/werkzeug http daemon, you can quickly run it in demo mode:

    python -m ip_info

I would however recommend using a wsgi daemon such as uwsgi and a proper httpd
like nginx as frontend. 

Configuration examples
----------------------
Example nginx configuration:

    server {
        listen 80;
        listen  [::]:80;

        root /usr/share/nginx/www;
        index index.html index.htm;

        server_name ip.seveas.net;

        try_files $uri @uwsgi;
        location @uwsgi {
            include uwsgi_params;
            uwsgi_pass unix:/run/uwsgi/app/ip_info/socket;
        }
    }


Example uwsgi configuration:

    [uwsgi]
    plugins       = python
    module        = ip_info:app
    env           = IP_SETTINGS=/etc/ip_settings
    env           = HOME=/nonexistent

    shared-socket = 1
    chown_socket  = www-data
    log-reopen    = 1

    processes     = 10
    harakiri      = 60
    max-requests  = 20
    reload-on-as  = 1024
    auto-procname = 1
    procname-prefix-spaced = ip_info

The `IP_SETTINGS` environment variable can be used to point to a configuration
file. This configuration file can be used to set any Flask setting you want.
ip\_info itself only has one setting: A `DB` variable that can point to a
custon GeoIP data file, such as the data file that contains city information.

License
-------
Copyright (c) 2014 Dennis Kaarsemaker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
