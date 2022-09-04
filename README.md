# bot-clony

## What is this?

A companion of bot-sony for the MechKeys discord.
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

1. `cp .env-example .env` and modify values as needed
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -U -r requirements.txt`
5. `python3 ./main.py`

or, you build with docker and let 'er rip.

Maybe it also runs on heroku. I don't know, I just followed some guide I found
on Medium to prepare it for that.

## TODO

* Try out pypy
* Migrate to pycord/hikari/whatever
* features
    * commands
      * all users (verified)
        * ~~!help2~~
        * ~~!wiki (page)~~
          * ~~ex. !wiki stabs, !wiki lube~~
          * ~~!wiki listall~~
        * ~~!sanitize~~
      * helpers
        * ~~!eject~~
          * ~~!ejectwarn~~
          * ~~!uneject~~
          * ~~!tempeject~~
        * ~~!wiki define*~~
          * ~~!wiki define page stabs STABILIZERS.html~~
          * ~~!wiki define root https://mechkeys.me~~
        * ~~!slowmode \[interval\]~~
      * mods
        * ~~!reboot~~
          * ~~!update~~
    * listeners etc.
      * ~~attempted role-evasion~~
    * db integration
      * ~~roles renewal~~
      * ~~wiki page locations~~
