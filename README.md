# FoodWorld
An Alexa skill to help you cooking based on ingredients you want to use.

Try the skill here: [https://www.amazon.com/Oliver-Dressler-Food-World/dp/B0728825YG/](https://www.amazon.com/Oliver-Dressler-Food-World/dp/B0728825YG/)

Food World uses a state machine to keep track of the complete conversation with alexa.
This also makes it quite easy to save and restore a session, since all information should be contained in the state machine. 
Further, I tried to separate manipulation and rendering of the state. In general, if you are following the normal conversation the answer is rendered using reply() in dialog.py. Exceptions and other additional information is "rendered" and returned directly.

The alexa/ folder contains the data used to setup the skill in the "store" (intents, utterances, logos and ingredients).

#### Running this code

This repository does **NOT** include the actual recipes file. This means you will have to provide your own recipes, which makes this tedious, sorry. I'm just not sure about the licensing & hope this is still useful as a reference.
The approx 25k recipes are scraped and cleaned from [recipes.wikia.com](recipes.wikia.com).

If you can provide your own recipes, install all the modules required (best in a venv):

`pip install flask flask_ask flask_sqlalchemy inflect`

Then create a new DB using:

`python manage.py createdb`

Finally run the flask server:

development: `python manage.py runserver`
or via gunicorn: `sh webserver/gunicorn.sh`

Don't forget that you will need to accept the requests via HTTPS (e.g. a tunnel using ngrok).
