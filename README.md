# d20 Monte Carlo simulator

This library provides a Monte Carlo simulator for combat encounters in d20 tabletop RPG systems.
The current implementation supports Dungeons & Dragons fifth edition (2014).
The primary use case is for game masters to playtest statistics for custom monsters under the assumption that the monster will appear in a combat encounter that is part of a larger adventuring day (see [Rationale](#rationale) for more details).
An adventuring day is assumed to consist of six combat encounters with a short rest after the second and fourth encounters.

Given a party level for the player characters and the number of monsters in an encounter, the simulator will run Monte Carlo simulations for a large number of adventuring days.
The output will report the mean and standard deviation of the number of player characters surviving at the end of the last encounter on each day.
From testing against balanced combat enounters using a party of four player characters and monsters from the Monster Manual, a balanced encounter will produce a mean survival of 1.0 (see [Details and Assumptions](#details-and-assumptions) below for more details).

# Setup

## Requirements

- `python>=3.10`
- `numpy`

## Installation

- Clone this GitHub repo.

# Usage

Usage is `python d20_mc_simulator.py [OPTIONS]`.
Use `python d20_mc_simulator.py -h` to see a description of all options.

## Simulate a large number of adventuring days

The default behavior is to simulate a large number of adventuring days and report descriptive statistics on player character survival.
Usage for this behavior is

`python d20_mc_simulator.py -m $MONSTER_NAME -n $NUM_MONSTERS -p $PARTY_LEVEL`

where `$MONSTER_NAME` is a string corresponding to the name of the monster, `$NUM_MONSTERS` is the number of monsters per combat encounter, and `$PARTY_LEVEL` is the level of the player characters.
For example, to simulate a party of level one characters using a combat encounter consisting of four kobolds, use

`python d20_mc_simulator.py -m Kobold -n 4 -p 1`

Several but not all monsters from the Monster Manual are supported.
The full list is in the dictionary `mm_creatures` in `mm_bestiary.py`.
For a combat encounter with multiple types of monsters, use a comma-separated list (no spaces) of both monster names and monster numbers.
For example, to simulate a party of level four characters using combat encounter consisting of one ogre, three orcs, and three kobolds, use

`python d20_mc_simulator.py -m Ogre,Orc,Kobold -n 1,3,3 -p 4`

Player characters are supported from level one to level eight.
The default party composition is a cleric, fighter, rogue, and wizard.
Only those four classes are supported.
To specify a different composition or different number of player characters, use a comma-separated list with the `-c` flag.
For example, to simulate a party of three player characters with a fighter and two wizards, use

`python d20_mc_simulator.py -m Kobold -n 4 -p 1 -c Fighter,Wizard,Wizard`

The number of adventuring days simulated is 1000 by default and can be changed with the `-a` flag.
For example, to simulate 500 adventuring days, use

`python d20_mc_simulator.py -m Kobold -n 4 -p 1 -a 500`

Use the `-v` flag to print detailed information about actions taken and dice rolled during combat encounters.
This will print a lot of text, especially with the default number of adventuring days.

`python d20_mc_simulator.py -m Kobold -n 4 -p 1 -a 1 -v`

Output for the default behavior is a string reporting the party level, the name and number of each type of monster, and the mean +/- standard deviation of player character survival.

## Debug monster behavior

Use the `-d` flag to simulate a single adventuring day and print detailed information like the verbose `-v` flag.
This is useful to debug the behavior of a new custom monster.

`python d20_mc_simulator.py -m Kobold -n 4 -p 1 -d`

## Test abstract statistics without a detailed stat block

To simulate abstract statistics (e.g. those in the table "Monster Statistics by Challenge Rating" in the Dungeon Master's Guide p.274) rather than a detailed stat block, use the monster name "Test".
Use the `-t` flag to pass a comma-separated list of six integers corresponding to the attack modifier, armor class, total damage per round, total hit points, number of attacks, and proficiency bonus.
For example, to simulate four test creatures with a +3 attack modifier, 13 armor class, 2 damage per round, 20 hit points, 1 attack per turn, and +2 proficiency bonus, use

`python d20_mc_simulator.py -m Test -n 4 -p 1 -t 3,13,2,20,1,2`

# Adding a new custom monster

Adding a custom monster requires modifying the python code in the library.
Knowledge of class objects and inheritance in python will be helpful.
If you are uncomfortable with writing your own python code, use the "Test" monster described [above](#test-abstract-statistics-without-a-detailed-stat-block).

The library provides an abstract class `Creature` with the abstract attribute `hit_die` and the abstract methods `initialize_features(self)`, `start_encounter(self, encounter)`, and `take_turn(self, encounter)`.
In `custom_bestiary.py`, create a new `class` derived from the `Creature` class, or copy the code from a similar existing monster in `mm_bestiary.py`.
Minimally, you should override `initialize_features` to provide the attribute `hit_die` and override `take_turn` to provide logic for how the monster takes its turn.
`initialize_features` can also set ability scores, armor, skill and save proficiencies, immunities, resistances, weaknesses, proficiency bonus, total hit dice, spells, and weapon attacks.

Weapon attacks should use the `Weapon` class defined in `creature.py`.
Conditions that last for a set duration or that trigger effects at the start or end of a creature's turn should use a class derived from the `Duration` class in `duration.py`.
Spells should use a class derived from the `Spell` class in `spells.py`.
Creatures with legendary actions should use the `LegendaryCeature` class from `creature.py`.
Constructs should include `self.construct = True` in `initialize_features()` to determine validity for spell targets.
Undead should include `self.undead = $CHALLENGE_RATING` where `$CHALLENGE_RATING` is the creature's challenge rating to determine validity for spell targets and the cleric's Turn Undead feature.

In `mm_bestiary.py`, see `Kobold` for an example of a minimal derived class for a simple monster with a single weapon attack and Pack Tactics.
See `Mage` for an example of a detailed derived class for a monster that casts spells.
See `Banshee` for an example of a detailed derived class for a complex monster with `Duration` effects and branching logic in `take_turn()`.
See `Aboleth` for an example of a detailed derived class for a complex monster with lair actions and legendary actions.

When the derived class is finished, add the key-value pair `name: custom_class` to the dictionary `custom_creatures` at the bottom of `custom_bestiary.py`.
`name` is the string used to identify the monster to the `-m` flag on the command line, and `custom_class` is the name of the derived class.
It is recommended to use the debug flag `-v` to make sure that the monster behaves as expected during a combat encounter before estimating survival from a large number of adventuring days.

# Rationale

I created this tool because the guidelines for creating custom monsters in the Dungeon Master's Guide (DMG) are limiting.
The DMG guidelines tend to produce monsters that have high defense and low offense compared to most monsters in the Monster Manual.
Additionally, the DMG guidelines seem to be tuned for monsters that will be encountered in a ratio close to one monster per player character.
The DMG guidelines don't describe how to adjust monster stats for monsters intended to be encountered in large groups or as solo/boss monsters.
Finally, the DMG guidelines suggest playtesting to tune monster statistics such as attack modifiers or armor class.
However, there is a lot of variability in the outcome of combat encounters due to dice rolls.
Additionally, the fifth edition system as a whole is balanced around resource allocation between short and long rests, so monsters that are balanced in the same way as those in the Monster Manual are expected to be encountered as part of an adventuring day consisting of six to eight resource-draining encounters.

This tool is designed to playtest the game statistics of custom monsters with the following features:
- Simulate multiple combat encounters with short rests over a full adventuring day
- Simulate a large number of adventuring days to sample the variability in dice rolls
- Simulate player characters whose actions are determined by a simple strategy agnostic to the details of the monsters to avoid tuning against the strategy of a particular group of players
- Explicitly specify the number of monsters in a combat encounter to tune game statistics for large groups or solo monsters

The expected usage for this tool is to use the guidelines from the DMG (or another source) to create a candidate stat block for a custom monster and then run Monte Carlo simulations to explore variations around the candidate statistics.
For example, you might know that you want a glass cannon monster with high offense but low defense.
Given a specified damage output, this tool can help you explore whether the monster's attack modifier should be one higher or lower or whether to adjust defensive stats such as armor class or hit points.
Alternatively, it can help you decide how to adjust the game statistics if you give a monster an ability such as Pack Tactics to maintain the same challenge.

# Details and assumptions

Implementing detailed logic for combatants is beyond the scope of this project, so the combat encounter simulations are simplified with several assumptions.

First, there is no combat grid or notion of positioning.
Movement abilities are not implemented.

Second, all combatants are valid targets for all other combatants unless a condition such as invisibility or stealth is active.
This means abilities such as Pack Tactics trigger when at least one other ally is alive.

Third, area of effect abilities will target up to two creatures.

Fourth, targets for attacks or other features are chosen randomly between valid targets.
Other than avoiding invalid targets---such as attacking a dead creature or casting a spell that deals fire damage at a creature immune to fire damage---logic for deciding which opponent to attack is not implemented.

Fifth, player characters will ration usages of class features with limited uses based on two encounters per short rest and six encounters per long rest.
An equal number of uses will be consumed in each encounter, with additional uses allocated to either earlier or later encounters.
For example, the fighter's Second Wind feature recharges on a short rest, and it's more useful to use this feature earlier.
If the total number of uses of Second Wind is two, the fighter will use Second Wind once per encounter.
If the total number of uses of Second Wind is one, the fighter will use Second Wind in the first encounter after a short rest.
Spellcasters will ration spell slots based on the total number of slots of any spell level and will use higher spell slots first.
The wizard will use spells earlier.
For example, a level six wizard with ten total spell slots will use two spell slots per encounter in the first four encounters after a long rest and one spell slot per encounter for the remaining two encounters.
The cleric will use spells later.
For example, a level six cleric with ten total spell slots will use one spell slot per encounter in the first two encounters after a long rest and two spell slots per encounter for the remaining four encounters.
However, the cleric will always use a spell slot to heal if at least one ally is unconscious at zero hit points and there is a spell slot available.

An adventuring day consists of six combat encounters.
After the second and fourth encounters, the party will take a short rest.
During a short rest, the cleric will use Channel Divinity: Preserve Life and spell slots if available to heal unconscious allies, and then the party will spend hit dice to recover hit points.
The wizard will also use arcane recovery if available.
At the end of the adventuring day, the cleric (if still alive) will use Channel Divinity: Preserve Life and any remaining spell slots to heal as many unconscious allies as possible.
Then, survival for the adventuring day is computed by counting the number of player characters with hit points above zero.
If all player characters reach zero hit points simultaneously, then the adventuring day immediately ends with survival equal to 0.

## Calibration of reported mean survival

To calibrate the reported mean survival given these assumptions, I calculated mean survival over 1000 adventuring days for several monsters from the Monster Manual per CR for a party of four player characters.
Monster CR varied between CR 0 and CR 11, the number of monsters between 1 and 16 (1, 2, 4, 8, and 16), and party level between 1 and 8.
Full results are included in `mm_survival.txt`.
A threshold of 1.0 for mean survival was selected to reproduce encounter building guidelines in the Dungeon Master's Guide (DMG) and Xanathar's Guide to Everything (XGE).
The table below compares CR for a balanced encounter given a party level (rows) and a number of monsters (columns) according to DMG guidlines, XGE guidelines, or this Monte Carlo simulator (MC) with mean survival 1.0.

| Party Level | DMG |  16 |   8 |   4 |   2 |   1 | XGE |  16 |   8 |   4 |   2 |   1 | MC |  16 |   8 |   4 |   2 |   1 |
|-------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|----|-----|-----|-----|-----|-----|
|           1 |     |     |   0 | 1/8 | 1/4 |   1 |     |   0 | 1/8 | 1/4 | 1/2 |   1 |    |     |   0 | 1/8 | 1/4 |   1 |
|           2 |     |     |   0 | 1/4 | 1/2 |   2 |     |   0 | 1/4 | 1/2 |   1 |   2 |    |   0 |   0 | 1/4 |   1 |   2 |
|           3 |     |   0 | 1/8 | 1/4 |   1 |   3 |     | 1/8 | 1/4 | 1/2 |   1 |   3 |    |   0 | 1/8 | 1/2 |   1 |   3 |
|           4 |     |   0 | 1/4 | 1/2 |   2 |   4 |     | 1/4 | 1/2 |   1 |   2 |   4 |    |   0 | 1/4 |   1 |   2 |   4 |
|           5 |     | 1/8 | 1/2 |   1 |   3 |   5 |     | 1/2 |   1 |   2 |   3 |   7 |    | 1/8 | 1/2 |   2 |   4 |   7 |
|           6 |     | 1/8 | 1/2 |   1 |   3 |   6 |     | 1/2 |   1 |   2 |   4 |   8 |    | 1/4 |   1 |   2 |   4 |   8 |
|           7 |     | 1/4 | 1/2 |   2 |   4 |   7 |     | 1/2 |   1 |   3 |   4 |   9 |    | 1/4 |   1 |   3 |   5 |   9 |
|           8 |     | 1/4 |   1 |   2 |   4 |   8 |     |   1 |   2 |   3 |   4 |  10 |    | 1/4 |   1 |   3 |   6 |  10 |

Results for this MC simulator are similar to the DMG guidelines when the number of monsters is greater than the number of player characters and similar to the XGE guidelines when the number of monsters is less than the number of player characters.
