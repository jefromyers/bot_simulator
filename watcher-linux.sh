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

inotifywait -m -e close_write --format '%w%f' $FILE_PATH | while read FILE
do
  meow
done

