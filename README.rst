=======================================
Tire Testing Consortium Website Scraper
=======================================

Description
===========
A fairly simple program that will log into the TTC "secure" forum and then
download all testing data.

Installation
============
In order to use this program, you will need to have Python 3 installed.
Preferably the latest version.

First, obtain the source code by either downloading a copy from `github <>`_ or
cloning the source directly with `git`::
    
    git clone ------

If you want to install the program you can do so with the following command
(may require superuser privileges). ::

    python setup.py install

.. note::
     Note that you do **not** need to install the program in order to use it.

Usage
=====
There are two ways you can run this program. Installing it as a package gives
you access to the `scrape_ttc` command, however that is more of a convenience
thing and there aren't any other big differences.

To run the program, change to the project's root directory and type::

    python3 -m ttc_scraper YOUR_USERNAME YOUR_PASSWORD

Or if you installed the program::

    scrape_ttc YOUR_USERNAME YOUR_PASSWORD

Having the program installed also allows you to run the program from anywhere
with the `python -m ...` command. Note that the `scrape_ttc` command is just a
shortcut for the `python -m ...` command used above, perfect for the lazy among
us.

Halp!
-----
If you are having issues or want to customise how the program runs, then a good
idea is to check out the program's help with::

    scrape_ttc --help

If you think you find a bug in the program or you've followed the above
installation instructions correctly yet it keeps crashing then create an issue
at the github link above.

Licensing
=========
Although this project is MIT licensed (meaning you can share, hack or do
whatever you want with it, within reason), it is highly recommended that you
read the TTC website's terms and conditions before using this scraper.

Also, because you are downloading massive amounts of data in a short amount 
of time, there is the remote possibility that you'll end up overloading their 
website and/or get your account banned. 

It hasn't happened yet but if you fuck up, well, you **were** warned.

