import pickle
import random

import inflect

# The inflect engine (we use it to tunr plurals into singulars)
inflect_engine = inflect.engine()

# Load all 25k recipes; format:
# all_recipes = [
#   [
#       'title',
#       [
#           ['ingredients verbose 1', 'ingredient verbose 2'],
#           ['ingredient1', 'ingredient2']
#       ],
#       ['step1', 'step2'],
#       ['category1', 'category2'],
#       'country',
#       'username'
#   ],
#   ...
# ]
all_recipes = pickle.load(open('app/utils/recipes.pickle', 'r'))


def find_recipes(ingredients):
    '''
        Find all recipes which contain all ingredients
        returns: list of recipe indices
    '''
    # We want singulars (attention if this is changed need to change in data cleaning)
    ing = []
    for ingredient in ingredients:
        ingredient = ingredient.lower()

        # Ignored ingredients
        if ingredient in ('water', 'salt', 'pepper'):
            continue

        s = ingredient.split(' ')
        sing = inflect_engine.singular_noun(s[-1])
        if sing:
            if len(s) > 1:
                ing.append(' '.join(s[:-1] + [sing]))
            else:
                ing.append(sing)
        else:
            ing.append(ingredient)

    # Find recipes
    ingredients = set(ing)
    recipes = []
    for i, recipe in enumerate(all_recipes):
        if recipe[1][1].issuperset(ingredients):
            recipes.append(i)

    # Shuffle to give more random results
    random.shuffle(recipes)

    return recipes


def show_recipe(recipe):
    '''
        Simply print a recipe; only used for debugging...
    '''
    try:
        print recipe[0].title()
        if recipe[3]:
            print '\nCATEGORIES:'
            print ', '.join(recipe[3])
        print '\nINGREDIENTS (short):'
        print recipe[1][1]
        print '\nINGREDIENTS (full):'
        print '\n'.join([r.capitalize() + '.' for r in recipe[1][0]])
        print '\nDIRECTIONS (separated instructions):'
        print '\n'.join([r.capitalize() + '.' for r in recipe[2]])
    except:
        print '!!! Recipe contains non ascii chars...\n'


if __name__ == '__main__':
    import time

    ingredients = ['chicken', 'eggplant']

    before = time.time()
    n = 100
    for i in range(n):
        recipes = find_recipes(ingredients)

    duration = round((time.time() - before )/n, 1)
    print 'Found {} recipes, {} s per request'.format(len(recipes), duration)

    show_recipe(all_recipes[recipes[0]])