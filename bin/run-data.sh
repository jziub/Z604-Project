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
TEXTS_DIR=$WORK_DIR/rawtext

### ALERT! PREVIOUS RESULTS ARE REMOVED! ###
rm -r $TEXTS_DIR; mkdir -p $TEXTS_DIR;


echo "###############################################"
echo "##  Downloading texts from HTRC Data API...  ##"
echo "###############################################"
python $HOME/text_download/DownloadVolumes.py $VOLUME_ID_FILE $TEXTS_DIR/rawtext.zip
unzip $TEXTS_DIR/rawtext.zip -d $TEXTS_DIR
rm $TEXTS_DIR/rawtext.zip
echo ""


echo "#########################################"
echo "##  Pre-processing texts in Hadoop...  ##"
echo "#########################################"
echo "Uploading texts to the local Hadoop cluster..."
DATE_OUTPUT=date-output
TF_OUTPUT=tf-output
hadoop fs -put $TEXTS_DIR $TEXTS_DIR
hadoop jar $HADOOP_HOME/contrib/streaming/hadoop-0.20.2-streaming.jar \
	-file $HOME/text_processing/map_reduce/getDateInText/mapper.py \
	-mapper $HOME/text_processing/map_reduce/getDateInText/mapper.py \
	-file $HOME/text_processing/map_reduce/getDateInText/reducer.py \
	-reducer $HOME/text_processing/map_reduce/getDateInText/reducer.py \
	-input $TEXTS_DIR \
	-output $DATE_OUTPUT
	
hadoop jar $HADOOP_HOME/contrib/streaming/hadoop-0.20.2-streaming.jar \
	-file $HOME/text_processing/map_reduce/getTF/mapper.py \
	-mapper $HOME/text_processing/map_reduce/getTF/mapper.py \
	-file $HOME/text_processing/map_reduce/getTF/reducer.py \
	-reducer $HOME/text_processing/map_reduce/getTF/reducer.py \
	-input $TEXTS_DIR \
	-output $TF_OUTPUT 
	
echo ""


### Steps below assume the MR job only outputs one result file! ###

echo "########################################"
echo "##  Downloading results from HDFS...  ##"
echo "########################################"
hadoop fs -copyToLocal $DATE_OUTPUT $WORK_DIR/$DATE_OUTPUT
hadoop fs -copyToLocal $TF_OUTPUT $WORK_DIR/$TF_OUTPUT
echo ""


echo "####################################"
echo "##  Run temporal classification   ##"
echo "####################################"
python $HOME/text_processing/getFirstDateInText.py $TEXTS_DIR >> $WORK_DIR/date1st_aa.txt
python $HOME/text_processing/importDate.py $WORK_DIR/$DATE_OUTPUT/part-00000 $WORK_DIR/date1st_aa.txt
python $HOME/text_processing/importTFDF.py $WORK_DIR/$TF_OUTPUT/part-00000
python $HOME/text_processing/TLM.py

python $HOME/classification/compare.py >> $WORK_DIR/final-result.txt

echo ""
