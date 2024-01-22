'''Greener Circuits database class'''

from datetime import datetime, timedelta
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, Integer, DateTime, String, Float
from sqlalchemy import text, select, update, delete, func
from sqlalchemy.dialects.mysql import TINYINT, TIME


class GCDatabase:   #pylint: disable=too-many-instance-attributes
    '''This class represents the Greener Circuits database'''

    def __init__(self):
        '''Constructor'''

        self.updating = True    # True if database has been recently updated

        connect_env = 'connect_gc'
        if connect_env not in os.environ:
            print('Connection string', connect_env, 'not set in environment')
            sys.exit()
        self.engine = create_engine(os.environ[connect_env], future=True, echo=False)

        self.metadata = MetaData()
        # To auto-load table structures from database, use this:
        #self.auto_load_tables()

        # To create table structures from scratch, use these:
        self.alert_table = self.define_alert_table()
        self.channel_table = self.define_channel_table()
        self.scratchpad_table = self.define_scratchpad_table()
        self.settings_table = self.define_settings_table()
        self.used_table = self.define_used_table()

        # Get settings
        with self.engine.begin() as conn:
            settings = conn.execute(select(self.settings_table)).one_or_none()
            if settings is None:
                self.consolidate_stamp = None
                self.history_days = 365
                conn.execute(self.settings_table.insert() \
                    .values(consolidate_stamp=self.consolidate_stamp,
                            history_days=self.history_days))
            else:
                self.consolidate_stamp = settings.consolidate_stamp
                self.history_days = settings.history_days



    def auto_load_tables(self):
        '''Load table structures from the database'''

        with self.engine.connect() as conn:
            self.alert_table = Table('alert', self.metadata, autoload_with=conn)
            self.channel_table = Table('channel', self.metadata, autoload_with=conn)
            self.scratchpad_table = Table('scratchpad', self.metadata, autoload_with=conn)
            self.settings_table = Table('settings', self.metadata, autoload_with=conn)
            self.used_table = Table('used', self.metadata, autoload_with=conn)


    def create_tables(self):
        '''Once tables have been defined, create them'''

        self.metadata.create_all(self.engine)


    def define_alert_table(self):
        '''Define the alert table structure'''

        return Table(
            'alert',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('channum', Integer),
            Column('greater', TINYINT),
            Column('watts', Integer),
            Column('minutes', Integer),
            Column('start', TIME),
            Column('end', TIME),
            Column('message', String(255)),
            Column('alerted', TINYINT)
        )


    def define_channel_table(self):
        '''Define the channel table structure'''

        return Table(
            'channel',
            self.metadata,
            Column('channum', Integer, primary_key=True, autoincrement=False),
            Column('name', String(255)),
            Column('type', Integer),
            Column('watts', Float),
            Column('stamp', DateTime)
        )


    def define_scratchpad_table(self):
        '''Define the scratchpad table structure (same as used except for name)'''

        return Table(
            'scratchpad',
            self.metadata,
            Column('channum', Integer),
            Column('watts', Integer),
            Column('stamp', DateTime)
        )


    def define_settings_table(self):
        '''Define the settings table structure'''

        return Table(
            'settings',
            self.metadata,
            Column('consolidate_stamp', DateTime),
            Column('history_days', Integer)
        )


    def define_used_table(self):
        '''Define the used table structure'''

        return Table(
            'used',
            self.metadata,
            Column('channum', Integer, index=True),
            Column('watts', Integer),
            Column('stamp', DateTime, index=True)
        )


    def get_channels(self):
        '''Get all channels from channel table'''

        with self.engine.connect() as conn:
            return conn.execute(select(self.channel_table).where(self.channel_table.c.type!=0))


    def insert_usage(self, channum, watts, utcnow):
        '''Insert usage into used and update channel table'''

        # TODO: Each insert and update takes a round trip, plus a commit after both
        #  - make bulk inserts and updates
        # TODO: Think about combining all readings from a single update into a single row
        #print('Inserting usage for channel', channum, 'to', watts, 'watts')
        with self.engine.begin() as conn:
            conn.execute(self.used_table.insert() \
                .values(channum=channum, watts=watts, stamp=utcnow))
            conn.execute(self.channel_table.update() \
                .where(self.channel_table.c.channum == channum) \
                .values(watts=watts, stamp=utcnow))

    def update_total_watts(self, utcnow):
        '''Update total home usage in channel table'''

        with self.engine.connect() as conn:
            query = select(func.sum(self.channel_table.c.watts)) \
                .where(self.channel_table.c.type > 0)
            total_watts = conn.execute(query).fetchone()[0]
            #print('Updating total watts to', total_watts)
        self.insert_usage(0, total_watts, utcnow)


    def get_min_used_stamp(self):
        '''Return the earliest timestamp from used table'''

        with self.engine.connect() as conn:
            query = select([func.min(self.used_table.c.stamp)])
            return conn.execute(query).fetchone()[0]


    def get_usage(self, channel, start_stamp, end_stamp, bar_seconds):
        '''Return usage representing bars of bar_seconds each'''

        with self.engine.connect() as conn:
            # TODO: Convert from text query to SQLAlchemy calls
            query = text("SELECT FROM_UNIXTIME(UNIX_TIMESTAMP(stamp) DIV " +
                     str(bar_seconds) + " * " + str(bar_seconds) + ") AS stamp, " +
                     "ROUND(AVG(watts)) AS watts " +
                 "FROM used " +
                 "WHERE channum = " + str(channel) +
                      " AND stamp BETWEEN '" + start_stamp.isoformat() +
                        "' AND '" + end_stamp.isoformat() + "' " +
                 "GROUP BY UNIX_TIMESTAMP(stamp) DIV " + str(bar_seconds))
            return conn.execute(query).fetchall()


    def consolidate(self, start_stamp, end_stamp):
        '''Consolidate records in used table into 1-minute intervals'''

        with self.engine.begin() as conn:
            start = datetime.utcnow()
            # - Clear scratchpad table
            conn.execute(delete(self.scratchpad_table))
            # - Consolidate appropriate rows into scratchpad table
            # TODO: Use SQLAlchemy instead of text for these
            query = text('INSERT INTO scratchpad '
                'SELECT '
                    'channum, '
                    'AVG(watts) AS watts, '
                    'FROM_UNIXTIME(UNIX_TIMESTAMP(stamp) DIV 60 * 60 ) AS stamp '
                'FROM used '
                'WHERE stamp >= "' + start_stamp.isoformat() + '" '
                    'AND stamp < "' + end_stamp.isoformat() + '" '
                'GROUP BY channum, UNIX_TIMESTAMP(stamp) DIV 60')
            conn.execute(query)
            # - Delete original rows.
            query = text('DELETE FROM used '
                'WHERE stamp >= "' + start_stamp.isoformat()
                + '" AND stamp < "' + end_stamp.isoformat() + '" ')
            conn.execute(query)
            # - Copy from scratchpad table to original table.
            query = text('INSERT INTO used SELECT * FROM scratchpad')
            conn.execute(query)

            # Update consolidate_stamp
            conn.execute(self.settings_table.update() \
                .values(consolidate_stamp=end_stamp))
            self.consolidate_stamp = end_stamp


        print('Done consolidating,', (datetime.utcnow() - start).total_seconds(), 'seconds')
        sys.stdout.flush()


    def cull(self, end_stamp):
        '''Cull records from used table where stamp is more than history_days old'''

        with self.engine.begin() as conn:
            start = datetime.utcnow()
            cull_start = end_stamp - timedelta(days=self.history_days)
            print('Culling records before', cull_start.isoformat())
            # TODO: Use SQLAlchemy instead of text for this
            stmt = text('DELETE FROM used WHERE stamp < "' + cull_start.isoformat() + '"')
            conn.execute(stmt)
            print('Done culling,', (datetime.utcnow() - start).total_seconds(), 'seconds')
            sys.stdout.flush()


    def delete_alerts(self):
        '''Delete all alerts in table'''
        with self.engine.begin() as conn:
            conn.execute(self.alert_table.delete())
            conn.execute(text('ALTER TABLE alert AUTO_INCREMENT = 1'))


    def create_alert(self, channum, greater, watts, minutes, start, end, message):  #pylint: disable=too-many-arguments
        '''Create an entry in the alert table'''

        # Convert times to datetimes to satisfy SQLAlchemy
        start = datetime.combine(datetime.now().date(), start)
        end = datetime.combine(datetime.now().date(), end)
        greater = 1 if greater else 0
        with self.engine.begin() as conn:
            conn.execute(self.alert_table.insert().values(
                channum=channum, greater=greater, watts=watts, minutes=minutes,
                start=start, end=end, message=message, alerted=0))


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
