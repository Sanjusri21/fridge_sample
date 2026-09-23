"""
Recipe Knowledge Base for ALINA.
Maps common fridge ingredients to practical recipes.
"""

from typing import List, Dict

RECIPE_DATABASE: Dict[str, List[str]] = {
    "chicken": [
        "Chicken rice",
        "Chicken curry",
        "Chicken noodles",
        "Grilled chicken salad",
        "Chicken stir fry"
    ],
    "egg": [
        "Omelette",
        "Egg fried rice",
        "Egg sandwich",
        "Scrambled eggs on toast",
        "Boiled egg salad"
    ],
    "eggs": [
        "Omelette",
        "Egg fried rice",
        "Egg sandwich",
        "Scrambled eggs on toast"
    ],
    "milk": [
        "Pancakes",
        "Fruit milkshake",
        "Oatmeal porridge",
        "Hot cocoa",
        "Creamy soup"
    ],
    "cheese": [
        "Grilled cheese sandwich",
        "Cheese pasta",
        "Cheesy baked potatoes",
        "Cheesy omelette"
    ],
    "apple": [
        "Apple cinnamon oatmeal",
        "Fresh apple & walnut salad",
        "Baked spiced apples",
        "Apple smoothie"
    ],
    "apples": [
        "Apple cinnamon oatmeal",
        "Fresh apple & walnut salad",
        "Baked spiced apples"
    ],
    "bread": [
        "French toast",
        "Garlic herb toast",
        "Crispy bread croutons",
        "Club sandwich"
    ],
    "rice": [
        "Vegetable fried rice",
        "Rice bowl with protein",
        "Garlic butter rice",
        "Rice pudding"
    ],
    "fish": [
        "Pan-seared fish fillets",
        "Fish curry",
        "Fish tacos",
        "Baked herb fish"
    ],
    "vegetables": [
        "Rainbow stir-fry veggies",
        "Hearty vegetable soup",
        "Roasted vegetables bowl",
        "Vegetable pasta"
    ],
    "curd": [
        "Seasoned curd rice",
        "Fruit raita",
        "Refreshing buttermilk"
    ],
    "yogurt": [
        "Berry yogurt parfait",
        "Yogurt dip with herbs",
        "Fruit smoothie bowl"
    ]
}


def get_recipes_for_ingredient(ingredient_name: str) -> List[str]:
    """Retrieves list of recipes matching ingredient name or normalized key."""
    key = ingredient_name.strip().lower()
    if key in RECIPE_DATABASE:
        return RECIPE_DATABASE[key]

    for k, recipes in RECIPE_DATABASE.items():
        if k in key or key in k:
            return recipes

    return []
