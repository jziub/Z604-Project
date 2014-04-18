# Copyright 2013 The Trustees of Indiana University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either expressed or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
