# 311 Data Jam

These are my materials for the 311 Data Jam as a part of the 2017 Day of Civic
Hacking. The project that I am working on is the effect of severe weather events
on NYC's 311 hotline.

## Background

From the 311 Data Jam project document:

> Large-scale events such as adverse weather can place a significant and
> unexpected burden upon New York City’s resources. Trained emergency workers
> from a variety of city agencies swing into action to address zero-day attacks
> on our health and safety, but these events also have a long tail of recovery.
> It has taken years to fully recover from hurricanes such as Irene or Sandy
> - events so impactful that their their impact on city services can’t easily be
> measured. (In the case of Sandy, whole new projects, teams, and tools were
> created to coordinate recovery.)
>
> At some point after adverse events, city agencies need to return to a “normal”
> mode, resuming business as usual. Recovery doesn’t just mean addressing the
> direct impacts of a major event, but also addressing the backlog of normal
> work which has piled up in the meantime. The 100 Resilient Cities project
> defines resilience as “the capacity of individuals, communities, institutions,
> businesses, and systems within a city to survive, adapt, and grow no matter
> what kinds of chronic stresses and acute shocks they experience.”

## What's In Here

* A Docker Compose setup of:
  * Jupyter Notebook
  * Postgresql
* Peewee models representing the relevant data types we want to query on.
* Some Jupyter notebooks to play with the data.

## Bringing This Up

1. `docker-compose up`
2. `docker exec -it -u 0 data-jam-notebook python manage.py migrate`
3. `docker exec -it -u 0 data-jam-notebook python import_service_request_data <path-to-311-data>`
4. `docker exec -it -u 0 data-jam-notebook python import_storm_data data/storms.csv`
5. `docker exec -it -u 0 data-jam-Notebook python import_permitted_events_data data/permitted_events.csv`
