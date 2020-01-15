pwd
diplom=`pwd`

touch $diplom/logs/`date '+%Y.%m.%d'`.log
LogFile=$diplom/logs/`date '+%Y.%m.%d'`.log
CodeFile=$diplom/code

echo "start:" `date '+%Y.%m.%d.%H-%M-%S'` >> $LogFile

export PYENV_VERSION=3.7.0
echo $PYENV_VERSION

python3 $CodeFile/main.py $var>> $LogFile 2>&1

echo -e "finish:" `date '+%Y.%m.%d.%H-%M-%S'` "\n" >> $LogFile
