
Simple per-uri Access Log for Nginx
===================================

Python 3 implementation of a simple UDP syslog server which gets uri access data from nginx server and increments stats data into a MongoDB database.

About
-----

Allows not to mess with heavy nginx access.log files and get data on fly to syslog

Every message from syslog goes to redis memory cache, then after every `CACHE_TIMEOUT` seconds all data saved to database with a single query

Be aware the that the UDP packages are not encrypted.

See ``requirements.txt`` for installed packages and the used versions.

Example guide based on Ubuntu 18.04 installation

Usage
-----

Install Nginx server
--------------------

    echo "deb http://nginx.org/packages/ubuntu/ bionic nginx" | sudo tee /etc/apt/sources.list.d/nginx.list
    echo "deb-src http://nginx.org/packages/ubuntu/ bionic nginx" | sudo tee /etc/apt/sources.list.d/nginx.list
    wget https://nginx.org/keys/nginx_signing.key -O - | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install nginx



**Then modify the default parameters in the ``settings.py`` to set nginx access_log**


    sudo nano /etc/nginx/nginx.conf


**Insert following**



    log_format json_combined escape=json
          '{'
              '"request":"$request"'
          '}';
    access_log syslog:server=127.0.0.1:12000,nohostname json_combined;

**Restart nginx**


    sudo nginx -s reload

Install Mongodb
---------------

    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4
    echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    sudo service mongod start
    sudo cat /var/log/mongodb/mongod.log | grep waiting




Install Redis
-------------
    sudo apt install redis


**You can also set maxmemory policy in redis.conf if want to**


    sudo nano /etc/redis/redis.conf

**Insert following**


    supervised systemd
    maxmemory 1500mb
    maxmemory-policy allkeys-lru



Getting source from the git
---------------------------

Install the required ``requirements.txt`` in the global Python 3
environment or in a virtual Python 3 environment. The latter has the advantage that
the packages are isolated from other projects and also from the system wide
installed global once. If things get messed up, the virtual environment can
just be deleted and created from scratch again.

    cd ~
    mkdir per_uri_stats
    cd per_uri_stats
    git clone https://github.com/A-Iskakov/python3_simple_per_uri_access_log_nginx
    sudo pip3 install -r requirements.txt



**Then modify the default parameters in the ``settings.py``.**

    nano settings.py

**Launch syslog server**

    python3 syslogserver.py


Systemd service
---------------

An example `nginx-stats.service` is also included to show how to run the syslog server
as a systemd service at startup.
In the example .service file a virtual Python 3 environment is used to execute
the script. The local user name and the path to the virtual Python 3 environment
needs to be adjusted before it can be used.

To activate the systemd service execute following commands.

**Modify the default parameters in the `nginx-stats.service`.**

    nano nginx-stats.service

**Copy to systemd dir**

    sudo cp nginx-stats.service /etc/systemd/system/

**Create temp dir for service**

```sh
echo "d /run/nginx-stats 0755 ubuntu ubuntu -" | sudo tee /etc/tmpfiles.d/nginx-stats.conf
```



**Launch service**
```sh
sudo systemctl enable nginx-stats.service
sudo systemctl start nginx-stats.service
sudo systemctl status nginx-stats.service
```