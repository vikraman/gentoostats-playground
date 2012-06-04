About
=====

The Gentoostats project aims to collect and analyse various statistics about
Gentoo systems.

This repository contains only the new Django server for GSoC 2012. For the old
one [look here](https://github.com/vh4x0r/gentoostats/tree/master/server).

You can find the updated client for GSoC 2012
[here](https://github.com/gg7/gentoostats/tree/gg7).

Installation
============

Gentoo systems
--------------

    emerge -av >=dev-python/django-1.4         # required
    emerge -av dev-python/south                # optional
    emerge -av dev-python/django-extensions    # optional

Make sure to create a suitable settings.py. You can use settings.py.example as
an example. Remember to modify the secret key, the database section, and the
installed apps section.

Other systems
--------------

Currently unsupported.

Upgrading
=========

You can use [South](http://south.aeracode.org/) for database migrations.

Usage
=====

Just like any other Django app.

Links
=====

GSoC 2011 Project:  http://www.google-melange.com/gsoc/project/google/gsoc2011/vh4x0r/26001  
GSoC 2011 Proposal: http://www.google-melange.com/gsoc/proposal/review/google/gsoc2011/vh4x0r/1  
GSoC 2012 Project:  http://www.google-melange.com/gsoc/project/google/gsoc2012/gg7/28001  
