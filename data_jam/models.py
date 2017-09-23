"""Module that defines helper models for this data jam."""

import csv
import decimal
import os

from dateutil.parser import parse as date_parse

import bs4
import geocoder
import numpy
import peewee
import requests

from playhouse.postgres_ext import ArrayField
from playhouse.db_url import connect
from playhouse.hybrid import hybrid_property, hybrid_method
from playhouse.shortcuts import case
from peewee_migrate import Router


DB = connect(os.environ['DATABASE'])
MIGRATION_ROUTER = Router(DB)


class ServiceRequest(peewee.Model):
    agency = peewee.CharField(null=False)
    type = peewee.CharField(null=False)
    descriptor = peewee.CharField(null=True)
    borough = peewee.CharField(null=True, index=True)
    latitude = peewee.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
    )
    longitude = peewee.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
    )
    created = peewee.DateTimeField(null=False, index=True)
    closed = peewee.DateTimeField(null=True)

    class Meta:
        db_table = 'service_requests'
        database = DB

    @classmethod
    @DB.atomic()
    def import_from_csv(cls, file_obj):
        chunk_size = 10000
        reader = csv.DictReader(file_obj)
        rows = []

        for idx, row in enumerate(reader):
            rows.append({
                'agency': row['Agency'],
                'type': row['Complaint Type'],
                'descriptor': row['Descriptor'],
                'borough': row['Borough'],
                'latitude': row['Latitude'],
                'longitude': row['Longitude'],
                'created': row['Created Date'],
                'closed': row['Closed Date'] or None,
            })

            if idx > 0 and idx % chunk_size == 0:
                cls.insert_many(rows).execute()
                rows = []
                print(f"Inserted {idx} service requests!")

        if rows:
            cls.insert_many(rows).execute()

    @hybrid_method
    def happened_between(self, start, end):
        return (self.created >= start) & (self.created <= end)

    @classmethod
    def count_by_day(cls, start, end):
        query = (
            cls
            .select(
                peewee.fn.DATE(cls.created).alias('date'),
                peewee.fn.COUNT(cls.id).alias('calls'),
            )
            .where(cls.happened_between(start, end))
        )
        query = (
            query
            .group_by(query.c.date)
            .order_by(query.c.date.asc())
        )

        return query.tuples()

    @classmethod
    def lat_lngs(cls, query=None):
        query = (
            (query or cls.select())
            .select(cls.latitude, cls.longitude)
            .where(cls.latitude != None, cls.longitude != None)
        )

        return numpy.asarray(query.tuples(), dtype=float)


class Storm(peewee.Model):
    county = peewee.CharField(null=False, index=True)
    date = peewee.DateField(null=False)
    type = peewee.CharField(null=False)
    deaths = peewee.IntegerField(null=False, default=0)
    injured = peewee.IntegerField(null=False, default=0)

    COUNTY_BOROUGH_MAPPING = (
        ('BRONX (ZONE)', 'BRONX'),
        ('BRONX CO.', 'BRONX'),
        ('KINGS (BROOKLYN) (ZONE)', 'BROOKLYN'),
        ('KINGS CO.', 'BROOKLYN'),
        ('NEW YORK (MANHATTAN) (ZONE)', 'MANHATTAN'),
        ('NEW YORK CO.', 'MANHATTAN'),
        ('NORTHERN QUEENS (ZONE)', 'QUEENS'),
        ('QUEENS CO.', 'QUEENS'),
        ('RICHMOND (STATEN IS.) (ZONE)', 'STATEN ISLAND'),
        ('RICHMOND CO.', 'STATEN ISLAND'),
        ('SOUTHERN QUEENS (ZONE)', 'QUEENS'),
    )

    @hybrid_property
    def borough(self):
        return dict(self.COUNTY_BOROUGH_MAPPING)[self.county]

    @borough.expression
    def borough(cls):
        return case(cls.county, cls.COUNTY_BOROUGH_MAPPING)

    class Meta:
        db_table = 'storms'
        database = DB

    @classmethod
    @DB.atomic()
    def import_from_csv(cls, file_obj):
        reader = csv.DictReader(file_obj)
        rows = []

        for row in reader:
            rows.append({
                'county': row['county'],
                'date': date_parse(row['date']).date(),
                'type': row['type'],
                'deaths': row['dth'],
                'injured': row['inj'],
            })

        cls.insert_many(rows).execute()


