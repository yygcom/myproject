ipconfig /flushdns
scp adx.conf gate1:/etc/dnsmasq.d/
ssh gate1 '/etc/init.d/dnsmasq restart'
ipconfig /flushdns
