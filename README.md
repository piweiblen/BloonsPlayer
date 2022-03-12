#BloonsPlayer 0.1.7
BloonsPlayer is a screen scraping tool for scripting and playing Bloons Tower Defense 6. 
If you want to contribute your scripts to the project join the [discord](https://discord.gg/uJfudc3RfV).

#Dependencies
BloonsPlayer supports python 3 on Windows and requires
[PyAutoGui](https://pypi.org/project/PyAutoGUI/), and [scipy](https://pypi.org/project/scipy/).
In game, the hotkeys must be set to default, auto start must be on, and placement must be set to drag and drop.

#Usage
The BloonsPlayer code can be found in the src folder. 
For users who want nothing to do with programming, a precompiled executable can be found in the build folder.

It should be noted that while the script is running your computer will not really be usable, 
as the script needs to occasionally input keystrokes and take control of your mouse. 
Besides directly killing the program by exiting the terminal window 
or killing execution in your IDE, 
you can move your cursor to any corner of your monitor which will eventually trigger PyAutoGui's built in fail safe.

#Scripting
The scripts for BloonsPlayer are stored in the `data\tas\\` directory.
Each script consists of a list of commands separated by a single newline. 
The script file name is interpreted as the title of that particular script.


##Command overview
All commands follow the format of a command word followed by command arguments.
Anything after a # sign in the command will be ignored.
The arguments of each command should be separated by commas, parentheses and spaces will not affect the arguments.
Commands are not case-sensitive.
The first command must be top open the track with arguments of track name, difficulty, and mode respectively. 
The second command and onward do not have special requirements, 
but it should be noted that after the second command is executed the tas will start the game, 
meaning usually the second command will be to place a tower that can be immediately afforded.

##Command examples
The following is a comprehensive list of the types of commands and how they are used. 
See also the tas directory for more examples.

###First command, opening the track
The first command should be the "open" command and should follow the following format.
```
open monkey meadow, easy, standard  # specify map, difficulty, and mode to open
```
This command can also optionally specify a hero, which the bot will then make sure is selected when the track is opened.
```
open monkey meadow, easy, standard, quincy
```
The valid course names are:
* adora's temple
* alpine run
* another brick
* balance
* bazaar
* bloody puddles
* bloonarius prime
* candy falls
* cargo
* carved
* chutes
* cornfield
* cracked
* cubism
* dark castle
* downstream
* encrypted
* end of the road
* firing range
* flooded valley
* four circles
* frozen over
* geared
* haunted
* hedge
* high finance
* in the loop
* infernal
* kartsndarts
* logs
* lotus island
* mesa
* monkey meadow
* moon landing
* muddy puddles
* off the coast
* ouch
* park path
* pat's pond
* peninsula
* quad
* quiet street
* rake
* ravine
* resort
* sanctuary
* skates
* spice islands
* spillway
* spring spring
* streambed
* sunken columns
* the cabin
* town center
* tree stump
* underground
* winter park
* workshop
* x factor

The valid course difficulties are:
* easy
* medium
* hard

And the valid course modes are:
* alternate bloons rounds
* apopalypse
* chimps
* deflation
* double hp moabs
* half cash
* impoppable
* magic monkeys only
* military only
* primary only
* reverse
* standard

And the valid heroes are:
* admiral brickell
* adora
* benjamin
* captain churchill
* etienne
* ezili
* gwendolin
* obyn greenfoot
* pat fusty
* psi
* quincy
* sauda
* striker jones

###Placing a tower
The "place" command is used to place a tower. The arguments are: the type of tower, 
the relative placement coordinates, and a unique name for the monkey which will be used in later commands.
The coordinates should be two floats between 0 and 1, for the x and y position. 
To find these coordinates reliably, use the print mouse position button in the BloonsPlayer menu. 
Note also that placement commands do not wait and a delay must often be used to ensure sufficient funds.
```
place spikes, (0.43, 0.33), first spikes  # place a spike factory at (0.43, 0.33)
```
The valid tower types are:
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

###Delays
There are four types of delays: time, money, round, and life. 
Time delays wait the given amount of time in seconds, the syntax is an integer or float. 
Money delays wait until you have a given amount of cash, the syntax is "money \<number>". 
Round delays wait until you reach the given round, the syntax is "round \<number>". 
Life delays wait until you drop to a certain number of lives, the syntax is "lives \<number>".
```
delay 10  # delay ten seconds
money 1200  # wait until cash reaches $1200
round 22  # wait until round 22
lives 100  # wait until lives drop to 100
```

###Upgrades
The "upgrade" command upgrades a given tower. 
The first argument is the name of the tower to upgrade which will have been specified in the "place" command.
The next arguments are integers specifying which paths to upgrade, 1 being top, 2 middle, and 3 bottom. 
Unlike tower placement, this function does not require other delay functions 
and will automatically wait until you have enough money to buy a particular upgrade. 
Note that heroes are upgraded in the same way, except the number of times upgraded can be specified by the number of 
arguments, or if there's one argument the value of the argument.
```
money 1200
place spikes, (0.43, 0.33), first spikes
upgrade first spikes, 2, 2, 1, 1, 1, 1  # upgrade our spike factory to spiked mines with even faster production
```

###Changing targeting
The "target" command changes the targeting of the given tower. 
The first argument should be the name of the tower to change.
The second argument should be the number of times to change the targeting, 
note that this is equivalent to hitting the right arrow button. 
In the case of the mortar tower, a position must also be specified.
In the case of the dartling gunner, a position may also be specified when using locked targeting.
```
target dartName, 3  # set dart monkey to strong
target mortarName, 1, (0.43, 0.33)  # change position of mortar target
target dartlingName, 0, (0.43, 0.33)  # change position of dartling gunner
```

###Activated abilities
There are four commands regarding activating abilities. 
The "use ability" command simply activates the given ability once. 
The "repeat ability" command will repeat the given ability once every second until the round ends.
The "stop ability" command cancels all currently repeated abilities.
The "stop all abilities" command cancels all currently repeated abilities.
The command will simply press the key it is given, 
so this command can be used for keys other than abilities. 
The default ability hotkeys are "1234567890-=".
```
use ability 2  # use the second ability in the list
repeat ability 1  # repeatedly use the first ability in the list
delay 20  # delay twenty seconds
stop ability 2  # cancel repeated use of ability 2
stop all abilities  # cancel all repeated ability use
```

###Changing priority
The "priority" command changes the target priority of the given tower. 
This is the camo target priority option that some monkeys have and the plane flight direction option.
```
priority planeName
```

###Selling a tower
The "sell" command sells the tower specified by its name.
```
sell first spikes
```

###Removing an obstacle
The "remove" command removes a course obstacle at the given position.
This does not wait until you have enough money, so one will likely need to accompany it with a delay as well.
```
money 1000
remove (0.13, 0.37)  # remove an obstacle at (0.13, 0.37)
```

###Click
The "click" command simply clicks at the given relative coordinates.
This can be used to activate map gimmicks, or anything really.
```
click (0.13, 0.37)  # click at (0.13, 0.37)
```

###Move
The "move" command simply moves the mouse to the given relative coordinates.
This can be used to collect money, or anything really.
```
move (0.13, 0.37)  # move to (0.13, 0.37)
```