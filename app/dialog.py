from flask_ask import session

from .utils.recipes import all_recipes


def reply():
    '''
        Reply renders a response based on the current state.
        All information should be contained within the session object.

        This function does NOT update the state in any way!
    '''
    sess = session.attributes
    state = sess.get('state')
    if not state:
        answer = u'Please restart the app!'

    elif state == 'ingredients':
        answer = u'Add more ingredients or search for recipes.'

    elif state == 'search':
        recipe = all_recipes[sess['recipe']]
        answer = u''
        if sess['recipe'] == sess['recipe_list'][0]:
            answer = u'Found {} recipes. '.format(len(sess['recipe_list']))

        answer += u'Do you want to cook {}?'.format(recipe[0])
        if recipe[3]:
            answer += u' It\'s a {}.'.format(recipe[3])

    # Prepare lists up to 3 lines of ingredients
    # for the user to check whether he has them.
    elif state == 'prepare':
        step = sess['step']
        recipe = all_recipes[sess['recipe']]
        ingredients = recipe[1][0][step:step+4]

        answer = u''
        if step == 0:
            answer = u'This recipe requires the following {} ingredients: '.format(len(recipe[1][0]))
        else:
            answer = u'Next you\'ll need '

        if len(ingredients) > 1:
            answer += u', '.join(ingredients[:-1])
            answer += u' and ' + ingredients[-1]
        elif len(ingredients) == 1:
            answer += ingredients[0]
        else:
            print ingredients
            print 'whyyy?'
            return 'Are you ready to cook?'

        answer += u'. Do you have these ingredients?'

    # Cook walks through the cooking instructions
    elif state == 'cook':
        step = sess['step']
        recipe = all_recipes[sess['recipe']]

        if step == 0:
            answer = u'Let\'s get started! '
        else:
            answer = u''
        answer += u' Step {}: '.format(step+1)
        answer += recipe[2][step]

        # Need instructions
        answer += '. When you\'re done use: alexa, next.'


    return answer.encode('utf-8')


def recipe_card():
    recipe = all_recipes[session.attributes['recipe']]

    text = u'INGREDIENTS'
    text += u'\n'.join([r.capitalize() + '.' for r in recipe[1][0]])
    text += u'\nDIRECTIONS'
    text += u'\n'.join([r.capitalize() + '.' for r in recipe[2]])

    if recipe[5]:
        text += u'\nSubmitted by {} on recipes.wikia.com.'.format(recipe[5])
    else:
        text += u'Recipe from recipes.wikia.com.'

    return {'title': recipe[0], 'content': text}