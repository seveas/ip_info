# ip_info - Show IP information of connecting clients
# Similar to e.g. whatismyip.com, but without clutter

from flask import Flask, request, current_app, Response, Markup
from flask.views import View
from socket import gethostbyaddr, herror
from whelk import shell
from publicsuffix import PublicSuffixList
import GeoIP
import json
import os
import re

class IpView(View):
    template = """<!DOCTYPE html>
<html>
<head>
  <title>{% block title %}IP address info{% endblock %}</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <link href='http://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400' rel='stylesheet' type='text/css'>
  <link href='http://fonts.googleapis.com/css?family=Source+Code+Pro:400' rel='stylesheet' type='text/css'>
  <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.0/jquery.min.js"></script>
  <script type="text/javascript">
    function resize() {
        if($("#main").height() < $(window).height()) {
            $("#main").css({'top': ($(window).height() - $("#main").height())/2});
        }
        else {
            console.log("not smaller");
            $("#main").css({'top': 0});
        }
        if($("#main").width() < $(window).width()) {
            $("#main").css({'left': ($(window).width() - $("#main").width())/2});
        }
        else {
            $("#main").css({'left': 0});
        }
    }
    $(window).ready(function() { resize(); });
    $(window).resize(function() { resize(); });
  </script>
  <style type="text/css">
  body,input,select,a,a:hover,a:active {
    font-family: 'Source Sans Pro';
    font-size: 28px;
    font-weight: 300;
    color: #2d2d2d;
    background-color: #ffffee;
  }
  .opts {
    text-align: left;
  }
  #main {
    margin: 0px;
    position: absolute;
    text-align: center;
  }
  td,th {
    text-align: left;
    vertical-align: top;
  }
  th {
    font-weight: 400;
  }
  .forkme {
    position: fixed;
    top: 0;
    right: 0;
    border: 0;
    z-index: 9;
  }
  pre, pre a, pre a:hover, pre a:active {
    font-family: 'Source Code Pro';
    font-weight: 400;
    font-size: 12px;
    text-align: left;
  }
  </style>
</head>
<body>
<a href="https://github.com/seveas/ip_info"><img class="forkme" src="https://s3.amazonaws.com/github/ribbons/forkme_right_red_aa0000.png" /></a>
<div id="main">
{% block content %}
<table>
  <tr><th>Your IP:</th><td><a href="./whois-ip/">{{ ip }}</a></td></tr>
  {% if geo %}
  <tr><th>Location:</th><td>{% if geo.city %}{{ geo.city }}, {% endif %}{{ geo.country_name }}</td></tr>
  {% endif %}
  {% if hostname %}<tr><th>Your hostname:</th><td><a href="./whois-host/">{{ hostname }}</a></td></tr>{% endif %}
  {% if proxies or local_ip %}
  {% if proxies %}<tr><th>Proxy detected:</th><td>{% for proxy in proxies %}{{ proxy }}</br>{% endfor %}</td></tr>{% endif %}
  {% if local_ip %}<tr><th>Your local IP:</th><td>{{ local_ip }}</td></tr>{% endif %}
  {% endif %}
</table>
{% endblock %}
</div>
</body>
</html>"""

    def dispatch_request(self):
        return Response(self.template.render(self.get_data()))
         
    def get_data(self):
        data = {'ip': request.environ['REMOTE_ADDR'], 'hostname': None}
        try:
            data['hostname'] = gethostbyaddr(data['ip'])[0]
        except herror:
            pass
        if current_app.config['HAS_CITIES']:
            geo = current_app.geoip.record_by_addr(data['ip']) or {'country_name': 'Unknown'}
        else:
            geo = {'country_name': current_app.geoip.country_name_by_addr(data['ip'])}
        for k in geo:
            if isinstance(geo[k], str):
                geo[k] = geo[k].decode('iso-8859-1', 'replace')
        data['geo'] = geo
        data['proxies'] = request.headers.get('via')
        if data['proxies']:
            data['proxies'] = data['proxies'].split(',')
        data['local_ip'] = request.headers.get('x-forwarded-for')
        return data

class WhoisView(IpView):
    template = """{% extends "ipview.html" %}
{% block title %}Whois info for {{ target }}{% endblock %}
{% block content %}
<pre>{{ whois|linkify }}</pre>
{% endblock %}"""
    def get_data(self):
        data = super(WhoisView, self).get_data()
        if request.endpoint == 'whois-ip':
            data['target'] = data['ip']
        else:
            data['target'] = data['hostname']
            if not data['target']:
                data['whois'] = '(hostname not found)'
                return data
            data['target'] = current_app.psl.get_public_suffix(data['target'])
        data['whois'] = shell.whois(data['target'], stderr=shell.STDOUT).stdout
        return data

class Defaults:
    DB = None
    DEBUG = False

app = Flask(__name__)
app.config.from_object(Defaults)
if 'IP_SETTINGS' in os.environ:
    app.config.from_envvar("IP_SETTINGS")

app.psl = PublicSuffixList()
if app.config['DB']:
    app.geoip = GeoIP.open(app.config['DB'], GeoIP.GEOIP_STANDARD)
    app.config['HAS_CITIES'] =  app.geoip.record_by_name('1.1.1.1') is not None
else:
    app.geoip = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
    app.config['HAS_CITIES'] = False

app.add_url_rule('/', view_func=IpView.as_view('index'))
app.add_url_rule('/whois-ip/', view_func=WhoisView.as_view('whois-ip'))
app.add_url_rule('/whois-host/', view_func=WhoisView.as_view('whois-name'))

@app.template_filter()
def linkify(value):
    value = Markup.escape(value)
    value = re.sub(r'(?P<link>https?://[-a-zA-Z0-9._/&%=?;]+)', lambda match: Markup('<a href="%(link)s">%(link)s</a>' % match.groupdict()), value)
    value = re.sub(r'(?P<addr>[-a-zA-Z0-9_.+]+@[-a-zA-Z0-9.]+)', lambda match: Markup('<a href="mailto:%(addr)s">%(addr)s</a>' % match.groupdict()), value)
    return value

for view in (IpView, WhoisView):
    if isinstance(view.template, str):
        view.template = app.jinja_env.from_string(view.template)
        app.jinja_env.cache[view.__name__.lower() + '.html'] = view.template

if __name__ == '__main__':
    os.chdir('/')
    app.run('0.0.0.0')
