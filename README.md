=================================
Eve Trader
=================================


Summary
-------

This is used in conjunction with eve_go_db (I should rename that) and a postgres db in order to make my life for trading a little bit easier. 

Some Notes:
If you wanted to use this, you'd have to use in conjunction with eve_go_db. I'm trying to move away from this program making ANY http requests, and will instead move any of that functionality to something else. The reasoning being that I was making too many requests, and I thought it'd be better to have something else just mirror what crest would give me and just talk to that, so that's what I'm doing. In the future, I may just bring that into this project as well and just collapse it in. At the moment, I'll leave it abstracted out and mostly will just make DB calls to get the information I need  


Example Usage
------------
Command for libre office:


For Just checking an item in jita

./eve_trader.py --item 35

Another System

./eve_trader.py --item 35 --system [system_id]

With an item file
./eve_trader.py --file [file_name] # all items in file

Shipping
./eve_trader.py --file [file_name] --shipping [system_from] [system_to] cost



Example Usage with Sheets
------------------------

I use pyoo for LibreOffice, and it will make a spreadsheet and save it.
This is the command for office to accept connections ( I use a seperate terminal for it, I'll work it into the program somehow later on)

soffice --accept="socket,host=localhost,port=2002;urp;" --norestore --nologo --nodefault

Shipping
./eve_trader.py --file [file_name] --shipping [system_from] [system_to] cost --sheet
