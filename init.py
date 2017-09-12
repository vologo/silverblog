import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os.path

from flask import Flask, abort

from common import file, page, console

rss = None
menu_list = None
page_name_list = list()
cache_page = dict()
template_config = None
app = Flask(__name__)

console.log("info", "Loading configuration")

system_config = json.loads(file.read_file("./config/system.json"))

if system_config["Author_Image"] == "" and system_config["Author_Name"] != "":
    import urllib.request

    r = {"entry": [{"hash": ""}]}
    console.log("info", "Get the Gravatar URL")
    try:
        r = urllib.request.urlopen(
            "https://en.gravatar.com/{0}.json".format(system_config["Author_Name"])).read().decode('utf-8')
    except urllib2.HTTPError:
        console.log("Error", "Get the error")
        pass
    req = json.loads(r)
    gravatar_hash = req["entry"][0]["hash"]
    system_config["Author_Image"] = "https://secure.gravatar.com/avatar/{0}".format(gravatar_hash)
    file.write_file("./config/system.json", json.dumps(system_config))

page_list = json.loads(file.read_file("./config/page.json"))

if os.path.exists("./config/menu.json"):
    menu_list = json.loads(file.read_file("./config/menu.json"))

for item in page_list:
    page_name_list.append(item["name"])

if os.path.exists("./document/rss.xml"):
    rss = file.read_file("document/rss.xml")

if os.path.exists("./templates/{0}/config.json".format(system_config["Theme"])):
    template_config = json.loads(file.read_file("./templates/{0}/config.json".format(system_config["Theme"])))

system_config["API_Password"] = None

console.log("Success", "load the configuration file successfully")


# Subscribe
@app.route("/rss")
@app.route("/feed")
def load_rss():
    if rss is None:
        abort(404)
    return rss, 200, {'Content-Type': 'text/xml; charset=utf-8'}


@app.route("/static/")
def static_file():
    abort(400)

@app.route("/")
@app.route("/index/")
@app.route('/index/p/<int:page_index>/')
def index_route(page_index=1):
    result = None
    page_url = "/index/p/{0}".format(page_index)
    if page_url in cache_page:
        console.log("info", "Get cache Success: {0}".format(page_url))
        return cache_page[page_url]

    console.log("info", "Trying to build: {0}".format(page_url))

    if result is None:
        result, row = page.build_index(page_index, system_config, page_list, menu_list, False, template_config)

    console.log("info", "Writing to cache: {0}".format(page_url))
    if len(cache_page) >= 100:
        page_keys = sorted(cache_page.keys())
        console.log("info", "Delete cache: {0}".format(page_keys[0]))
        del cache_page[page_keys[0]]
    cache_page[page_url] = result
    console.log("Success", "Get success: {0}".format(page_url))

    return result


@app.route("/post/<file_name>/")
def index_route(file_name=None):
    result = None
    if file_name is None or not os.path.exists("document/{0}.md".format(file_name)):
        abort(404)
    if page_url in cache_page:
        console.log("info", "Get cache Success: {0}".format(page_url))
        return cache_page[page_url]
    if result is None:
        result = page.build_page(file_name, system_config, page_list, page_name_list, menu_list, False,
                                 template_config)
    console.log("info", "Writing to cache: {0}".format(page_url))
    if len(cache_page) >= 100:
        page_keys = sorted(cache_page.keys())
        console.log("info", "Delete cache: {0}".format(page_keys[0]))
        del cache_page[page_keys[0]]
    cache_page[page_url] = result
    console.log("Success", "Get success: {0}".format(page_url))

    return result


def add_post_header(item):
    item["name"] = "post/{0}".format(item["name"])
    return item
