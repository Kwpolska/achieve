Achieve
=======

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ff068d9259f949d8b68c4b74bfb1a4de)](https://www.codacy.com/app/kwpolska/achieve?utm_source=github.com&utm_medium=referral&utm_content=Kwpolska/achieve&utm_campaign=badger)

A task management/productivity web app, written in Django (Python). It loosely
follows GTD principles.

This project is currently in stagnation. It is generally finished for the web
part; the API was not started yet. A list of finished and unfinished features
is available below.

Setup
-----

Requirements: Python 3, PostgreSQL or SQLite3, nginx, uWSGI, Unix (Linux)

1. Pick a database engine and configure it in `achieveapp/settings.py`. I
   recommend PostgreSQL, but for small deployments SQLite3 will work well
   enough.
2. [Set up nginx and uWSGI][]. Put the app in `/srv/achieve`, use this
   repository for your `appdata`, and make sure to install `requirements.txt`.
   If you want to use PostgreSQL, `pip install psycopg2`.
   You will need the following environment variables:

        DJANGO_SETTINGS_MODULE=achieveapp.settings
        DEBUG=0
        DB_TYPE=postgres   # or sqlite3
        SECRET_KEY=  # set to something random
        DB_PASSWORD=  # set to whatever your database password is (PostgreSQL)
        DJANGO_LOG_PATH=/srv/achieve/logs/django.log
        DJANGO_STATIC_ROOT=/srv/achieve/static

3. Create a `local-config` file that `export`s those variables (use something
   different for `DJANGO_LOG_PATH` and set `DEBUG=1`) to use `./manage.py`
4. Run the following commands:

        source local-config
        ./manage.py migrate
        ./manage.py collectstatic
        ./manage.py createsuperuser
5. Edit `templates/achieve/pub_index.html` and add some way to contact you for
   prospective new users (if you want those).
6. (Re)start nginx and uWSGI.

[Set up nginx and uWSGI]: https://chriswarrick.com/blog/2016/02/10/deploying-python-web-apps-with-nginx-and-uwsgi-emperor/

Features and tasks (partial list)
---------------------------------

 - [X] Task, project, tag management
 - [X] Reminders (using browser notifications)
 - [X] Mobile friendly
 - [X] Pagination support
 - [X] Timezone support
 - [X] User account support
 - [X] Filtering and sorting (partial)
 - [ ] API
 - [ ] Exporting data
 - [ ] Search
 - [ ] Subtasks
 - [ ] Template system

License
-------

Copyright © 2015-2017, Chris Warrick.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions, and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions, and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

3. Neither the name of the author of this software nor the names of
   contributors to this software may be used to endorse or promote
   products derived from this software without specific prior written
   consent.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
