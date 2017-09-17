"""Module that defines helper models for this data jam."""

import csv
import os

import peewee

from playhouse.db_url import connect


DB = connect(os.environ['DATABASE'])


class ServiceRequest(peewee.Model):
    agency = peewee.CharField(null=False)
    type = peewee.CharField(null=False)
    descriptor = peewee.CharField(null=True)
    latitude = peewee.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=False,
    )
    longitude = peewee.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=False,
    )
    created = peewee.DateTimeField(null=False)
    closed = peewee.DateTimeField(null=True)

    class Meta:
        db_table = 'service_requests'
        database = DB

    @classmethod
    def import_from_csv(cls, path):
        chunk_size = 1000

        with DB.atomic(), open(path, 'r') as fp:
            reader = csv.DictReader(fp)
            rows = []

            for idx, row in reader:
                rows.append({
                    'agency': row['Agency'],
                    'type': row['Type'],
                    'descriptor': row['Descriptor'],
                    'latitude': row['Latitude'],
                    'longitude': row['Longitude'],
                    'created': row['Created Date'],
                    'closed': row['Closed Date'] or None,
                })

                if idx > 0 and idx % chunk_size == 0:
                    cls.insert_many(rows)
                    rows = []
