#!/usr/bin/python -u

import os, sys, re, getopt, pprint
from subprocess import Popen, PIPE
from operator import add

def getvdevs(zpool):
    # FIXME separate HDDs/SSDs
    # FIXME translate dXpX, dXsX into dX notation
    # FIXME FreeBSD devices
    stats = os.popen('zpool list -v ' + zpool).read()
    if not stats:
        print "No vdevs in zpool " + zpool
        sys.exit(2)

    vdevs = ''
    for l in stats.splitlines():
        for s in l.split():
            if re.match('^c[0-9]+t.*d[0-9]', s):
                if vdevs:
                    vdevs += '|'
                vdevs += s
    return '.*(' + vdevs + ')'

def column(arr, i):
    return [row[i] for row in arr]

def avg(l):
    return sum(l) / float(len(l))
def extract_stat(arr, aggr_func, label):
    #     r/s    w/s   kr/s   kw/s wait actv wsvc_t asvc_t  %w  %b device
    if arr:
        return {
            "count-%s_reqs_sec" % label: aggr_func(map(add, column(arr, 0), column(arr, 1))),
            "kbytes-%s_kb_sec" % label: aggr_func(map(add, column(arr, 2), column(arr, 3))),
            "count-wait_%s_no" % label: aggr_func(column(arr, 4)),
            "count-active_%s_no" % label: aggr_func(column(arr, 5)),
            "latency-wait_%s_time" % label: aggr_func(column(arr, 6)),
            "latency-active_%s_time" % label: aggr_func(column(arr, 7)),
            "percent-wait_%s_pct" % label: aggr_func(column(arr, 8)),
            "percent-disk_%s_busy" % label: aggr_func(column(arr, 9))
        }
    else:
        return None

def coll_print(stat):
    #PUTVAL hbs3/disk-c0t5000C5004F52F08Fd0/percent-wait_pct interval=30 N:0
    if not stat:
        return None
    for s in stat:
        print "PUTVAL %s/io_zpool-%s/%s interval=%s N:%f" % (hostname, zpool, s, interval, stat[s])
    return None

hostname = os.getenv("COLLECTD_HOSTNAME") or os.popen('hostname').read().rstrip()
interval = "%.0f" % (os.getenv("COLLECTD_INTERVAL") and float(os.getenv("COLLECTD_INTERVAL")) or 30)
zpool = len(sys.argv)>1 and sys.argv[1] or os.popen('zpool list').readlines()[1].split()[0]

vdevs = re.compile(getvdevs(zpool), flags=re.IGNORECASE)

iostat = Popen(['stdbuf', '-oL', 'iostat', '-xn', interval], stdout=PIPE)

combo_stat = []
while True:
    line = iostat.stdout.readline().rstrip()
    if vdevs.match(line):
        combo_stat.append(map(float, line.split()[:-1]))
    if re.match('.*extended device statistics',line):
        coll_print(extract_stat(combo_stat, max, "max"))
        coll_print(extract_stat(combo_stat, avg, "avg"))
        combo_stat = []
