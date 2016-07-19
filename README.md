# ZFS collectd plugins
Collection of collectd plugins to monitor ZFS

- [zpiostat.py](zpiostat.py) - per-(physical)disk iostat of ZFS zpool

```
<Plugin exec>
    Exec "nobody:nobody" "/opt/collectd/libexec/zpiostat.py" "tank3
</Plugin>
```
