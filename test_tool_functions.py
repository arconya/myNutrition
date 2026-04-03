import pprint
from recipes import Recipies
from user import User
import os
from langchain.chat_models import init_chat_model
from nutritionAdvisor import NutritionAdvisor

# ------------------------------------------------------------------
# Initialize LLM model
# ------------------------------------------------------------------

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
id = "gpt-4o-mini"
model = init_chat_model(id)

def test_nutrition_advisor():
    """Test function that calls all functions in NutritionAdvisor class"""
    myNutrition = NutritionAdvisor(model, "1")


def test_set_user_data():
    """Test function that calls all set user data functions with certain values"""
    # Create a test user with a test ID
    test_user = User(id=9999)

    test_data = {
        "vegetarian": True,
        "first Name": "John",
        "last Name": "Doe",
        "age": 30,
        "gender": "male",
        "vegan": False,
        "disliked ingredients": ["banana", "onion", "cilantro"]
    }

    # Test setting vegetarian preference
    test_user.update_user_data({"vegetarian": test_data["vegetarian"]})
    print("Set vegetarian: True")

    # Test setting first name
    test_user.update_user_data({"first Name": test_data["first Name"]})
    print("Set first Name: John")

    # Test setting last name
    test_user.update_user_data({"last Name": test_data["last Name"]})
    print("Set last Name: Doe")

    # Test setting age
    test_user.update_user_data({"age": test_data["age"]})
    print("Set age: 30")

    # Test setting gender
    test_user.update_user_data({"gender": test_data["gender"]})
    print("Set gender: male")

    # Test setting vegan preference
    test_user.update_user_data({"vegan": test_data["vegan"]})
    print("Set vegan: False")

    # Test setting disliked ingredients
    test_user.update_user_data({"disliked ingredients": test_data["disliked ingredients"]})
    print("Set disliked ingredients: ['banana', 'onion', 'cilantro']")

    # Test setting multiple fields at once
    test_user2 = User(id=2)
    test_data2 = {
        "vegetarian": True,
        "first Name": "Jane",
        "last Name": "Smith",
        "age": 28,
        "gender": "female",
        "vegan": True,
        "disliked ingredients": ["mushrooms", "olives"]
    }
    test_user2.update_user_data(test_data2)
    print("Set multiple fields at once")

    print("\nAll set user data functions called successfully!")

    data = test_user.get_filtered_user_data({"vegetarian": 1, "vegan": 1, "disliked ingredients": 1})
    pprint.pp(data)
    data2 =test_user2.get_filtered_user_data({"vegetarian": 1, "vegan": 1, "disliked ingredients": 1})
    pprint.pp(data2)

    if test_data["disliked ingredients"] == data["disliked ingredients"] \
            and test_data["vegan"] == data["vegan"] \
            and test_data["vegetarian"] == data["vegetarian"]:
        print("user data of test user 1 correctly persisted")
    else:
        print("ERROR: user data of test user 1 not persisted correctly")

    if test_data2["disliked ingredients"] == data2["disliked ingredients"]\
            and test_data2["vegan"] == data2["vegan"]\
            and test_data2["vegetarian"] == data2["vegetarian"]:
        print("user data of test user 2 correctly persisted")
    else:
        print("ERROR: user data of test user 2 not persisted correctly")

def test_find_recipe():
    recipies = Recipies(None)

    print("\n--- Testing find_recipe with no parameters (any recipe) ---")
    print(recipies.find_recipe({}))

    print("\n--- Testing find_recipe with vegan=True and disliked ingredients=['tomato'] ---")
    print(recipies.find_recipe({"vegan": True, "disliked ingredients": ["tomato"]}))

    print("\n--- Testing find_recipe with vegetarian=True ---")
    print(recipies.find_recipe({"vegetarian": True}))

    print("\n--- Testing find_recipe with vegan=True ---")
    print(recipies.find_recipe({"vegan": True}))

    print("\n--- Testing find_recipe with disliked ingredients=['onion', 'cheese'] ---")
    print(recipies.find_recipe({"disliked ingredients": ["onion", "cheese"]}))

    print("\n--- Testing find_recipe with vegan=True, vegetarian=True, and disliked ingredients=['tomato', 'onion'] ---")
    print(recipies.find_recipe({"vegan": True, "vegetarian": True, "disliked ingredients": ["tomato", "onion"]}))

    print("\n--- Testing find_recipe with vegan=True and vegetarian=False ---")
    print(recipies.find_recipe({"vegan": True, "vegetarian": False}))

    print("\n--- Testing find_recipe with vegan=False and vegetarian=True ---")
    print(recipies.find_recipe({"vegan": False, "vegetarian": True}))

    print("\n--- Testing find_recipe with vegan=True and vegetarian=True ---")
    print(recipies.find_recipe({"vegan": True, "vegetarian": True}))


if __name__ == "__main__":
    test_set_user_data()
    test_find_recipe()