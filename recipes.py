import random
from urllib.parse import quote_plus
from langchain_core.messages import SystemMessage, HumanMessage
from pymongo.server_api import ServerApi
from pymongo import MongoClient, InsertOne
import json
import os


class Recipies:
    def __init__(self, model):
        self.model = model

        # load environment variables
        MONGO_DB_KEY = os.environ.get("MONGO_DB_KEY")
        USERNAME = "annchristin_db_user"

        if not MONGO_DB_KEY:
            raise RuntimeError("No environment variable 'MONGO_DB_KEY' set.")

        try:
            username_encoded = quote_plus(USERNAME)
            password_encoded = quote_plus(MONGO_DB_KEY)

            uri = f"mongodb+srv://{username_encoded}:{password_encoded}@arconya.347ydq4.mongodb.net/?appName=Arconya"

            client = MongoClient(uri, server_api=ServerApi("1"))
            db = client.myNutrition
            client.admin.command("ping")
            print("Connected to MongoDB!")

            collist = db.list_collection_names()
            #print(collist)

            self.collection = db.recipies
            self.collection_eng = db.recipies_eng

            if "recipies" not in collist:
                with open("Data/chefkochRecipies100.txt", "r", encoding="utf-8") as file:
                    recipies = json.load(file)

                requesting = []
                requesting_eng = []
                count = len(recipies)
                count_eng = 0

                for recipe in recipies:
                    requesting.append(InsertOne(recipe))
                    #pprint.pp(recipe)

                    try:
                        recipe_eng = json.loads(self.translate(recipe))
                        recipe_eng["tags"] = recipe["tags"]
                        requesting_eng.append(InsertOne(recipe_eng))
                        count_eng += 1
                    except Exception as e:
                        print(e)

                self.collection.bulk_write(requesting)
                self.collection_eng.bulk_write(requesting_eng)

                print(f"{count} German recipies added to recipe database.")
                print(f"{count_eng} English recipies added to recipe_eng database.")

        except Exception as e:
            print(e)

    # parameters may contain: "vegetarian", "vegan", "disliked ingredients"
    def find_recipe(self, parameters):
        if not parameters:
            return self.collection_eng.find_one()

        query_parts = []

        vegetarian = parameters.get("vegetarian")
        if vegetarian is True:
            query_parts.append({"tags": "vegetarisch"})

        vegan = parameters.get("vegan")
        if vegan is True:
            query_parts.append({"tags": "vegan"})

        disliked_ingredients = parameters.get("disliked ingredients")
        if disliked_ingredients:
            disliked = "|".join(disliked_ingredients)
            query_parts.append(
                {"ingredients.name": {"$not": {"$regex": f"(?i){disliked}"}}}
            )

        if not query_parts:
            cursor = self.collection_eng.find()
        elif len(query_parts) == 1:
            cursor = self.collection_eng.find(query_parts[0])
        else:
            myquery = {"$and": query_parts}
            cursor = self.collection_eng.find(myquery)

        available_recipes = list(cursor)

        if len(available_recipes) == 0:
            return None
        elif len(available_recipes) == 1:
            return available_recipes[0]
        else:
            random_index = random.randint(0, len(available_recipes) - 1)
            return available_recipes[random_index]

    def translate(self, recipe, count=0):
        recipe_string = json.dumps(recipe)

        system_prompt = """
        you are a professional translator. you only answer with the translated sentence, even if it is already in english.
        please preserve the provided format including spaces and tabs. if you do not understand something, leave it as it is.
        Do not translate URLs. Keep them as a whole link. Evaluate whether all requirements are met before answering. Do not translate the "tags" values.

        Some examples how you translate:

        "n. B." becomes "to taste"
        "TL" becomes "tsp"
        "EL" becomes "tbsp"

        Please translate to english:
        """

        messages = [SystemMessage(system_prompt), HumanMessage(recipe_string)]
        response = self.model.invoke(messages)
        recipe_eng = response.content

        return recipe_eng

