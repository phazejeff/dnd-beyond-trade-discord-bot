# DND Beyond Discord Bot

A discord bot that adds the commands /give and /pay to discord, which allows players to give eachother items and pay eachother currencies between their DND Beyond characters.

DND Beyond does not have a public API, therefore I am using an admittedly hacky workaround to access the website.

## Usage

`/give (player)` - give an item from your inventory to the player. This will give a simple menu you can follow to choose the item you want to give.

`/pay (player) [cp] [sp] [ep] [gp] [pp]` - Pay the player some amount of currency. All currency parameters are optional, so if you want to send just gold you can use just the `gp` parameter.

## Setup

I do not run this bot for public use. If you want to use this bot, you will need to run it yourself for your own server. 