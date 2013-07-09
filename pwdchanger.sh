#!/bin/bash
pwdlen=8

char=(0 1 2 3 4 5 6 7 8 9 a b c d e f g h i j k l m n o p q r s t u v w x y z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z ! @ \# ^)

max=${#char[*]}


for i in `mysql -pXXXX $DB -e "SELECT url FROM servers ORDER BY url ASC" | grep -v url | awk '{print $1}' | tr -s \\n`
do
        password="";
        for j in `seq 1 $pwdlen`
        do
                let rand=${RANDOM}%${max}
                password="${password}${char[$rand]}"
        done

        echo "Changing root password for $i to $password"
        ssh -p 1964 $i "echo $password | passwd --stdin root"
        echo "Updating winston's DB"
        mysql -pXXXX $DB -e "UPDATE servers SET system_user=aes_encrypt('root / $password', '94*\$HN^3)}%d@jdf88-lcx') WHERE url='$i'"
        echo "----------------------------"
done
