import network
import utime


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return

    import config
    print("Scanning networks...")
    for ap in wlan.scan():
        print(" ", ap[0].decode(), "ch:", ap[2], "rssi:", ap[3])
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    for _ in range(10):
        if wlan.isconnected():
            print("WiFi connected:", wlan.ifconfig())
            return
        print("WiFi status:", wlan.status())
        utime.sleep(1)

    raise RuntimeError("WiFi connection failed after 10 retries")