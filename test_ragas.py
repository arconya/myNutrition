import pprint
import os
from langchain.chat_models import init_chat_model
from nutritionAdvisor import NutritionAdvisor
from ragas import EvaluationDataset, SingleTurnSample
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import AnswerRelevancy, Faithfulness
from langchain_openai import OpenAIEmbeddings as LCOpenAIEmbeddings

# ------------------------------------------------------------------
# Initialize LLM model
# ------------------------------------------------------------------

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
id = "gpt-5.2"
model = init_chat_model(id)

def test_nutrition_advisor():
    """Test function that calls all functions in NutritionAdvisor class"""
    myNutrition = NutritionAdvisor(model, "1")

    samples =[]

    with open("urls_questions.txt", "r") as f:
        for line in f:
            prompt = str(line)
            print(prompt)
            context = myNutrition.get_context(prompt)
            response = myNutrition.get_response(prompt, context)

            samples.append(SingleTurnSample(user_input=prompt, retrieved_contexts=[context], response=response))

    #with open("test_ragas.py", "a") as f:
    #    f.write(str(samples))

    pprint.pp(samples)
    dataset = EvaluationDataset(samples=samples)
    print(f"Created EvaluationDataset with {len(samples)} samples.")

    ragas_embeddings = LangchainEmbeddingsWrapper(LCOpenAIEmbeddings())

    metrics = [
        Faithfulness(llm=model),
        AnswerRelevancy(llm=model, embeddings=ragas_embeddings, strictness=1)
    ]

    print("Running RAGAs evaluation (this may take a minute)...")
    result = evaluate(dataset=dataset, metrics=metrics)

    print("=== Aggregate RAGAs Scores ===")
    print(result)

    df = result.to_pandas()

    display_cols = [
        "user_input",
        "faithfulness",
        "answer_relevancy",
    ]
    available_cols = [c for c in display_cols if c in df.columns]

    print("=== Per-Question Breakdown ===")
    print(df[available_cols].to_string(index=False))

    #{'faithfulness': 0.8445, 'answer_relevancy': 0.6954}

if __name__ == "__main__":
    test_nutrition_advisor()