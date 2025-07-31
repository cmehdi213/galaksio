############################################################
# Dockerfile to build Galaksio container images
# Based on official HTTPD
############################################################
# Set the base image to official HTTP
FROM httpd:2.4

# File Author / Maintainer
MAINTAINER Tomas Klingström

################## BEGIN INSTALLATION ######################
# INSTALL THE DEPENDENCIES
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        wget \
        libapache2-mod-wsgi-py3 \
        python3 \
        python3-pip \
        python3-dev \
        build-essential \
    && apt-get clean \
    && pip3 install --upgrade pip \
    && pip3 install \
        bioblend==1.6.0 \
        flask==3.0.0 \
        requests==2.31.0 \
        fpdf==1.7.2 \
        fpdf2==2.7.6 \
    && apt-get remove -y python3-dev build-essential \
    && apt-get autoremove -y

# DOWNLOAD AND INSTALL THE APP CODE
RUN wget -O /tmp/galaksio.zip https://github.com/sgbc/galaksio/archive/master.zip \
    && unzip /tmp/galaksio.zip -d /tmp/galaksio \
    && mv /tmp/galaksio/*/ /usr/local/apache2/htdocs/ \
    && rm -r /tmp/galaksio/ \
    && rm /tmp/galaksio.zip \
    && sed -i 's/application\.launch/#application\.launch/' /usr/local/apache2/htdocs/server/launch_server.py \
    && sed -i 's/isDocker = False/isDocker = True/' /usr/local/apache2/htdocs/server/launch_server.py \
    && sed -i 's/8081/80/' /usr/local/apache2/htdocs/server/resources/example_serverconf.cfg

COPY configs/entrypoint.sh /usr/bin/entrypoint.sh
COPY configs/httpd.conf /usr/local/apache2/conf/httpd.conf
COPY configs/galaksio.wsgi /usr/local/apache2/htdocs/galaksio.wsgi

RUN chmod +x /usr/bin/entrypoint.sh \
    && chown -R www-data:www-data /usr/local/apache2/htdocs

##################### INSTALLATION END #####################
VOLUME ["/usr/local/apache2/htdocs/server/conf/"]
EXPOSE 80
ENTRYPOINT ["/usr/bin/entrypoint.sh"]
