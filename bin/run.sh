#!/bin/bash

# set env
BIN=`dirname "$0"`
BIN=`cd "$BIN"; pwd`
HOME=`dirname "$BIN"`/..
WORK_DIR=$HOME/working-dir
VOLUME_ID_FILE=$HOME/idlist
METADATA_DIR=$WORK_DIR/metadata

mkdir -p $WORK_DIR
mkdir -p $METADATA_DIR

echo "###############################################"
echo "##  Downloading texts from HTRC Data API...  ##"
echo "###############################################"
python $HOME/text_download/DownloadVolumes.py $VOLUME_ID_FILE $WORK_DIR/rawtext.zip


echo "##############################################"
echo "##  Downloading MARC xml from HTRC Solr...  ##"
echo "##############################################"
python $HOME/metadata_processing/downloadMetadata.py $VOLUME_ID_FILE $WORK_DIR/metadata


echo "#########################################"
echo "##  Populating MARC xml to MongoDB...  ##"
echo "#########################################"
# create a db in mongodb first?
python $HOME/metadata_processing/getDV.py $WORK_DIR/metadata


echo "#########################################"
echo "##  Pre-processing texts in Hadoop...  ##"
echo "#########################################"



echo "####################################"
echo "##  Run temporal classification   ##"
echo "####################################"

