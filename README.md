# Botty

## Installation

To run Botty, you will need an up-to-date version of Python3.12+. 

First create a virtual environment:
```
$ python3.12 -m venv .venv
```

The install the required packages : 
```
$ pip install -r requirements.txt
```

---- 


## Setting up bots

To set up bots, go into your `~/.botty` folder and create a new folder, with its name corresponding to the bot's name. 
All configuration files and directory will be automatically created. 

--- 

## Starting the script

To start the script, move to the directory and activate the  

```
$ cd </path/to/git>/botty/ ; source .venv/bin/activate
```

Then run with Python

```
(.venv) $ python .
```

---

## Contributing

If you want to contribute, please considere that for the moment I am alone to 

You can contribute by adding 4 kinds of objects : 

### Discussions Providers

Discussions providers are related to source of the discussion. It actually only requires Telegram, but you could add some others. 

You can add your discussion providers in the [`definer_providers` directory](https://github.com/Kaki-In/Botty/tree/main/defined_providers).

### Chatbots

Chatbots are the agents which can wait for a discussion to be completable. 
Agents should not depend on the plateform they are responding to, and should be able to handle any discussion type.
Creating a different kind of agent should not be related to adding more information on the context. For that, use a discussion modifiers as described below. 

### Creators

Creators are objects which can create some elements, taking some times. For instance, generating an image is a creator. 
Creators can be called at any time from any object, although they should be called through a `CreatorsMap` so that they can be interrupted as soon as needed. 

### Discussions Modifiers

Discussions modifiers can modify a discussion completion (e.g. adding messages, modifying some of them, specifying current time, adding tools). 

---

Made with ❤️ by Kaki In. 
