#!/bin/bash
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
DATE_OUTPUT=date-output
TF_OUTPUT=tf-output
hadoop fs -put $TEXTS_DIR $TEXTS_DIR
hadoop jar $HADOOP_HOME/contrib/streaming/hadoop-0.20.0-streaming.jar \
	-file $HOME/text_processing/getDateInText/mapper.py \
	-mapper $HOME/text_processing/getDateInText/mapper.py \
	-file $HOME/text_processing/getDateInText/reducer.py \
	-reducer $HOME/text_processing/getDateInText/reducer.py \
	-input $TEXTS_DIR \
	-output $DATE_OUTPUT \
hadoop jar $HADOOP_HOME/contrib/streaming/hadoop-0.20.0-streaming.jar \
	-file $HOME/text_processing/getTF/mapper.py \
	-mapper $HOME/text_processing/getTF/mapper.py \
	-file $HOME/text_processing/getTF/reducer.py \
	-reducer $HOME/text_processing/getTF/reducer.py \
	-input $TEXTS_DIR \
	-output $TF_OUTPUT \
echo ""


echo "########################################"
echo "##  Downloading results from HDFS...  ##"
echo "########################################"
hadoop fs -copyToLocal $DATE_OUTPUT $WORK_DIR/$DATE_OUTPUT
hadoop fs -copyToLocal $TF_OUTPUT $WORK_DIR/$TF_OUTPUT
echo ""


echo "####################################"
echo "##  Run temporal classification   ##"
echo "####################################"
#python $HOME/text_processing/getFirstDateInText.py $TEXTS_DIR
#python $HOME/text_processing/getDateProb.py $WORK_DIR/$DATE_OUTPUT
#python $HOME/text_processing/getTFDF.py $WORK_DIR/$TF_OUTPUT
#python $HOME/text_processing/getTLM.py

echo ""
