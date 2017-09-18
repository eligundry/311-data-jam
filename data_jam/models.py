"""Module that defines helper models for this data jam."""

import csv
import os

from dateutil.parser import parse as date_parse

import geocoder
import numpy
import peewee

from playhouse.db_url import connect
from playhouse.hybrid import hybrid_property
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
    created = peewee.DateTimeField(null=False)
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

    @classmethod
    def lat_lngs(cls, expression=None):
        query = (
            cls
            .select(cls.latitude, cls.longitude)
            .where(cls.latitude != None, cls.longitude != None)
        )

        if expression:
            query = query.where(expression)

        return numpy.asarray(list(query.tuples()), dtype=float)


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
