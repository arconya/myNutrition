from urllib.parse import quote_plus
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

class User:
    def __init__(self, id):
        self.id = id
        self.collection = None

        # Load environment variables
        self.MONGO_DB_KEY = os.environ.get("MONGO_DB_KEY")
        self.USERNAME = "annchristin_db_user"

        # ------------------------------------------------------------------
        # Configure and connect to MongoDB
        # ------------------------------------------------------------------
        try:
            # URL-encode credentials to avoid InvalidURI errors
            username_encoded = quote_plus(self.USERNAME)
            password_encoded = quote_plus(self.MONGO_DB_KEY)

            uri = f"mongodb+srv://{username_encoded}:{password_encoded}@arconya.347ydq4.mongodb.net/?appName=Arconya"

            # Create a new client and connect to the server
            client = MongoClient(uri, server_api=ServerApi("1"))

            db = client.myNutrition

            client.admin.command("ping")
            print("Connected to MongoDB!")

            self.collection = db.user_data

            data = self.collection.find_one({"_id": self.id})

            if not data:
                element = {"_id": self.id}
                self.collection.insert_one(element)
        except Exception as e:
            print(e)

    """Update user data in the database. data is a dictionary in the following jason format:
    {"Vegetarian": True, "first Name": "Andrew", "last name": "Chen", "age": 25, "gender": "male", "vegan": False, "disliked ingredients": ["banana", "onion"]}
    Available fields are: "vegetarian", "first Name", "last Name", "age", "gender", "vegan", "disliked ingredients"
    """
    def update_user_data(self, data):
        if self.collection is None:
            raise RuntimeError("MongoDB collection is not available.")

        query = {"_id": self.id}
        new_values = {"$set": data}
        self.collection.update_one(query, new_values)

    # delete user data
    def delete_user_data(self):
        if self.collection is None:
            raise RuntimeError("MongoDB collection is not available.")

        query = {"_id": self.id}

        self.collection.delete_one(query)
        self.collection.insert_one(query)

    # get all user data
    def get_user_data(self):
        if self.collection is None:
            raise RuntimeError("MongoDB collection is not available.")

        data = self.collection.find_one(
            {"_id": self.id},
        )
        return data

        # parameters is a dictionary like {"first name": 1, "last name": 1}
    def get_filtered_user_data(self, parameters):
        if self.collection is None:
            raise RuntimeError("MongoDB collection is not available.")

        if type(parameters) is dict:
            parameters["_id"] = 0
        else:
            return self.collection.find_one({"_id": self.id})

        data = self.collection.find_one(
            {"_id": self.id},
            parameters
        )
        return data