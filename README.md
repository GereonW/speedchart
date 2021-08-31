# Speedchart

Speedchart gathers network connection informations via [speedtest-cli](https://www.speedtest.net/de/apps/cli) in a [Round-Robin-Database](https://de.wikipedia.org/wiki/RRDtool) and maps them into a graph.

This script comes with basic upload functionality using `HTTP PUT`, good enough to upload the resulting graph to say a NextCloud instance.

## Quick reference

This is a major makeover of Florian Heinle's [Speedchart](https://hub.docker.com/r/fheinle/speedchart)

[Florian Heinle](https://launchpad@planet-tiax.de)

Originals: [Blog-Post](https://blog.florianheinle.de/speedtest-rrdtool-docker), [Docker-Version](https://hub.docker.com/r/fheinle/speedchart), [Git-Version](https://github.com/fheinle/speedtest-rrdtool-docker)

## Supported tags

* latest
* v0.3
* v0.2  [Deprecated]
* v0.1  [Deprecated]

## Getting Started

### Prerequisites


In order to run this container you'll need docker installed.

* [Windows](https://docs.docker.com/windows/started)
* [OS X](https://docs.docker.com/mac/started/)
* [Linux](https://docs.docker.com/linux/started/)

Before you start you need to set up a place where the container can save its database and so on.

Preferably you create a new directory where you wish. In there you must create at least the settings.ini

```shell
mkdir speedchart && cd speedchart
curl https://github.com/GereonW/speedchart/blob/main/settings.ini > settings.ini
mkdir data
```

### Usage

Now you can run the docker image for the first time with:

```shell
docker run -v $(pwd)/data:/data -v $(pwd)/settings.ini:/settings.ini:ro --name speedchart wolfg/speedchart
```

To run the container frequently (e.g. every 20 min) simply add the following to your crontab:

```shell
# to open it
crontab -e

# paste in
*/20 * * * * /usr/bin/docker start speedchart
```

#### Container Parameters

You might use `$(pwd)/` instead of `./` as you can see in the example above.

* `-v ./data:/data` - mount the data folder(created on first exit. no need to create manually)
* `-v ./settings.ini:/settings.ini:ro` - mount the configuration file(must exist before container creation)
* `--name speedchart` - give your container a meaningful name

#### Useful File Locations

* `./settings.ini` - Configuration

* `./data/speed.rrd` - Round robin database

* `./data/graph.png` - Produced Image

## Settings.ini

### Overview

The configuration takes place via an `ini` file which is mounted to the container.

This allows you to change the settings without re-building the container.

| Section                      | Setting     | Default \| (Options/Minimal)                                 | Description                                                  |
| :--------------------------- | :---------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| `general`                    | `log_level` | info \| debug                                                | Set to `debug` for more information in `docker logs`         |
|                              | `measure`   | true \| false                                                | Set to `false` if you want to skip measuring (for debugging) |
|                              | `frequency` | 20 \| min 1                                                  | Only on first start-up relevant. Delete `./data/speed.rrd` when changing this. Determines how often data points are expected by the database. When `frequency`min * 3 is surpassed without a new entry, the database will mark the entry as missing and add `UNKNOWN`. For further information see [Documentation](https://oss.oetiker.ch/rrdtool/doc/rrdcreate.en.html#DS:ds-name[=mapped-ds-name[[source-index]]]:DST:dst_arguments) at *'heartbeat'* just below [COMPUTE](https://oss.oetiker.ch/rrdtool/doc/rrdcreate.en.html#COMPUTE). |
| `graph`                      | `width`     | 600                                                          | Width of the graph-image in pixels.                          |
|                              | `height`    | 200                                                          | A third of the final size. When width=600px then height=200px will make the picture square. |
|                              | `name`      | graph.png                                                    | Picture name. Use .png as suffix only.                       |
|                              | `timeframe` | end-1w \| end-{anynumber}{y\|months\|w\|d\|h\|minutes\|s}    | See the [Documentation](https://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html#AT-STYLE_TIME_SPECIFICATION) of **RRD** |
|                              | `max`       | 00FF00                                                       | Colour for the 'Preferable'-line in hex-format (no #)        |
|                              | `avg`       | FFBB00                                                       | Colour for the 'Average'-line in hex-format (no #)           |
|                              | `min`       | FF0000                                                       | Colour for the 'Worst'-line in hex-format (no #)             |
| `graph_upload`               | `enable`    | false                                                        | Enable uploading `graph.png` via webdav                      |
|                              | `url`       | <empty>                                                      | The directory where the image will be uploaded to (`HTTP PUT`) |
|                              | `user`      | <empty>                                                      | Username used for HTTP Authentication                        |
|                              | `password`  | <empty>                                                      | Password used for HTTP Authentication                        |
| **Section**                  | **Setting** | **Download \| Upload \| Ping**                               | **Description**                                              |
| `download`, `upload`, `ping` | `title`     | Download Speed(Mbit/s) \| Upload Speed(Mbit/s) \| Response Time(ms) | Graph titles                                                 |
|                              | `unit`      | Mbit/s \| Mbit/s \| ms                                       | Label names                                                  |
|                              | `top`       | 110 \| 45 \| 100                                             | This determines the upper limit the graph is showing         |
|                              | `bot`       | 0                                                            | This determines the lower limit the graph is showing         |
|                              | `max`       | 100 \| 40 \| 10                                              | This value sets the height of the of the 'Preferable'-line. You can find details on this in the product information sheet from your provider. |
|                              | `avg`       | 83 \| 33 \| 30                                               | This value sets the height of the of the 'Average'-line. You can find details on this in the product information sheet from your provider. |
|                              | `min`       | 50 \| 20 \| 60                                               | This value sets the height of the of the 'Worst'-line. You can find details on this in the product information sheet from your provider. |
|                              | `color`     | 0000FF                                                       | Colour for the data-line in hex-format (no #)                |

### Changing the `max` values

Be careful when changing the `max` values(not the colour). The database `rrdtool` uses is initialized with this value too and changing the `max` requires starting over with the rrd database.

### Uploading the graph

This script comes with basic upload functionality using `HTTP PUT`, good enough to upload the resulting graph to say a NextCloud instance.

To enable uploading the graph, edit the `settings.ini` file:

```ini
[graph_upload]
enable = true
url = https://subdomain.domain.tld/directory/
user = username
password = password
```

### Full ini file

```editorconfig
[general]
log_level = info
measure = true
; must remove ./data/speed.rrd when change frequency to take action
frequency = 20

[graph]
width = 600
height = 200
name = graph.png
; e.g.: end-6h | end-1d | ... | end-6d | end-1w | end-2w | ...
timeframe = end-1w
max = 00FF00
avg = FFBB00
min = FF0000

[graph_upload]
enable = false
url = https://subdomain.domain.tld/directory/
user = username
password = password

; These values are taken from my vDSL 100/40 German Telekom connection
[download]
title = Download Speed(Mbit/s)
unit = Mbit/s
top = 110
bot = 0
max = 100
avg = 83
min = 50
color = 0000FF

[upload]
title = Upload Speed(Mbit/s)
unit = Mbit/s
top = 45
bot = 0
max = 40
avg = 33
min = 20
color = 0000FF

[ping]
title = Response Time(ms)
unit = ms
top = 100
bot = 0
max = 10
avg = 30
min = 60
color = 0000FF
```

## Built With

* [python:3.8-buster](https://hub.docker.com/layers/python/library/python/3.8-buster/images/sha256-2026d1d1423985328e00b73a415b73416d9b6c9e4f7cbf89b631c96e0e3518c1?context=explore)
* [rrdtool](https://oss.oetiker.ch/rrdtool/) by Tobias Oetiker
* [speedtest-cli](https://www.speedtest.net/de/apps/cli)

## Find Me

* [GitHub](https://github.com/gereonw)

## Copyright

* **Florian Heinle** - Initial work - [Speedchart](https://github.com/fheinle/speedtest-rrdtool-docker)
* **Gereon Wolf** - Adding parameters & optical appearance - [This](https://github.com/GereonW/speedchart)

This project is licensed under the MIT License. [See](https://github.com/GereonW/speedchart/blob/main/LICENSE)

