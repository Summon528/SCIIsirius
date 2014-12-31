SCIIsirius
==========

###Hello! Welcome to ClanSR's offical website
Feel free to fork us anytime
[Our Website](http://sciisirius.appspot.com)

Also remember to add a file call secret.json
It's should be something like this
CLIENT_ID and CLIENT_SECRET is for [Battle.net API](https://dev.battle.net/) 

```
{
	"CLIENT_ID" : "...",
	"CLIENT_SECRET" : "...",
	"REDIRECT_URI" : "https://sciisirius.appspot.com/account/connect",
	"CLIENT_ID2" : "...",
	"CLIENT_SECRET2" : "...",
	"REDIRECT_URI2" : "https://sciisirius.appspot.com/account/connect_again",
	"SECRET":"...",
	"SECRET2":"...",
	"PROFILE_URI":"https://kr.api.battle.net/sc2/profile/%s/2/%s/?locale=ko_KR&apikey=...",
	"LADDERS_URL":"https://kr.api.battle.net/sc2/profile/%s/2/%s/ladders?locale:ko_KR&apikey=..."
}
```