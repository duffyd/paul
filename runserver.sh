#!/bin/zsh
ZSHRC=/Users/tim/.zshrc
WORKING_DIR=/Users/tim/Documents/workspace/paul
source ${ZSHRC}
echo "Changing into ${WORKING_DIR}"
cd ${WORKING_DIR}
echo "Starting postgres"
pg_ctl -D /usr/local/var/postgres start
echo "Activating paul"
pyenv activate paul 
echo "Starting flask"
flask run
