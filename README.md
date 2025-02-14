### Work in progress!

# On the Minecraft server:
Install zabbix-agent2 and copy the Zabbixagent/minestats_agent.conf to the /etc/zabbix/zabbix-agent2.d/ directory, restart the agent.
Place the minestat.py in /opt/minestats/minestats.py and chmod 0755
If you renamed the world or not installed in /opt/minecraft, edit the python script.

# On the Zabbix server:
Import the template to Zabbix, add the host and add the template.
(Go to Data collection > templates and use import)

To map player ID's to player names: 
In the template list, search minecraft, click "Discovery 1"
Click "Discover player statistics"
In the preprocessing step, edit the Javascript.

Wait for 2 minutes. or filter in latest data for the tag 'execute_now' to speed up.
All data will come in and you see hunders of items per player, tagged by player (name or id), "Static type" and "Static item"


Keep in mind: The minecraft server will save data once every 5 minutes
