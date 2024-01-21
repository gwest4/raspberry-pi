import json, machine, network, re, requests, time
from picozero import LED, Speaker, Button

station_id = '41180' # Kedzie to Loop (Brown Line)
dest_name = 'Loop'   # Destination to filter trains at the above stop
notif_mins_out = 4   # How many mins out an ETA will trigger the notification
wlan_ssid = 'West 2G'
wlan_password = 'fudgiemilkyway204'
api_key = 'baeac4e81d284f258876778afedacb25'
api_interval = 15
max_cons_errs = 8
notif_sound = [ ['e5', 1/4], # So Long, Farewell (Sound of Music)
                ['g5', 3/4], ['e5', 1/4], ['g5', 3/4], ['e5', 1/4],
                ['c5', 1/4], ['d5', 1/4], ['e5', 1/4], ['f5', 1/4], ['g5', 1/4], ['a5', 2/4], ['e5', 1/4],
                ['g5', 3/4], ['e5', 1/4], ['g5', 3/4], ['e5', 1/4],
                ['c5', 1/4], ['d5', 1/4], ['e5', 1/4], ['f5', 1/4], ['g5', 1/4], ['a5', 2/4], [None, 1/4] ]

def connect_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wlan_ssid, wlan_password)
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(1)
    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('Connection failed ({})'.format(wlan.status()))
    else:
        status = wlan.ifconfig()
        print('Connected to {} (IP={})'.format(wlan_ssid, status[0]))
        
def format_url(url, params):
    if not params:
        return url
    params_list = []
    for k, v in params.items():
        params_list.append('='.join((k, v)))
    return url + '?' + '&'.join(params_list)

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
    except requests.exceptions.RequestException:
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



###
# Main program
#

leds = [LED(0),LED(1),LED(4),LED(5),LED(6),LED(7),LED(9),LED(10),LED(11),LED(12)]
speaker = Speaker(18)
button = Button(21)
api_url = format_url('http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx',
        { 'mapid': station_id, 'key': api_key, 'outputType': 'JSON' })
cons_errs = 0
notif_scheduled = False

# Schedule/unschedule notifications with the button
def schedule_notif():
    global notif_scheduled
    notif_scheduled = not notif_scheduled
    speaker.off()
    if notif_scheduled:
        speaker.play([['c6', .1], ['e6', .1], ['g6', .1]], wait=False)
    else:
        speaker.play([['g6', .1], ['c6', .1]], wait=False)
button.when_pressed = schedule_notif

# Test the LEDs
for led in leds:
    led.blink(n=1)
time.sleep(1.01)

# Connect to Wi-Fi
try:
    connect_wlan()
    for led in leds:
        led.blink(on_time=0.01, n=1, wait=True) # Synchronous
except RuntimeError as e:
    # Handle connection error by performing soft reset
    print(e)
    print('Soft reset in 30 seconds...')
    time.sleep(30)
    machine.soft_reset()

while True:
    try:
        # Get all predictions for the specified station
        predictions, status = fetch_predictions()
        if status == 1:
            # Keep track of consecutive errors
            # If too many consecutive errors, throw an error
            cons_errs += 1
            if cons_errs == max_cons_errs:
                raise RuntimeError('Too many consecutive errors')
            leds[0].blink(on_time=.01, off_time=.25, n=3)
        elif status == 0:
            cons_errs = 0
        # Filter predictions for specified destination
        predictions = list(filter(lambda p: p['destNm'] == dest_name, predictions))
        # Convert predictions to ETAs (in minutes)
        etas = list(map(get_eta_in_mins, predictions))
        # Filter out ETAs further out than we can handle with our LED display
        etas = set(filter(lambda e: e < len(leds), etas))
        if len(etas) > 0:
            for i, led in enumerate(leds):
                if i in etas: # Turn eta LED on if not already
                    if not led.is_active:
                        led.pulse(fade_in_time=1, fade_out_time=2)
                        # Play notification if scheduled
                        if i == notif_mins_out and notif_scheduled:
                            notif_scheduled = False
                            speaker.play(notif_sound, wait=False)
                else:
                    led.off()
        elif status == 0:
                leds[0].pulse(fade_in_time=.01, fade_out_time=.25, n=1, fps=50)
        # Wait for the next API call
        time.sleep(api_interval)
    except Exception as e:
        # Handle unexpected errors by performing soft reset
        print(e)
        print('Soft reset in 10 seconds...')
        time.sleep(10)
        machine.soft_reset()