#!/usr/bin/env python3

"""
measure internet speed and graph with rrdtool


Florian Heinle <launchpad@planet-tiax.de>
MIT Licence
"""


import configparser
import datetime
import logging
import os
import subprocess
import tempfile

from dateutil import tz
from PIL import Image, ImageFilter
import requests
import speedtest

main_logger = logging.getLogger('speedchart')

def create_rrd_file():
    '''create the rrd database with values from settings'''
    frequency = int(SETTINGS['general']['frequency'])
    step_rate = str(frequency * 60)
    heartbeat = str(frequency * 60 * 3)
    rows      = str(int(24 * 7 * 60 / frequency))
    subprocess.run(
        [
            'rrdtool', 'create',
            RRD_FNAME,
            '--step={}'.format(step_rate),
            '--no-overwrite',
            'DS:download:GAUGE:{}:0:{}'.format(heartbeat, SETTINGS['download']['top']),
            'DS:upload:GAUGE:{}:0:{}'.format(heartbeat, SETTINGS['upload']['top']),
            'DS:ping:GAUGE:{}:0:{}'.format(heartbeat, SETTINGS['ping']['top']),
            'RRA:MAX:0.5:2:{}'.format(rows)
        ]
    )
    main_logger.debug("step_rate: " + step_rate + " heartbeat: " + heartbeat + " rows: " + rows)


def run_speedtest():
    '''perform the ping, download and upload test

    return the results as a dict'''
    speed_tester = speedtest.Speedtest()
    speed_tester.get_best_server()
    speed_tester.download()
    speed_tester.upload()

    utc_timestamp = datetime.datetime.strptime(
        speed_tester.results.timestamp,
        '%Y-%m-%dT%H:%M:%S.%fZ'
    ).replace(tzinfo=tz.tzutc())

    return dict(
        timestamp=utc_timestamp.astimezone(tz.tzlocal()).timestamp(),
        download=round(speed_tester.results.download / 1024 / 1024, 2),
        upload=round(speed_tester.results.upload / 1024 / 1024, 2),
        ping=round(speed_tester.results.ping)
    )


def update_rrd_file(timestamp, ping, download, upload):
    '''update the rrd file with a measurement from run_speedtest'''
    subprocess.run(
        [
            'rrdtool', 'update',
            RRD_FNAME,
            "{ts}:{dl}:{ul}:{pi}".format(
                ts=timestamp,
                ul=upload,
                dl=download,
                pi=ping
            )
        ]
    )


def graph_rrd_file():
    '''graph the rrd file according to settings'''
    graph_images = {}
    for data_set in ('download', 'upload', 'ping'):
        image_tmpfile_name = tempfile.mkstemp(suffix='.png', prefix=data_set)[1]
        graph_data_set(data_set, image_tmpfile_name)
        graph_images["{}_graph".format(data_set)] = image_tmpfile_name
    return graph_images


def graph_data_set(data_set, image_fname):
    '''graph the given dataset from the rrd file according to settings'''
    subprocess.run(
        [
         
            'rrdtool', 'graph',
            image_fname,
            '-t {}'.format(SETTINGS[data_set]['title']),
            '-w {}'.format(SETTINGS['graph']['width']),
            '-h {}'.format(SETTINGS['graph']['height']),
            '-u {}'.format(SETTINGS[data_set]['top']), # upper limit
            '-l {}'.format(SETTINGS[data_set]['bot']), # lower limit
            '--start={}'.format(SETTINGS['graph']['timeframe']), # timeframe
            '--legend-position=north', #
            '--grid-dash=1:3', # grid-dash on:off
            '--border=2', # border around graph
            '--right-axis=1:0',
            '--right-axis-label={}'.format(SETTINGS[data_set]['unit']),
            '--vertical-label={}'.format(SETTINGS[data_set]['unit']),
            '--force-rules-legend',
            'DEF:{}={}:{}:MAX'.format(data_set, RRD_FNAME, data_set),
            'LINE1:{}#{}:{}'.format(
                    SETTINGS[data_set]['max'],
                    SETTINGS['graph']['max'],
                    "Preferably| " + SETTINGS[data_set]['max'] + SETTINGS[data_set]['unit']
                ), # best value
            'LINE1:{}#{}:{}'.format(
                    SETTINGS[data_set]['avg'],
                    SETTINGS['graph']['avg'],
                    "Avarage| " + SETTINGS[data_set]['avg'] + SETTINGS[data_set]['unit']
                ), # avarage value
            'LINE1:{}#{}:{}'.format(
                    SETTINGS[data_set]['min'],
                    SETTINGS['graph']['min'],
                    "Worst| " + SETTINGS[data_set]['min'] + SETTINGS[data_set]['unit']
                ), # worst value
            'LINE1:{}#{}:{}'.format(data_set, SETTINGS[data_set]['color'], data_set.capitalize()),
        ],
        stdout=subprocess.PIPE
        #HRULE:valuecolor[:[legend][:dashes[=on_s[,off_s[,on_s,off_s]...]][:dash-offset=offset]]]
    )


