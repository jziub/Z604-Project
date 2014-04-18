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

MONGODB_DBPATH=~/mongodb-data
MONGODB_LOGPATH=~/mongodb-log
HADOOP_PATH=~/hadoop-data

### ALERT! PREVIOUS RESULTS ARE REMOVED! ###
stop-all.sh
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
sleep 10
start-mapred.sh
echo ""