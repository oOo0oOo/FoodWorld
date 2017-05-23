from copy import deepcopy
from random import choice

from flask import render_template
from flask_ask import statement, question, session

from . import alexa, db
from .utils.recipes import find_recipes, all_recipes
from .dialog import reply, recipe_card
from .models import User


#####
#
# Helpers for long-term session persistence
#
####

def load_state(user):
    '''
        Loads the current state from the DB and sets session.attributes
    '''
    for k, v in user.state_machine.items():
        session.attributes[k] = v

    # Check if the session is correctly loaded...
    all_keys = session.attributes.keys()
    for k in ['state','ingredient_list','recipe_list','recipe','step','confirm_for_restart']:
        if k not in all_keys:
            break
    else:
        return True

    return False


def save_state(user):
    '''
        Save the current state to the DB
    '''
    if session.attributes.get('state', False):
        user.state_machine = deepcopy(dict(session.attributes))


def reset_state():
    session.attributes['state'] = 'ingredients'
    session.attributes['ingredient_list'] = []
    session.attributes['recipe_list'] = []
    session.attributes['recipe'] = -1
    session.attributes['step'] = 0 # Step is used both during prepare and cook to keep track of the current step
    session.attributes['confirm_for_restart'] = False # Need to roll our own confirmation dialog...


def start_session():
    '''
        This starts or resumes a previous session.
        Typically happens when the user (re-)enters the skill.
    '''
    user_id = session.user['userId']
    user = User.query.get(user_id)

    # Complete reset only if new user
    if user == None:
        reset_state()

        # Create new user and save state
        user = User(user_id = user_id)
        db.session.add(user)
        save_state(user)

    # Resume from last time
    else:
        user.update_online()
        success = load_state(user)

        # If something is not ok, reset everything...
        if not success:
            reset_state()
            save_state(user)

    db.session.commit()


#####
#
# The standard events
#
#####

@alexa.launch
def launched():
    # Start session if not already done
    if not session.attributes.get('state', False):
        print 'Todo: Investigate why this happens'
        start_session()

    if session.attributes['state'] == 'ingredients':
        answer = '''
            Welcome to food world! Discover exciting new recipes!
            First add some ingredients you want to use. For example: alexa, add {}.
        '''
        answer = answer.format(choice(['tomatoes', 'potatoes', 'flour', 'coconut', 'avocado']))
        return question(answer)
    else:
        answer = u'Welcome back to food world! Let\'s continue where we left off. '
        answer += u'You can restart any time using: alexa, restart. ' + reply()

        # Resume, also send card if recipe is selected
        if session.attributes['recipe'] == -1:
            return question(answer)
        else:
            return question(answer).simple_card(**recipe_card())


@alexa.on_session_started
def new_session():
    '''
        Reset the state. (we start by selecting ingredients)
    '''
    # Start session if not already done
    if not session.attributes.get('state'):
        start_session()


@alexa.intent('AMAZON.HelpIntent')
def help():
    helping = '''
        Food world let\'s you discover recipes from all over the world!
        You can add ingredients using for example: alexa, add eggs.
        You can also search for recipes using: alexa, search recipes.
    '''
    return question(helping)


@alexa.intent('AMAZON.CancelIntent')
def cancel():
    user = User.query.get(session.user['userId'])
    save_state(user)
    db.session.commit()
    return statement('Thanks for using food world!')


@alexa.intent('AMAZON.StopIntent')
def stop():
    user = User.query.get(session.user['userId'])
    save_state(user)
    db.session.commit()
    return statement('Thanks for using food world!')


@alexa.session_ended
def session_ended():
    user = User.query.get(session.user['userId'])
    save_state(user)
    db.session.commit()
    return statement('Thanks for using food world!')


#####
#
# Events tightly bound to the state machine:
# ingredient -> search -> prepare -> cook
#
# Session variables:
# status                the current status (e.g. search)
# step                  relevant for keeping track of ingredient and cooking steps
# ingredient_list           all the ingredients the user wants to cook with
# recipe                the selected recipe
# recipe_list           in search we only calculate recipes once
#
#####

@alexa.intent('YesIntent')
def confirm():
    '''
        "Let's start", "Yes", "Here we go!"

        Confirm a question
        Used in search, prepare and cook
    '''
    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes
    state = sess.get('state')

    if not state:
        pass

    # User says yes to reset, we reset.
    elif sess['confirm_for_restart']:
        reset_state()

    # Update the state machine
    elif state == 'ingredients':
        pass

    # Yes to recipe = start preparing (listing amounts)
    elif state == 'search':
        sess['state'] = 'prepare'
        sess['step'] = 0

    # Check all the ingredients
    elif state == 'prepare':
        recipe = all_recipes[sess['recipe']]

        # Advance among the list of ingredients
        # Reply() will handle if less than three are left...
        max_step = len(recipe[1][0]) - 1

        # Done with all the ingredients
        if sess['step'] + 4 >= max_step:
            sess['state'] = 'cook'
            sess['step'] = 0

        # Some more left to show
        else:
            sess['step'] += 4

    else:
        return question('Ok with me...')

    return question(reply())


