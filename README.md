BloonsPlayer
============
BloonsPlayer is a screen scraping tool for scripting and playing Bloons Tower Defense 6. 
If you want to contribute your scripts to the project join the [discord](https://discord.gg/uJfudc3RfV).

Dependencies
============
BloonsPlayer supports python 3 on Windows and requires [PyAutoGui](https://pypi.org/project/PyAutoGUI/).

Usage
=====
The BloonsPlayer code can be found in the src folder. 
For users who want nothing to do with programming, a precompiled executable can be found in the build folder.

It should be noted that while the script is running your computer will not really be usable, 
as the script needs to occasionally input keystrokes and take control of your mouse. 
Further, besides directly killing the program by exiting the terminal window, 
or killing execution in your IDE, 
you can move your cursor to any corner of your monitor which will eventually trigger PyAutoGui's built in fail safe.

Scripting
=========
The scripting information for BloonsPlayer is stored in the tas file `tas.txt`. 
The tas file consists of a list of tas scripts separated by two newlines. 
Each script consists of a list of commands separated by a single newline. 


Command overview
----------------
All commands are evaluated as python expressions and should thus be written with valid python syntax.
Each script must start with a string command that will be interpreted as the title of that particular script. 
The second command must be a tuple of three strings which should be the track name, difficulty, and mode respectively. 
The third command and onward do not have special requirements, 
but it should be noted that after the third command is executed the player will begin the track, 
meaning usually the third command will be to place a tower that can be immediately afforded.

Command examples
----------------
The following is a comprehensive list of the types of commands and how they are used. 
See also the tas file for more examples.

The first two commands should follow the following format.
```python
"monkey meadow (easy)"  # title to display in BloonsPlayer menu
("monkey meadow", "easy", "standard")  # specify map, difficulty, and mode to open
```

The command to place a tower is a tuple with two elements, 
the first element is the name of the tower in a string, 
the second element is the relative placement coordinates. 
The coordinates should be a tuple of two floats between 0 and 1, for the x and y position. 
To find these coordinates reliably, use the print mouse position button in the BloonsPlayer menu. 
Note also that placement commands do not wait and a delay must often be used to ensure sufficient funds.
```python
("spikes", (0.43, 0.33))  # place a spike factory at (0.43, 0.33)
```
The valid tower names are:
* "hero": whichever hero is selected
* "dart": dart monkey
* "boomerang": boomerang monkey
* "bomb": bomb shooter
* "tack": tack shooter
* "ice": ice monkey
* "glue": glue gunner
* "sniper": sniper monkey
* "sub": monkey sub
* "boat": monkey buccaneer
* "plane": monkey ace
* "heli": heli pilot
* "mortar": mortar monkey
* "dartling": dartling gunner
* "wizard": wizard monkey
* "super": super monkey
* "ninja": ninja monkey
* "alchemist": alchemist
* "druid": druid
* "farm": banana farm
* "spikes": spike factory
* "village": monkey village
* "engineer": engineer monkey

There are four types of delays: time, money, round, and life. 
Time delays wait the given amount of time in seconds, the syntax is simply an integer. 
Money delays wait until you have a given amount of cash, the syntax is "money \<number>". 
Round delays wait until you reach the given round, the syntax is "round \<number>". 
Life delays wait until you drop to a certain number of lives, the syntax is "lives \<number>".
```python
10  # delay ten seconds
"money 1200"  # wait until cash reaches $1200
"round 22"  # wait until round 22
"lives 100"  # wait until lives drop to 100
```

The command to upgrade a tower is a tuple with two elements. 
The first element is the integer of the tower to upgrade, towers are indexed starting at 0.
The second element is a tuple of the paths to upgrade. 
Unlike tower placement, this function does not require other delay functions 
and will automatically wait until you have enough money to buy a particular upgrade. 
Note that heroes are upgraded in the same way, but the path does not matter.
```python
(0, (2, 2, 1, 1, 1, 1))  # upgrade our spike factory to spiked mines with even faster production
```

There are three commands regarding activating abilities. 
The ability command simply activates the given ability once. 
The repeat ability command will repeat the given ability once every second until the round ends.
The cancel repeat abilities command cancels all currently repeated abilities.
The command will simply press the key it is given, 
so this command can be used for keys other than abilities. 
The default ability hotkeys are "1234567890-=".
```python
"ability 2"  # use the second ability in the list
"repeat ability 1"  # repeatedly use the first ability in the list
20  # delay twenty seconds
"cancel repeat abilities"  # cancel the repeated ability use
```

The last type of command is to simply click at the specified location. 
The syntax of this command is simply a tuple of two floats which are coordinates. 
This can be used to activate map gimmicks, change targeting, or anything really.
```python
(0.13, 0.37)  # click at (0.13, 0.37)
```