=================================
Eve Trader
=================================


Summary
-------

This program was made for myself to try and make trading, especially regional, a little bit easier.


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
