"""Peewee migrations -- 001_Initial.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['model_name']            # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.python(func, *args, **kwargs)        # Run python code
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.drop_index(model, *col_names)
    > migrator.add_not_null(model, *field_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)

"""

import datetime as dt
import peewee as pw


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    with database.atomic():
        migrator.sql("""
CREATE TABLE service_requests (
    id integer NOT NULL,
    agency character varying(255) NOT NULL,
    type character varying(255) NOT NULL,
    descriptor character varying(255),
    borough character varying(255),
    latitude numeric(10,8),
    longitude numeric(11,8),
    created timestamp without time zone NOT NULL,
    closed timestamp without time zone
);
ALTER TABLE service_requests OWNER TO postgres;
CREATE SEQUENCE service_requests_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE service_requests_id_seq OWNER TO postgres;
ALTER SEQUENCE service_requests_id_seq OWNED BY service_requests.id;
ALTER TABLE ONLY service_requests ALTER COLUMN id SET DEFAULT nextval('service_requests_id_seq'::regclass);
ALTER TABLE ONLY service_requests
    ADD CONSTRAINT service_requests_pkey PRIMARY KEY (id);
CREATE INDEX service_requests_borough ON service_requests USING btree (borough);
        """)
        migrator.sql("""
CREATE TABLE storms (
    id integer NOT NULL,
    county character varying(255) NOT NULL,
    date date NOT NULL,
    type character varying(255) NOT NULL,
    deaths integer NOT NULL,
    injured integer NOT NULL
);
ALTER TABLE storms OWNER TO postgres;
CREATE SEQUENCE storms_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE storms_id_seq OWNER TO postgres;
ALTER SEQUENCE storms_id_seq OWNED BY storms.id;
ALTER TABLE ONLY storms ALTER COLUMN id SET DEFAULT nextval('storms_id_seq'::regclass);
ALTER TABLE ONLY storms
    ADD CONSTRAINT storms_pkey PRIMARY KEY (id);
        """)
        migrator.sql("""
--
-- Name: permitted_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE permitted_events (
    id integer NOT NULL,
    name character varying(1000),
    borough character varying(255),
    latitude numeric(10,8),
    longitude numeric(11,8),
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone NOT NULL
);
ALTER TABLE permitted_events OWNER TO postgres;
CREATE SEQUENCE permitted_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE permitted_events_id_seq OWNER TO postgres;
ALTER SEQUENCE permitted_events_id_seq OWNED BY permitted_events.id;
ALTER TABLE ONLY permitted_events ALTER COLUMN id SET DEFAULT nextval('permitted_events_id_seq'::regclass);
ALTER TABLE ONLY permitted_events
    ADD CONSTRAINT permitted_events_pkey PRIMARY KEY (id);
CREATE INDEX permitted_events_borough ON permitted_events USING btree (borough);
        """)



def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.sql("DROP TABLE service_requests;")
    migrator.sql("DROP TABLE storms;")
    migrator.sql("DROP TABLE permitted_events;")