def merge_images(download_graph, upload_graph, ping_graph):
    '''merge three graphs into one for easier handling'''
    main_logger.debug("Loading temporary images...")
    main_logger.debug("\t0/3 | please wait.")
    download_image = Image.open(download_graph)
    main_logger.debug("\t1/3 | please wait..")
    upload_image = Image.open(upload_graph)
    main_logger.debug("\t2/3 | please wait...")
    ping_image = Image.open(ping_graph)
    main_logger.debug("\t3/3 | All images loaded correctly.")
    combined_size = (
        download_image.size[0],
        download_image.size[1] + upload_image.size[1] + ping_image.size[1]
    )
    main_logger.debug("Combining temporary images...")
    combined_image = Image.new('RGB', combined_size)
    combined_image.paste(im=download_image, box=(0,0))
    combined_image.paste(im=upload_image, box=(0, download_image.size[1]))
    combined_image.paste(im=ping_image, box=(0, download_image.size[1] + upload_image.size[1]))
    main_logger.debug("\tDone")
    main_logger.debug("Resharpening image...")
    combined_image = combined_image.filter(ImageFilter.SHARPEN)
    main_logger.debug("\tDone")
    #combined_image = combined_image.filter(ImageFilter.SHARPEN)
    combined_image.save(GRAPH_FNAME)

    for no_longer_needed in (download_graph, upload_graph, ping_graph):
        os.unlink(no_longer_needed)
    main_logger.debug("Marking temporary images as deprecated")
    return GRAPH_FNAME


def upload(fname):
    '''upload the graph image using HTTP PUT, i.e. using WebDAV

    return the HTTP status code. For NextCloud, 204 is ok '''
    http_request = requests.put(SETTINGS['graph_upload']['url'] + SETTINGS['graph']['name'],
        auth=(SETTINGS['graph_upload']['user'], SETTINGS['graph_upload']['password']),
        data=open(fname, 'rb').read()
    )
    return http_request.status_code


def load_settings(settings_fname='settings.ini'):
    '''load config settings from ini file'''
    ini_file = configparser.ConfigParser()
    ini_file.read('settings.ini')

    # dependencies
    # uploading needs upload settings
    if ini_file.getboolean('graph_upload', 'enable'):
        for setting in ('url', 'user', 'password'):
            if not ini_file.has_option('graph_upload', setting):
                raise RuntimeError('Uploading enabled but not all upload settings present')
    return ini_file

SETTINGS = load_settings()
RRD_FNAME = './data/speed.rrd'
GRAPH_FNAME = './data/{}'.format(SETTINGS['graph']['name'])

def main():
    '''when started from cli'''

    logging.basicConfig(
        level=getattr(logging, SETTINGS['general']['log_level'].upper()),
        format='%(asctime)s %(message)s'
    )
    main_logger = logging.getLogger('speedchart')

    if not os.path.isfile(RRD_FNAME):
        main_logger.debug(
            "RRD file %s not found, creating",
            RRD_FNAME
        )
        create_rrd_file()
    else:
        main_logger.debug(
            "RRD file %s present, continuing",
            RRD_FNAME
        )

    if SETTINGS.getboolean('general', 'measure'):
        main_logger.debug('Starting speedtest')
        speedtest_results = run_speedtest()
        main_logger.info(
            "Download: %s Upload: %s Ping: %s",
            speedtest_results['download'],
            speedtest_results['upload'],
            speedtest_results['ping']
        )
        update_rrd_file(
            timestamp=speedtest_results['timestamp'],
            download=speedtest_results['download'],
            upload=speedtest_results['upload'],
            ping=speedtest_results['ping']
        )
    main_logger.debug('Updating graph')
    graph_images = graph_rrd_file()
    final_graph = merge_images(**graph_images)

    if SETTINGS.getboolean('graph_upload', 'enable'):
        main_logger.debug('Uploading graph')
        response_code = upload(final_graph)
        main_logger.debug('Upload response code: %s', response_code)
    else:
        main_logger.debug('Not uploading graph')


if __name__ == '__main__':
    main()
