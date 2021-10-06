'''Greener Circuits database class'''

from datetime import datetime, timedelta
import sys
import os
from sqlalchemy import create_engine, MetaData, Table, text, select, update, func
#from sqlalchemy.dialects.mysql import TINYINT


class GCDatabase:
    '''This class represents the Greener Circuits database'''

    def __init__(self):
        '''Constructor'''

        self.updating = True    # True if database has been recently updated
        self.alert_id = 1

        connect_env = 'connect_gc'
        if connect_env not in os.environ:
            print('Connection string', connect_env, 'not set in environment')
            sys.exit()
        self.engine = create_engine(os.environ[connect_env], future=True, echo=False)

        self.metadata = MetaData()
        with self.engine.connect() as conn:
            self.alert_table = Table('alert', self.metadata, autoload_with=conn)
            self.channel_table = Table('channel', self.metadata, autoload_with=conn)
            self.scratchpad_table = Table('scratchpad', self.metadata, autoload_with=conn)
            self.settings_table = Table('settings', self.metadata, autoload_with=conn)
            self.used_table = Table('used', self.metadata, autoload_with=conn)


    def delete_alerts(self):
        '''Delete all alerts in table'''
        with self.engine.begin() as conn:
            conn.execute(self.alert_table.delete())
        self.alert_id = 1


    def create_alert(self, channum, greater, watts, minutes, start, end, message):
        '''Create an entry in the alert table'''

        # Convert times to datetimes to satisfy SQLAlchemy
        start = datetime.combine(datetime.now().date(), start)
        end = datetime.combine(datetime.now().date(), end)
        greater = 1 if greater else 0
        with self.engine.begin() as conn:
            conn.execute(self.alert_table.insert().values(
                id=self.alert_id, channum=channum, greater=greater, watts=watts, minutes=minutes,
                start=start, end=end, message=message, alerted=0))
        self.alert_id += 1


    def get_alerts(self):
        '''Get all alerts from alert table'''

        with self.engine.connect() as conn:
            return conn.execute(select(self.alert_table))


    def set_alerted(self, alert_id, state):
        '''Set the alerted column for alert alert_id to state'''

        with self.engine.begin() as conn:
            alert_value = '1' if state else '0'
            stmt = update(self.alert_table) \
                .where(self.alert_table.c.id == alert_id) \
                .values(alerted=alert_value)
            conn.execute(stmt)


    def alert_triggered(self, alert):
        '''Look at interval alert.minutes in the past
           Return 1 if condition is true for all updates in the interval
           Return 0 if condition is not true for at least one update during the interval
           Return -1 if no records appear during the interval
        '''

        timestamp_limit = (datetime.utcnow() - timedelta(minutes=alert.minutes)).isoformat()
        with self.engine.connect() as conn:

            query1 = select([func.count()]).select_from(self.used_table) \
                .where(self.used_table.c.channum == alert.channum) \
                .where(self.used_table.c.stamp >= timestamp_limit)
            # Look for any records in interval opposite our condition (i.e. would disprove alert)
            if alert.greater:
                query2 = query1.where(self.used_table.c.watts < alert.watts)
            else:
                query2 = query1.where(self.used_table.c.watts > alert.watts)
            disprove_count = conn.execute(query2).fetchone()[0]

            # If records found that disprove alert, alert is not triggered
            if disprove_count != 0:
                return 0
            # If matching records during that time, alert is confirmed to be triggered
            records_count = conn.execute(query1).fetchone()[0]
            if records_count != 0:
                return 1
            # If there are no records during that timeframe, we don't know if it's triggered
            return -1


    def get_channel_name(self, channum):
        '''Return the name for channel channum'''

        with self.engine.connect() as conn:
            # This assumes channel exists. # TODO: handle case where it doesn't
            return conn.execute(select(self.channel_table.c.name) \
                .where(self.channel_table.c.channum == channum)) \
                .one() \
                .name


    def updating_changed(self):
        '''Return True if started or stopped updating'''

        with self.engine.connect() as conn:
            stamp = conn.execute(text('SELECT MAX(stamp) FROM used')).first()[0]
            old_updating = self.updating
            self.updating = (datetime.utcnow() - stamp).total_seconds() < 60
            return self.updating != old_updating


#This is how we would define the alerts table 'by hand'
#self.alerts_table = Table(
#    'alert',
#    self.metadata,
#    Column('id', Integer, primary_key=True),
#    Column('channum', Integer),
#    Column('greater', TINYINT),
#    Column('watts', Integer),
#    Column('minutes', Integer),
#    Column('start', DateTime),
#    Column('end', DateTime),
#    Column('message', String(255)),
#    Column('alerted', TINYINT)
#)