@alexa.intent('NoIntent')
def deny():
    '''
        "No." "Never." "This sounds awful."

        Deny a question
        Used in search and prepare
    '''
    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes
    state = sess.get('state')

    # A card is sent if a new recipe is displayed
    send_card = False

    if not state:
        pass

    # No to reset: proceed as usual
    elif sess['confirm_for_restart']:
        sess['confirm_for_restart'] = False

    # Update the state machine
    elif state == 'ingredients':
        pass

    # No in search = move to next recipe
    # No in prepare = also move to next recipe
    elif state in ('search', 'prepare'):
        next = (sess['recipe_list'].index(sess['recipe']) + 1) % len(sess['recipe_list'])
        sess['recipe'] = sess['recipe_list'][next]

        # Needed for prepare
        sess['state'] = 'search'
        send_card = True

    else:
        return question('Ok with me...')

    if not send_card:
        return question(reply())
    else:
        return question(reply()).simple_card(**recipe_card())


@alexa.intent('RepeatIntent')
def repeat():
    '''
        "Can you repeat that?"

        Repeat the last statement.
        Used in search, prepare and cook.
    '''
    if not session.attributes.get('state', False):
        start_session()

    # The simplest of them all, no changes to state machine = same result:)
    return question(reply())


@alexa.intent('PreviousIntent')
def back():
    '''
        "Can we go back to the last step?"

        Used in cook or search
    '''
    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes
    state = sess['state']

    # Previous in cook
    if state == 'cook':
        recipe = all_recipes[sess['recipe']]

        if sess['step'] > 0:
            sess['step'] -= 1

    # Previous in prepare
    elif state == 'prepare':
        recipe = all_recipes[sess['recipe']]
        sess['step'] -= 4
        if sess['step'] < 0:
            sess['step'] = 0

    # Previous in search
    elif state == 'search':
        next = (sess['recipe_list'].index(sess['recipe']) - 1) % len(sess['recipe_list'])
        sess['recipe'] = sess['recipe_list'][next]

    else:
        return question('Fine with me!')

    return question(reply())


@alexa.intent('NextIntent')
def next():
    '''
        "next step"
    '''
    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes
    state = sess['state']

    if state == 'cook':
        recipe = all_recipes[sess['recipe']]
        sess['step'] += 1

        # Finished cooking (app & session ends)
        if sess['step'] >= len(recipe[2]):
            # We reset the state and save it
            reset_state()
            save_state(User.query.get(session.user['userId']))
            db.session.commit()

            answer = u'Your done preparing {}! Thanks for using food world and enjoy your meal!'.format(recipe[0])
            return statement(answer)

    # Next in search = new recipe
    elif state == 'search':
        next = (sess['recipe_list'].index(sess['recipe']) + 1) % len(sess['recipe_list'])
        sess['recipe'] = sess['recipe_list'][next]

    else:
        return question('Fine with me!')

    return question(reply())


@alexa.intent('AddIntent')
def add_ingredient(ingredient):
    '''
        "I want to use ..."

        User specifies ingredients to be used in recipe.
    '''
    if ingredient is None:
        return question('Please specify an ingredient, for example: alexa, add parsley.')

    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes

    # Add ingredient to ingredient_list
    if ingredient not in sess['ingredient_list']:
        sess['ingredient_list'].append(ingredient)
        prefix = u'Added ' + ingredient + u'. '

        # Go back to the adding stage
        sess['state'] = 'ingredients'
    else:
        prefix = ingredient + u' is already on the ingredient list. '

    return question(prefix + reply())


@alexa.intent('RemoveIntent')
def remove_ingredient(ingredient):
    '''
        "I want to remove ..."

        Remove ingredients from the ingredient list
    '''
    if ingredient is None:
        return question('Please specify an ingredient, for example: alexa, remove coconut.')

    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes

    # Add ingredient to ingredient_list
    if ingredient not in sess['ingredient_list']:
        prefix = ingredient + u' is not on the ingredient list. '

    else:
        sess['ingredient_list'].remove(ingredient)
        prefix = u'Remove ' + ingredient + u' from the ingredient list. '

    return question(prefix + reply())


@alexa.intent('SearchIntent')
def search():
    '''
        "Search recipes"

        Based on previously collected ingredient list
    '''
    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes
    state = sess.get('state')

    if not state:
        return question(reply())

    # Search for recipes
    if len(sess['ingredient_list']) > 0:
        # Search for recipes
        recipes = find_recipes(sess['ingredient_list'])

        if recipes:
            # Update the state machine
            sess['state'] = 'search'
            sess['recipe_list'] = recipes
            sess['recipe'] = recipes[0]

        else:
            answer = u'Could not find a recipe. Try removing an ingredient, your current list is: '
            answer += u', '.join(sess['ingredient_list'][:-1]) + u' and ' + sess['ingredient_list'][-1]
            return question(answer)

    else:
        return question(u'I need at least one ingredient. Add ingredients using for example: alexa, add marshmallows.')

    return question(reply()).simple_card(**recipe_card())


#####
#
# More general purpose intents
#
#####

@alexa.intent('ClarificationIntent')
def clarification(ingredient):
    '''
        "How many eggs did i need again?"
    '''
    if ingredient is None:
        return question('Please specify an ingredient, for example: alexa, how much bread did i need?')

    if not session.attributes.get('state', False):
        start_session()

    sess = session.attributes
    recipe = all_recipes[sess['recipe']]

    for line in recipe[1][0]:
        if ingredient in line:
            answer = u'You need ' + line + u'. Repeat the last step using: alexa, repeat.'
            break
    else:
        answer = u'Could not find any {} in this recipe.'.format(ingredient)

    return question(answer)


@alexa.intent('RestartIntent')
def restart():
    '''
        "Let's start from the top."

        We need to implement our own confirmation bc its only available in Builder Beta:(
    '''
    if not session.attributes.get('state', False):
        start_session()

    session.attributes['confirm_for_restart'] = True
    return question('Restarting ends the current recipe and resets the ingredients. Are you sure?')