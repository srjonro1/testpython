import requests
import json
import psycopg2
import time
import os
time.sleep(60)
old=[]
conn = psycopg2.connect(
    host=os.getenv('DB_CONTAINER'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'))
cursor = conn.cursor()
cursor.execute("SELECT gc.connection_name,gcp.parameter_value FROM guacamole_connection as gc join guacamole_connection_parameter as gcp on gc.connection_id = gcp.connection_id WHERE gcp.parameter_name = 'hostname';")
old=[]
for row in cursor.fetchall():
    aux = row[0] + ':' + row[1]
    if not aux in old:
        old.append(aux)
while True:
    b = requests.get("http://consul:8500/v1/health/state/passing")
    if b.json():
        cursor = conn.cursor()
        a = b.json()
        new = []
        for i in range(1,len(a)):
            if a[i]['ServiceTags'][0] == 'back':
                new.append(a[i]['Output'][12:-13] + a[i]['CheckID'][21:-5])
        if new != old:
            for j in range(0,len(new)):
                if not new[j] in old:
                    name=new[j].split(':')[1]
                    ip=new[j].split(':')[0]
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO guacamole_connection (protocol,max_connections, max_connections_per_user,connection_name) VALUES ('vnc',1,1,'" + name + "');")
                    cursor.execute("SELECT connection_id FROM guacamole_connection WHERE connection_name= '" + name + "';")
                    conn.commit()
                    for row in cursor.fetchall():
                        id1=str(row[0])
                    cursor.execute("INSERT INTO  guacamole_connection_parameter VALUES ('" + id1 + "','hostname','" + ip + "');")
                    cursor.execute("INSERT INTO  guacamole_connection_parameter VALUES ('" + id1 + "','port','5900');")
                    old.append(new[j])
                conn.commit()
            k=0
            while k < len(old):
                if not old[k] in new:
                    name=old[k].split(':')[1]
                    ip=old[k].split(':')[0]
                    cursor = conn.cursor()
                    cursor.execute("SELECT connection_id FROM guacamole_connection WHERE connection_name='" + name + "';")
                    conn.commit()
                    for row in cursor.fetchall():
                        id1=str(row[0])
                    cursor.execute("DELETE FROM guacamole_connection WHERE connection_id='" + id1 + "';")
                    cursor.execute("DELETE FROM guacamole_connection_parameter WHERE connection_id='" + id1 + "';")
                    old.remove(old[k])
                conn.commit()
                k=k+1
        time.sleep(10)
