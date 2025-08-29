import gc, json, machine, network, ntptime, os, re, requests, sys, time
from picozero import LED, Speaker, Button

###
# Configuration
#

from config import (
    STATION_ID,
    DEST_NAME,
    NOTIF_MINS_OUT,
    WLAN_SSID,
    WLAN_PASSWORD,
    API_KEY,
    API_INTERVAL,
    MAX_CONS_ERRS,
    RESET_HOUR,
    NOTIF_SOUND,
    LED_PINS,
    INDICATOR_LED_INDEX,
    BUTTON_PIN,
    SPEAKER_PIN
    )


###
# Globals
#

leds = list(map(lambda pin: LED(pin), LED_PINS))
speaker = Speaker(SPEAKER_PIN)
button = Button(BUTTON_PIN)
indicator_led = leds[INDICATOR_LED_INDEX]
api_url = ('http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx'
    + '?mapid=' + STATION_ID
    + '&key=' + API_KEY
    + '&outputType=JSON')
cons_errs = 0
notif_scheduled = False
timer = None
startup_ticks = time.ticks_ms()

def connect_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WLAN_SSID, WLAN_PASSWORD)
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        log('Waiting for connection...')
        time.sleep(1)
    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('Connection failed ({})'.format(wlan.status()))
    else:
        status = wlan.ifconfig()
        log('Connected to {} (IP={})'.format(WLAN_SSID, status[0]))

def fetch_predictions():
    try:
        response = requests.get(api_url)
        data = json.loads(response.text)
        predictions = data['ctatt'].get('eta')
        return (predictions or [], 0)
    except KeyError:
        print('Unexpected API response:')
        print(response.text)
        return ([], 1)
    except Exception:
        print('Request failed')
        return ([], 1)

def parse_date(date_str):
    # Example date_str: '2023-11-30T19:34:21'
    match = re.match('(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)', date_str)
    # Convert match tuple from strings to integers
    date_tuple = tuple(map(int, match.groups()))
    # Get current local time tuple (just to get inferred last 2 digits of 8-tuple date)
    now = time.gmtime()
    # Append last 2 digits of current time to date_tuple
    date_tuple += (now[6], now[7],) # Day of week (0-6), day of year (1-366)
    date_int = time.mktime(date_tuple) # Number of seconds since Jan 1, 2000
    return date_int

def get_eta_in_mins(prediction):
    if prediction['isApp'] == '1' and prediction['isSch'] == '0':
        return 0 # Train is approaching
    arr_secs = parse_date(prediction['arrT'])
    pre_secs = parse_date(prediction['prdt'])
    eta_mins = (arr_secs - pre_secs) // 60
    return eta_mins

def get_is_for_dest(prediction):
    return prediction['destNm'] == DEST_NAME
        
def blink_all(**kwargs):
    for led in leds:
        led.blink(**kwargs)
        
def log(*args):
    (y, mo, d, h, m, s, _, _) = time.localtime()
    ts = '[{}-{}-{:02} {}:{:02}:{:02}]'.format(y, mo, d, h, m, s)
    # Create or append to logfile
    logfile = open('log', 'a')
    # Print to both logfile and sys.stdout
    for out in [logfile, sys.stdout]:
        if args[0] and isinstance(args[0], Exception):
            print(ts, file=out)
            sys.print_exception(args[0], out)
        else:
            print(ts, *args, file=out)
    logfile.close()

def log_and_reset(*args):
    log(*args)
    log('Reset in 30 seconds...')
    blink_all()
    time.sleep(30)
    log('Calling machine.reset()')
    machine.reset()

# Schedule/unschedule notifications with the button
def schedule_notif():
    global notif_scheduled
    notif_scheduled = not notif_scheduled
    speaker.off()
    if notif_scheduled:
        speaker.play([['c6', .1], ['e6', .1], ['g6', .1]], wait=False)
    else:
        speaker.play([['g6', .1], ['c6', .1]], wait=False)
        
def on_press():
    global timer
    timer = machine.Timer(period=3000,
                          mode=machine.Timer.ONE_SHOT,
                          callback=lambda t:machine.reset())
    
def on_release():
    global timer
    if timer:
        timer.deinit()
        timer = None
        schedule_notif()
    
def check_scheduled_reset():
    (_, _, _, hour, _, _, _, _) = time.localtime()
    startup_diff = time.ticks_diff(time.ticks_ms(), startup_ticks)
    hours_since_startup = startup_diff / 1000 / 60 / 60
    if hour == RESET_HOUR and hours_since_startup > 1:
        log_and_reset('Performing scheduled reset')
        
def check_gc_collect():
    alloc = gc.mem_alloc()
    free = gc.mem_free()
    total = alloc + free
    alloc_ratio = alloc / total
    # print('Memory usage: {}%'.format(alloc_ratio * 100, alloc, total))
    if alloc_ratio > .8:
        gc.collect()

###
# Main
#

log('Initializing...')

# Event handler registration
button.when_pressed = on_press
button.when_released = on_release

# Test the LEDs
blink_all(n=1)
time.sleep(2)

# Connect to Wi-Fi
try:
    connect_wlan()
    for led_group in [[0, 5], [1, 6], [2, 7], [3, 8], [4, 9]]:
        leds[led_group[0]].blink(on_time=0.01, n=1)
        leds[led_group[1]].blink(on_time=0.01, n=1, wait=True) # Synchronous
except RuntimeError as e:
    log_and_reset(e)
    
# Sync time
try:
    log('Syncing time over NTP')
    ntptime.settime()
    log('Local time synced')
except Exception as e:
    log_and_reset(e)

# Run the main loop
try:
    while True:
        check_scheduled_reset()
        # Get all predictions for the specified station
        predictions, status = fetch_predictions()
        if status == 1:
            # Keep track of consecutive errors
            # If too many consecutive errors, throw an error
            cons_errs += 1
            if cons_errs == MAX_CONS_ERRS:
                raise RuntimeError('Too many consecutive errors')
            indicator_led.blink(on_time=.01, off_time=.25, n=3)
        elif status == 0:
            cons_errs = 0
        # Filter predictions for specified destination
        predictions = list(filter(get_is_for_dest, predictions))
        # Convert predictions to ETAs (in minutes)
        etas = list(map(get_eta_in_mins, predictions))
        # Filter out ETAs further out than we can handle with our LED display
        etas = set(filter(lambda e: e < len(leds), etas))
        for i, led in enumerate(leds):
            # Loop through all LEDs for which there is an ETA
            if i in etas:
                # Turn ETA LED on if not already
                if not led.is_active:
                    if i == 0:
                        led.pulse(fade_in_time=1, fade_out_time=2)
                    else:
                        led.on()
                    # Play notification if scheduled
                    if i == NOTIF_MINS_OUT and notif_scheduled:
                        notif_scheduled = False
                        speaker.play(NOTIF_SOUND, wait=False)
            # Turn off LEDs that don't have an associated ETA
            else:
                led.off()
        # Preemptively free memory
        check_gc_collect()
        # Wait for the next API call
        time.sleep(API_INTERVAL)
except Exception as e:
    log_and_reset(e)
