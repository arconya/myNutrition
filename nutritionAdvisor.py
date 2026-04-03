from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings
import sys
import os
import json
from recipes import Recipies
from user import User
from langchain.agents import create_agent

class NutritionAdvisor:

    def __init__(self, model, u_id):
        self.model = model
        self.u_id = u_id

        self.count_input_tokens = 0
        self.count_output_tokens = 0
        self.count_cached_tokens = 0

        self.price_input_tokens = 0.00000151
        self.price_output_tokens = 0.00000015
        self.price_cached_tokens = .00001208

        self.SYSTEM_PROMPT = self.get_system_prompt()
        self.THREAD_ID = "conversation-1"

        self.checkpointer = InMemorySaver()     # Create checkpointer for memory
        self.config = {"configurable": {"thread_id": self.THREAD_ID}}     # Use the agent with thread-based memory

        # Load and set environment variables
        self.CHROMA_DB_KEY = os.environ.get("CHROMA_DB_KEY")
        self.COLLECTION_NAME = "nutrition_knowledge_base_test"
        self.OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        os.environ["USER_AGENT"] = "NutritionAdvisor/0.8"

        self.recipies = Recipies(model)
        self.user = User(u_id)

        # ------------------------------------------------------------------
        # Configure and connect to ChromaDB
        # ------------------------------------------------------------------
        settings = Settings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials = self.CHROMA_DB_KEY
        )

        try:
            self.client = chromadb.HttpClient(
                host="localhost",
                port=8000,
                settings=settings
            )
            self.client.heartbeat()
            print("Successfully connected to ChromaDB.")
        except Exception as e:
            print(f"Error: Could not connect to ChromaDB: {e}")
            print("Please make sure the ChromaDB server is running.")
            sys.exit(1)

        # ------------------------------------------------------------------
        # Initialize embeddings
        # ------------------------------------------------------------------
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=self.OPENAI_API_KEY,
        )

        # ------------------------------------------------------------------
        # Check if collection already exists, skip init if it does
        # ------------------------------------------------------------------
        #self.client.delete_collection(name=self.COLLECTION_NAME)
        existing_collections = [col.name for col in self.client.list_collections()]

        if self.COLLECTION_NAME not in existing_collections:
            print(f"Collection '{self.COLLECTION_NAME}' not found. Running initialization...")
            self.vector_store = self.initialize()
        else:
            print(f"Collection '{self.COLLECTION_NAME}' already exists. Skipping initialization.")
            self.vector_store = Chroma(
                collection_name=self.COLLECTION_NAME,
                embedding_function=self.embeddings,
                client=self.client
            )

        # ------------------------------------------------------------------
        # Define tools correctly as closures, not instance methods
        # ------------------------------------------------------------------
        @tool
        def update_user_first_name(first_name: str):
            """Update the user's first name in the database."""
            self.user.update_user_data({"first Name": first_name})
            return f"Updated first name to {first_name}"

        @tool
        def update_user_last_name(last_name: str):
            """Update the user's last name in the database."""
            self.user.update_user_data({"last Name": last_name})
            return f"Updated last name to {last_name}"

        @tool
        def update_user_age(age: int):
            """Update the user's age in the database."""
            self.user.update_user_data({"age": age})
            return f"Updated age to {age}"

        @tool
        def update_user_gender(gender: str):
            """Update the user's gender in the database."""
            self.user.update_user_data({"gender": gender})
            return f"Updated gender to {gender}"

        @tool
        def update_user_vegetarian(vegetarian: bool):
            """Update the user's vegetarian preference in the database."""
            self.user.update_user_data({"vegetarian": vegetarian})
            return f"Updated vegetarian preference to {vegetarian}"

        @tool
        def update_user_vegan(vegan: bool):
            """Update the user's vegan preference in the database."""
            self.user.update_user_data({"vegan": vegan})
            return f"Updated vegan preference to {vegan}"

        @tool
        def update_user_disliked_ingredients(disliked_ingredients: list):
            """Update the user's disliked ingredients in the database. Make sure to pass all ingredients in singular form!"""
            self.user.update_user_data({"disliked ingredients": disliked_ingredients})
            return f"Updated disliked ingredients to {disliked_ingredients}"

        @tool
        def get_user_data():
            """Get user data from the database."""
            data = self.user.get_user_data()
            return json.dumps(data, default=str)

        @tool
        def delete_user_data():
            """Delete all user data from the database."""
            data = self.user.delete_user_data()
            return "All user data deleted successfully."

        @tool
        def find_recipe():
            """Find a recipe based on user preferences."""
            parameters = self.user.get_filtered_user_data(
                {"vegetarian": 1, "vegan": 1, "disliked ingredients": 1}
            )
            recipe = self.recipies.find_recipe(parameters)
            return json.dumps(recipe, default=str)

        self.tools = [
            update_user_first_name,
            update_user_last_name,
            update_user_age,
            update_user_gender,
            update_user_vegetarian,
            update_user_vegan,
            update_user_disliked_ingredients,
            get_user_data,
            delete_user_data,
            find_recipe,
        ]

        # ------------------------------------------------------------------
        # Create agent
        # ------------------------------------------------------------------
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.SYSTEM_PROMPT,
            checkpointer=self.checkpointer,
        )

    # Load documents from URLs and WHO PDF and store them in ChromaDB.
    def initialize(self) -> Chroma:
        urls = self.load_urls_from_file("Data/resource_urls.txt")
        print(f"Loaded {len(urls)} URLs.")

        loader = WebBaseLoader(
            web_paths=urls,
            #bs_kwargs={"parse_only": bs4_strainer},
            header_template={'User-Agent': 'NutritionAdvisor/1.0'}
        )
        docs = list(loader.lazy_load())
        print(f"Fetched {len(docs)} documents.")

        #response = self.model.invoke(f"please write 50 questions that can be answered with the following content: '{str(docs)}' each question should be seperated by a new line.")
        #with open("urls_questions.txt", "a") as f:
        #    f.write(response.content)

        pdf_loader = PDFMinerLoader(
            file_path="./Data/WHO.pdf",
            mode="single",
            pages_delimiter = ''
        )
        pdfs = list(pdf_loader.lazy_load())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(pdfs)

        for chunk in chunks:
            chunk.metadata["source"] = "WHO: 'Vitamin and mineral requirements in human nutrition', Second edition, 2004: https://www.who.int/publications/i/item/9241546123"
        print(f"Split into {len(chunks)} chunks.")
        docs.extend(chunks)

        store = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            collection_name=self.COLLECTION_NAME,
            client=self.client
        )
        print("Vector store initialized and documents stored successfully.")
        return store

    @staticmethod
    def load_urls_from_file(filepath: str) -> list[str]:
        urls = []
        with open(filepath) as f:
            for line in f:
                url = line.strip()
                if url and url.startswith("http"):
                    urls.append(url)
        return urls

    @staticmethod
    def get_system_prompt():
        try:
            with open("Data/systemPrompt.txt", "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError("Error: System prompt file not found.")

    def context_necessary(self, query: str) -> bool:
        systemprompt = f"""You area professional evaluator. Is the following question nutrition or health related? Answer with yes or no. Question: {query}"""
        response = self.model.invoke(systemprompt)
        print(response.content.lower() != "no")
        if response.content.lower() == "no":
            return False
        return True

    def get_response(self, query: str, context: str = None):
        query = str(query)
        if context or self.context_necessary(query):
            if not context:
                context = self.get_context(query)

            prompt = f"""
    Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.
    <context>{context}</context>
    <question>{query}</question>
    """
        else:
            prompt = query
        message = {"messages": [{"role": "user", "content": prompt}]}
        response = self.agent.invoke(message, config=self.config)
        return response["messages"][-1].content

    def get_response_stream(self, query: str):
        context = self.get_context(query)
        prompt = f"""
Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.
<context>{context}</context>
<question>{query}</question>
"""
        message = {"messages": [{"role": "user", "content": prompt}]}

        full_content = ""
        for chunk in self.agent.stream(message, config=self.config):
            if "messages" in chunk:
                msg = chunk["messages"][-1]
                if hasattr(msg, "content") and msg.content:
                    new_content = msg.content[len(full_content):]
                    full_content = msg.content
                    if new_content:
                        yield new_content

    def get_context(self, query: str):
        query = str(query)
        results = self.vector_store.similarity_search(query, k=5)

        context = "\n"
        for doc in results:
            source = doc.metadata.get("source", "N/A")
            context += f"### {doc.page_content} FROM SOURCE: {source}"
        return context

    def clear_history(self):
        self.checkpointer.delete_thread(thread_id=self.THREAD_ID)