class PermittedEvent(peewee.Model):
    name = peewee.CharField(max_length=1000, null=True)
    borough = peewee.CharField(null=True, index=True)
    latitude = peewee.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
    )
    longitude = peewee.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
    )
    start_time = peewee.DateTimeField(null=False)
    end_time = peewee.DateTimeField(null=False)

    class Meta:
        db_table = 'permitted_events'
        database = DB

    @classmethod
    @DB.atomic()
    def import_from_csv(cls, file_obj):
        reader = csv.DictReader(file_obj)
        rows = []

        for row in reader:
            coded = geocoder.google(row['Event Location'])

            if coded.ok:
                longitude, latitude = (
                    coded.geojson['features'][0]['geometry']['coordinates']
                )
            else:
                continue

            rows.append({
                'name': row['Event Name'],
                'start_time': row['Start Date/Time'],
                'end_time': row['End Date/Time'],
                'borough': row['Event Borough'].upper(),
                'latitude': latitude,
                'longitude': longitude,
            })

        cls.insert_many(rows).execute()


class Event(peewee.Model):
    short_description = peewee.CharField(null=True)
    description = peewee.TextField(null=True)
    start_time = peewee.DateTimeField(index=True, null=True)
    end_time = peewee.DateTimeField(null=True)
    borough = peewee.CharField(null=True, index=True)
    latitude = peewee.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
    )
    longitude = peewee.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
    )

    NORMALIZED_BOURUGHS = {
        'qn': 'QUEENS',
        'mn': 'MANHATTAN',
        'bk': 'BROOKLYN',
        'bx': 'BRONX',
        'si': 'STATEN ISLAND',
        'other': 'MANHATTAN',
    }

    class Meta:
        db_table = 'events'
        database = DB

    @classmethod
    def import_from_site(cls, start_page=1):
        url = 'http://www1.nyc.gov/calendar/api/json/search.htm'
        params = {
            'sort': 'DATE',
            'pageNumber': start_page,
        }
        is_last_page = False

        while not is_last_page:
            resp = requests.get(url, params=params)

            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                continue

            data = resp.json()
            rows = []

            with DB.atomic():
                for item in data['items']:
                    geo = item.get('geometry')

                    if not geo:
                        coded = geocoder.google(item['address'])

                        if not coded.ok:
                            continue

                        longitude, latitude = (
                            coded.geojson['features'][0]['geometry']['coordinates']
                        )

                    else:
                        longitude = geo[0]['lng']
                        latitude = geo[0]['lat']

                    soup = bs4.BeautifulSoup(item.get('desc', ''), 'html5lib')

                    for borough in item['boroughs']:
                        try:
                            rows.append({
                                'short_description': item['shortDesc'],
                                'description': soup.get_text(),
                                'start_time': item.get('startDate'),
                                'end_time': item.get('endDate'),
                                'borough': cls.NORMALIZED_BOURUGHS[borough.lower()],
                                'latitude': decimal.Decimal(latitude),
                                'longitude': decimal.Decimal(longitude),
                            })
                        except:
                            continue

                cls.insert_many(rows).execute()
                rows = []
                params['pageNumber'] += 1
                progress = data['pagination']['currentPage'] * 10
                print(f"Imported {progress} Events!")


            is_last_page = data['pagination']['isLastPage']


class Weather(peewee.Model):
    date = peewee.DateField(null=False, index=True)
    temp_avg = peewee.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
    )
    temp_low = peewee.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
    )
    temp_high = peewee.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
    )
    precipitation = peewee.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
        default=0,
    )
    humidity = peewee.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
    )
    dew_point = peewee.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
    )
    events = ArrayField(field_class=peewee.CharField)

    class Meta:
        db_table = 'weather'
        database = DB

    @classmethod
    @DB.atomic()
    def import_from_csv(cls, file_obj):
        reader = csv.DictReader(file_obj)
        rows = []

        for row in reader:
            events = [event.strip() for event in row['event'].split(',')]

            if events == ['']:
                events = []

            rows.append({
                'date': row['Date'],
                'temp_avg': row['T_avg'],
                'temp_low': row['T_low'],
                'temp_high': row['T_high'],
                'precipitation': row['R_sum'],
                'humidity': row['H_high'],
                'dew_point': row['DP_high'],
                'events': events,
            })

        cls.insert_many(rows).execute()
