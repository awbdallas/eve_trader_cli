Eve Trader
=================================


Summary
-------

This is used in conjunction with eve_go_db (I should rename that) and a postgres db in order to make my life for trading a little bit easier. 

Some Notes:
If you wanted to use this, you'd have to use in conjunction with eve_go_db. I'm trying to move away from this program making ANY http requests, and will instead move any of that functionality to something else. The reasoning being that I was making too many requests, and I thought it'd be better to have something else just mirror what crest would give me and just talk to that, so that's what I'm doing. In the future, I may just bring that into this project as well and just collapse it in. At the moment, I'll leave it abstracted out and mostly will just make DB calls to get the information I need  
