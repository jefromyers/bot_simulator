#!/bin/bash

FILE_PATH="./data/output/screen.txt"

# Allow a different file
if [ -n "$1" ]; then
  FILE_PATH="$1"
fi

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

