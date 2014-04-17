#!/bin/bash

MONGODB_DBPATH=~/mongodb-data
MONGODB_LOGPATH=~/mongodb-log
HADOOP_PATH=~/hadoop-data

### ALERT! PREVIOUS RESULTS ARE REMOVED! ###
killall java; 
killall mongod;
rm -fr $MONGODB_DBPATH; rm -fr $MONGODB_LOGPATH; rm -fr $HADOOP_PATH
mkdir -p $MONGODB_DBPATH; mkdir -p $MONGODB_LOGPATH; mkdir -p $HADOOP_PATH

echo "###########################"
echo "##  Starting MongoDB...  ##"
echo "###########################"
#mongod --dbpath $MONGODB_DBPATH --fork --logpath $MONGODB_LOGPATH
mongod --dbpath $MONGODB_DBPATH > $MONGODB_LOGPATH/mongolog.log 2>&1 &
echo ""

echo "##########################"
echo "##  Starting Hadoop...  ##"
echo "##########################"
hadoop namenode -format
start-dfs.sh
sleep 3
start-mapred.sh
echo ""