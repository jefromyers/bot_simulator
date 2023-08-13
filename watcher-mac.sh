#!/bin/bash

# XXX: Just hard code for now
FILE_PATH="./data/output/screen.txt"

meow() {
  clear
  cat $FILE_PATH
}

if [ ! -f $FILE_PATH ]; then
  echo "🤖 Creating output file $FILE_PATH"
  touch $FILE_PATH
fi

fswatch -0 $FILE_PATH | while read -d "" FILE
do
  meow
done

