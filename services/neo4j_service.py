# services/neo4j_service.py
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

class Neo4jService:
    def __init__(self, uri, user, password, database):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database
        print(f"Neo4jService initialized for database: {database}")

    def close(self):
        if self._driver is not None:
            self._driver.close()
            print("Neo4j Driver closed.")

    def _execute_query(self, query, parameters=None):
        with self._driver.session(database=self._database) as session:
            results = session.run(query, parameters)
            return [record.data() for record in results]

    def get_recommended_recipes(self, recipe_name_query, category_query, mood_query):
        """
        根據菜名、分類、心情查詢推薦食譜列表 (聯集邏輯)。
        如果所有條件為空，則返回所有食譜。
        """
        params = {
            "recipeNameQuery": recipe_name_query if recipe_name_query else "",
            "categoryQuery": category_query if category_query else "",
            "moodQuery": mood_query if mood_query else ""
        }

        # --- 修正後的 Cypher 查詢 (移除了行內註解和錯誤的 WITH 子句) ---
        query = (
            "MATCH (r:Recipe) "
            "OPTIONAL MATCH (r)-[:BELONGS_TO_CATEGORY]->(c:Category) "
            "OPTIONAL MATCH (r)-[:SUITS_MOOD]->(m:Mood) "
            "WITH r, "
            "     collect(DISTINCT c.name) AS recipeCategories, "
            "     collect(DISTINCT m.name) AS recipeMoods "
            "WHERE "
            "    ($recipeNameQuery = '' AND $categoryQuery = '' AND $moodQuery = '') "
            "    OR "
            "    ( "
            "        ($recipeNameQuery <> '' AND r.name CONTAINS $recipeNameQuery) "
            "        OR ($categoryQuery <> '' AND $categoryQuery IN recipeCategories) "
            "        OR ($moodQuery <> '' AND $moodQuery IN recipeMoods) "
            "    ) "
            "RETURN DISTINCT r.name AS recipeName, "
            "       r.description_for_recommendation AS recommendationDescription, "
            "       r.difficulty_stars AS difficultyStars, "
            "       recipeMoods AS moods, "
            "       recipeCategories AS categories "
            "ORDER BY r.name "
            "LIMIT 20"
        )
        print(f"Executing UNION recommendation query with params: {params}")
        results = self._execute_query(query, params)
        print(f"Query results count: {len(results)}")
        return results

    def get_recipe_details(self, recipe_name):
        # 這是您提供的版本，保持不變
        params = {"recipeName": recipe_name}
        query = (
            "MATCH (r:Recipe {name: $recipeName}) "
            "RETURN "
            "    r.name AS recipeName, "
            "    r.difficulty_stars AS difficultyStars, "
            "    r.difficulty_text AS difficultyText, "
            "    r.required_items_text AS requiredItemsText, "
            "    r.calculations_text AS calculationsText, "
            "    r.notes_text AS notesText, "
            "    r.source_file AS sourceFile"
        )
        result = self._execute_query(query, params)
        return result[0] if result else None

    def get_recipe_steps(self, recipe_name):
        # 這是您提供的版本，保持不變
        params = {"recipeName": recipe_name}
        query = (
            "MATCH (r:Recipe {name: $recipeName})-[:FIRST_STEP]->(first_step:Step) "
            "MATCH path = (first_step)-[:NEXT_STEP*0..]->(any_step:Step) "
            "WITH any_step "
            "ORDER BY any_step.order ASC "
            "RETURN "
            "    any_step.order AS stepOrder, "
            "    any_step.instruction AS stepInstruction, "
            "    any_step.animationCue AS animationCue, "
            "    any_step.audioPathMandarin AS audioPathMandarin, "
            "    any_step.audioPathTaiwanese AS audioPathTaiwanese"
        )
        return self._execute_query(query, params)

# 建立 Neo4jService 的單一實例 (保持不變)
neo4j_service_instance = Neo4jService(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)

def close_neo4j_on_exit(): # 保持不變
    print("Closing Neo4j connection from neo4j_service...")
    neo4j_service_instance.close()
