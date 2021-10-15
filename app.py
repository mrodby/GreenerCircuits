from flask import Flask, render_template, request
from datetime import datetime, timedelta
import json

from gcdatabase import GCDatabase
import gclib

app = Flask(__name__)


def query_parm(name, default):
    '''Return query parameter 'name'; if not there, return default'''

    value = request.args.get(name)
    if value is None:
        value = default
    else:
        value = int(value)
    return value


@app.route('/')
def power():
    '''Show current power use'''

    database = GCDatabase()

    # Get URL query parameters
    channel = query_parm('channel', 0)          # Channel number
    page_hours = query_parm('pageHours', 24)    # Hours per page displayed in chart
    page_seconds = page_hours * 3600
    bar_minutes = query_parm('barMinutes', 1)   # Minutes per bar
    bar_seconds = bar_minutes * 60
    page = query_parm('page', 0)                # How many pages backward in time, starting from now

    # Get current channels states
    rows = database.get_channels()

    # Convert to list of dictionaries, eliminating type 0 (unused) channels
    # and get the name of the selected channel
    channels = []
    channel_name = 'Unknown'
    for row in rows:
        channels.append(dict(row))
        if row.channum == channel:
            channel_name = row.name
    # Sort by channel name
    channels = sorted(channels, key=lambda d: d['name'].upper())

    # Convert hours/interval/page to start/end timestamps
    # - end_stamp is the next multiple of bar_seconds after now adjusted by page pages
    # - start_stamp is page_seconds earlier
    end_stamp = datetime.now().timestamp() - page_seconds * page
    end_stamp = datetime.fromtimestamp(end_stamp + bar_seconds - (end_stamp - 1) % bar_seconds)
    start_stamp = end_stamp - timedelta(seconds=page_seconds)

    # Do database query to get usage
    usage_rows = database.get_usage(channel, start_stamp, end_stamp, bar_seconds)
    total_watts = 0
    usage = [['Time', 'Power']]
    for row in usage_rows:
        watts = int(row.watts)
        usage.append([str(row.stamp), watts])
        total_watts += watts
    kwh = total_watts / (60 / bar_minutes) / 1000

    # Construct title
    title = f'{channel_name} (Total: {kwh:.3f} kWh)'

    # Render result
    return render_template(
        'power.html',
        now=datetime.now().isoformat(),
        channels=channels,
        title=title,
        usage=usage,
        channel=channel,
        page_hours=page_hours,
        bar_minutes=bar_minutes,
        page=page)

