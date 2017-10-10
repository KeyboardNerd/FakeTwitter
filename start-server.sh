# argument check
if [ -z "$1" ]
    then
        echo "Usage: "
        echo "start-server.sh <site-id>"
        exit
fi
# start server
python server.py $1 config.json datafile$1