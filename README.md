# acm-userpage

Host academic homepage for ACM Class students with URL like `https://acm.sjtu.edu.cn/~jaccount`. Go to management here: <https://acm.sjtu.edu.cn/userpage-manage>.

## Server Setup

```
$ sudo useradd -m userpage_web
$ sudo visudo
userpage_web ALL=(ALL:ALL) NOPASSWD:ALL
$ sudo mkdir /home/userpage
$ sudo chown root:root /home /home/userpage
$ sudo chmod 755 /home /home/userpage
$ sudo groupadd userpage
$ sudo vim /etc/ssh/sshd_config
Subsystem sftp internal-sftp
Match Group userpage
    ChrootDirectory %h
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
    PasswordAuthentication no
$ sudo service ssh restart

$ sudo apt-get install quota quotatool
$ sudo vim /etc/fstab
UUID=blah   /  ext4  errors=remount-ro,usrquota  0  1
$ sudo mount -o remount /
$ sudo quotacheck -cum /
$ sudo quotaon /

$ sudo apt-get install nginx
$ sudo vim /etc/nginx/sites-enabled/default
location ~ ^/~(.+?)(/.*)?$ {
    alias /home/userpage/$1/public_html$2;
    autoindex on;
}
$ sudo service nginx reload

$ git clone https://github.com/abcdabcd987/acm-userpage.git
$ cp config.example.py config.py
$ vim config.py
$ sudo apt-get install python3-pip gunicorn3
$ sudo -H pip3 install -r requirements.txt
# production run
$ gunicorn3 -b 0.0.0.0:5869 --access-logfile - userpage:app
# debug run
$ export OAUTHLIB_INSECURE_TRANSPORT=1
$ python3 userpage.py
```

## Reference

* OAuth2
    * <http://developer.sjtu.edu.cn/wiki/JAccount>
    * <https://aaronparecki.com/oauth-2-simplified/>
* SFTP
    * <https://wiki.archlinux.org/index.php/SFTP_chroot>
    * <https://askubuntu.com/questions/134425/how-can-i-chroot-sftp-only-ssh-users-into-their-homes>
* Quota
    * <https://www.digitalocean.com/community/tutorials/how-to-enable-user-and-group-quotas>
    * <https://serverfault.com/a/564253/267780>
