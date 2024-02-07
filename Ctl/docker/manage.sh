PREFIXCTL_HOME=/srv/service

. $PREFIXCTL_HOME/venv/bin/activate
cd $PREFIXCTL_HOME/main

./manage.py $@
