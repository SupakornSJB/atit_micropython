import network
import utime


def connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return

    wlan.connect(ssid, password)

    for _ in range(10):
        if wlan.isconnected():
            print("WiFi connected:", wlan.ifconfig())
            return
        print("WiFi status:", wlan.status())
        utime.sleep(1)

    raise RuntimeError("WiFi connection failed after 10 retries")
