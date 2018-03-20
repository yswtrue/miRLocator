FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-add-repository ppa:j-4/vienna-rna
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y vienna-rna
RUN apt-get install -y python-pip
RUN pip install --upgrade pip
RUN pip install scikit-learn
RUN pip install flask
RUN pip install numpy
RUN pip install scipy
RUN apt-get install -y imagemagick
