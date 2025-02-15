### Work in progress!

# On the Minecraft server:
Install zabbix-agent2 and copy the Zabbixagent/minestats_agent.conf to the /etc/zabbix/zabbix-agent2.d/ directory, restart the agent.
Place the minestat.py in /opt/minestats/minestats.py and chmod 0755
Install the required pip packages from requirements.txt
If you renamed the world or not installed in /opt/minecraft, edit the python script.
Check your server.properties file to set the following:

'''
enable-rcon=true
rcon.password=m1n3cr4ft
rcon.port=25575
'''

(A safer password would be great, but you can keep the port firewalled anyway)

# On the Zabbix server:
Import the template to Zabbix, add the host and add the template.
(Go to Data collection > templates and use import)
Change the macro's and make sure the values match with server.properties

To map player ID's to player names:
In the template list, search minecraft, click "Discovery 1"
Click "Discover player statistics"
In the preprocessing step, edit the Javascript.

Wait for 2 minutes. or filter in latest data for the tag 'execute_now' to speed up.
All data will come in and you see hunders of items per player, tagged by player (name or id), "Static type" and "Static item"
