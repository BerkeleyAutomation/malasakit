#!/bin/sh
# Script that backs up the specified MySQL databases and sends them to the specified remote machine.
# Run this on a chron job every day.

mysqldump="$(which mysqldump)"
tar_name=backupsql_$(date +%d%m%y).tgz

# root directory of the project
root_dir=/var/www/opinion/opinion.berkeley.edu/pcari

# List all the databases you want to back up here
databases=(test test1 test2)

mkdir -p ${root_dir}/db_backups
for db in ${databases[*]}; do
    # There cannot be a space between -p and $mysql_pass
    $mysqldump -u root -p$mysql_pass --opt $db > ${root_dir}/db_backups/${db}_backup.sql
done

tar -zcvf ${root_dir}/$tar_name ${root_dir}/db_backups/*.sql

# removes tarballs and backup files more than 2 days old
find -name '*.tgz' -type f -mtime +2 -exec rm -f {} \;
find -name '*_backup.sql' -type f -mtime +2 -exec rm -f {} \;

# scp ${root_dir}/$tar_name justinmi@10.0.0.157:/Users/justinmi/GDrive/Cal/work/Autolab/pcari/db_backups

scp /var/www/opinion/opinion.berkeley.edu/pcari/backupsql_180118.tgz justinmi@127.0.0.1:/Users/justinmi/GDrive/Cal/work/Autolab/pcari/db_backups