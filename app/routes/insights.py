from fastapi import APIRouter

router = APIRouter()

@router.post("/insights/recommend")
def recommend_prompt():

    return {
        "baseline_score": 0.41,
        "recommendations": [
            {
                "variant": "Add example input/output",
                "predicted_score": 0.52
            },
            {
                "variant": "Add constraints",
                "predicted_score": 0.48
            }
        ]
    }