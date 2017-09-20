#!/bin/bash

USERNAME=$1
if [ -z "$1" ]; then
    echo "please provide username"
    exit 1
fi

homedir=/home/userpage/$USERNAME

id -u $USERNAME > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # create user
    useradd -d $homedir -G userpage -m -s /bin/false $USERNAME
    quotatool -u $USERNAME -b -q 100M -l 100M /

    chown root:root $homedir
    chmod 755 $homedir

    mkdir -p $homedir/public_html
    chown $USERNAME:$USERNAME $homedir/public_html
    chmod 775 $homedir/public_html
fi

# mkdirs
mkdir -p $homedir/.ssh
touch $homedir/.ssh/authorized_keys
chown -R $USERNAME:$USERNAME $homedir/.ssh
chmod 775 $homedir/.ssh
chmod 664 $homedir/.ssh/authorized_keys

# paste keys
cat > $homedir/.ssh/authorized_keys
