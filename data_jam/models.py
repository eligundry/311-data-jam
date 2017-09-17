"""Module that defines helper models for this data jam."""

import csv
import os

import numpy
import peewee

from playhouse.db_url import connect
from playhouse.hybrid import hybrid_property
from playhouse.shortcuts import case


DB = connect(os.environ['DATABASE'])


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
    def import_from_csv(cls, file_obj):
        chunk_size = 100

        with DB.atomic():
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
    def import_from_csv(cls, file_obj):
        with DB.atomic():
            reader = csv.DictReader(file_obj)
            rows = []

            for row in reader:
                rows.append({
                    'county': row['county'],
                    'date': row['date'],
                    'type': row['type'],
                    'deaths': row['dth'],
                    'injured': row['inj'],
                })

            cls.insert_many(rows).execute()
