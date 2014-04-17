#!/bin/bash

HOME=`dirname "$0"`/..
WORK_DIR=$HOME/working-dir
VOLUME_ID_FILE=$HOME/idlist
METADATA_DIR=$WORK_DIR/metadata

### ALERT! PREVIOUS RESULTS ARE REMOVED! ###
rm -f $METADATA_DIR; mkdir -p $METADATA_DIR

echo "##############################################"
echo "##  Downloading MARC xml from HTRC Solr...  ##"
echo "##############################################"
python $HOME/metadata_processing/downloadMetadata.py $VOLUME_ID_FILE $METADATA_DIR
echo ""

echo "#########################################"
echo "##  Populating MARC xml to MongoDB...  ##"
echo "#########################################"
python $HOME/metadata_processing/getDV.py $METADATA_DIR
echo ""
