=======
PREQUEL
=======

*simplfy your data ingest problem*


PREQUEL moves your data to SQLite3. The aim is to enable sophisticated
queries over data that is currently stored in the wild as JSON, CSV and
spreadsheet form. It is inspired by [SQLShare][ss], which aims to empower
people by enabling them to access to a raw query interface. PREQUEL differs
markedly however though, in that it seeks to give people access to structured
data on their own machine rather than need to do that via the cloud.

 [ss]: http://escience.washington.edu/sqlshare

MOTIVATION
----------

SQL and databases are excellent at manipulating data, but getting datasets
into those tools rarely a very nice experience. Prequel aims to simplify the
data ingest problem.

Research from the University of Washington's eScience Institute (citation to
follow) shows that the big data problem that is really being felt by
researchers is bringing data together from many sources. Most datasets fit
within the GB range. Datasets of this magnitude can be easily handled by
SQLite3. SQLite3 is free, easy to install and is actually pretty fast. Let's
make use of that.

CAVEAT
------

Many of features described in this document have not yet been implemented.
Consider this a case of [Readme driven development][rdd].

 [rdd]: http://tom.preston-werner.com/2010/08/23/readme-driven-development.html

USAGE
-----

## Basic


Run PREQUEL from the command line:

```sh
prequel tax-spending.csv
```

This will generate a database called `tax-spending.db`, and will use the
headings from the first line of `tax-spending.csv` to generate the column
names within it.

Let's say that `tax-spending.csv` looks something like this..

```csv
Region,Area,Spend
A,Education,4000000
A,Health,3000000
A,Law and Order,1000000
B,Education,3400000
B,Health,2300000
B,Law and Order,600000
```

..then something like the following SQL will be executed:

```sql
CREATE TABLE tax_spending (
  region,
  area,
  spend
);

INSERT INTO tax_spending VALUES ('A', 'Education', '4000000');
INSERT INTO tax_spending VALUES ('A', 'Health', '3000000');
...
INSERT INTO tax_spending VALUES ('A', 'Law and Order', '600000');
```

Many data input formats provide typed data. With this additional information,
PREQUEL does a little more work. Consider the following command:

```sh
prequel tax-spending.json
```

Where `tax-spending.json` is a file that contains the following data:

```js
[
  { "Region":"A", "Area":"Education", "Spend":4000000 },
  { "Region":"A", "Area":"Health", "Spend":3000000 },
  { "Region":"A", "Area":"Law and Order", "Spend":1000000 },
  { "Region":"B", "Area":"Education", "Spend":3400000 },
  { "Region":"B", "Area":"Health", "Spend":2300000 },
  { "Region":"B", "Area":"Law and Order", "Spend":600000 }
]
```
The following SQL will be executed:

```sql
CREATE TABLE tax_spending (
  region TEXT,
  area TEXT,
  spend NUMERIC
);

INSERT INTO tax_spending VALUES ('A', 'Education', 4000000);
INSERT INTO tax_spending VALUES ('A', 'Health', 3000000);
...
INSERT INTO tax_spending VALUES ('A', 'Law and Order', 600000);
```

## Type Hinting


If you would like to provide type hints yourself, you can use the
following syntax:

```sh
prequel tax-spending.csv -h "Spend:integer"
```

The following type hints are supported:

- blob
- category
- integer
- numeric (either real or integer)
- text
- object
- time
- real

## Categorical Data

A providing the type hint of `category` will indicate to PREQUEL that it
should normalize the data in that column. Here's an example.

Command:

```sh
prequel tax-spending.csv \
  -h "region:category" \
  -h "area:category" \
  -h "spend:integer"
```

SQL:

```sql
CREATE TABLE regions (
  id PRIMARY KEY AUTOINCREMENT,
  region UNIQUE
);

CREATE TABLE areas (
  id PRIMARY KEY AUTOINCREMENT,
  area UNIQUE
)

CREATE TABLE tax_spending (
  region INTEGER,
  area INTEGER,
  spend NUMERIC,

  FOREIGN KEY(region) REFERENCES regions(id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY(area) REFERENCES areas(id) DEFERRABLE INITIALLY DEFERRED
);
```

Database (in pseudo-markup):

```
regions (
  1, A
  2, B
)

areas (
  1, Education
  2, Health
  3, Law and Order
)

tax_spending (
  1,1,4000000
  1,2,3000000
  1,3,1000000
  2,1,3400000
  2,2,2300000
  2,3,600000
)
```

What that means is data will not be duplicated. This saves a lot of disk space,
and perhaps increases the performance for some queries.


## Object Data


If a field represented a serialised object, PREQUEL will attempt to
normalise the data. If the data is not JSON encoded, you should provide
a python callable and a module name to import.




LEGAL
-----

### No Warranty

PREQUEL comes with no warranty, except as required by law. Use the software
at your own risk.


### Copyright: Owner

The copyright owner of PREQUEL is Tim McNamara.


### Copyright: Documentation

PREQUEL's documentation is licenced under CC-BY-NZ 3.0, available in summary
and full forms from the URLs below:

- http://creativecommons.org/licenses/by/3.0/nz/
- http://creativecommons.org/licenses/by/3.0/nz/legalcode

To fulfil the attribution requirement, include a URL in your work to the
location where you downloaded PREQUEL from.


### Copyright: Code

PREQUEL is licenced under the Apache License, Version 2, available from the
Apache Software Foundation at the following URL: http://www.apache.org/licenses/LICENSE-2.0.html


If you do not agree to the terms of the licence, do not use the software.


### Trade mark

PREQUEL is an unregistered trade mark owned by Tim McNamara. If you create a
derivative product according to the copyright licence, do not use the word 
"prequel" in its name.



### Consumer Guarantees

Under the Consumer Guarantees Act 1993, non-business users of
PREQUEL may have certain minimal rights. Bearing in mind that I
am providing this software for free and that PREQUEL is not fit
for any particular purpose, the following sites may be of interest:

- http://www.consumeraffairs.govt.nz/for-consumers/law/consumer-guarantees-act
- http://www.justice.govt.nz/tribunals/disputes-tribunal


### Jurisdiction

If any dispute were to arise, they will be resolved under the laws of
New Zealand.

