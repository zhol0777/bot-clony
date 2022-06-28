# bot-clony

## What is this?

A clone of bot-sony, a bot originally written by sony for the MechKeys discord.
It's not done yet.

## Why re-write it?

I want more features.

* New commands
  * !deport, !uneject
  * Reapply eject/deport/evict on re-join
  * !sanitize
* More helper commands
  * Define links to wiki (by default is https://mechkeys.me)
  * Modify slow-mode command

## How do I run this?

1. Apply values to `.env` from `.env-exmpmle`as needed. 
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -U -r requirements.txt`
5. `python3 ./main.py`

Maybe it also runs on heroku. I don't know, I just followed some guide I found
on Medium to prepare it for that.

## TODO

* Migrate to pypy
* features
    * commands
      * all users (verified)
        * !help
        * ~~!buy~~
        * ~~!map~~
        * ~~!trade~~
          * re-add trade disclaimer once i rejoin server
        * ~~!vendors~~
        * ~~!flashsales~~
        * ~~!wiki (page)~~
          * ~~ex. !wiki stabs, !wiki lube~~
          * ~~!wiki listall~~
        * ~~!sanitize~~
        * ~~!lifealert~~
          * ~~!fakelifealert~~
      * helpers
        * show help channel on how to use all these only in helper-lounge
        * ~~!eject~~
          * ~~!ejectwarn~~
          * ~~!uneject~~
        * ~~!deport~~
        * ~~!wiki define*~~
          * ~~!wiki define page stabs STABILIZERS.html~~
          * ~~!wiki define root https://mechkeys.me~~
        * ~~!slowmode \[interval\]~~
      * mods
        * ~~!purge~~ ???
          * ~~!purgelast (number of messages?)~~ ???
          * verify that works as intended
        * ~~!reboot~~
          * ~~!update~~
    * modmail
      * slur-watch
      * attempted role-evasion
    * verification channel thing
    * region role reaction thing
    * db integration
      * roles renewal
      * ~~wiki page locations~~
